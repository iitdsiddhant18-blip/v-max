# Blu Visual Teacher — Part 3a: Multilingual, Cue-Synchronized Delivery

Fully local educational lesson planner with 3-language delivery in **English**, **Hindi**, and **Kannada**.
One lesson plans once in English, translates into Hindi and Kannada while preserving code, visual labels, and teaching structure, synthesizes native speech, synchronizes on-screen diagrams and captions to exact audio-measured cues, and exports standalone UTF-8 SRT subtitles and 720p H.264/AAC MP4 videos.

## Architecture and Language Pipelines

1. **English (`en`)**:
   - Voice: Kokoro ONNX `hm_omega` (lang `en-us`).
   - Planned via local Ollama planner (`qwen3:4b` / `llama3.2:3b`).
   - Prepared timeline in `backend/cache/lessons/<id>`.
2. **Hindi (`hi`)**:
   - Translation: Local offline `ai4bharat/indictrans2-en-indic-dist-200M` (`eng_Latn` -> `hin_Deva`) with protected programming tokens and glossary round-tripping.
   - Voice: Kokoro ONNX `hf_alpha` (lang `hi`).
   - Prepared timeline, PCM-aligned cues, and SRT in `backend/cache/localized/<id>`.
3. **Kannada (`kn`)**:
   - Translation: Local offline `ai4bharat/indictrans2-en-indic-dist-200M` (`eng_Latn` -> `kan_Knda`) with code token protection.
   - Voice: `ai4bharat/indic-parler-tts` executed in separate isolated `.venv-tts` via worker `backend/scripts/kannada_tts_worker.py`.
   - Sequential GPU lifecycle: Ollama -> IndicTrans2 -> Parler TTS (no simultaneous dual heavy models on GPU).
   - Prepared timeline, PCM-aligned cues, and SRT in `backend/cache/localized/<id>`.

## Requirements already installed on the demo laptop

- Windows project root `C:\blu`.
- Main Python virtual environment `.venv` (PyTorch, transformers, Kokoro ONNX, IndicTransToolkit).
- Kannada TTS Python virtual environment `.venv-tts` (PyTorch, transformers, Parler-TTS, soundfile).
- Local Hugging Face offline cache in `%USERPROFILE%\.cache\huggingface\hub` containing:
  - `models--ai4bharat--indictrans2-en-indic-dist-200M`
  - `models--ai4bharat--indic-parler-tts`
  - `models--hexgrad--Kokoro-82M`
- Kokoro ONNX models: `models/kokoro-v1.0.onnx` and `models/voices-v1.0.bin`.
- Locally bundled fonts: Noto Sans, Noto Sans Devanagari, Noto Sans Kannada.
- Local `ffmpeg`, `ffprobe`, and Playwright Chromium.

## Run

Open two PowerShell terminals from `C:\blu`:

Backend terminal:
```powershell
.\.venv\Scripts\python -m uvicorn backend.app.main:app --port 8000
```

Frontend terminal:
```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`. Enter any lesson topic, choose level and duration, then click **Create lesson**.
In the generated player:
- Toggle between **English**, **हिन्दी**, and **ಕನ್ನಡ** seamlessly for the same lesson without replanning.
- Use controls: **Play**, **Pause**, **Next scene**, **Replay**, and timeline scrub.
- Download **UTF-8 SRT subtitles** with exact timestamps.
- Export **720p MP4** in any of the three languages with burned-in native script captions.

## Automated Verification

From `C:\blu`:

```powershell
# Run all Python unit and integration tests (93 tests total)
.\.venv\Scripts\python -m pytest backend/tests -q

# Run specific Part 3a contract and media tests
.\.venv\Scripts\python -m pytest backend/tests/test_translation_contract.py -q -vv
.\.venv\Scripts\python -m pytest backend/tests/test_localized_media.py -q -vv

# Build production frontend
cd frontend
npm run build
cd ..

# Run Part 3a 3-language end-to-end smoke test (requires backend and frontend running)
.\.venv\Scripts\python backend/scripts/smoke_3a.py

# Rerun baseline Part 2b English live smoke and Part 1b sample smoke
.\.venv\Scripts\python backend/scripts/smoke_2b.py
.\.venv\Scripts\python backend/scripts/smoke_part1b.py
```

## Contract Invariants and Safeguards

- **Content & Beat Contract**: Spoken facts are paired with visual labels (`label :: fact`). Each fact is individually translated and synthesized into its own PCM WAV chunk to derive exact cue timestamps.
- **Code Walkthrough Safety**: In `code_walkthrough` scenes, Python source code, line numbers (`Line 1`, `Line 2`), keywords (`for`, `range`, `print`), variables, and numeric literals (`0`, `1`, `2`) are strictly protected from modification.
- **No Inferred/Timer Captions**: Caption cues reflect real audio duration measured from PCM frames. Subtitle SRT files contain no padding or silent pause captions.
- **Cache Isolation**: English lessons are stored in `backend/cache/lessons/`; localized Hindi and Kannada lessons are stored in `backend/cache/localized/`.
- **Zero-Width Character Sanitization**: Invisible characters (`\u200b`, `\u200c`, `\u200d`, `\ufeff`) that disrupt speech synthesis or font shaping are safely stripped.
