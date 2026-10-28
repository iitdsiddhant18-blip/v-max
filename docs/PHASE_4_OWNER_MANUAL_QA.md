# BLU VISUAL TEACHER — PHASE 4 OWNER MANUAL QA CHECKLIST

This document contains step-by-step procedures for the system owner to physically verify non-functional and linguistic requirements that cannot be proven by automated software tests alone.

---

## 1. Physical Offline Verification (Wi-Fi Physically Disconnected)

> [!IMPORTANT]
> Software mocks blocking HTTP sockets demonstrate that code does not make external calls, but **only physical disconnection** proves complete offline readiness.

### Objective
Verify that BLU generates, plans, synthesizes speech, renders visuals, and exports video completely without an active internet connection.

### Step-by-Step Procedure

1. **Disconnect Network Interfaces:**
   - On Windows 11, click the network/volume icon in the bottom-right taskbar (or press `Win + A`).
   - Click the **Wi-Fi** tile to turn it **OFF**.
   - If an Ethernet cable is connected, disconnect it.
   - Verify by opening a command prompt and confirming `ping 8.8.8.8` returns `General failure` or `Destination host unreachable`.

2. **Start Backend Server:**
   ```powershell
   cd C:\blu
   .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000
   ```
   Confirm server starts without errors at `http://127.0.0.1:8000`.

3. **Start Frontend Dev Server:**
   In a second PowerShell window:
   ```powershell
   cd C:\blu\frontend
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

4. **Test Uncached Topic Generation:**
   - Enter a completely fresh, uncached topic, for example:
     `"How do sound waves travel through air and water?"`
   - Select **Auto** duration, Level **Beginner**.
   - Click **Generate Lesson**.
   - Confirm local Ollama plans the lesson, Kokoro synthesizes English audio, and the player displays animated SVG diagrams.

5. **Test Language Localization:**
   - In the lesson player, select **Hindi (HI)**. Verify Hindi speech and captions.
   - Select **Kannada (KN)**. Verify Kannada speech and captions.

6. **Test Video Export:**
   - Click **Export MP4**.
   - Confirm a 720p H.264/AAC MP4 video is downloaded and plays locally.

7. **Restore Network:**
   - Click the Wi-Fi tile in `Win + A` to turn Wi-Fi back **ON**.

### Owner Sign-off
- [ ] **Physical Offline Test:** `[NOT VERIFIED / PENDING OPERATOR EXECUTION]`
  - Tested Date: `_______________`
  - Observed Result: `________________________________________________`

---

## 2. Native-Speaker Linguistic & Pronunciation QA (Hindi & Kannada)

> [!NOTE]
> Automated tests verify Devanagari and Kannada character ranges, token counts, and audio alignment. However, only a fluent native speaker can assess natural pronunciation, phrasing, and intelligibility.

### Listening Criteria
1. **Pronunciation Clarity:** Are technical terms understandable? Does the voice mispronounce common words?
2. **Cadence & Prosody:** Is the speech speed natural, or does it sound clipped / robotic?
3. **Synchronization:** Do labels on the screen appear at the same time the narrator introduces them?
4. **Grammar & Context:** Did machine translation produce nonsensical literal phrasing or natural pedagogical explanation?

### Test Artifacts to Review
1. **Biology (B1):**
   - Hindi: `outputs/localized/7ceaff23944d612e5498fdc9b55a6762b5336e2b21129e2883c8715f79b4e3f8.42347f7baeadc35664978e7201e7794550c4f6ba34efda53809fbfa2a933bb2e.mp4`
   - Kannada: `outputs/localized/3ebb3714198ccce341e1c205a5d9896f416f4c158a6a94aade7930b2e30eebea.7fdf1cd0475bdb79af19dd93ca83999cf4e69c99b5ce13aafa3be8aee860a75f.mp4`
2. **Algorithm (CS1):**
   - Hindi: `outputs/localized/6aec256136cd591600b7882597b575d12269e618505563f06537f8e5a120c6f3.mp4`
   - Kannada: `outputs/localized/c92638bebb65c8f2bdace7a95312464e7461f8a1d27438d7d4bdab65ba8f77f2.mp4`
3. **Mathematics (M1):**
   - Hindi: `outputs/localized/f6e70c66ef0abea60b95af503c1a51d8f1aae8a8ffcc5911598c315e2b847730.3483ea199042739ac03fd25ec3d25c8505c50b1b28e59d649254b021ce99ae72.mp4`

### Reviewer Sign-off
- [ ] **Hindi (HI) Native Listening Review:** `[NOT VERIFIED / PENDING NATIVE REVIEWER]`
  - Reviewer Name: `_______________`
  - Rating (1–5): `___` | Notes: `________________________________________`
- [ ] **Kannada (KN) Native Listening Review:** `[NOT VERIFIED / PENDING NATIVE REVIEWER]`
  - Reviewer Name: `_______________`
  - Rating (1–5): `___` | Notes: `________________________________________`

---

## 3. CPU-Only Performance Evaluation

### Objective
Measure inference time, RAM usage, and export speed on systems without an NVIDIA discrete GPU.

### Procedure
1. Set environment variables to hide CUDA:
   ```powershell
   $env:CUDA_VISIBLE_DEVICES="-1"
   $env:DEV="cpu"
   ```
2. Run single-topic generation benchmark:
   ```powershell
   cd C:\blu
   .\.venv\Scripts\python.exe backend\scripts\visual_qa_matrix.py --limit 1 --cpu --output outputs\phase4-evidence\cpu_benchmark.json
   ```
3. Record duration and resource utilization from `cpu_benchmark.json`.

### Evaluation Status
- [ ] **CPU-Only Workflow:** `[NOT MEASURED ON CURRENT GPU-EQUIPPED HARDWARE]`
  - Host Specs: Intel Core i7 12th Gen, NVIDIA RTX 3050 Laptop GPU (4 GB VRAM)
  - Result: `NOT MEASURED` (Development and benchmark conducted on GPU-accelerated runtime).
