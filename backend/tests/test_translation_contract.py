"""Model-free translation, captions and code-safety contract tests."""
import pytest

from backend.app.schema import Lesson
from backend.app.translated_lesson import translate_lesson, has_script, clean_text
from backend.app.subtitles import manifest_to_srt, srt_time


def english_lesson() -> Lesson:
    return Lesson.model_validate({
        "title": "Python loops", "level": "beginner", "language": "en",
        "scenes": [
            {"type": "title_card", "heading": "What is a loop?", "narration": "Loops repeat steps."},
            {"type": "code_walkthrough", "heading": "Read the code",
             "code": "for i in range(3):\n    print(i)", "highlight_lines": [1, 2],
             "items": ["Line 1 :: Take each next value from range three.",
                       "Line 2 :: Print the current value to the screen."],
             "narration": "Take each next value from range three. Print the current value to the screen."},
            {"type": "step_list", "heading": "Recap", "narration": "Loop then print.",
             "items": ["Next :: A loop gets a new value from its input.",
                       "Print :: The body prints the value from that pass."]},
        ],
    })


@pytest.mark.parametrize("lang,phrase", [("hi", "यह हिंदी वाक्य है।"),
                                          ("kn", "ಇದು ಕನ್ನಡ ವಾಕ್ಯವಾಗಿದೆ.")])
def test_translation_keeps_code_scene_count_items_and_line_numbers(lang, phrase):
    english = english_lesson()
    calls = []

    def fake_translate(texts, target):
        calls.append((texts, target))
        return [phrase for _ in texts]

    localized = translate_lesson(english, lang, fake_translate)
    assert localized.language == lang
    assert [s.type for s in localized.scenes] == [s.type for s in english.scenes]
    assert localized.scenes[1].code == english.scenes[1].code
    assert localized.scenes[1].highlight_lines == [1, 2]
    assert localized.scenes[1].items[0].startswith("Line 1 :: ")
    assert localized.scenes[1].items[1].startswith("Line 2 :: ")
    assert localized.scenes[1].narration == phrase + " " + phrase
    assert calls[0][1] == lang


def test_source_cannot_be_mislabelled_and_english_echo_fails():
    with pytest.raises(ValueError, match="English source"):
        translate_lesson(english_lesson(), "en", lambda x, _lang: x)
    with pytest.raises(ValueError, match="No expected"):
        translate_lesson(english_lesson(), "hi", lambda x, _lang: x)


def test_wrong_translation_count_fails_closed():
    with pytest.raises(ValueError, match="count mismatch"):
        translate_lesson(english_lesson(), "kn", lambda x, _lang: ["ಕನ್ನಡ"])


def test_zero_width_removed_but_script_kept():
    assert clean_text("क\u200bन्नड़") == "कन्नड़"
    assert has_script("ಪಾಠ", "kn")


def test_srt_has_exact_real_cue_times_and_no_pauses():
    manifest = {"total_seconds": 4.0, "scenes": [
        {"start_seconds": 0, "audio_seconds": 1.25, "cues": [
            {"text": "पानी", "start_seconds": 0, "end_seconds": 0.75},
            {"text": "धूप", "start_seconds": 0.75, "end_seconds": 1.25}]},
        {"start_seconds": 1.75, "audio_seconds": 1.75, "cues": [
            {"text": "ಬೆಳಕು", "start_seconds": 0, "end_seconds": 1.75}]},
    ]}
    output = manifest_to_srt(manifest)
    assert "00:00:00,750 --> 00:00:01,250" in output
    assert "00:00:01,750 --> 00:00:03,500" in output
    assert "पानी" in output and "ಬೆಳಕು" in output
    assert srt_time(3661.001) == "01:01:01,001"


def test_srt_rejects_wrong_cue_order():
    manifest = {"total_seconds": 2, "scenes": [{"start_seconds": 0, "audio_seconds": 2,
        "cues": [{"text": "text", "start_seconds": 1, "end_seconds": .5}]}]}
    with pytest.raises(ValueError, match="overlapping"):
        manifest_to_srt(manifest)
