"""Standalone Kannada Parler-TTS worker invoked exclusively in .venv-tts.

Loads the local cached Parler model once per job, generates all audio segments
in sequence, writes mono PCM16 WAV files, and exits to free GPU memory.
"""
import argparse
import io
import json
import os
import sys
from pathlib import Path

# Ensure UTF-8 I/O on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

DEFAULT_MODEL = "ai4bharat/indic-parler-tts"
DEFAULT_DESCRIPTION = (
    "Anu speaks in a clear, moderate-paced, neutral tone with very clear "
    "audio quality and no background noise."
)


APPROVED_TECHNICAL_TOKENS = {
    "sin", "cos", "tan", "cot", "sec", "csc", "log", "ln", "exp", "lim",
    "max", "min", "det", "abs", "sqrt", "pi", "rad", "deg", "dx", "dt", "dy", "dz",
    "m", "s", "kg", "km", "cm", "mm", "ms", "hz", "khz", "mhz", "ghz",
    "pa", "kpa", "j", "kj", "w", "kw", "v", "mv", "a", "ma", "mol", "k", "db", "n", "ohm",
    "alice", "bob", "python", "dna", "rna", "atp", "adp", "ph",
    "def", "int", "str", "float", "bool", "len", "range", "print", "return",
    "for", "in", "if", "else", "elif", "while", "null", "true", "false",
    "none", "void", "class", "var", "let", "const",
}


def has_kannada_script(text: str) -> bool:
    return any(0x0C80 <= ord(c) <= 0x0CFF for c in text)


def is_exempt_technical_segment(text: str) -> bool:
    import re
    cleaned = text.strip()
    if not cleaned:
        return False
    words = re.findall(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b", cleaned)
    if not words:
        return True
    for word in words:
        w_lower = word.lower()
        if len(word) == 1 or w_lower in APPROVED_TECHNICAL_TOKENS or re.fullmatch(r"[A-Z][a-z]?\d*", word):
            continue
        return False
    return True


def run_job(job_path: Path) -> dict:
    if not job_path.is_file():
        raise FileNotFoundError(f"Job file not found: {job_path}")

    job_data = json.loads(job_path.read_text(encoding="utf-8"))

    language = job_data.get("language")
    if language != "kn":
        raise ValueError(f"Worker only supports language 'kn', got '{language}'")

    segments = job_data.get("segments", [])
    if not segments:
        raise ValueError("Job contains no segments to synthesize")

    # Validate all segments before loading heavy models
    for idx, seg in enumerate(segments):
        text = str(seg.get("text", "")).strip()
        if not text:
            raise ValueError(f"Segment {idx} has empty text")
        if not has_kannada_script(text) and not is_exempt_technical_segment(text):
            raise ValueError(f"Segment {idx} contains no Kannada script characters: '{text}'")
        out_path = Path(seg.get("output_path", ""))
        if not out_path.name.endswith(".wav"):
            raise ValueError(f"Segment {idx} invalid output path: '{out_path}'")

    model_id = job_data.get("model_id") or DEFAULT_MODEL
    description = job_data.get("description") or DEFAULT_DESCRIPTION

    import soundfile as sf
    import torch
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer

    device = os.environ.get("DEV", "cuda:0" if torch.cuda.is_available() else "cpu")
    dtype = torch.bfloat16 if str(device).startswith("cuda") else torch.float32

    model = ParlerTTSForConditionalGeneration.from_pretrained(
        model_id, torch_dtype=dtype, local_files_only=True
    ).to(device)
    model.eval()

    tok = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    desc_tok = AutoTokenizer.from_pretrained(
        model.config.text_encoder._name_or_path, local_files_only=True
    )

    d = desc_tok(description, return_tensors="pt").to(device)
    sr = int(model.config.sampling_rate)

    results = []
    for idx, seg in enumerate(segments):
        text = seg["text"].strip()
        out_path = Path(seg["output_path"]).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        p = tok(text, return_tensors="pt").to(device)
        with torch.no_grad():
            gen = model.generate(
                input_ids=d.input_ids,
                attention_mask=d.attention_mask,
                prompt_input_ids=p.input_ids,
                prompt_attention_mask=p.attention_mask,
            )
        audio = gen.float().cpu().numpy().squeeze()
        if len(audio) == 0:
            raise ValueError(f"Parler produced empty audio for segment {idx}")

        sf.write(str(out_path), audio, sr, subtype="PCM_16")

        frames = len(audio)
        results.append({
            "output_path": str(out_path),
            "frames": frames,
            "duration_seconds": round(frames / sr, 6),
            "sample_rate": sr,
        })

    return {"status": "ok", "sampling_rate": sr, "segments": results}


def main():
    parser = argparse.ArgumentParser(description="Kannada Parler TTS Worker")
    parser.add_argument("job_file", help="Path to JSON job specification")
    args = parser.parse_args()

    try:
        result = run_job(Path(args.job_file))
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    except Exception as exc:
        err = {"status": "error", "error": str(exc)}
        print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
