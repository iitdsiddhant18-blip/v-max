"""Render a generated lesson with the same SVG frames as the browser player."""
import math
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from .exporter import FPS, FRONTEND_URL, probe_mp4
from .live import LIVE_ROOT, lesson_folder, load_lesson
from .media import ROOT


def export_lesson(identifier: str, *, frontend_url: str = FRONTEND_URL,
                  root: Path = LIVE_ROOT, output_root: Path | None = None) -> dict:
    manifest = load_lesson(identifier, root=root)
    parsed = urlparse(frontend_url)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost"):
        raise ValueError("Lesson renderer must be a local HTTP server")
    total = float(manifest["total_seconds"])
    if not math.isfinite(total) or not 0 < total <= 600:
        raise ValueError("Invalid lesson audio duration")
    folder = lesson_folder(identifier, root)
    audio = folder / "combined.wav"
    destination = (output_root or ROOT / "outputs" / "lessons") / f"{identifier}.mp4"
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = math.ceil(total * FPS)

    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory(prefix="lesson_frames_", dir=folder) as directory:
        frames = Path(directory)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 720},
                                        device_scale_factor=1, reduced_motion="reduce")

                def local_only(route):
                    if urlparse(route.request.url).hostname in ("127.0.0.1", "localhost"):
                        route.continue_()
                    else:
                        route.abort()

                page.route("**/*", local_only)
                page.goto(f"{frontend_url}/render-lesson?id={identifier}",
                          wait_until="domcontentloaded", timeout=30000)
                page.wait_for_function("window.__BLU_READY__ === true", timeout=30000)
                stage = page.locator("#lesson-stage")
                bounds = stage.bounding_box()
                if not bounds or round(bounds["width"]) != 1280 or round(bounds["height"]) != 720:
                    raise ValueError(f"SVG render surface not 1280x720: {bounds}")
                for frame in range(count):
                    stamp = min(frame / FPS, total - 0.000001)
                    page.evaluate("(t) => window.__BLU_SET_TIME__(t)", stamp)
                    page.wait_for_function(
                        "(t) => { const s = document.querySelector('#lesson-stage'); "
                        "return s && Math.abs(Number(s.dataset.time) - t) < 0.000002; }",
                        arg=stamp, timeout=10000)
                    stage.screenshot(path=str(frames / f"frame_{frame:06d}.png"),
                                     animations="disabled")
            finally:
                browser.close()
        args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate",
                str(FPS), "-i", str(frames / "frame_%06d.png"), "-i", str(audio),
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.6f}",
                "-movflags", "+faststart", str(destination)]
        try:
            subprocess.run(args, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"FFmpeg failure: {exc.stderr[-2000:]}") from exc

    details = probe_mp4(destination)
    if abs(details["duration_seconds"] - total) > 0.25:
        raise ValueError("MP4 and WAV durations differ")
    return {"video_url": f"/api/lesson/video/{identifier}", "fps": FPS,
            "frames": count, "expected_duration_seconds": total, **details}
