"""Generate Unicode SRT from real per-cue PCM-derived timestamps."""
import math


def srt_time(seconds: float) -> str:
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("Invalid subtitle time")
    millis = round(seconds * 1000)
    hours, remain = divmod(millis, 3_600_000)
    minutes, remain = divmod(remain, 60_000)
    secs, millis = divmod(remain, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def manifest_to_srt(manifest: dict) -> str:
    subtitles = []
    prior_end = 0.0
    total = float(manifest["total_seconds"])
    for entry in manifest["scenes"]:
        scene_start = float(entry["start_seconds"])
        audio_end = scene_start + float(entry["audio_seconds"])
        for cue in entry.get("cues", []):
            start = scene_start + float(cue["start_seconds"])
            end = scene_start + float(cue["end_seconds"])
            text = str(cue.get("text", "")).strip()
            if (not text or not (0 <= start and prior_end <= start + 0.002
                                 and start < end <= audio_end + 0.002)
                    or end > total + 0.002):
                raise ValueError("Malformed or overlapping subtitle cue")
            subtitles.append(f"{len(subtitles)+1}\n{srt_time(start)} --> {srt_time(end)}\n{text}\n")
            prior_end = end
    if not subtitles:
        raise ValueError("No subtitle cues")
    return "\n".join(subtitles) + "\n"
