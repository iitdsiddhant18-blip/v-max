import json

import pytest
from pydantic import ValidationError

from backend.app.fallback import FALLBACK_DIR, load_fallback_lesson
from backend.app.schema import GenerateRequest, Lesson, Scene


def _valid_lesson_dict():
    with open(FALLBACK_DIR / "python_loop.json", encoding="utf-8") as f:
        return json.load(f)


def test_fallback_lesson_loads_and_has_expected_shape():
    lesson = load_fallback_lesson()
    assert lesson.title == "How a Python loop works"
    assert lesson.language == "en"
    assert [s.type for s in lesson.scenes] == [
        "title_card",
        "code_walkthrough",
        "diagram",
        "step_list",
    ]


def test_every_fallback_file_is_a_valid_lesson():
    files = sorted(FALLBACK_DIR.glob("*.json"))
    assert files, "no fallback lessons found"
    for path in files:
        Lesson.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_lesson_with_too_few_scenes_is_rejected():
    data = _valid_lesson_dict()
    data["scenes"] = data["scenes"][:2]
    with pytest.raises(ValidationError):
        Lesson.model_validate(data)


def test_lesson_with_too_many_scenes_is_rejected():
    data = _valid_lesson_dict()
    data["scenes"] = data["scenes"] + data["scenes"][:3]  # 7 scenes
    with pytest.raises(ValidationError):
        Lesson.model_validate(data)


def test_unknown_scene_type_is_rejected():
    data = _valid_lesson_dict()
    data["scenes"][0]["type"] = "javascript_widget"
    with pytest.raises(ValidationError):
        Lesson.model_validate(data)


def test_code_walkthrough_without_code_is_rejected():
    with pytest.raises(ValidationError):
        Scene(type="code_walkthrough", heading="h", narration="n")


def test_highlight_line_outside_code_is_rejected():
    # code has 2 lines, so line 3 does not exist
    with pytest.raises(ValidationError):
        Scene(
            type="code_walkthrough",
            heading="h",
            narration="n",
            code="a = 1\nb = 2",
            highlight_lines=[3],
        )


def test_highlight_line_zero_is_rejected_because_lines_are_one_based():
    with pytest.raises(ValidationError):
        Scene(
            type="code_walkthrough",
            heading="h",
            narration="n",
            code="a = 1\nb = 2",
            highlight_lines=[0],
        )


def test_diagram_without_items_is_rejected():
    with pytest.raises(ValidationError):
        Scene(type="diagram", heading="h", narration="n")


def test_blank_narration_is_rejected():
    with pytest.raises(ValidationError):
        Scene(type="title_card", heading="h", narration="   ")


def test_extra_unknown_fields_from_the_llm_are_ignored_not_fatal():
    data = _valid_lesson_dict()
    data["scenes"][0]["color"] = "red"
    lesson = Lesson.model_validate(data)
    assert not hasattr(lesson.scenes[0], "color")


def test_generate_request_defaults():
    req = GenerateRequest(topic="  photosynthesis ")
    assert req.topic == "photosynthesis"
    assert req.level == "beginner"
    assert req.language == "en"
    assert req.target_seconds == 60


@pytest.mark.parametrize("seconds", [29, 91])
def test_target_seconds_outside_30_to_90_is_rejected(seconds):
    with pytest.raises(ValidationError):
        GenerateRequest(topic="loops", target_seconds=seconds)


@pytest.mark.parametrize("seconds", [30, 90])
def test_target_seconds_boundaries_30_and_90_are_accepted(seconds):
    assert GenerateRequest(topic="loops", target_seconds=seconds).target_seconds == seconds


def test_unsupported_language_is_rejected():
    with pytest.raises(ValidationError):
        GenerateRequest(topic="loops", language="ta")
