# Blu Visual Teacher — Part 2b

Fully local educational lesson planner and English visual narrator. Part 3a will
add automatic translation and narration for Hindi and Kannada; Part 3b will add
the final landing-page design, offline demo rehearsal and licensing audit.

## Requirements already installed on the demo laptop

- Windows project root `C:\blu`; main Python environment `.venv` and optional
  Kannada environment `.venv-tts` are not to be rebuilt.
- Ollama running locally with `qwen3:4b` (live lesson default) or `llama3.2:3b`.
  `BLU_PLANNER_MODEL` can explicitly select either preinstalled model. The
  separate frozen Part 2a planner/benchmarks retain their original default.
- Kokoro ONNX files in `models/kokoro-v1.0.onnx` and `models/voices-v1.0.bin`.
- Local `ffmpeg`, `ffprobe` and Playwright Chromium installed.
- Frontend Node dependencies installed in `frontend/node_modules`.

## Run

Open two PowerShell terminals.

Backend terminal from `C:\blu`:

```powershell
.\.venv\Scripts\python -m uvicorn backend.app.main:app --port 8000
```

Frontend terminal from `C:\blu`:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`. Enter any lesson topic, choose level and duration,
then click **Create lesson**. The text is planned locally through Ollama. Click
**Prepare and preview lesson**, then **Play**, **Pause**, **Next scene**, **Replay**
or **Export this lesson as 720p MP4**. The legacy English/Hindi fixed Python-loop
sample player remains available below the live lesson form.
Prepared lessons also have a larger review page at `/lesson?id=<lesson-id>`.
On narrow screens, the current spoken sentence is repeated below the SVG at
normal text size, with expandable scene/code details.

**Language limitation:** generated lessons are English-only until Part 3a.
Selecting Hindi or Kannada in the topic form currently preserves the requested
language as metadata but creates an English lesson; it does not translate it.
The existing fixed Hindi sample continues to work.

## Verify

From `C:\blu` with both local servers active:

```powershell
.\.venv\Scripts\python -m pytest backend/tests -q
cd frontend
npm run build
cd ..
.\.venv\Scripts\python backend/scripts/smoke_2b.py
.\.venv\Scripts\python backend/scripts/smoke_part1b.py
```

Open and listen to the exported *photosynthesis* and *Python loop* MP4s; verify
that all diagrams and subtitles match the new topics. Repeat a complete run
with Wi-Fi off and confirm no external network request is made. Compare the
browser SVG at a known playback time to its exported MP4 frame.

## Architecture and file ownership

- `backend/app/planner.py`: Ollama-local structured JSON lesson planning, retry,
  content validation and topical fallback.
- `backend/app/live.py`: English voice per scene, content-addressed lesson
  cache, audio-measured scene durations.
- `backend/app/live_export.py`: browser-equivalent deterministic SVG frames
  rendered by Playwright and encoded by FFmpeg as H.264/AAC 1280x720 MP4.
- `frontend/src/DynamicSceneContent.tsx`: generic data-driven title, diagram,
  code walkthrough and step-list SVG components. No model-authored code runs.
- `frontend/src/LessonPlayer.tsx`: real lesson preview, audio-synced controls,
  MP4 download and a headless export route.
- `backend/app/media.py`, `backend/app/exporter.py`, `frontend/src/SamplePlayer.tsx`:
  previously verified Part 1b fixed sample, intentionally preserved.

All runtime requests go only to localhost. Do not upgrade working models,
packages or voices during the hackathon. Generated media lives beneath
`backend/cache/lessons/` and `outputs/lessons/` and is not source code.

## Limitations and next phases

Playable generated lessons are measured at **30–90 seconds**, including the
existing 0.5-second scene pauses. Create lesson now plans AND measures speech;
if the script is outside that range, it rewrites teaching content and measures
again. Speech speed and silence are not stretched to satisfy the limit. The
30/60/90 choice guides the script within that range. If a complete timed lesson
cannot be produced, the UI clearly shows a fallback outline without a video player.

Generated item data pairs a short visual label with one spoken fact, separated
internally by ` :: `. Code labels identify actual line numbers. The backend
builds narration from these same facts; each fact is synthesized once into the
scene WAV. Its exact PCM boundaries drive captions and concept/code focus in both
the browser and export; there are no equal-percentage item reveals. Concept
diagrams use local SVG illustrations, molecules, sunlight, water, plants, energy
and process arrows according to the lesson's labels. The frozen Part 2a planner
file remains unchanged; the Part 2b live layer adds teaching/relevance checks
through its existing local transport hook. Model facts still need human review.
The photosynthesis and Python-loop teaching briefs add explicit causal questions,
worked examples and factual checks. These are grounded planning instructions;
they are not a guarantee of factual correctness for every arbitrary subject.
Python display code is parsed to catch syntax and missing-input mistakes; it is
never executed. A fallback outline is not labelled as a completed narrated lesson.

Advanced formula/chart illustration is outside this stage. Hindi/Kannada automatic translation, voice, captions
and SRT are deliberately left for Part 3a. The robot design and verified model
and asset licences belong to Part 3b. Verify every licence from primary sources
before submitting the project.
