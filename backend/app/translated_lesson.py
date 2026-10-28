"""Pure content translation preserving the exact English teaching-beat structure.

The caller supplies a real local translator. This module never loads or downloads models.
"""
import re
from collections.abc import Callable

from .live import BEAT_SEPARATOR, visual_beats
from .schema import Lesson

INDIC_SCRIPTS = {"hi": (0x0900, 0x097F), "kn": (0x0C80, 0x0CFF)}
ZERO_WIDTH = re.compile("[\u200b\u200c\u200d\ufeff]")

# Approved technical / mathematical tokens exempt from Indic script requirement when standalone
APPROVED_TECHNICAL_TOKENS = {
    # Math functions & constants
    "sin", "cos", "tan", "cot", "sec", "csc", "log", "ln", "exp", "lim",
    "max", "min", "det", "abs", "sqrt", "pi", "rad", "deg", "dx", "dt", "dy", "dz",
    # Units
    "m", "s", "kg", "km", "cm", "mm", "ms", "hz", "khz", "mhz", "ghz",
    "pa", "kpa", "j", "kj", "w", "kw", "v", "mv", "a", "ma", "mol", "k", "db", "n", "ohm",
    # Domain entities & biology/chemistry terms
    "alice", "bob", "python", "dna", "rna", "atp", "adp", "ph",
    # Common code keywords
    "def", "int", "str", "float", "bool", "len", "range", "print", "return",
    "for", "in", "if", "else", "elif", "while", "null", "true", "false",
    "none", "void", "class", "var", "let", "const",
}


def clean_text(value: str) -> str:
    """Remove invisible characters known to break local voice/caption alignment."""
    return ZERO_WIDTH.sub("", value).strip()


def has_script(text: str, language: str) -> bool:
    if language not in INDIC_SCRIPTS:
        return False
    lower, upper = INDIC_SCRIPTS[language]
    return any(lower <= ord(char) <= upper for char in text)


def is_exempt_technical_fact(fact: str) -> bool:
    """Determine if a visual fact consists purely of numbers, mathematical formulas,
    coordinates, chemical formulas, code tokens, or approved technical symbols."""
    cleaned = clean_text(fact)
    if not cleaned:
        return False
    words = re.findall(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b", cleaned)
    if not words:
        # Purely numeric/symbolic (e.g. "(0, 0)", "1, 2, 3", "+5 - 3 = 2")
        return True
    for word in words:
        w_lower = word.lower()
        if len(word) == 1:
            # Single-letter variable names (x, y, i, j, n, a, b, c, etc.)
            continue
        if w_lower in APPROVED_TECHNICAL_TOKENS:
            continue
        # Chemical formulas like H2O, CO2, NaCl, C6H12O6
        cleaned_formula = re.sub(r"[₀-₉0-9]", "", word)
        if re.fullmatch(r"(?:[A-Z][a-z]?)+", cleaned_formula) and len(cleaned_formula) <= 8:
            continue
        # Unapproved English word indicates untranslated English prose
        return False
    return True


def validate_translated_fact(fact: str, language: str) -> None:
    cleaned = clean_text(fact)
    if not cleaned:
        raise ValueError("Empty or whitespace translated visual fact")
    if has_script(cleaned, language):
        return
    if is_exempt_technical_fact(cleaned):
        return
    raise ValueError("A spoken visual fact is not in the requested script")


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
    if not has_script(result.title, language):
        raise ValueError(f"Translated title lacks target script ({language})")

    for source, translated in zip(english.scenes, result.scenes):
        if (source.type != translated.type or source.code != translated.code
                or source.highlight_lines != translated.highlight_lines
                or len(source.items) != len(translated.items)):
            raise ValueError("Translation changed code or visual topology")
        if not has_script(translated.heading, language):
            raise ValueError(f"Scene heading lacks target script ({language})")
        if source.subtitle and not has_script(translated.subtitle or "", language):
            raise ValueError(f"Scene subtitle lacks target script ({language})")
        if not has_script(translated.narration, language):
            raise ValueError("A spoken visual fact is not in the requested script")

        if source.type == "title_card":
            for item in translated.items:
                fact = item.partition(BEAT_SEPARATOR)[2] if BEAT_SEPARATOR in item else item
                validate_translated_fact(fact, language)
        else:
            for item in translated.items:
                label, sep, fact = item.partition(BEAT_SEPARATOR)
                if not sep:
                    raise ValueError("Localized visual item missing beat separator")
                if source.type != "code_walkthrough":
                    validate_translated_fact(label, language)
                validate_translated_fact(fact, language)

    return result
