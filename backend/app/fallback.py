"""Built-in sample lessons. These guarantee the demo never breaks."""
import json
from pathlib import Path

from .schema import Lesson

FALLBACK_DIR = Path(__file__).resolve().parent.parent / "fallback"
DEFAULT_FALLBACK = "python_loop"


def load_fallback_lesson(name: str = DEFAULT_FALLBACK) -> Lesson:
    """Load and validate a built-in lesson. Raises if the file is missing or invalid,
    because a broken fallback must be caught by tests, never at demo time."""
    path = FALLBACK_DIR / f"{name}.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Lesson.model_validate(data)
