# Blu Visual Teacher

Offline system that turns a typed concept into a short, narrated, animated lesson
(English, Hindi, Kannada) that plays in the browser and exports as a 720p MP4.

Status: Phase 1a (backend skeleton + frontend shell). The lesson returned by the API is
a built-in sample; the local-LLM planner, narration and export come in later phases.

## Run (Windows PowerShell, from the project root)

Backend (terminal 1):

    .venv\Scripts\Activate.ps1
    python -m uvicorn backend.app.main:app --reload --port 8000

Frontend (terminal 2):

    cd frontend
    npm install
    npm run dev

Open http://127.0.0.1:5173

Tests:

    python -m pytest backend/tests -q

## Models, voices and licences

To be completed before submission (see BLU_VISUAL_TEACHER_PLAN.md, section 4).
