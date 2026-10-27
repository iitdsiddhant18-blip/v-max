"""Generated lesson media checks with synthetic WAVs, no models or browser."""
import json
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.live import lesson_folder, lesson_id, load_lesson, prepare_lesson
from backend.app.live_export import export_lesson
from backend.app.main import app
from backend.app.schema import Lesson
from backend.app.generic_fallback import make_generic_fallback
from backend.app.schema import GenerateRequest


def lesson(topic="Photosynthesis") -> Lesson:
    return make_generic_fallback(GenerateRequest(topic=topic))


def fake_voice(text: str, destination: Path) -> None:
    with wave.open(str(destination), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(bytes(8000 * 2))


def test_topic_changes_content_hash_and_has_64_hex_characters():
    one, two = lesson_id(lesson()), lesson_id(lesson("Newton's first law"))
    assert len(one) == 64 and len(two) == 64 and one != two
    assert all(c in "0123456789abcdef" for c in one)


def test_three_scene_audio_controls_timeline_not_guesswork(tmp_path):
    prepared = prepare_lesson(lesson(), root=tmp_path, synthesize=fake_voice)
    assert prepared["kind"] == "generated"
    assert prepared["total_seconds"] == 4.5
    assert [s["start_seconds"] for s in prepared["scenes"]] == [0.0, 1.5, 3.0]
    assert all("/api/lesson/media/" in s["audio_url"] for s in prepared["scenes"])


def test_identical_lesson_reuses_wavs_and_manifest(tmp_path):
    calls = []

    def synth(text, dest):
        calls.append(text)
        fake_voice(text, dest)

    a = prepare_lesson(lesson(), root=tmp_path, synthesize=synth)
    b = prepare_lesson(lesson(), root=tmp_path, synthesize=synth)
    assert a == b
    assert len(calls) == len(lesson().scenes)
    assert load_lesson(a["lesson_id"], root=tmp_path) == a


def test_cache_invalidated_if_scene_audio_is_missing(tmp_path):
    a = prepare_lesson(lesson(), root=tmp_path, synthesize=fake_voice)
    (lesson_folder(a["lesson_id"], tmp_path) / "scene_01.wav").unlink()
    with pytest.raises(ValueError, match="incomplete"):
        load_lesson(a["lesson_id"], root=tmp_path)
    prepare_lesson(lesson(), root=tmp_path, synthesize=fake_voice)
    assert load_lesson(a["lesson_id"], root=tmp_path)["lesson_id"] == a["lesson_id"]


@pytest.mark.parametrize("identifier", ["../../models", "abc", "a" * 63 + "/"])
def test_identifier_cannot_traverse_cache(identifier):
    with pytest.raises(ValueError, match="identifier"):
        lesson_folder(identifier)


def test_no_non_english_speech_masquerading_as_translation(tmp_path):
    data = lesson().model_dump()
    data["language"] = "hi"
    def unexpected_speech(*_args):
        raise AssertionError("Non-English speech must be rejected before TTS is attempted")
    with pytest.raises(ValueError, match="English-only"):
        prepare_lesson(Lesson.model_validate(data), root=tmp_path, synthesize=unexpected_speech)


def test_manifest_tamper_rejected(tmp_path):
    manifest = prepare_lesson(lesson(), root=tmp_path, synthesize=fake_voice)
    folder = lesson_folder(manifest["lesson_id"], tmp_path)
    file = folder / "timeline.json"
    changed = json.loads(file.read_text(encoding="utf-8"))
    changed["lesson"]["title"] = "Another topic"
    file.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="identifier"):
        load_lesson(manifest["lesson_id"], root=tmp_path)


def test_export_rejects_nonlocal_frontend_before_browser(tmp_path):
    manifest = prepare_lesson(lesson(), root=tmp_path, synthesize=fake_voice)
    with pytest.raises(ValueError, match="local"):
        export_lesson(manifest["lesson_id"], root=tmp_path,
                      frontend_url="https://remote.example.org")


def test_api_rejects_invalid_lesson_and_bad_media_filename():
    client = TestClient(app)
    assert client.post("/api/lesson/prepare", json={"lesson": {}}).status_code == 422
    assert client.get("/api/lesson/media/" + "a" * 64 + "/../data").status_code in (404, 422)
    assert client.get("/api/lesson/timeline/invalid").status_code == 404


def test_sentence_cues_follow_unequal_real_pcm_lengths(tmp_path):
    import numpy as np
    from backend.app.live import synthesize_scene
    from backend.app.schema import Scene

    class Engine:
        def create(self, text, **_options):
            return np.zeros(4000 if text.startswith("Sunlight") else 12000), 8000

    scene = Scene(type="diagram", heading="Inputs", items=["Sunlight", "Water"],
                  narration="Sunlight reaches the leaf. Water reaches the roots.")
    path = tmp_path / "scene.wav"
    cues = synthesize_scene(scene.narration, path, Engine(), scene)
    assert [(c["start_seconds"], c["end_seconds"]) for c in cues] == [(0, .5), (.5, 2)]
    assert [c["item_index"] for c in cues] == [0, 1]
    assert " ".join(c["text"] for c in cues) == scene.narration
    with wave.open(str(path)) as wav:
        assert wav.getnframes() == 16000


def test_playable_duration_is_inclusive_30_to_90_seconds():
    from backend.app.live import _check_duration
    for seconds in (29.999, 90.001):
        with pytest.raises(ValueError, match="30–90"):
            _check_duration({"total_seconds": seconds})
    for seconds in (30, 90):
        _check_duration({"total_seconds": seconds})


def test_measured_short_lesson_replans_content_before_returning():
    from backend.app.live import plan_timed_lesson
    request = GenerateRequest(topic="Photosynthesis")
    calls = []

    def planner(req, **_options):
        calls.append(req.topic)
        data = lesson().model_dump()
        data["title"] += f" revision {len(calls)}"
        return "llm", Lesson.model_validate(data)

    durations = iter([20, 48])
    source, final = plan_timed_lesson(request, planner=planner,
                                    prepare=lambda _lesson: {"total_seconds": next(durations)})
    assert source == "llm" and final.title.endswith("revision 2")
    assert calls == [request.topic, request.topic]


def test_repeated_timing_failure_is_not_presented_as_a_ready_lesson():
    from backend.app.live import plan_timed_lesson
    calls = []

    def planner(req, **_options):
        calls.append(req)
        return "llm", lesson()

    source, final = plan_timed_lesson(GenerateRequest(topic="Photosynthesis"), planner=planner,
                                    prepare=lambda _lesson: {"total_seconds": 20})
    assert len(calls) == 3 and source == "fallback"
    assert "Photosynthesis" in final.title


def test_teaching_rejects_spoken_values_inconsistent_with_range_three():
    from backend.app.fallback import load_fallback_lesson
    from backend.app.live import validate_teaching
    data = load_fallback_lesson().model_dump()
    data["scenes"][1]["narration"] = "This code prints 1, 2, and 3."
    with pytest.raises(ValueError, match="range"):
        validate_teaching(Lesson.model_validate(data), GenerateRequest(topic="Python loops"), 0)


def test_teaching_rejects_unrelated_subject_after_markup_topic():
    from backend.app.fallback import load_fallback_lesson
    from backend.app.live import validate_teaching
    with pytest.raises(ValueError, match="changed subjects"):
        validate_teaching(load_fallback_lesson(), GenerateRequest(topic="<img onerror=alert(1)> and DNA"), 0)


def test_science_does_not_accept_an_invented_program_as_explanation():
    from backend.app.fallback import load_fallback_lesson
    from backend.app.live import validate_teaching
    data = load_fallback_lesson().model_dump()
    data["title"] = "Photosynthesis"
    with pytest.raises(ValueError, match="not a programming topic"):
        validate_teaching(Lesson.model_validate(data), GenerateRequest(topic="Photosynthesis"), 0)


def test_photosynthesis_does_not_claim_roots_absorb_sunlight():
    from backend.app.fallback import load_fallback_lesson
    from backend.app.live import validate_teaching
    data = load_fallback_lesson().model_dump()
    data["title"] = "Photosynthesis"
    data["scenes"][1].update(type="diagram", code=None, highlight_lines=[],
                              items=["Sunlight", "Water", "Carbon dioxide", "Sugar", "Oxygen"],
                              narration="Plants absorb sunlight and water through roots.")
    with pytest.raises(ValueError, match="Leaves capture sunlight"):
        validate_teaching(Lesson.model_validate(data), GenerateRequest(topic="Photosynthesis"), 0)


def test_worked_example_must_show_the_actual_doubled_outputs():
    from backend.app.fallback import load_fallback_lesson
    from backend.app.live import validate_teaching
    data = load_fallback_lesson().model_dump()
    data["scenes"][1].update(code="for n in [2, 4, 6]:\n    print(n * 2)",
                              narration="The loop multiplies each number by two.")
    with pytest.raises(ValueError, match="4,8,12"):
        validate_teaching(Lesson.model_validate(data), GenerateRequest(topic="Python loops"), 0)


def test_intro_cleanup_preserves_facts_and_never_changes_display_code():
    from backend.app.fallback import load_fallback_lesson
    from backend.app.live import clean_teaching_intro
    data = load_fallback_lesson().model_dump()
    data["scenes"][0]["narration"] = "A loop visits values. By the end, you will know everything about loops."
    data["scenes"][1]["narration"] = "The `print` instruction displays a value."
    original = Lesson.model_validate(data)
    cleaned = clean_teaching_intro(original)
    assert cleaned.scenes[0].narration == "A loop visits values."
    assert cleaned.scenes[1].narration == "The print instruction displays a value."
    assert cleaned.scenes[1].code == original.scenes[1].code
    assert "By the end" in original.scenes[0].narration


def test_live_decoding_grammar_does_not_mutate_the_shared_schema():
    from backend.app.fallback import load_fallback_lesson
    from backend.app.live import plan_timed_lesson
    from backend.app.planner import make_payload
    captured = []
    before = Lesson.model_json_schema()

    def send(payload):
        captured.append(payload)
        return {"message": {"content": load_fallback_lesson().model_dump_json()}}

    def planner(req, model, transport):
        with pytest.raises(ValueError):
            transport(make_payload(req, model))
        return "fallback", lesson()

    plan_timed_lesson(GenerateRequest(topic="Photosynthesis"), planner=planner, transport=send)
    schema = captured[0]["format"]
    assert schema["properties"]["scenes"]["minItems"] == schema["properties"]["scenes"]["maxItems"] == 5
    assert "code_walkthrough" not in schema["$defs"]["Scene"]["properties"]["type"]["enum"]
    assert schema["$defs"]["Scene"]["properties"]["code"] == {"type": "null"}
    assert Lesson.model_json_schema() == before


def python_display_example(code, items):
    from backend.app.fallback import load_fallback_lesson
    data = load_fallback_lesson().model_dump()
    data["scenes"][1].update(code=code, items=items, highlight_lines=[])
    data["scenes"].insert(3, {"type": "step_list", "heading": "Apply the idea",
        "narration": "Check the input names before following each instruction.", "items": ["Check inputs"]})
    return Lesson.model_validate(data)


def test_missing_python_input_is_rejected_until_visible_context_defines_it():
    from backend.app.live import validate_teaching
    request = GenerateRequest(topic="Python loops")
    code = "for name in names:\n    print(name)"
    with pytest.raises(ValueError, match="Define example inputs"):
        validate_teaching(python_display_example(code, []), request, 0)
    validate_teaching(python_display_example(code, ["names = ['Alice', 'Bob']"]), request, 0)


def test_model_display_code_is_parsed_but_never_executed():
    from backend.app.live import validate_teaching
    validate_teaching(python_display_example("raise RuntimeError('This must never execute')", []),
                      GenerateRequest(topic="Python loops"), 0)


def test_visual_pairs_replace_summary_with_the_exact_spoken_facts():
    from backend.app.live import normalize_visual_beats
    original = lesson()
    data = original.model_dump()
    for scene in data["scenes"][1:]:
        scene["items"] = ["First :: This is the first concrete explanation.",
                          "Second :: This is a different concrete explanation."]
    normalized = normalize_visual_beats(Lesson.model_validate(data))
    assert normalized.scenes[1].narration == (
        "This is the first concrete explanation. This is a different concrete explanation.")
    assert original.scenes[1].narration != normalized.scenes[1].narration


def test_visual_focus_is_explicit_even_when_labels_and_speech_share_no_words(tmp_path):
    import numpy as np
    from backend.app.live import synthesize_scene
    from backend.app.schema import Scene

    class Engine:
        def create(self, text, **_options):
            return np.zeros(4000 if text.startswith("Roots") else 12000), 8000

    facts = ["Roots absorb liquid from the soil.", "Leaves collect energy from the sun."]
    scene = Scene(type="diagram", heading="A plant", narration=" ".join(facts),
                  items=["A :: " + facts[0], "B :: " + facts[1]])
    cues = synthesize_scene(scene.narration, tmp_path / "paired.wav", Engine(), scene)
    assert [(c["label"], c["item_indices"]) for c in cues] == [("A", [0]), ("B", [1])]
    assert [(c["start_seconds"], c["end_seconds"]) for c in cues] == [(0, .5), (.5, 2)]


def test_code_visual_pair_cannot_highlight_a_nonexistent_line():
    from backend.app.live import visual_beats
    from backend.app.schema import Scene
    scene = Scene(type="code_walkthrough", heading="Code", narration="Display the number on screen.",
                  code="print(5)", items=["Line 2 :: Display the number on screen."])
    with pytest.raises(ValueError, match="nonexistent code line"):
        visual_beats(scene, strict=True)


def test_equal_spoken_text_keeps_each_scenes_own_visual_pair(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    from backend.app import live, media
    data = lesson().model_dump()
    for i, scene in enumerate(data["scenes"][1:]):
        scene.update(narration="The same words can describe different visual labels.",
                     items=[f"Visual {i} :: The same words can describe different visual labels."])
    model = tmp_path / "model"; model.touch()
    monkeypatch.setattr(media, "MODEL_PATH", model)
    monkeypatch.setattr(media, "VOICES_PATH", model)
    monkeypatch.setitem(sys.modules, "kokoro_onnx", SimpleNamespace(Kokoro=lambda *_: object()))
    def synth(text, path, engine, scene):
        fake_voice(text, path)
        return [{"label": scene.items[0].split(" :: ")[0]}] if scene.items else []
    monkeypatch.setattr(live, "synthesize_scene", synth)
    manifest = prepare_lesson(Lesson.model_validate(data), root=tmp_path / "cache")
    assert [s["cues"][0]["label"] for s in manifest["scenes"][1:]] == ["Visual 0", "Visual 1"]
