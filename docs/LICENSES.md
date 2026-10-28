# Model, Library, Font, and Voice License Audit

Phase 4 provenance addendum (2026-10-28): no Python/npm package, model, font or
external illustration was installed or downloaded. All new diagram geometry,
layout, plotting and trace code was authored locally under `frontend/src/visuals`
and `backend/app/algorithm_trace.py`. This phase does not introduce a third-party
SVG/image licence. It reuses the locally bundled fonts and libraries audited
below. The handwritten bounded numeric evaluator avoids a new mathjs dependency.
The existing audit remains historical evidence; no new broad re-audit of all
pre-existing licence claims is asserted by this addendum.

**Document Date:** October 28, 2026  
**Auditor:** Blu Visual Teacher Verification Agent  
**Environment:** Local Windows 11 (`C:\blu`)  

---

## 1. Machine Learning Models & Weights

| Component / Artifact | Model ID / Local Path | Primary Source URL | Declared License | Attribution Required? | Bundled in Submission? | Unresolved Issues |
|---|---|---|---|---|---|---|
| **Translation Engine** | `ai4bharat/indictrans2-en-indic-dist-200M` (Snapshot: `2cfd0a20057756d7560868f7d988891515255474`) | [HuggingFace: IndicTrans2](https://huggingface.co/ai4bharat/indictrans2-en-indic-dist-200M) | MIT License | Yes (Cite Gala et al., 2023) | No (Local cache `~/.cache/huggingface/hub`) | None |
| **Kannada TTS Engine** | `ai4bharat/indic-parler-tts` (Snapshot: `660bc53c64ae83150613264111708a04df0a9eb8`) | [HuggingFace: Indic-Parler-TTS](https://huggingface.co/ai4bharat/indic-parler-tts) | Apache-2.0 | Yes (AI4Bharat / Hugging Face Parler) | No (Local cache `~/.cache/huggingface/hub`) | None |
| **English & Hindi TTS** | `hexgrad/Kokoro-82M` (Snapshot: `f3ff3571791e39611d31c381e3a41a3af07b4987`) | [HuggingFace: Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | Apache-2.0 | Yes (hexgrad / Kokoro project) | No (Local cache `~/.cache/huggingface/hub`) | None |
| **Kokoro ONNX & Voices** | `C:\blu\models\kokoro-v1.0.onnx`, `voices-v1.0.bin` | [GitHub: kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) | Apache-2.0 | Yes | No (Excluded via `.gitignore`) | None |
| **Local LLM Planner** | `llama3.2:3b` via Ollama | [Ollama: llama3.2](https://ollama.com/library/llama3.2) / [Meta Llama 3.2](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) | Llama 3.2 Community License | Yes ("Built with Meta Llama 3.2") | No (Managed by Ollama service) | None |

---

## 2. Typography & Fonts

| Component | Package / File | Primary Source URL | Declared License | Attribution Required? | Bundled in Submission? |
|---|---|---|---|---|---|
| **Latin Typography** | `@fontsource/noto-sans` (v5.3.0) | [Google Noto Sans](https://fonts.google.com/noto/specimen/Noto+Sans) | SIL Open Font License 1.1 (OFL-1.1) | Yes (OFL copyright notice preserved) | Yes (Compiled frontend static asset) |
| **Devanagari Typography** | `@fontsource/noto-sans-devanagari` (v5.3.0) | [Google Noto Sans Devanagari](https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari) | SIL Open Font License 1.1 (OFL-1.1) | Yes (OFL copyright notice preserved) | Yes (Compiled frontend static asset) |
| **Kannada Typography** | `@fontsource/noto-sans-kannada` (v5.3.0) | [Google Noto Sans Kannada](https://fonts.google.com/noto/specimen/Noto+Sans+Kannada) | SIL Open Font License 1.1 (OFL-1.1) | Yes (OFL copyright notice preserved) | Yes (Compiled frontend static asset) |

---

## 3. Frontend Libraries & Web Assets

| Package | Version | Primary Source URL | License | Bundled in Submission? |
|---|---|---|---|---|
| `react` | 19.3.1 | [GitHub: React](https://github.com/facebook/react) | MIT | Yes (`package.json`) |
| `react-dom` | 19.3.1 | [GitHub: React](https://github.com/facebook/react) | MIT | Yes (`package.json`) |
| `three` | 0.183.1 | [GitHub: Three.js](https://github.com/mrdoob/three.js) | MIT | Yes (`package.json`) |
| `@react-three/fiber` | 9.1.4 | [GitHub: react-three-fiber](https://github.com/pmndrs/react-three-fiber) | MIT | Yes (`package.json`) |
| `vite` | 8.3.5 | [GitHub: Vite](https://github.com/vitejs/vite) | MIT | Yes (Dev dependency) |
| `tailwindcss` | 4.3.3 | [GitHub: Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) | MIT | Yes (Dev dependency) |
| `typescript` | 7.0.2 | [GitHub: TypeScript](https://github.com/microsoft/TypeScript) | Apache-2.0 | Yes (Dev dependency) |

---

## 4. Backend Libraries & System Runtimes

| Library / Tool | Primary Source URL | Declared License | Usage & Bundling |
|---|---|---|---|
| `fastapi` | [FastAPI](https://github.com/fastapi/fastapi) | MIT | Backend HTTP web server |
| `pydantic` | [Pydantic](https://github.com/pydantic/pydantic) | MIT | Lesson data schema validation |
| `uvicorn` | [Uvicorn](https://github.com/encode/uvicorn) | BSD-3-Clause | ASGI web server runtime |
| `playwright` | [Playwright Python](https://github.com/microsoft/playwright-python) | Apache-2.0 | Headless frame rendering |
| `PyTorch` | [PyTorch](https://github.com/pytorch/pytorch) | BSD-3-Clause | Tensor inference runtime |
| `transformers` | [Transformers](https://github.com/huggingface/transformers) | Apache-2.0 | Hugging Face model loading |
| `soundfile` | [PySoundFile](https://github.com/bastibe/python-soundfile) | BSD-3-Clause | WAV file I/O |
| `FFmpeg` | [FFmpeg](https://ffmpeg.org/) | LGPL 2.1+ / GPL 2.0+ | System binary on PATH; video/audio multiplexing |
| `espeak-ng` | [espeak-ng](https://github.com/espeak-ng/espeak-ng) | GPLv3 | Phonemizer dependency used by Kokoro TTS |

---

## 5. Attributions & Compliance Notes

1. **Meta Llama 3.2**: Used solely for local offline lesson planning. Users must adhere to the Llama 3.2 Community License Agreement.
2. **AI4Bharat IndicTrans2 & Indic-Parler-TTS**: Developed by the AI4Bharat research team at IIT Madras and Hugging Face. Commercial and academic usage permitted under respective MIT / Apache-2.0 terms with citation.
3. **Hexgrad Kokoro**: Permissive Apache-2.0 lightweight speech synthesis weights.
4. **Google Noto Fonts**: All fonts distributed under SIL Open Font License 1.1; embedding in compiled web applications is fully compliant without commercial royalties.
5. **Zero Remote Telemetry**: No proprietary 3D scenes, external CDN stylesheets, or remote asset trackers are present in the runtime.
