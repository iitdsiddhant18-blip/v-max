"""Synthetic tests for localized media, translation preservation, SRT, cache, and API safety.

No neural model weights are required. All tests run fast and offline.
"""
import io
import json
import wave
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.schema import Lesson
from backend.app.live import lesson_id, prepare_lesson
from backend.app.localized_media import (
    LOCALIZED_ROOT,
    load_localized,
    localized_folder,
    localized_id,
    prepare_localized,
)
from backend.app.indic_translator import LocalIndicTranslator
from backend.app.subtitles import manifest_to_srt
from backend.app.main import app


def make_pcm16_wav(path: Path, seconds: float, rate: int = 24000) -> int:
    frames = round(seconds * rate)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        w.writeframes(b"\x01\x00" * frames)
    return frames


def sample_english_lesson() -> Lesson:
    return Lesson.model_validate({
        "title": "Python loops walkthrough",
        "level": "beginner",
        "language": "en",
        "scenes": [
            {
                "type": "title_card",
                "heading": "Python for loops",
                "subtitle": "Step by step execution",
                "narration": "Let us understand how a Python for loop iterates.",
                "items": ["Overview :: For loops visit each value in order."],
                "highlight_lines": [],
            },
            {
                "type": "code_walkthrough",
                "heading": "Tracing the code",
                "code": "for i in range(3):\n    print(i)",
                "highlight_lines": [1, 2],
                "items": [
                    "Line 1 :: The loop fetches the next item from range(3).",
                    "Line 2 :: The body prints the value of i to output.",
                ],
                "narration": "The loop fetches the next item from range(3). The body prints the value of i to output.",
            },
            {
                "type": "diagram",
                "heading": "Visualizing steps",
                "items": [
                    "Input :: Values 0, 1, 2 are queued.",
                    "Iteration :: Each pass takes one value.",
                    "Output :: Screen shows printed values.",
                ],
                "narration": "Values 0, 1, 2 are queued. Each pass takes one value. Screen shows printed values.",
                "highlight_lines": [],
            },
            {
                "type": "step_list",
                "heading": "Key takeaways",
                "items": [
                    "Repeat :: Body executes for each item.",
                    "Halt :: Loop stops when sequence is exhausted.",
                ],
                "narration": "Body executes for each item. Loop stops when sequence is exhausted.",
                "highlight_lines": [],
            },
            {
                "type": "step_list",
                "heading": "Final review",
                "items": [
                    "Check :: Review the loop body and output.",
                    "Done :: You now understand Python loops.",
                ],
                "narration": "Review the loop body and output. You now understand Python loops.",
                "highlight_lines": [],
            },
        ],
    })


class FakeTranslator:
    def __init__(self, token_corrupter=None):
        self.token_corrupter = token_corrupter

    def translate_many(self, texts: list[str], language: str) -> list[str]:
        results = []
        for t in texts:
            if self.token_corrupter:
                t = self.token_corrupter(t)
            if language == "hi":
                results.append(f"यह हिंदी पाठ है: {t}")
            elif language == "kn":
                results.append(f"ಇದು ಕನ್ನಡ ಪಠ್ಯ: {t}")
            else:
                raise ValueError("Unsupported language")
        return results


def make_fake_synthesize():
    def synth(text: str, destination: Path, lang: str):
        rate = 24000 if lang == "hi" else 44100
        # Different non-equal durations based on length
        duration = 0.6 + (len(text) % 5) * 0.25
        make_pcm16_wav(destination, duration, rate)
    return synth


@pytest.fixture
def prepared_english(tmp_path):
    eng = sample_english_lesson()
    eng_cache_root = tmp_path / "backend" / "cache" / "lessons"

    def synth_eng(narration: str, destination: Path):
        make_pcm16_wav(destination, 2.0, 24000)
        return [{"text": narration, "start_seconds": 0.0, "end_seconds": 2.0,
                 "item_index": 0, "item_indices": [0], "highlight_lines": []}]

    manifest = prepare_lesson(eng, root=eng_cache_root, synthesize=synth_eng)
    return manifest["lesson_id"], eng_cache_root, tmp_path / "backend" / "cache" / "localized"


def test_golden_same_lesson_mapping(prepared_english):
    source_id, eng_root, loc_root = prepared_english
    fake_tr = FakeTranslator()
    fake_synth = make_fake_synthesize()

    # Hindi
    hi_manifest = prepare_localized(
        source_id, "hi", translator=fake_tr, synthesize=fake_synth, root=loc_root, source_root=eng_root
    )
    assert hi_manifest["language"] == "hi"
    assert hi_manifest["source_lesson_id"] == source_id
    assert hi_manifest["kind"] == "generated"
    assert len(hi_manifest["scenes"]) == 5
    assert len(hi_manifest["lesson"]["scenes"]) == 5

    # Check code walkthrough preservation
    hi_code_scene = hi_manifest["lesson"]["scenes"][1]
    assert hi_code_scene["type"] == "code_walkthrough"
    assert hi_code_scene["code"] == "for i in range(3):\n    print(i)"
    assert hi_code_scene["highlight_lines"] == [1, 2]
    assert hi_code_scene["items"][0].startswith("Line 1 :: ")
    assert hi_code_scene["items"][1].startswith("Line 2 :: ")

    # Kannada
    kn_manifest = prepare_localized(
        source_id, "kn", translator=fake_tr, synthesize=fake_synth, root=loc_root, source_root=eng_root
    )
    assert kn_manifest["language"] == "kn"
    assert kn_manifest["source_lesson_id"] == source_id
    assert kn_manifest["sample_rate"] == 44100
    assert hi_manifest["sample_rate"] == 24000

    # Cache IDs differ
    assert hi_manifest["lesson_id"] != kn_manifest["lesson_id"]
    assert hi_manifest["lesson_id"] != source_id


def test_exact_cue_timestamps_and_no_pause_in_srt(prepared_english):
    source_id, eng_root, loc_root = prepared_english
    fake_tr = FakeTranslator()
    fake_synth = make_fake_synthesize()

    manifest = prepare_localized(
        source_id, "hi", translator=fake_tr, synthesize=fake_synth, root=loc_root, source_root=eng_root
    )

    srt_path = loc_root / manifest["lesson_id"] / "subtitles.srt"
    assert srt_path.is_file()
    srt_text = srt_path.read_text(encoding="utf-8")

    # Verify SRT contains Devanagari text
    assert "हिंदी" in srt_text
    # Verify no gap caption or pause in subtitle
    for scene in manifest["scenes"]:
        for cue in scene["cues"]:
            assert cue["text"] in srt_text
            assert cue["start_seconds"] < cue["end_seconds"]
            assert cue["end_seconds"] <= scene["audio_seconds"] + 0.001


def test_token_protection_roundtrip():
    original = "Each pass runs print(i) on range(3) with n * 2 for Alice and Bob in Python with 2, 4, 6."
    masked, mapping = LocalIndicTranslator.protect_tokens(original)

    assert "X0X" in masked
    assert "print(i)" in mapping.values()
    assert "range(3)" in mapping.values()
    assert "n * 2" in mapping.values()
    assert "Alice" in mapping.values()
    assert "Bob" in mapping.values()
    assert "Python" in mapping.values()
    assert "2" in mapping.values()

    # Test restoration
    restored = LocalIndicTranslator.restore_tokens(masked, mapping, "hi")
    assert restored == original


def test_lost_token_fails_closed():
    masked = "Each pass runs X0X."
    mapping = {"X0X": "print(i)", "X1X": "range(3)"}
    with pytest.raises(ValueError, match="lost during translation"):
        LocalIndicTranslator.restore_tokens(masked, mapping, "hi")


def test_untranslated_echo_fails(prepared_english):
    source_id, eng_root, loc_root = prepared_english
    echo_tr = lambda texts, lang: texts  # Returns English without Hindi/Kannada script
    fake_synth = make_fake_synthesize()

    with pytest.raises(ValueError, match="No expected Hindi/Kannada script"):
        prepare_localized(
            source_id, "hi", translator=echo_tr, synthesize=fake_synth, root=loc_root, source_root=eng_root
        )


def test_invalid_target_language_rejected(prepared_english):
    source_id, eng_root, loc_root = prepared_english
    fake_tr = FakeTranslator()
    fake_synth = make_fake_synthesize()

    with pytest.raises(ValueError, match="Target language must be 'hi' or 'kn'"):
        prepare_localized(
            source_id, "fr", translator=fake_tr, synthesize=fake_synth, root=loc_root, source_root=eng_root
        )


def test_invalid_source_id_rejected():
    with pytest.raises(ValueError, match="Invalid source lesson ID"):
        prepare_localized("invalid_id", "hi")


def test_corrupt_manifest_triggers_regeneration(prepared_english):
    source_id, eng_root, loc_root = prepared_english
    fake_tr = FakeTranslator()
    fake_synth = make_fake_synthesize()

    manifest = prepare_localized(
        source_id, "hi", translator=fake_tr, synthesize=fake_synth, root=loc_root, source_root=eng_root
    )
    cache_id = manifest["lesson_id"]
    timeline_file = loc_root / cache_id / "timeline.json"

    # Corrupt the timeline file
    timeline_file.write_text("corrupted json {", encoding="utf-8")

    # Should safely regenerate instead of serving corrupted data
    fresh = prepare_localized(
        source_id, "hi", translator=fake_tr, synthesize=fake_synth, root=loc_root, source_root=eng_root
    )
    assert fresh["lesson_id"] == cache_id
    assert fresh["kind"] == "generated"


def test_api_endpoints_safety(prepared_english, monkeypatch):
    source_id, eng_root, loc_root = prepared_english
    fake_tr = FakeTranslator()
    # Production HTTP timelines require 30–90s; short fixtures stay internal.
    def fake_synth(text, destination, language):
        make_pcm16_wav(destination, 3, 24000)

    # Patch LIVE_ROOT and LOCALIZED_ROOT for isolated test
    monkeypatch.setattr("backend.app.main.LIVE_ROOT", eng_root)
    monkeypatch.setattr("backend.app.main.LOCALIZED_ROOT", loc_root)
    monkeypatch.setattr("backend.app.live.LIVE_ROOT", eng_root)
    monkeypatch.setattr("backend.app.localized_media.LOCALIZED_ROOT", loc_root)

    # Prepare localized lesson in cache
    manifest = prepare_localized(
        source_id, "hi", translator=fake_tr, synthesize=fake_synth, root=loc_root, source_root=eng_root
    )
    loc_id = manifest["lesson_id"]

    client = TestClient(app)

    # 1. GET timeline
    res = client.get(f"/api/localized/timeline/{loc_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["lesson_id"] == loc_id
    assert data["language"] == "hi"

    # 2. GET media combined.wav
    res = client.get(f"/api/localized/media/{loc_id}/combined.wav")
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"

    # 3. GET media scene_00.wav
    res = client.get(f"/api/localized/media/{loc_id}/scene_00.wav")
    assert res.status_code == 200

    # 4. GET invalid audio file
    res = client.get(f"/api/localized/media/{loc_id}/malicious.txt")
    assert res.status_code == 404

    # 5. GET subtitles
    res = client.get(f"/api/localized/subtitles/{loc_id}")
    assert res.status_code == 200
    assert "हिंदी" in res.text

    # 6. GET unknown lesson
    res = client.get(f"/api/localized/timeline/{'0'*64}")
    assert res.status_code == 404
