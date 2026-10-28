"""Read-only quality gate for three already-prepared, already-exported lesson IDs.

No AI calls, downloads, deletions, media writes or model loads are performed.
"""
import argparse
import json
import subprocess
from pathlib import Path
from urllib.request import urlopen

from backend.app.media import ROOT

BASE = "http://127.0.0.1:8000"


def api(path: str) -> dict:
    with urlopen(BASE + path, timeout=20) as response:
        return json.load(response)


def probe(path: Path) -> dict:
    if not path.is_file():
        raise AssertionError(f"Expected MP4 missing: {path}")
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height:format=duration", "-of", "json", str(path),
    ], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def check_video(path: Path, seconds: float) -> None:
    details = probe(path)
    video = next(s for s in details["streams"] if s["codec_type"] == "video")
    audio = next(s for s in details["streams"] if s["codec_type"] == "audio")
    assert (video["codec_name"], video["width"], video["height"]) == ("h264", 1280, 720)
    assert audio["codec_name"] == "aac"
    assert abs(float(details["format"]["duration"]) - seconds) <= 0.25


def check_cues(manifest: dict) -> None:
    cursor = 0
    for scene in manifest["scenes"]:
        start = float(scene["start_seconds"])
        assert abs(start - cursor) <= .003
        prior = 0
        for cue in scene.get("cues", []):
            lower, upper = float(cue["start_seconds"]), float(cue["end_seconds"])
            assert prior <= lower + .003 < upper <= float(scene["audio_seconds"]) + .003
            assert cue["text"].strip()
            prior = upper
        cursor += float(scene["duration_seconds"])
    assert abs(cursor - float(manifest["total_seconds"])) <= .01


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--english-id", required=True)
    parser.add_argument("--hindi-id", required=True)
    parser.add_argument("--kannada-id", required=True)
    args = parser.parse_args()

    english = api(f"/api/lesson/timeline/{args.english_id}")
    hindi = api(f"/api/localized/timeline/{args.hindi_id}")
    kannada = api(f"/api/localized/timeline/{args.kannada_id}")
    source = english["lesson"]

    for lang, item in [("en", english), ("hi", hindi), ("kn", kannada)]:
        assert item["language"] == lang
        assert 30 <= float(item["total_seconds"]) <= 90
        assert len(item["scenes"]) == len(source["scenes"])
        check_cues(item)
        if lang != "en":
            assert item["source_lesson_id"] == args.english_id
            assert item["semantic_lesson"] == source
            for original, translated in zip(source["scenes"], item["lesson"]["scenes"]):
                assert original["code"] == translated["code"]
                assert original["highlight_lines"] == translated["highlight_lines"]

        folder = "lessons" if lang == "en" else "localized"
        path = ROOT / "outputs" / folder / f"{item['lesson_id']}.mp4"
        check_video(path, float(item["total_seconds"]))
        print(lang, item["lesson_id"], round(item["total_seconds"], 3),
              "seconds", "MP4 PASS")

    print("FINAL LOCAL SOURCE/VOICE/MP4 STRUCTURE: PASS")
    print("NOTE: Physical Wi-Fi-off and human language quality MUST be checked separately.")


if __name__ == "__main__":
    main()
