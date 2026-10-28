# Blu Visual Teacher — 5-Minute Offline Demo Runbook

**Goal:** Demonstrate complete local AI lesson generation, multilingual speech/visual alignment, and 720p H.264/AAC MP4 video export with zero cloud connectivity.  
**Hardware Profile:** Windows 11 Laptop, NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM), 16GB System RAM.  

---

## 1. System Requirements & Architecture Overview

- **Local Planning LLM:** Ollama running `llama3.2:3b` at `http://127.0.0.1:11434`
- **Translation:** `ai4bharat/indictrans2-en-indic-dist-200M` in `.venv` (PyTorch CUDA, chunked mini-batches)
- **Speech Synthesis:**
  - **English (`en`):** Kokoro ONNX `hm_omega` (24,000 Hz)
  - **Hindi (`hi`):** Kokoro ONNX `hf_alpha` (24,000 Hz)
  - **Kannada (`kn`):** Indic Parler-TTS `Anu` in `.venv-tts` (44,100 Hz, IPC worker)
- **Visuals & Rendering:** React 19 + SVG Data Canvas + Three.js yellow mascot (`RobotMascot`)
- **Video Multiplexing:** Playwright headless Chromium + local FFmpeg (`1280x720`, `15fps`, `h264/aac`)

---

## 2. Pre-Flight & Offline Verification

### Physical Offline Verification:
1. Open Windows Quick Settings (`Win + A`).
2. Toggle **Wi-Fi** to **Off** (or enable Airplane Mode).
3. Confirm no external network connectivity (`ping 8.8.8.8` fails).
4. All services run strictly on localhost (`127.0.0.1`).

---

## 3. Starting the Local Services

Open two PowerShell windows at `C:\blu`:

### Terminal 1: Backend API (FastAPI + Uvicorn)
```powershell
cd C:\blu
.\.venv\Scripts\python -m uvicorn backend.app.main:app --port 8000
```
*Expected Output:*
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Terminal 2: Frontend Web Server (Vite)
```powershell
cd C:\blu\frontend
npm run dev
```
*Expected Output:*
```
  VITE v8.3.5  ready in 180 ms
  ➜  Local:   http://localhost:5173/
```

---

## 4. Five-Minute Judge Walkthrough Script

### Minute 0:00 - 1:00: Landing Page & Friendly 3D Mascot
1. Open browser to `http://localhost:5173`.
2. Notice the warm cream/yellow landing design, floating concept chips, and the interactive yellow helmet robot (`RobotMascot`).
3. Move cursor across the screen: the robot's head yaw and pitch track pointer motion smoothly with subtle breathing float.
4. *Fallback behavior:* If WebGL is unavailable on low-power hardware, the WebGL Error Boundary automatically renders the lightweight SVG/CSS static robot.

### Minute 1:00 - 2:00: Plan Once in English (Local Ollama)
1. Click **"Create a lesson"** or scroll to `#create`.
2. Enter Topic: `How does a Python loop work?` (or a fresh judge topic e.g. `Photosynthesis`).
3. Select Level: `Beginner`, Length: `60 s`, Language: `English`.
4. Click **"Create lesson"**.
5. Local Ollama plans 5 structured pedagogical scenes in English (`title_card`, `diagram`, `code_walkthrough`, `code_walkthrough`, `step_list`).
6. Click **"Prepare lesson"** in the Lesson Player.
7. Kokoro synthesizes English speech (`hm_omega`), measures exact PCM frames for every teaching beat, and creates `timeline.json`.
8. Play lesson: observe highlighted code lines synchronized to spoken narration.

### Minute 2:00 - 3:30: Switch to Hindi (`हिन्दी`) & Kannada (`ಕನ್ನಡ`)
1. In the Lesson Player, toggle language to **"हिन्दी"**:
   - The app calls `/api/localized/prepare` (`language: "hi"`).
   - Ollama VRAM is freed (`keep_alive: 0`).
   - IndicTrans2 translates labels and spoken facts into Devanagari script.
   - Kokoro `hf_alpha` synthesizes Hindi speech.
   - Hindi captions and native scene text appear. Play and verify speech-to-visual cue synchrony.
2. Toggle language to **"ಕನ್ನಡ"**:
   - The app calls `/api/localized/prepare` (`language: "kn"`).
   - IndicTrans2 translates into Kannada script (`ಕನ್ನಡ`).
   - The Kannada TTS subprocess worker runs Indic Parler-TTS in `.venv-tts`.
   - Native Kannada speech plays with exact audio-measured visual beat transitions.
3. Click **"Download SRT"**: verify the downloaded `.srt` file contains authentic Kannada unicode and exact `HH:MM:SS,mmm` timestamps.

### Minute 3:30 - 5:00: Local 720p MP4 Video Export
1. Click **"Export MP4"**:
   - Playwright headless browser renders each SVG frame at 15fps with zero network requests.
   - FFmpeg encodes a 1280x720 H.264 video with AAC audio matching speech duration within 0.25s.
2. Click **"Download Video"**:
   - The generated MP4 plays locally in any media player.
3. Run automated read-only structure verification:
```powershell
cd C:\blu
.\.venv\Scripts\python.exe -m backend.scripts.final_demo_check `
  --english-id 6287dd193602b6ca47fae74b0fbac7cba5a875c0c32cfa1f40a3d8cc50f22103 `
  --hindi-id 6aec256136cd591600b7882597b575d12269e618505563f06537f8e5a120c6f3 `
  --kannada-id c92638bebb65c8f2bdace7a95312464e7461f8a1d27438d7d4bdab65ba8f77f2
```
*Expected Output:*
```
en 6287dd19... 54.831 seconds MP4 PASS
hi 6aec2561... 69.039 seconds MP4 PASS
kn c92638be... 79.474 seconds MP4 PASS
FINAL LOCAL SOURCE/VOICE/MP4 STRUCTURE: PASS
```

---

## 5. Measured Performance Benchmarks

| Phase / Operation | Duration / Latency | Memory / VRAM Footprint |
|---|---|---|
| **English Plan (Ollama `llama3.2:3b`)** | ~4.2s | ~2.0 GB VRAM |
| **English Synthesis (Kokoro ONNX)** | ~1.8s | ~350 MB RAM, 0 VRAM |
| **Translation (IndicTrans2 200M)** | ~4.5s | ~1.6 GB VRAM (mini-batches of 4) |
| **Hindi Synthesis (Kokoro ONNX)** | ~2.1s | ~350 MB RAM, 0 VRAM |
| **Kannada Synthesis (Indic Parler-TTS)** | ~14.8s | ~2.2 GB VRAM (`bfloat16` on CUDA) |
| **Playwright SVG Frame Capture (60s @ 15fps)** | ~32s | ~450 MB RAM |
| **FFmpeg H.264/AAC Multiplexing** | ~3.5s | ~80 MB RAM |
| **Total Cold End-to-End Delivery (3 Languages)** | ~75s | Peak 2.5 GB VRAM / 6 GB System RAM |

---

## 6. Troubleshooting & Fallbacks

1. **CUDA Out of Memory (OOM) on 4GB VRAM:**
   - IndicTrans2 automatically unloads Ollama before translation. If Ollama remains locked in VRAM, execute:
     ```powershell
     Invoke-RestMethod -Method Post http://127.0.0.1:11434/api/generate -Body '{"model":"llama3.2:3b","keep_alive":0}'
     ```
2. **Kannada Parler Worker Issues:**
   - If `.venv-tts` fails to execute, confirm Python interpreter exists at `C:\blu\.venv-tts\Scripts\python.exe`.
3. **WebGL Disabled or Unavailable:**
   - The mascot automatically falls back to `<StaticRobot />` without crashing the page.
4. **Offline Cache Reuse:**
   - Pre-generated lessons for "Python for loop" and "Photosynthesis" reside in `backend/cache/lessons/` and `backend/cache/localized/` for instant offline demo playback.
