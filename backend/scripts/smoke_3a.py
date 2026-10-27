"""Real local 3-language offline end-to-end smoke test for Blu Part 3a.

Validates planning once in English, preparing Hindi and Kannada delivery,
measuring per-fact PCM cues, generating SRT subtitles, exporting 720p H.264/AAC MP4s,
and running ffprobe assertions across all 3 languages.
"""
import json
import subprocess
import sys
from urllib.request import Request, urlopen

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = "http://127.0.0.1:8000"


def api(path: str, body: dict | None = None) -> dict:
    if body is None:
        request = Request(ROOT + path)
    else:
        request = Request(
            ROOT + path,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
    with urlopen(request, timeout=900) as response:
        return json.load(response)


def get_text(path: str) -> str:
    request = Request(ROOT + path)
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def probe_video(video_path: str) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type,codec_name,width,height,duration:format=duration",
        "-of",
        "json",
        video_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def has_devanagari(text: str) -> bool:
    return any(0x0900 <= ord(c) <= 0x097F for c in text)


def has_kannada(text: str) -> bool:
    return any(0x0C80 <= ord(c) <= 0x0CFF for c in text)


def main() -> None:
    topic = "How a Python for loop works"
    print(f"=== Blu Part 3a Multilingual Smoke Test: '{topic}' ===")

    # 1. Plan once in English
    planned = api("/api/generate", {
        "topic": topic, "level": "beginner", "language": "en", "target_seconds": 60
    })
    print(f"[1] Planned source: {planned['source']}")
    lesson = planned["lesson"]
    assert lesson["language"] == "en"
    assert len(lesson["scenes"]) >= 3

    # 2. Prepare English
    en_timeline = api("/api/lesson/prepare", {"lesson": lesson})
    en_id = en_timeline["lesson_id"]
    en_total = float(en_timeline["total_seconds"])
    print(f"[2] Prepared English: id={en_id[:16]}..., audio={en_total:.2f}s, voice={en_timeline['voice']}")

    # Export English MP4
    en_export = api(f"/api/lesson/export/{en_id}", {})
    assert en_export["video_codec"] == "h264"
    assert en_export["audio_codec"] == "aac"
    assert (en_export["width"], en_export["height"]) == (1280, 720)
    print(f"    English MP4 exported: {en_export['video_url']}")

    # 3. Prepare Hindi (Kokoro hf_alpha)
    print("\n[3] Preparing Hindi delivery (IndicTrans2 -> Kokoro hf_alpha)...")
    hi_timeline = api("/api/localized/prepare", {"source_lesson_id": en_id, "language": "hi"})
    hi_id = hi_timeline["lesson_id"]
    hi_total = float(hi_timeline["total_seconds"])
    print(f"    Hindi id={hi_id[:16]}..., audio={hi_total:.2f}s, sample_rate={hi_timeline['sample_rate']}")
    assert hi_timeline["language"] == "hi"
    assert hi_timeline["source_lesson_id"] == en_id
    assert hi_id != en_id
    assert len(hi_timeline["scenes"]) == len(en_timeline["scenes"])

    # Validate Hindi script in title, headings, narration, and cues
    hi_title = hi_timeline["lesson"]["title"]
    assert has_devanagari(hi_title), f"No Devanagari in Hindi title: {hi_title}"
    print(f"    Hindi Title: {hi_title}")

    # Validate Hindi subtitles
    hi_srt = get_text(hi_timeline["subtitle_url"])
    assert has_devanagari(hi_srt), "No Devanagari in Hindi SRT"
    assert "-->" in hi_srt
    print(f"    Hindi Subtitles PASS ({len(hi_srt.splitlines())} lines)")

    # Export Hindi MP4
    print("    Exporting Hindi 720p MP4...")
    hi_export = api(f"/api/localized/export/{hi_id}", {})
    assert hi_export["video_codec"] == "h264"
    assert hi_export["audio_codec"] == "aac"
    assert (hi_export["width"], hi_export["height"]) == (1280, 720)
    assert abs(hi_export["duration_seconds"] - hi_total) <= 0.25
    print(f"    Hindi MP4 PASS: duration={hi_export['duration_seconds']:.2f}s")

    # 4. Prepare Kannada (Indic Parler-TTS in .venv-tts)
    print("\n[4] Preparing Kannada delivery (IndicTrans2 -> Indic Parler-TTS in .venv-tts)...")
    kn_timeline = api("/api/localized/prepare", {"source_lesson_id": en_id, "language": "kn"})
    kn_id = kn_timeline["lesson_id"]
    kn_total = float(kn_timeline["total_seconds"])
    print(f"    Kannada id={kn_id[:16]}..., audio={kn_total:.2f}s, sample_rate={kn_timeline['sample_rate']}")
    assert kn_timeline["language"] == "kn"
    assert kn_timeline["source_lesson_id"] == en_id
    assert kn_id != en_id
    assert kn_id != hi_id
    assert len(kn_timeline["scenes"]) == len(en_timeline["scenes"])

    # Validate Kannada script
    kn_title = kn_timeline["lesson"]["title"]
    assert has_kannada(kn_title), f"No Kannada script in title: {kn_title}"
    print(f"    Kannada Title: {kn_title}")

    # Validate Kannada subtitles
    kn_srt = get_text(kn_timeline["subtitle_url"])
    assert has_kannada(kn_srt), "No Kannada script in Kannada SRT"
    assert "-->" in kn_srt
    print(f"    Kannada Subtitles PASS ({len(kn_srt.splitlines())} lines)")

    # Export Kannada MP4
    print("    Exporting Kannada 720p MP4...")
    kn_export = api(f"/api/localized/export/{kn_id}", {})
    assert kn_export["video_codec"] == "h264"
    assert kn_export["audio_codec"] == "aac"
    assert (kn_export["width"], kn_export["height"]) == (1280, 720)
    assert abs(kn_export["duration_seconds"] - kn_total) <= 0.25
    print(f"    Kannada MP4 PASS: duration={kn_export['duration_seconds']:.2f}s")

    # 5. FFprobe assertions on generated MP4 outputs
    print("\n[5] Running FFprobe stream and codec assertions...")
    for lang, vid_id, exp_dur in [("en", en_id, en_total), ("hi", hi_id, hi_total), ("kn", kn_id, kn_total)]:
        rel_path = f"outputs/lessons/{vid_id}.mp4" if lang == "en" else f"outputs/localized/{vid_id}.mp4"
        info = probe_video(rel_path)
        streams = info.get("streams", [])
        v_stream = next(s for s in streams if s["codec_type"] == "video")
        a_stream = next(s for s in streams if s["codec_type"] == "audio")
        assert v_stream["codec_name"] == "h264"
        assert v_stream["width"] == 1280
        assert v_stream["height"] == 720
        assert a_stream["codec_name"] == "aac"
        fmt_dur = float(info["format"]["duration"])
        assert abs(fmt_dur - exp_dur) <= 0.25, f"{lang} duration drift: {fmt_dur} vs {exp_dur}"
        print(f"    ffprobe {lang.upper()}: {v_stream['width']}x{v_stream['height']} {v_stream['codec_name']}/{a_stream['codec_name']}, format_duration={fmt_dur:.2f}s (PASS)")

    print("\n=== BLU PART 3A 3-LANGUAGE SMOKE TEST: ALL GATES PASS ===")


if __name__ == "__main__":
    main()
