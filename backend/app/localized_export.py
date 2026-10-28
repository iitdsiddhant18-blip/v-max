"""Render a localized generated lesson with Playwright and FFmpeg to 720p H.264/AAC MP4."""
import math
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from .exporter import FPS, FRONTEND_URL, probe_mp4
from .localized_media import LOCALIZED_ROOT, load_localized, localized_folder
from .media import ROOT


def export_localized(
    identifier: str,
    *,
    frontend_url: str = FRONTEND_URL,
    root: Path = LOCALIZED_ROOT,
    output_root: Path | None = None,
) -> dict:
    """Export a localized lesson to 1280x720 H.264/AAC MP4 using browser-rendered SVG frames."""
    manifest = load_localized(identifier, root=root, enforce_duration=True)
    from .visual_cache import attach_visual
    manifest = attach_visual(manifest)
    revision = manifest.get('render_id')
    parsed = urlparse(frontend_url)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost"):
        raise ValueError("Localized lesson renderer must be a local HTTP server")

    total = float(manifest["total_seconds"])
    if not math.isfinite(total) or not 30 <= total <= 90:
        raise ValueError(f"Invalid localized lesson audio duration: {total}")

    folder = localized_folder(identifier, root)
    audio = folder / "combined.wav"
    if not audio.is_file():
        raise FileNotFoundError(f"Combined WAV not found for localized lesson {identifier}")

    destination = (output_root or ROOT / "outputs" / "localized") / f"{identifier}{'.'+revision if revision else ''}.mp4"
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = math.ceil(total * FPS)

    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory(prefix="loc_frames_", dir=folder) as directory:
        frames = Path(directory)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(
                    viewport={"width": 1280, "height": 720},
                    device_scale_factor=1,
                    reduced_motion="reduce",
                )

                def local_only(route):
                    if urlparse(route.request.url).hostname in ("127.0.0.1", "localhost"):
                        route.continue_()
                    else:
                        route.abort()

                page.route("**/*", local_only)
                page.goto(
                    f"{frontend_url}/render-localized?id={identifier}" + (f"&revision={revision}" if revision else ''),
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
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
                        arg=stamp,
                        timeout=10000,
                    )
                    stage.screenshot(
                        path=str(frames / f"frame_{frame:06d}.png"),
                        animations="disabled",
                    )
            finally:
                browser.close()

        args = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames / "frame_%06d.png"),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-t",
            f"{total:.6f}",
            "-movflags",
            "+faststart",
            str(destination),
        ]
        try:
            subprocess.run(args, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"FFmpeg failure: {exc.stderr[-2000:]}") from exc

    details = probe_mp4(destination)
    if abs(details["duration_seconds"] - total) > 0.25:
        raise ValueError(
            f"MP4 ({details['duration_seconds']:.2f}s) and WAV ({total:.2f}s) durations differ by >0.25s"
        )
    from .subtitles import manifest_to_srt
    destination.with_suffix('.srt').write_text(manifest_to_srt(manifest),encoding='utf-8')

    if revision:
        alias=destination.with_name(identifier+'.mp4')
        if not alias.exists():
            import shutil
            shutil.copyfile(destination,alias)
    return {
        "video_url": f"/api/localized/video/{identifier}" + (f"?revision={revision}" if revision else ''),
        "render_id": revision, "output_path": str(destination),
        "subtitle_url": f"/api/localized/subtitles/{identifier}",
        "fps": FPS,
        "frames": count,
        "expected_duration_seconds": total,
        **details,
    }
