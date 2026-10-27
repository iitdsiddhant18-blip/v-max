"""Blu Visual Teacher API: Part 1a endpoints plus Part 1b sample export."""
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .exporter import export_sample
from .fallback import load_fallback_lesson
from .media import CACHE_ROOT, ROOT, load_timeline, prepare_sample
from .schema import GenerateRequest, GenerateResponse

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
    # Keep the verified Part 1a behaviour unchanged.
    lesson = load_fallback_lesson()
    return GenerateResponse(request=req, source="fallback", lesson=lesson)


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
