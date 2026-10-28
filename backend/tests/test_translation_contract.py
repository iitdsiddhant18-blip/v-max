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


def multi_scene_english_lesson() -> Lesson:
    return Lesson.model_validate({
        "title": "Algorithm and Data", "level": "beginner", "language": "en",
        "scenes": [
            {
                "type": "title_card",
                "heading": "Introduction to Algorithms",
                "narration": "Algorithms solve computational problems step by step.",
                "items": ["Overview :: Core computing fundamentals."],
            },
            {
                "type": "diagram",
                "heading": "Memory and Variables",
                "items": [
                    "Memory :: Values are stored in addressed cells.",
                    "Pointer :: References point directly to memory locations.",
                ],
                "narration": "Values are stored in addressed cells. References point directly to memory locations.",
            },
            {
                "type": "code_walkthrough",
                "heading": "Execution Step",
                "code": "x = 10\nprint(x)",
                "highlight_lines": [1, 2],
                "items": [
                    "Line 1 :: Assign integer ten to variable x.",
                    "Line 2 :: Output variable x to standard output stream.",
                ],
                "narration": "Assign integer ten to variable x. Output variable x to standard output stream.",
            },
        ],
    })


@pytest.mark.parametrize("lang,phrase", [("hi", "यह हिंदी अनुवाद है।"),
                                          ("kn", "ಇದು ಕನ್ನಡ ಅನುವಾದವಾಗಿದೆ.")])
def test_valid_multi_scene_translation_preserves_topology_and_code(lang, phrase):
    english = multi_scene_english_lesson()
    localized = translate_lesson(english, lang, lambda texts, _l: [phrase for _ in texts])
    assert localized.language == lang
    assert len(localized.scenes) == 3
    assert localized.scenes[0].type == "title_card"
    assert localized.scenes[1].type == "diagram"
    assert localized.scenes[2].type == "code_walkthrough"
    assert localized.scenes[2].code == english.scenes[2].code
    assert localized.scenes[2].highlight_lines == [1, 2]
    assert localized.scenes[2].items[0].startswith("Line 1 :: ")
    assert localized.scenes[2].items[1].startswith("Line 2 :: ")
    assert has_script(localized.title, lang)
    assert all(has_script(s.narration, lang) for s in localized.scenes)


@pytest.mark.parametrize("lang,phrase", [("hi", "यह हिंदी अनुवाद है।"),
                                          ("kn", "ಇದು ಕನ್ನಡ ಅನುವಾದವಾಗಿದೆ.")])
def test_scene_two_narration_in_english_rejected(lang, phrase):
    english = multi_scene_english_lesson()
    # Scene 0 has 4 phrases (title, heading, narration, label, fact) -> wait, let's map by text index or phrase
    # Let's count phrases for multi_scene_english_lesson:
    # 0: title "Algorithm and Data"
    # Scene 0: heading (1), narration (2), item label (3), item fact (4)
    # Scene 1: heading (5), item 1 label (6), fact (7), item 2 label (8), fact (9)
    # Scene 2: heading (10), item 1 fact (11), item 2 fact (12)
    def translator_leaking_scene_two(texts, _l):
        out = []
        for t in texts:
            if "addressed cells" in t:
                # English leak in scene 1 (second scene) narration fact
                out.append("Values are stored in addressed cells without translation.")
            else:
                out.append(phrase)
        return out

    with pytest.raises(ValueError, match="script"):
        translate_lesson(english, lang, translator_leaking_scene_two)


@pytest.mark.parametrize("lang,phrase", [("hi", "यह हिंदी अनुवाद है।"),
                                          ("kn", "ಇದು ಕನ್ನಡ ಅನುವಾದವಾಗಿದೆ.")])
def test_scene_three_narration_in_english_rejected(lang, phrase):
    english = multi_scene_english_lesson()

    def translator_leaking_scene_three(texts, _l):
        out = []
        for t in texts:
            if "variable x" in t:
                # English leak in scene 2 (last scene) narration fact
                out.append("Assign integer ten to variable x in pure English.")
            else:
                out.append(phrase)
        return out

    with pytest.raises(ValueError, match="script"):
        translate_lesson(english, lang, translator_leaking_scene_three)


@pytest.mark.parametrize("lang,phrase", [("hi", "यह हिंदी अनुवाद है।"),
                                          ("kn", "ಇದು ಕನ್ನಡ ಅನುವಾದವಾಗಿದೆ.")])
def test_last_scene_english_visual_fact_rejected(lang, phrase):
    english = multi_scene_english_lesson()

    def translator_leaking_last_fact(texts, _l):
        out = []
        for t in texts:
            if "standard output stream" in t:
                out.append("This is untranslated narrative prose describing the output stream.")
            else:
                out.append(phrase)
        return out

    with pytest.raises(ValueError, match="script"):
        translate_lesson(english, lang, translator_leaking_last_fact)


@pytest.mark.parametrize("lang,phrase", [("hi", "यह हिंदी अनुवाद है।"),
                                          ("kn", "ಇದು ಕನ್ನಡ ಅನುವಾದವಾಗಿದೆ.")])
def test_symbolic_coordinates_and_code_tokens_retained_without_script_rejection(lang, phrase):
    math_lesson = Lesson.model_validate({
        "title": "Quadratic Plot", "level": "intermediate", "language": "en",
        "scenes": [
            {"type": "title_card", "heading": "Plotting Functions", "narration": "We plot the parabola."},
            {"type": "diagram", "heading": "Key Points",
             "items": ["Vertex :: The origin coordinates are (0, 0) on the plane.",
                       "Coordinates :: Plotted points are x = -2, y = 4; x = 2, y = 4."],
             "narration": "Notice the symmetry around the origin."},
            {"type": "step_list", "heading": "Summary",
             "items": ["Formula :: The standard quadratic curve follows y = x^2.",
                       "Result :: Curvature opens upward symmetrically across the axis."],
             "narration": "The curve is symmetric across the y axis."},
        ],
    })

    def math_translator(texts, _l):
        out = []
        for t in texts:
            if "x = -2" in t:
                # Retain purely symbolic ASCII mathematical coordinates without Indic script
                out.append("x = -2, y = 4; x = 2, y = 4")
            elif "y = x^2" in t:
                # Retain purely symbolic formula
                out.append("y = x^2")
            else:
                out.append(phrase)
        return out

    localized = translate_lesson(math_lesson, lang, math_translator)
    assert localized.language == lang
    assert "x = -2, y = 4" in localized.scenes[1].items[1]
    assert "y = x^2" in localized.scenes[2].items[0]


def test_title_card_items_with_translated_paired_facts():
    english = Lesson.model_validate({
        "title": "Introduction", "level": "beginner", "language": "en",
        "scenes": [
            {"type": "title_card", "heading": "Title Heading", "narration": "Introductory words.",
             "items": ["Goal :: Master algorithms", "Prereq :: Basic math"]},
            {"type": "diagram", "heading": "Concept Diagram", "narration": "Core explanation text.",
             "items": ["Item 1 :: First detail explains the core algorithm mechanism.",
                       "Item 2 :: Second detail traces the state transition accurately."]},
            {"type": "step_list", "heading": "Takeaway", "narration": "Closing recap text.",
             "items": ["Summary :: Key learning points are reviewed thoroughly here.",
                       "Next :: Practice exercises reinforce theoretical understanding."]},
        ],
    })
    hi_phrase = "यह हिंदी वाक्य है।"
    localized = translate_lesson(english, "hi", lambda texts, _l: [hi_phrase for _ in texts])
    assert localized.language == "hi"
    assert len(localized.scenes[0].items) == 2
    assert localized.scenes[0].items[0] == f"{hi_phrase} :: {hi_phrase}"
