"""Blu Visual Teacher API: Part 2a local planner plus Part 1b sample export."""
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from .exporter import export_sample
from .media import CACHE_ROOT, ROOT, load_timeline, prepare_sample
from .schema import GenerateRequest, GenerateResponse, Lesson
from .live import LIVE_ROOT, lesson_folder, load_lesson, prepare_lesson, plan_timed_lesson as plan_lesson
from .live_export import export_lesson
from .visual_cache import attach_visual
from .localized_media import LOCALIZED_ROOT, load_localized, localized_folder, prepare_localized
from .localized_export import export_localized

app = FastAPI(title="Blu Visual Teacher", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    # Part 2a: JSON-only local planner; never runs model-written code.
    # English lesson text is intentional until translation in Part 3a.
    source, lesson = plan_lesson(req)
    return GenerateResponse(request=req, source=source, lesson=lesson)


class SampleRequest(BaseModel):
    language: Literal["en", "hi"] = "en"


@app.post("/api/sample/prepare")
def sample_prepare(req: SampleRequest) -> dict:
    try:
        return prepare_sample(req.language)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/sample/timeline/{language}")
def sample_timeline(language: Literal["en", "hi"]) -> dict:
    try:
        return load_timeline(language)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/sample/media/{language}/{filename}")
def sample_media(language: Literal["en", "hi"], filename: str) -> FileResponse:
    valid = filename == "combined.wav" or (
        filename.startswith("scene_") and filename.endswith(".wav")
        and len(filename) == len("scene_00.wav") and filename[6:8].isdigit()
        and int(filename[6:8]) < 6
    )
    if not valid:
        raise HTTPException(status_code=404, detail="Unknown sample audio file")
    path = CACHE_ROOT / language / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Prepare the sample first")
    return FileResponse(path, media_type="audio/wav", filename=filename,
                        content_disposition_type="inline")


@app.post("/api/sample/export")
def sample_export(req: SampleRequest) -> dict:
    try:
        manifest = load_timeline(req.language)
        return export_sample(req.language, manifest)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"MP4 export failed: {exc}") from exc


@app.get("/api/sample/video/{language}")
def sample_video(language: Literal["en", "hi"]) -> FileResponse:
    path: Path = ROOT / "outputs" / "part1b" / language / "python_loop.mp4"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Export this sample first")
    return FileResponse(path, media_type="video/mp4", filename=f"python_loop_{language}.mp4")


class LessonPrepareRequest(BaseModel):
    lesson: Lesson


@app.post("/api/lesson/prepare")
def lesson_prepare(req: LessonPrepareRequest) -> dict:
    try:
        manifest=attach_visual(prepare_lesson(req.lesson, enforce_duration=True))
        return {**manifest,'subtitle_url':f"/api/lesson/subtitles/{manifest['lesson_id']}"}
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/lesson/timeline/{identifier}")
def lesson_timeline(identifier: str) -> dict:
    try:
        from .live import _check_duration
        manifest=load_lesson(identifier)
        _check_duration(manifest)
        return {**attach_visual(manifest),'subtitle_url':f'/api/lesson/subtitles/{identifier}'}
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=404, detail="Unknown prepared lesson") from exc


@app.get("/api/lesson/media/{identifier}/{filename}")
def lesson_media(identifier: str, filename: str) -> FileResponse:
    if filename != "combined.wav" and not (
        len(filename) == len("scene_00.wav") and filename.startswith("scene_")
        and filename.endswith(".wav") and filename[6:8].isdigit()
    ):
        raise HTTPException(status_code=404, detail="Unknown audio")
    try:
        manifest = load_lesson(identifier)
        if filename.startswith("scene_") and int(filename[6:8]) >= len(manifest["scenes"]):
            raise ValueError("Unknown scene")
        path = lesson_folder(identifier) / filename
        if not path.is_file():
            raise FileNotFoundError
    except (ValueError, FileNotFoundError, OSError):
        raise HTTPException(status_code=404, detail="Unknown audio") from None
    return FileResponse(path, media_type="audio/wav", filename=filename,
                        content_disposition_type="inline")


@app.post("/api/lesson/export/{identifier}")
def lesson_export(identifier: str) -> dict:
    try:
        return export_lesson(identifier)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail="Unknown or incomplete lesson") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"MP4 export failed: {exc}") from exc


@app.get("/api/lesson/video/{identifier}")
def lesson_video(identifier: str, revision: str | None = None) -> FileResponse:
    try:
        lesson_folder(identifier)
        if revision is not None:lesson_folder(revision)
        path = ROOT / "outputs" / "lessons" / f"{identifier}{'.'+revision if revision else ''}.mp4"
        if not path.is_file():
            raise FileNotFoundError
    except (ValueError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="Export the lesson first") from None
    return FileResponse(path, media_type="video/mp4", filename=f"blu_{identifier[:12]}.mp4")


@app.get('/api/lesson/subtitles/{identifier}')
def english_subtitles(identifier: str) -> Response:
    from .subtitles import manifest_to_srt
    from .live import _check_duration
    try:
        manifest=load_lesson(identifier);_check_duration(manifest)
        text=manifest_to_srt(manifest)
    except (ValueError,FileNotFoundError,OSError):
        raise HTTPException(status_code=404,detail='Unknown English subtitles') from None
    return Response(text,media_type='text/plain; charset=utf-8',headers={
        'Content-Disposition':f'attachment; filename="subtitles_{identifier[:12]}.srt"'})


class LocalizedPrepareRequest(BaseModel):
    source_lesson_id: str
    language: Literal["hi", "kn"]


@app.post("/api/localized/prepare")
def localized_prepare(req: LocalizedPrepareRequest) -> dict:
    try:
        result = prepare_localized(req.source_lesson_id, req.language, enforce_duration=True)
        return attach_visual(result) if 'lesson' in result else result
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/localized/timeline/{identifier}")
def localized_timeline(identifier: str) -> dict:
    try:
        return attach_visual(load_localized(identifier, root=LOCALIZED_ROOT, enforce_duration=True))
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=404, detail="Unknown prepared localized lesson") from exc


@app.get("/api/localized/media/{identifier}/{filename}")
def localized_media(identifier: str, filename: str) -> FileResponse:
    if filename != "combined.wav" and not (
        len(filename) == len("scene_00.wav") and filename.startswith("scene_")
        and filename.endswith(".wav") and filename[6:8].isdigit()
    ):
        raise HTTPException(status_code=404, detail="Unknown audio")
    try:
        manifest = load_localized(identifier, root=LOCALIZED_ROOT)
        if filename.startswith("scene_") and int(filename[6:8]) >= len(manifest["scenes"]):
            raise ValueError("Unknown scene")
        path = localized_folder(identifier, root=LOCALIZED_ROOT) / filename
        if not path.is_file():
            raise FileNotFoundError
    except (ValueError, FileNotFoundError, OSError):
        raise HTTPException(status_code=404, detail="Unknown audio") from None
    return FileResponse(path, media_type="audio/wav", filename=filename,
                        content_disposition_type="inline")


@app.get("/api/localized/subtitles/{identifier}")
def localized_subtitles(identifier: str) -> FileResponse:
    try:
        folder = localized_folder(identifier, root=LOCALIZED_ROOT)
        path = folder / "subtitles.srt"
        if not path.is_file():
            raise FileNotFoundError
    except (ValueError, FileNotFoundError, OSError):
        raise HTTPException(status_code=404, detail="Unknown subtitles") from None
    return FileResponse(path, media_type="text/plain; charset=utf-8",
                        filename=f"subtitles_{identifier[:12]}.srt")


@app.post("/api/localized/export/{identifier}")
def localized_export_endpoint(identifier: str) -> dict:
    try:
        return export_localized(identifier)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail="Unknown or incomplete localized lesson") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Localized MP4 export failed: {exc}") from exc


@app.get("/api/localized/video/{identifier}")
def localized_video(identifier: str, revision: str | None = None) -> FileResponse:
    try:
        localized_folder(identifier)
        if revision is not None:localized_folder(revision)
        path = ROOT / "outputs" / "localized" / f"{identifier}{'.'+revision if revision else ''}.mp4"
        if not path.is_file():
            raise FileNotFoundError
    except (ValueError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="Export the localized lesson first") from None
    return FileResponse(path, media_type="video/mp4", filename=f"blu_{identifier[:12]}.mp4")
