"""Real local Ollama + Kokoro + Playwright + FFmpeg smoke; servers must be running."""
import json
from urllib.request import Request, urlopen

ROOT = "http://127.0.0.1:8000"


def api(path: str, body: dict | None = None) -> dict:
    if body is None:
        request = Request(ROOT + path)
    else:
        request = Request(ROOT + path, data=json.dumps(body).encode("utf-8"),
                          headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=900) as response:
        return json.load(response)


def main() -> None:
    identifiers = set()
    for topic in ("Photosynthesis", "How a Python for loop works"):
        planned = api("/api/generate", {"topic": topic, "level": "beginner",
                                        "language": "en", "target_seconds": 60})
        assert planned["source"] == "llm", f"Ollama unexpectedly fell back for {topic}"
        lesson = planned["lesson"]
        assert 3 <= len(lesson["scenes"]) <= 6
        types = [scene["type"] for scene in lesson["scenes"]]
        assert "diagram" in types
        assert ("code_walkthrough" in types) == ("Python" in topic)
        print("planned", topic, "source", planned["source"], "scene types", types, flush=True)
        timeline = api("/api/lesson/prepare", {"lesson": lesson})
        assert timeline["kind"] == "generated"
        assert timeline["lesson"] == lesson
        assert len(timeline["scenes"]) == len(lesson["scenes"])
        assert 30 <= timeline["total_seconds"] <= 90
        assert all(scene.get("cues") for scene in timeline["scenes"])
        identifiers.add(timeline["lesson_id"])
        print("lesson ID", timeline["lesson_id"], "WAV seconds", timeline["total_seconds"], flush=True)
        exported = api(f"/api/lesson/export/{timeline['lesson_id']}", {})
        assert exported["video_codec"] == "h264"
        assert exported["audio_codec"] == "aac"
        assert (exported["width"], exported["height"]) == (1280, 720)
        assert abs(exported["duration_seconds"] - timeline["total_seconds"]) < 0.25
        with urlopen(ROOT + exported["video_url"], timeout=60) as video:
            content = video.read()
            assert video.status == 200 and len(content) > 1024
            print("download", video.status, len(content), "bytes", flush=True)
        print(topic, "|", planned["source"], "|", len(lesson["scenes"]),
              "scenes |", timeline["total_seconds"], "seconds | MP4 PASS")
    assert len(identifiers) == 2
    print("Part 2b live English topic-to-MP4 smoke: PASS")


if __name__ == "__main__":
    main()
