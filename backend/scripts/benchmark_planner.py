"""Measure and inspect ten local topics. Does not call any external AI API."""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app.planner import ALLOWED_MODELS, plan_lesson
from backend.app.schema import GenerateRequest

CASES = [
    ("How a Python for loop works", "beginner"),
    ("Photosynthesis", "beginner"),
    ("Newton's first law of motion", "beginner"),
    ("Solving quadratic equations", "intermediate"),
    ("The water cycle", "beginner"),
    ("Acids and bases", "beginner"),
    ("How the human heart pumps blood", "intermediate"),
    ("The French Revolution", "intermediate"),
    ("How a computer network works", "beginner"),
    ("Mean, median and mode", "beginner"),
]

parser = argparse.ArgumentParser()
parser.add_argument("--model", choices=ALLOWED_MODELS, required=True)
parser.add_argument("--seconds", type=int, choices=(30, 60, 90), default=60)
args = parser.parse_args()

rows = []
for topic, level in CASES:
    request = GenerateRequest(topic=topic, level=level, target_seconds=args.seconds)
    start = time.perf_counter()
    source, lesson = plan_lesson(request, model=args.model)
    elapsed = round(time.perf_counter() - start, 2)
    row = {
        "topic": topic, "model": args.model, "source": source, "seconds": elapsed,
        "scene_types": [s.type for s in lesson.scenes],
        "narration_words": sum(len(s.narration.split()) for s in lesson.scenes),
        "lesson": lesson.model_dump(),
    }
    rows.append(row)
    print(topic, "|", source, "|", elapsed, "s |", len(lesson.scenes),
          "scenes |", row["narration_words"], "words")

folder = Path("outputs") / "benchmarks"
folder.mkdir(parents=True, exist_ok=True)
path = folder / f"planner_{args.model.replace(':', '_')}_{args.seconds}s.json"
path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print("LLM-valid lessons:", sum(row["source"] == "llm" for row in rows), "/", len(rows))
print("Raw lessons saved:", path)
print("Human review required: factual accuracy, level, scene choice, clarity, topic relevance")
