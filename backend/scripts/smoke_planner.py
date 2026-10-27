"""HTTP smoke for the real local planner; use while Ollama and FastAPI run."""
import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app.schema import Lesson

parser = argparse.ArgumentParser()
parser.add_argument("--base", default="http://127.0.0.1:8000")
parser.add_argument("--expect-source", choices=("llm", "fallback"), default="llm")
args = parser.parse_args()

topics = ("Photosynthesis", "How a Python for loop works")
for topic in topics:
    payload = {"topic": topic, "level": "beginner", "language": "kn", "target_seconds": 60}
    response = requests.post(f"{args.base.rstrip('/')}/api/generate", json=payload, timeout=240)
    response.raise_for_status()
    data = response.json()
    lesson = Lesson.model_validate(data["lesson"])
    assert data["source"] == args.expect_source, data
    assert data["request"] == payload
    assert lesson.language == "en"
    assert 3 <= len(lesson.scenes) <= 6
    assert lesson.scenes[0].type == "title_card"
    assert lesson.scenes[-1].type == "step_list"
    print("topic:", topic)
    print("source:", data["source"], "language:", lesson.language,
          "scenes:", len(lesson.scenes))
    print("title:", lesson.title)
    print("scene types:", [scene.type for scene in lesson.scenes])

print("Part 2a planner HTTP smoke: PASS")
