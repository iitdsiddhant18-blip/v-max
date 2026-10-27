"""Part 1b sample voices and sample-accurate timeline (no LLM/translation)."""
import hashlib
import json
import wave
from pathlib import Path
from typing import Callable, Literal

from .fallback import load_fallback_lesson
from .schema import Lesson

SampleLanguage = Literal["en", "hi"]
ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = ROOT / "backend" / "cache" / "part1b"
MODEL_PATH = ROOT / "models" / "kokoro-v1.0.onnx"
VOICES_PATH = ROOT / "models" / "voices-v1.0.bin"
PAUSE_SECONDS = 0.5
VOICE = {"en": ("hm_omega", "en-us"), "hi": ("hf_alpha", "hi")}
VERSION = "part1b-v1"


def sample_lesson(language: SampleLanguage) -> Lesson:
    if language == "en":
        return load_fallback_lesson()
    if language == "hi":
        return load_fallback_lesson("python_loop_hi")
    raise ValueError("Part 1b supports only en and hi")


def build_timeline(
    lesson: Lesson, language: SampleLanguage, audio_files: list[Path], combined_path: Path
) -> dict:
    """Concatenate mono PCM16 scene WAVs and 0.5 s silence, then return timings."""
    if language not in VOICE or lesson.language != language:
        raise ValueError("Timeline language must match the text language")
    if len(audio_files) != len(lesson.scenes):
        raise ValueError("There must be exactly one WAV per scene")
    sample_rate = None
    cursor_frames = 0
    timeline_scenes = []
    combined_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(combined_path), "wb") as joined:
        for index, (scene, path) in enumerate(zip(lesson.scenes, audio_files)):
            with wave.open(str(path), "rb") as source:
                if source.getnchannels() != 1 or source.getsampwidth() != 2 or source.getcomptype() != "NONE":
                    raise ValueError(f"Scene {index} WAV must be mono, PCM16, uncompressed")
                rate = source.getframerate()
                if sample_rate is None:
                    if rate <= 0:
                        raise ValueError("Invalid sample rate")
                    sample_rate = rate
                    joined.setnchannels(1)
                    joined.setsampwidth(2)
                    joined.setframerate(rate)
                elif rate != sample_rate:
                    raise ValueError("Scene WAVs have differing sample rates")
                frames = source.getnframes()
                if frames <= 0:
                    raise ValueError("TTS produced empty audio")
                audio_data = source.readframes(frames)
                if len(audio_data) != frames * 2:
                    raise ValueError("Truncated scene WAV")
            pause_frames = round(PAUSE_SECONDS * sample_rate)
            timeline_scenes.append({
                "index": index,
                "start_seconds": round(cursor_frames / sample_rate, 6),
                "audio_seconds": round(frames / sample_rate, 6),
                "duration_seconds": round((frames + pause_frames) / sample_rate, 6),
                "audio_url": f"/api/sample/media/{language}/scene_{index:02d}.wav",
            })
            joined.writeframesraw(audio_data)
            joined.writeframesraw(bytes(pause_frames * 2))
            cursor_frames += frames + pause_frames

    assert sample_rate is not None
    return {
        "language": language,
        "voice": VOICE[language][0],
        "sample_rate": sample_rate,
        "pause_seconds": PAUSE_SECONDS,
        "total_seconds": round(cursor_frames / sample_rate, 6),
        "audio_url": f"/api/sample/media/{language}/combined.wav",
        "lesson": lesson.model_dump(),
        "scenes": timeline_scenes,
    }


def prepare_sample(
    language: SampleLanguage,
    *,
    cache_root: Path = CACHE_ROOT,
    synthesize: Callable[[str, SampleLanguage, Path], None] | None = None,
) -> dict:
    """Prepare English or Hindi sample. Reuse cached WAV only for identical content/voice."""
    lesson = sample_lesson(language)
    folder = cache_root / language
    folder.mkdir(parents=True, exist_ok=True)
    signature = hashlib.sha256(
        json.dumps({"lesson": lesson.model_dump(), "voice": VOICE[language], "version": VERSION},
                   ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    wavs = [folder / f"scene_{i:02d}.wav" for i in range(len(lesson.scenes))]
    manifest_path = folder / "timeline.json"
    signature_path = folder / "signature.txt"
    combined_path = folder / "combined.wav"

    if (manifest_path.exists() and signature_path.exists() and combined_path.exists()
            and all(path.exists() for path in wavs)
            and signature_path.read_text(encoding="utf-8") == signature):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["language"] == language and len(manifest["scenes"]) == len(wavs):
                with wave.open(str(combined_path), "rb") as check:
                    if check.getnframes() > 0:
                        return manifest
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, EOFError):
            pass

    if synthesize is None:
        if not MODEL_PATH.is_file() or not VOICES_PATH.is_file():
            raise FileNotFoundError("Missing local Kokoro files in C:\\blu\\models")
        from kokoro_onnx import Kokoro
        import soundfile as sf

        engine = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
        voice, kokoro_language = VOICE[language]

        def synthesize(text: str, _language: SampleLanguage, destination: Path) -> None:
            samples, sample_rate = engine.create(
                text, voice=voice, lang=kokoro_language, speed=1.0
            )
            sf.write(str(destination), samples, sample_rate, subtype="PCM_16")

    for scene, path in zip(lesson.scenes, wavs):
        synthesize(scene.narration, language, path)
    manifest = build_timeline(lesson, language, wavs, combined_path)
    pending = manifest_path.with_suffix(".tmp")
    pending.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    pending.replace(manifest_path)
    signature_path.write_text(signature, encoding="utf-8")
    return manifest


def load_timeline(language: SampleLanguage, *, cache_root: Path = CACHE_ROOT) -> dict:
    path = cache_root / language / "timeline.json"
    if not path.is_file():
        raise FileNotFoundError("Prepare the sample before requesting its timeline")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["language"] != language:
        raise ValueError("Cached timeline language mismatch")
    return data
