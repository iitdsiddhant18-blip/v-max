"""Deterministic, offline 1280x720 Playwright/FFmpeg sample exporter."""
import json
import math
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from .media import CACHE_ROOT, ROOT, SampleLanguage

FPS = 15
FRONTEND_URL = "http://127.0.0.1:5173"


def probe_mp4(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,width,height:format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    if (not video or not audio or video.get("codec_name") != "h264"
            or audio.get("codec_name") != "aac"
            or (video.get("width"), video.get("height")) != (1280, 720)):
        raise ValueError(f"Unexpected MP4 video/audio streams: {data}")
    return {"width": 1280, "height": 720, "video_codec": "h264",
            "audio_codec": "aac", "duration_seconds": float(data["format"]["duration"])}


def export_sample(
    language: SampleLanguage, manifest: dict, *,
    frontend_url: str = FRONTEND_URL,
    cache_root: Path = CACHE_ROOT,
    output_root: Path | None = None,
) -> dict:
    """Render actual player frames at explicit timestamps; mux exact audio timeline."""
    if language not in ("en", "hi") or manifest["language"] != language:
        raise ValueError("Unsupported or mismatched sample language")
    parsed = urlparse(frontend_url)
    if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1"):
        raise ValueError("Export renderer must use a localhost frontend")
    total = float(manifest["total_seconds"])
    if not math.isfinite(total) or total <= 0 or total > 600:
        raise ValueError("Invalid sample duration")
    audio_path = cache_root / language / "combined.wav"
    if not audio_path.is_file():
        raise FileNotFoundError("Sample audio has not been prepared")
    target = (output_root or ROOT / "outputs" / "part1b") / language / "python_loop.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)
    frame_count = math.ceil(total * FPS)

    # Imports are lazy: Part 1a API/tests must work without a browser process.
    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory(prefix="frames_", dir=cache_root) as tmp:
        temp = Path(tmp)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 720},
                                        device_scale_factor=1, reduced_motion="reduce")

                def allow_local(route):
                    host = urlparse(route.request.url).hostname
                    if host in ("localhost", "127.0.0.1"):
                        route.continue_()
                    else:
                        route.abort()

                page.route("**/*", allow_local)
                page.goto(f"{frontend_url}/render?lang={language}",
                          wait_until="domcontentloaded", timeout=30000)
                page.wait_for_function("window.__BLU_READY__ === true", timeout=30000)
                stage = page.locator("#lesson-stage")
                stage.wait_for(state="visible")
                size = stage.bounding_box()
                if not size or round(size["width"]) != 1280 or round(size["height"]) != 720:
                    raise ValueError(f"Export stage must be exactly 1280x720: {size}")

                for frame in range(frame_count):
                    time_seconds = min(frame / FPS, total - 0.000001)
                    page.evaluate("(t) => window.__BLU_SET_TIME__(t)", time_seconds)
                    page.wait_for_function(
                        "(t) => { const s = document.querySelector('#lesson-stage'); "
                        "return s && Math.abs(Number(s.dataset.time) - t) < 0.000002; }",
                        arg=time_seconds, timeout=10000,
                    )
                    stage.screenshot(path=str(temp / f"frame_{frame:06d}.png"),
                                     animations="disabled")
            finally:
                browser.close()

        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-framerate", str(FPS), "-i", str(temp / "frame_%06d.png"),
            "-i", str(audio_path), "-c:v", "libx264", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-t", f"{total:.6f}", "-movflags", "+faststart", str(target),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"FFmpeg failed: {exc.stderr[-2000:]}") from exc

    details = probe_mp4(target)
    if abs(details["duration_seconds"] - total) > 0.25:
        raise ValueError("Exported MP4 duration differs from the audio timeline")
    return {"video_url": f"/api/sample/video/{language}", "frames": frame_count,
            "fps": FPS, "expected_duration_seconds": total, **details}
