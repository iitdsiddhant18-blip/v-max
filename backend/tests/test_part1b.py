"""Part 1b checks use synthetic WAVs: no model weights or browser required."""
import json
import wave
from pathlib import Path

import pytest

from backend.app.media import (
    PAUSE_SECONDS, build_timeline, load_timeline, prepare_sample, sample_lesson,
)
from backend.app.exporter import export_sample


def write_wav(path: Path, seconds: float = 1.0, rate: int = 8000, channels: int = 1):
    frames = round(rate * seconds)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(bytes(frames * channels * 2))


def test_english_and_hindi_samples_have_correct_text_language():
    english = sample_lesson("en")
    hindi = sample_lesson("hi")
    assert english.language == "en"
    assert hindi.language == "hi"
    assert len(english.scenes) == len(hindi.scenes) == 4
    assert any("लूप" in scene.narration for scene in hindi.scenes)


def test_timeline_is_derived_from_wav_frames_and_includes_exact_pause(tmp_path):
    assert PAUSE_SECONDS == 0.5
    files = [tmp_path / f"scene_{i:02d}.wav" for i in range(4)]
    for file in files:
        write_wav(file, 1.0)
    manifest = build_timeline(sample_lesson("en"), "en", files, tmp_path / "combined.wav")
    assert manifest["sample_rate"] == 8000
    assert manifest["total_seconds"] == 6.0
    assert [entry["start_seconds"] for entry in manifest["scenes"]] == [0.0, 1.5, 3.0, 4.5]
    assert [entry["duration_seconds"] for entry in manifest["scenes"]] == [1.5] * 4
    with wave.open(str(tmp_path / "combined.wav"), "rb") as wav:
        assert wav.getnframes() == 48000


def test_timeline_supports_unequal_audio_lengths(tmp_path):
    durations = [0.5, 1.25, 2.0, 0.75]
    files = [tmp_path / f"scene_{i:02d}.wav" for i in range(4)]
    for file, duration in zip(files, durations):
        write_wav(file, duration)
    manifest = build_timeline(sample_lesson("en"), "en", files, tmp_path / "combined.wav")
    assert manifest["total_seconds"] == 6.5
    assert [entry["start_seconds"] for entry in manifest["scenes"]] == [0.0, 1.0, 2.75, 5.25]


def test_wrong_scene_audio_count_is_rejected(tmp_path):
    file = tmp_path / "one.wav"
    write_wav(file)
    with pytest.raises(ValueError, match="exactly one WAV"):
        build_timeline(sample_lesson("en"), "en", [file], tmp_path / "combined.wav")


def test_mixed_sample_rates_are_rejected(tmp_path):
    files = [tmp_path / f"scene_{i:02d}.wav" for i in range(4)]
    for i, file in enumerate(files):
        write_wav(file, rate=16000 if i == 3 else 8000)
    with pytest.raises(ValueError, match="differing sample rates"):
        build_timeline(sample_lesson("en"), "en", files, tmp_path / "combined.wav")


def test_stereo_scene_audio_is_rejected(tmp_path):
    files = [tmp_path / f"scene_{i:02d}.wav" for i in range(4)]
    for i, file in enumerate(files):
        write_wav(file, channels=2 if i == 1 else 1)
    with pytest.raises(ValueError, match="mono"):
        build_timeline(sample_lesson("en"), "en", files, tmp_path / "combined.wav")


def test_language_mismatch_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="language must match"):
        build_timeline(sample_lesson("en"), "hi", [], tmp_path / "combined.wav")


def test_prepare_reuses_identical_cached_sample_without_synthesizing_again(tmp_path):
    calls = []

    def fake_synth(text, language, path):
        calls.append((language, text))
        write_wav(path, 1.0)

    first = prepare_sample("en", cache_root=tmp_path, synthesize=fake_synth)
    second = prepare_sample("en", cache_root=tmp_path, synthesize=fake_synth)
    assert len(calls) == 4
    assert first == second
    assert load_timeline("en", cache_root=tmp_path) == first
    assert json.loads((tmp_path / "en" / "timeline.json").read_text(encoding="utf-8")) == first


def test_hindi_synthesis_uses_hindi_narration_not_english(tmp_path):
    texts = []

    def fake_synth(text, language, path):
        texts.append(text)
        assert language == "hi"
        write_wav(path)

    manifest = prepare_sample("hi", cache_root=tmp_path, synthesize=fake_synth)
    assert manifest["lesson"]["language"] == "hi"
    assert len(texts) == 4
    assert "लूप" in texts[0]


def test_export_refuses_nonlocal_frontend_before_browser_launch(tmp_path):
    manifest = {"language": "en", "total_seconds": 4.0}
    with pytest.raises(ValueError, match="localhost"):
        export_sample("en", manifest, frontend_url="https://example.org", cache_root=tmp_path)


def test_export_refuses_language_mismatch_before_browser_launch(tmp_path):
    with pytest.raises(ValueError, match="mismatched"):
        export_sample("hi", {"language": "en", "total_seconds": 4.0}, cache_root=tmp_path)
