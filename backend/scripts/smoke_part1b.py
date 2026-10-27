"""Run against BOTH live servers: FastAPI :8000 and Vite :5173."""
import sys

import requests

base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")

for language in ("en", "hi"):
    response = requests.post(f"{base}/api/sample/prepare", json={"language": language}, timeout=600)
    response.raise_for_status()
    manifest = response.json()
    assert manifest["language"] == manifest["lesson"]["language"] == language
    assert len(manifest["scenes"]) == len(manifest["lesson"]["scenes"]) == 4
    assert manifest["total_seconds"] > 0
    print("prepared", language, "scenes", len(manifest["scenes"]),
          "audio-derived seconds", manifest["total_seconds"])

    audio = requests.get(f"{base}{manifest['audio_url']}", timeout=30)
    audio.raise_for_status()
    assert audio.content[:4] == b"RIFF"
    print("combined WAV", language, "bytes", len(audio.content))

    response = requests.post(f"{base}/api/sample/export", json={"language": language}, timeout=1200)
    response.raise_for_status()
    result = response.json()
    assert result["width"] == 1280 and result["height"] == 720
    assert result["video_codec"] == "h264" and result["audio_codec"] == "aac"
    assert abs(result["duration_seconds"] - manifest["total_seconds"]) < 0.25
    print("exported", language, "fps", result["fps"], "frames", result["frames"],
          "duration", result["duration_seconds"])
    video = requests.get(f"{base}{result['video_url']}", timeout=120)
    video.raise_for_status()
    assert len(video.content) > 1024
    print("download MP4", language, "status", video.status_code, "bytes", len(video.content))

print("Part 1b Gate 1 smoke: PASS")
