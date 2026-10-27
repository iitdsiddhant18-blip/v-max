"""Blu Visual Teacher API.

Phase 1a: the /api/generate endpoint validates the request and always returns the
built-in sample lesson. The real planner (local LLM) arrives in Phase 2a.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .fallback import load_fallback_lesson
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
    lesson = load_fallback_lesson()
    return GenerateResponse(request=req, source="fallback", lesson=lesson)
