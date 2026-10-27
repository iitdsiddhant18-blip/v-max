# Blu Visual Teacher

Offline project for short, narrated visual lessons in English, Hindi and Kannada.

**Status: Part 1b — sample lesson with English/Hindi Kokoro speech, an audio-driven
browser player and a 720p H.264/AAC MP4 export.** The local LLM planner,
automatic Hindi/Kannada translation, Kannada TTS, full visual engine and polished
landing page are later parts. `/api/generate` deliberately retains the Part 1a
English fallback behaviour regardless of requested language.

## Run (Windows PowerShell from `C:\blu`)

Terminal 1 (main environment; not `.venv-tts`):

    .venv\Scripts\Activate.ps1
    python -m uvicorn backend.app.main:app --port 8000

Terminal 2:

    cd frontend
    npm run dev

Open `http://127.0.0.1:5173`. The existing Part 1a topic form still works.
Below it, choose English or Hindi and click **Prepare sample voice**, then
**Play**, **Pause**, **Next scene**, **Replay**, or **Export 720p MP4**.

Part 1b requires these pre-installed local tools (do not reinstall or upgrade
working model environments): `kokoro-onnx`, `soundfile`, `playwright`, Playwright
Chromium, `ffmpeg`, and `ffprobe` on PATH. The Kokoro files must already exist at
`models/kokoro-v1.0.onnx` and `models/voices-v1.0.bin`. No external API is used.

Generated files (already excluded by Part 1a `.gitignore`):

- `backend/cache/part1b/en` and `backend/cache/part1b/hi` — scene WAVs,
  combined WAV and timeline manifest.
- `outputs/part1b/en/python_loop.mp4` and `outputs/part1b/hi/python_loop.mp4`.

## Verify

With the main `.venv` activated:

    python -m pytest backend/tests -q

With both servers running (can take several minutes because frames are captured
at 15 fps):

    python backend/scripts/smoke_part1b.py

Listen to both narration WAVs and watch both downloaded MP4s. Confirm the
caption language matches the spoken narration, the video begins with a title
card, the code walkthrough highlights a line, the diagram shows three steps,
and the recap ends before the final audio pause. Confirm export with Wi-Fi off.

## Timing and limitations

Part 1b uses two **fixed samples**: English from the existing Part 1a fallback
file and a manually prepared Hindi sample file. This is not general translation.
Each scene's WAV frame count sets its duration, plus 0.5 seconds of silence.
The browser clock follows the combined WAV; Playwright renders the same SVG at
explicit timestamps; FFmpeg encodes the frames and combined audio.
The code scene also shows the three values named in its narration; the diagram
shows each value passing through `print(i)` to its output. Those details remain
visible during the scene, without guessed word-level reveal times.

The sample may be shorter than 30 seconds. The requested 30/60/90-second
planning constraint will be handled by the real planner in Part 2a and
multilingual timing in Part 3a, rather than stretching speech artificially.

## Models and licences

Carry forward the model, voice, font and library licence audit from
`BLU_VISUAL_TEACHER_PLAN.md`. Verify official licences before submission.
