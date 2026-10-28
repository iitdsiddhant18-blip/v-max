"""Isolated localized media generation, WAV synthesis, cue alignment, and SRT creation.

Kept in a separate backend/cache/localized/<sha256>/ namespace from the English Part 2b lessons.
"""
import hashlib
import io
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from typing import Callable

from .live import ID_PATTERN, LIVE_ROOT, BEAT_SEPARATOR, load_lesson, visual_beats, lesson_id
from .media import MODEL_PATH, PAUSE_SECONDS, ROOT, VOICES_PATH
from .schema import Lesson
from .subtitles import manifest_to_srt
from .translated_lesson import translate_lesson

logger = logging.getLogger(__name__)

LOCALIZED_ROOT = ROOT / "backend" / "cache" / "localized"
LOCALIZED_VERSION = "localized-v1-visual-beats-v1"
LOCALIZED_VOICES = {
    "hi": ("hf_alpha", "hi", "kokoro-v1.0"),
    "kn": ("Anu", "kn", "indic-parler-tts-bfloat16"),
}

VENV_TTS_PYTHON = ROOT / ".venv-tts" / "Scripts" / "python.exe"
KANNADA_WORKER_SCRIPT = ROOT / "backend" / "scripts" / "kannada_tts_worker.py"


def localized_id(source_lesson_id: str, language: str, translated_lesson: Lesson) -> str:
    voice_info = LOCALIZED_VOICES.get(language, ("unknown", language, "unknown"))
    payload = {
        "source_lesson_id": source_lesson_id,
        "language": language,
        "translated_lesson": translated_lesson.model_dump(),
        "voice": voice_info[0],
        "model_version": voice_info[2],
        "version": LOCALIZED_VERSION,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def localized_folder(identifier: str, root: Path = LOCALIZED_ROOT) -> Path:
    if not ID_PATTERN.fullmatch(identifier):
        raise ValueError(f"Invalid localized lesson identifier: {identifier}")
    return root / identifier


def _valid_cached(folder: Path, identifier: str, expected_lang: str) -> dict | None:
    try:
        timeline_file = folder / "timeline.json"
        if not timeline_file.is_file():
            return None
        manifest = json.loads(timeline_file.read_text(encoding="utf-8"))
        if manifest.get("lesson_id") != identifier or manifest.get("kind") != "generated":
            return None
        if manifest.get("language") != expected_lang:
            return None
        scenes = manifest.get("scenes", [])
        if not scenes:
            return None
        for i in range(len(scenes)):
            scene_wav = folder / f"scene_{i:02d}.wav"
            if not scene_wav.is_file():
                return None
            with wave.open(str(scene_wav), "rb") as w:
                if w.getnframes() <= 0:
                    return None
        combined_wav = folder / "combined.wav"
        if not combined_wav.is_file():
            return None
        with wave.open(str(combined_wav), "rb") as w:
            if w.getnframes() <= 0:
                return None
        srt_file = folder / "subtitles.srt"
        if not srt_file.is_file() or srt_file.stat().st_size == 0:
            return None
        return manifest
    except (FileNotFoundError, ValueError, KeyError, TypeError, OSError,
            json.JSONDecodeError, EOFError, wave.Error):
        return None


def load_localized(identifier: str, *, root: Path = LOCALIZED_ROOT,
                   enforce_duration: bool = False) -> dict:
    folder = localized_folder(identifier, root)
    if not folder.is_dir():
        raise FileNotFoundError(f"Localized lesson folder not found for {identifier}")
    timeline_path = folder / "timeline.json"
    if not timeline_path.is_file():
        raise FileNotFoundError(f"timeline.json not found for {identifier}")
    manifest = json.loads(timeline_path.read_text(encoding="utf-8"))
    if manifest.get("lesson_id") != identifier:
        raise ValueError("Corrupt manifest: lesson_id mismatch")
    language = manifest.get("language")
    if language not in ("hi", "kn"):
        raise ValueError("Corrupt manifest: unsupported language")
    source_id = manifest.get("source_lesson_id", "")
    if not ID_PATTERN.fullmatch(source_id):
        raise ValueError("Corrupt manifest: invalid English source ID")
    english = Lesson.model_validate(manifest["semantic_lesson"])
    translated = Lesson.model_validate(manifest["lesson"])
    if english.language != "en" or lesson_id(english) != source_id:
        raise ValueError("Corrupt manifest: wrong English source")
    if translated.language != language or len(english.scenes) != len(translated.scenes):
        raise ValueError("Corrupt manifest: translation mismatch")
    for source, target in zip(english.scenes,translated.scenes):
        if (source.type!=target.type or source.code!=target.code
                or source.highlight_lines!=target.highlight_lines or len(source.items)!=len(target.items)):
            raise ValueError("Corrupt manifest: translation topology mismatch")
    for index,(source,entry) in enumerate(zip(english.scenes,manifest['scenes'])):
        if source.type=='title_card':continue
        expected=visual_beats(source,strict=True)
        if len(expected)!=len(entry.get('cues',[])):raise ValueError('Corrupt manifest: beat count mismatch')
        for beat,cue in zip(expected,entry['cues']):
            if (cue.get('item_index')!=beat['item_index'] or cue.get('item_indices')!=beat['item_indices']
                    or cue.get('highlight_lines')!=beat['highlight_lines']):
                raise ValueError('Corrupt manifest: visual cue linkage mismatch')
    if localized_id(source_id, language, translated) != identifier:
        raise ValueError("Corrupt manifest: content hash mismatch")
    if not _valid_cached(folder, identifier, language):
        raise ValueError("Corrupt manifest: media or SRT missing")
    if len(manifest["scenes"]) != len(translated.scenes):
        raise ValueError("Corrupt manifest: wrong scene count")
    _validate_timing(manifest, folder, enforce_duration=enforce_duration)
    return manifest


def _validate_timing(manifest: dict, folder: Path, *, enforce_duration: bool) -> None:
    total = manifest.get("total_seconds")
    if not isinstance(total, (int, float)) or not math.isfinite(total):
        raise ValueError("Corrupt manifest: nonfinite duration")
    if enforce_duration and not 30 <= total <= 90:
        raise ValueError("Corrupt manifest: duration must be 30–90s")
    rate = manifest["sample_rate"]
    cursor = 0
    for index, entry in enumerate(manifest["scenes"]):
        with wave.open(str(folder / f"scene_{index:02d}.wav"), "rb") as audio:
            if (audio.getframerate(), audio.getnchannels(), audio.getsampwidth()) != (rate, 1, 2):
                raise ValueError("Corrupt manifest: PCM format")
            frames = audio.getnframes()
        expected = (cursor / rate, frames / rate, (frames + round(PAUSE_SECONDS * rate)) / rate)
        actual = tuple(entry.get(k, float("nan")) for k in
                       ("start_seconds", "audio_seconds", "duration_seconds"))
        if entry.get("index") != index or any(not math.isfinite(v) or abs(v-e) > 1e-6
                                              for v, e in zip(actual, expected)):
            raise ValueError("Corrupt manifest: scene/WAV timing mismatch")
        end = 0.0
        for cue in entry.get("cues", []):
            start, stop = cue["start_seconds"], cue["end_seconds"]
            if not all(math.isfinite(v) for v in (start, stop)) or abs(start-end) > 1e-6 or stop <= start:
                raise ValueError("Corrupt manifest: invalid cue boundaries")
            end = stop
        if not entry.get("cues") or abs(end-frames/rate) > 1e-6:
            raise ValueError("Corrupt manifest: cue/WAV mismatch")
        scene=manifest['lesson']['scenes'][index]
        facts=([scene['narration']] if scene['type']=='title_card'
               else [item.partition(BEAT_SEPARATOR)[2] for item in scene['items']])
        if [c['text'] for c in entry['cues']]!=facts:
            raise ValueError('Corrupt manifest: spoken cue/content mismatch')
        cursor += frames + round(PAUSE_SECONDS * rate)
    with wave.open(str(folder / "combined.wav"), "rb") as audio:
        if audio.getnframes() != cursor or audio.getframerate() != rate:
            raise ValueError("Corrupt manifest: combined WAV mismatch")
    if abs(total-cursor/rate) > 1e-6:
        raise ValueError("Corrupt manifest: total/WAV duration mismatch")
    if (folder / "subtitles.srt").read_text(encoding="utf-8") != manifest_to_srt(manifest):
        raise ValueError("Corrupt manifest: subtitles/cue mismatch")


def synthesize_kannada_batch(segments: list[dict], output_dir: Path) -> dict[str, int]:
    """Execute kannada_tts_worker.py in .venv-tts once for all segments in a job."""
    if not VENV_TTS_PYTHON.is_file():
        raise FileNotFoundError(f"Python interpreter not found at {VENV_TTS_PYTHON}")
    if not KANNADA_WORKER_SCRIPT.is_file():
        raise FileNotFoundError(f"Kannada worker script not found at {KANNADA_WORKER_SCRIPT}")

    job_spec = {
        "language": "kn",
        "model_id": "ai4bharat/indic-parler-tts",
        "description": (
            "Anu speaks in a clear, moderate-paced, neutral tone with very clear "
            "audio quality and no background noise."
        ),
        "segments": segments,
    }

    job_file = output_dir / "kannada_job.json"
    job_file.write_text(json.dumps(job_spec, ensure_ascii=False, indent=2), encoding="utf-8")

    cmd = [str(VENV_TTS_PYTHON), str(KANNADA_WORKER_SCRIPT), str(job_file)]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["HF_DATASETS_OFFLINE"] = "1"

    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or proc.stdout.strip() or f"Exit code {proc.returncode}"
        raise RuntimeError(f"Kannada TTS generation failed: {err_msg}")

    try:
        res = json.loads(proc.stdout)
        if res.get("status") != "ok":
            raise RuntimeError(f"Kannada TTS worker error: {res.get('error')}")
        return res
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid worker output: {proc.stdout}") from exc


def prepare_localized(
    source_lesson_id: str,
    language: str,
    *,
    translator=None,
    synthesize=None,
    root: Path = LOCALIZED_ROOT,
    source_root: Path = LIVE_ROOT,
    enforce_duration: bool = False,
) -> dict:
    """Prepare a localized (hi/kn) lesson and audio timeline from an English prepared source."""
    if language not in ("hi", "kn"):
        raise ValueError(f"Target language must be 'hi' or 'kn', got '{language}'")
    if not ID_PATTERN.fullmatch(source_lesson_id):
        raise ValueError(f"Invalid source lesson ID: {source_lesson_id}")

    # Load source English prepared lesson
    source_manifest = load_lesson(source_lesson_id, root=source_root)
    source_lesson = Lesson.model_validate(source_manifest["lesson"])

    # Translation phase
    if translator is None:
        from .indic_translator import LocalIndicTranslator
        tr = LocalIndicTranslator()
        translate_fn = tr.translate_many
    elif hasattr(translator, "translate_many"):
        translate_fn = translator.translate_many
    elif callable(translator):
        translate_fn = translator
    else:
        raise ValueError("Invalid translator provided")

    try:
        translated = translate_lesson(source_lesson, language, translate_fn)
    finally:
        if translator is None:
            tr.unload()

    # Compute target cache ID
    identifier = localized_id(source_lesson_id, language, translated)
    folder = localized_folder(identifier, root)
    cached = _valid_cached(folder, identifier, language)
    if cached is not None:
        try:
            cached = load_localized(identifier, root=root, enforce_duration=enforce_duration)
            if (cached["source_lesson_id"] != source_lesson_id
                    or cached["lesson"] != translated.model_dump()):
                raise ValueError("Cached source/content mismatch")
            return cached
        except (ValueError, KeyError, TypeError, OSError) as exc:
            logger.warning("Localized cache invalidated %s: %s", identifier[:12], exc)

    staging_dir = Path(tempfile.mkdtemp(prefix=f"loc_{identifier[:8]}_", dir=root.parent))
    try:
        # Pre-calculate audio tasks
        import soundfile as sf

        # If synthesize is None, prepare engines
        kokoro_engine = None
        if synthesize is None and language == "hi":
            from kokoro_onnx import Kokoro
            if not MODEL_PATH.is_file() or not VOICES_PATH.is_file():
                raise FileNotFoundError("Kokoro model files missing from models/")
            kokoro_engine = Kokoro(str(MODEL_PATH), str(VOICES_PATH))

        # Collect all segments to synthesize
        # Each segment: scene_index, beat_index, text, output_file
        job_segments: list[dict] = []
        scene_beat_data: list[list[dict]] = []

        for s_idx, (src_scene, trans_scene) in enumerate(zip(source_lesson.scenes, translated.scenes)):
            beats_meta = []
            if trans_scene.type == "title_card":
                text = trans_scene.narration
                out_path = staging_dir / f"scene_{s_idx:02d}_beat_00.wav"
                job_segments.append({"output_path": str(out_path), "text": text})
                beats_meta.append({
                    "label": trans_scene.heading,
                    "text": text,
                    "item_index": None,
                    "item_indices": [],
                    "highlight_lines": [],
                    "output_file": out_path,
                })
            else:
                src_beats = visual_beats(src_scene, strict=True)
                for b_idx, (src_beat, trans_item) in enumerate(zip(src_beats, trans_scene.items)):
                    trans_label, sep, trans_fact = trans_item.partition(BEAT_SEPARATOR)
                    out_path = staging_dir / f"scene_{s_idx:02d}_beat_{b_idx:02d}.wav"
                    job_segments.append({"output_path": str(out_path), "text": trans_fact})
                    beats_meta.append({
                        "label": trans_label,
                        "text": trans_fact,
                        "item_index": src_beat["item_index"],
                        "item_indices": src_beat.get("item_indices", [src_beat["item_index"]]),
                        "highlight_lines": src_beat.get("highlight_lines", []),
                        "output_file": out_path,
                    })
            scene_beat_data.append(beats_meta)

        # Synthesize all segments
        if synthesize is not None:
            for seg in job_segments:
                synthesize(seg["text"], Path(seg["output_path"]), language)
        elif language == "hi":
            assert kokoro_engine is not None
            for seg in job_segments:
                samples, sr = kokoro_engine.create(
                    seg["text"], voice="hf_alpha", lang="hi", speed=1.0
                )
                sf.write(seg["output_path"], samples, sr, format="WAV", subtype="PCM_16")
        elif language == "kn":
            synthesize_kannada_batch(job_segments, staging_dir)

        # Join fact WAVs into scene WAVs and measure exact PCM cues
        scene_files: list[Path] = []
        scene_cues: list[list[dict]] = []
        global_rate = None

        for s_idx, beats in enumerate(scene_beat_data):
            scene_wav_path = staging_dir / f"scene_{s_idx:02d}.wav"
            cues = []
            cursor = 0

            with wave.open(str(scene_wav_path), "wb") as joined:
                scene_rate = None
                for beat in beats:
                    beat_wav_path = beat["output_file"]
                    with wave.open(str(beat_wav_path), "rb") as b_wav:
                        if b_wav.getnchannels() != 1 or b_wav.getsampwidth() != 2:
                            raise ValueError(f"WAV for '{beat['text']}' must be mono PCM16")
                        rate = b_wav.getframerate()
                        if scene_rate is None:
                            scene_rate = rate
                            joined.setparams((1, 2, rate, 0, "NONE", "not compressed"))
                        elif scene_rate != rate:
                            raise ValueError(f"Sample rate mismatch: {scene_rate} vs {rate}")
                        frames = b_wav.getnframes()
                        if frames <= 0:
                            raise ValueError(f"Empty audio for fact '{beat['text']}'")
                        audio_bytes = b_wav.readframes(frames)
                        joined.writeframesraw(audio_bytes)

                    cues.append({
                        "label": beat["label"],
                        "text": beat["text"],
                        "item_index": beat["item_index"],
                        "item_indices": beat["item_indices"],
                        "highlight_lines": beat["highlight_lines"],
                        "start_seconds": round(cursor / rate, 6),
                        "end_seconds": round((cursor + frames) / rate, 6),
                    })
                    cursor += frames

            if global_rate is None:
                global_rate = scene_rate
            elif global_rate != scene_rate:
                raise ValueError("Different scenes have different sample rates")

            scene_files.append(scene_wav_path)
            scene_cues.append(cues)

        assert global_rate is not None

        # Build combined.wav with verified 0.5s pause
        combined_wav_path = staging_dir / "combined.wav"
        cursor_frames = 0
        pause_frames = round(PAUSE_SECONDS * global_rate)
        timeline_scenes = []

        with wave.open(str(combined_wav_path), "wb") as joined_all:
            joined_all.setparams((1, 2, global_rate, 0, "NONE", "not compressed"))
            for s_idx, scene_path in enumerate(scene_files):
                with wave.open(str(scene_path), "rb") as s_wav:
                    frames = s_wav.getnframes()
                    audio_bytes = s_wav.readframes(frames)
                timeline_scenes.append({
                    "index": s_idx,
                    "start_seconds": round(cursor_frames / global_rate, 6),
                    "audio_seconds": round(frames / global_rate, 6),
                    "duration_seconds": round((frames + pause_frames) / global_rate, 6),
                    "audio_url": f"/api/localized/media/{identifier}/scene_{s_idx:02d}.wav",
                    "cues": scene_cues[s_idx],
                })
                joined_all.writeframesraw(audio_bytes)
                joined_all.writeframesraw(bytes(pause_frames * 2))
                cursor_frames += frames + pause_frames

        total_seconds = round(cursor_frames / global_rate, 6)

        # Validate BEFORE atomically publishing; never leave an invalid-duration
        # target lesson looking ready after a failed request.
        if enforce_duration and not (30.0 <= total_seconds <= 90.0):
            raise ValueError(
                f"Localized narration is {total_seconds:.2f}s; expected 30–90s."
            )

        manifest = {
            "kind": "generated",
            "lesson_id": identifier,
            "source_lesson_id": source_lesson_id,
            "language": language,
            "voice": LOCALIZED_VOICES[language][0],
            "sample_rate": global_rate,
            "pause_seconds": PAUSE_SECONDS,
            "total_seconds": total_seconds,
            "audio_url": f"/api/localized/media/{identifier}/combined.wav",
            "subtitle_url": f"/api/localized/subtitles/{identifier}",
            "lesson": translated.model_dump(),
            "semantic_lesson": source_lesson.model_dump(),
            "scenes": timeline_scenes,
        }

        # Generate subtitles.srt
        srt_content = manifest_to_srt(manifest)
        (staging_dir / "subtitles.srt").write_text(srt_content, encoding="utf-8")

        # Write timeline.json
        (staging_dir / "timeline.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Atomic commit to cache folder
        folder.parent.mkdir(parents=True, exist_ok=True)
        if folder.exists():
            # Preserve corrupt/old artifacts for diagnosis, never erase user media.
            import uuid
            folder.rename(folder.with_name(identifier + ".invalid-" + uuid.uuid4().hex[:12]))
        staging_dir.rename(folder)

        return manifest
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
