"""Pure content translation preserving the exact English teaching-beat structure.

The caller supplies a real local translator. This module never loads or downloads models.
"""
import re
from collections.abc import Callable

from .live import BEAT_SEPARATOR, visual_beats
from .schema import Lesson

INDIC_SCRIPTS = {"hi": (0x0900, 0x097F), "kn": (0x0C80, 0x0CFF)}
ZERO_WIDTH = re.compile("[\u200b\u200c\u200d\ufeff]")


def clean_text(value: str) -> str:
    """Remove invisible characters known to break local voice/caption alignment."""
    return ZERO_WIDTH.sub("", value).strip()


def has_script(text: str, language: str) -> bool:
    lower, upper = INDIC_SCRIPTS[language]
    return any(lower <= ord(char) <= upper for char in text)


def translate_lesson(
    english: Lesson, language: str,
    translate_many: Callable[[list[str], str], list[str]],
) -> Lesson:
    """Translate titles/visual facts, preserve scene order, type, code and cue mapping.

    All English visual items beyond the title card MUST have ``label :: spoken fact``.
    A code beat retains ``Line N`` as the semantic key; the localized fact is
    translated, but the line number is never translated or renumbered.
    """
    if english.language != "en" or language not in INDIC_SCRIPTS:
        raise ValueError("Expected an English source and target hi or kn")
    phrases: list[str] = [english.title]
    for index, scene in enumerate(english.scenes):
        phrases.append(scene.heading)
        if scene.subtitle:
            phrases.append(scene.subtitle)
        if scene.type == "title_card":
            phrases.append(scene.narration)
            for item in scene.items:
                label, sep, fact = item.partition(BEAT_SEPARATOR)
                if sep:
                    phrases.extend([label, fact])
                else:
                    phrases.append(item)
        else:
            beats = visual_beats(scene, strict=True)
            if not beats:
                raise ValueError("Missing explicit English visual facts")
            for beat_index, beat in enumerate(beats):
                if scene.type != "code_walkthrough":
                    phrases.append(beat["label"])
                phrases.append(beat["text"])

    translations = translate_many(phrases, language)
    if len(translations) != len(phrases):
        raise ValueError("Translator result count mismatch")
    translations = [clean_text(item) for item in translations]
    if not all(isinstance(t, str) and t for t in translations):
        raise ValueError("Empty translated string")
    # A total English echo is never considered a successful target-language lesson.
    if not any(has_script(t, language) for t in translations):
        raise ValueError("No expected Hindi/Kannada script in translation")

    iterator = iter(translations)
    data = english.model_dump()
    data["title"] = next(iterator)
    data["language"] = language
    for scene in data["scenes"]:
        scene["heading"] = next(iterator)
        if scene["subtitle"]:
            scene["subtitle"] = next(iterator)
        if scene["type"] == "title_card":
            scene["narration"] = next(iterator)
            title_items = []
            for item in scene["items"]:
                label, sep, _fact = item.partition(BEAT_SEPARATOR)
                if sep:
                    title_items.append(next(iterator) + BEAT_SEPARATOR + next(iterator))
                else:
                    title_items.append(next(iterator))
            scene["items"] = title_items
            continue
        localized_items: list[str] = []
        spoken_facts: list[str] = []
        for english_item in scene["items"]:
            label, sep, _fact = english_item.partition(BEAT_SEPARATOR)
            if not sep:
                raise ValueError("English visual item is missing beat separator")
            localized_label = label if scene["type"] == "code_walkthrough" else next(iterator)
            translated_fact = next(iterator)
            localized_items.append(localized_label + BEAT_SEPARATOR + translated_fact)
            spoken_facts.append(translated_fact)
        scene["items"] = localized_items
        scene["narration"] = " ".join(spoken_facts)
    try:
        next(iterator)
    except StopIteration:
        pass
    else:
        raise ValueError("Translator returned unconsumed strings")
    result = Lesson.model_validate(data)
    if len(result.scenes) != len(english.scenes):
        raise ValueError("Scene count changed")
    for source, translated in zip(english.scenes, result.scenes):
        if (source.type != translated.type or source.code != translated.code
                or source.highlight_lines != translated.highlight_lines
                or len(source.items) != len(translated.items)):
            raise ValueError("Translation changed code or visual topology")
        if source.type != "title_card" and not all(
            has_script(item.partition(BEAT_SEPARATOR)[2], language) for item in translated.items
        ):
            raise ValueError("A spoken visual fact is not in the requested script")
    return result
