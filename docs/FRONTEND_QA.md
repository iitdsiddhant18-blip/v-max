# Frontend QA & Acceptance Report: Blu Visual Teacher

Testing Environment: Windows 11, Node 24.14.1, Vite 8.3.5, React 19.3.1, Three.js 0.186.1, Playwright Headless Chromium.

---

## 1. Automated Acceptance Test Results

All 9 end-to-end tests executed via headless Playwright against the production built bundle:

| Test ID | Description | Result | Output Evidence |
|---|---|---|---|
| **E2E-01** | Desktop Landing Page (1440×900) layout, headline, truthful badges | **PASS** | `outputs/frontend-evidence/landing_1440x900.png` |
| **E2E-02** | Laptop Viewport (1366×768) responsive scaling | **PASS** | `outputs/frontend-evidence/landing_1366x768.png` |
| **E2E-03** | Mobile Viewport (390×844) with accessible navigation toggle | **PASS** | `outputs/frontend-evidence/landing_mobile_390x844.png` |
| **E2E-04** | Primary CTA ("Create a lesson") routing to `/studio` | **PASS** | `outputs/frontend-evidence/studio_desktop.png` |
| **E2E-05** | Direct browser reload at `/studio` | **PASS** | SPA handler serves Studio without 404 |
| **E2E-06** | Empty/short topic input validation in Studio | **PASS** | `[role="alert"]` displayed immediately |
| **E2E-07** | Studio navigation back to Home (`/`) | **PASS** | Back button restores landing page state |
| **E2E-08** | Pure render route isolation (`/render`, `/render-lesson`) | **PASS** | Verified 0 instances of `.blu-hero` or `.blu-robot-3d` |
| **E2E-09** | Graceful WebGL-disabled fallback robot | **PASS** | `outputs/frontend-evidence/webgl_fallback_robot.png` |

---

## 2. 3D Robot Mascot Verification

### Head-Tracking Physics & Limits
- **Pivot Point**: Neck collar joint at `[0, 0.42, 0.08]`.
- **Yaw Range**: Clamped to $\pm 0.45\text{ rad}$ ($\approx \pm 25.8^\circ$).
- **Pitch Range**: Clamped to $\pm 0.25\text{ rad}$ ($\approx \pm 14.3^\circ$).
- **Hero-wide Listener**: Cursor tracking computes normalized offset across the full `.blu-hero` bounding box relative to robot head center.
- **Eye Gaze**: Pupil meshes shift dynamically inside the dark glossy visor to match gaze direction.
- **Stability**: Torso, arms, held book stack, and floor base books remain firmly anchored during head turns.
- **Damping**: Linear interpolation via `delta * 5` in `useFrame` loop ensures smooth movement without jitter.
- **Idle Motion**: Natural sine-wave breathing suspended automatically under `prefers-reduced-motion: reduce`.

### WebGL Fallback
- When `gl` context is null or unsupported, `WebGLErrorBoundary` renders `<StaticRobot />` instantly with zero layout shift.
- Visual elements included in fallback: yellow rounded helmet, cyan antenna sphere, blue ear-cups, dark visor with glowing cyan eyes and pupils, held book stack, and base floor books.

---

## 3. Dedicated Lesson Studio (`/studio`) Verification

### Form Contract & Parameters
- **Topic Input**: Accessible `<textarea>` with 5 quick suggestion chips.
- **Level**: `beginner` (Introductory) or `intermediate` (In-depth).
- **Language**: `en` (English), `hi` (हिन्दी), `kn` (ಕನ್ನಡ).
- **Duration**: `0` (Auto complexity, default 30–90s nominal budget) or manual overrides (`30`, `60`, `90`).
- **Submission Safety**: Double-click prevented; button disabled during active generation.

### Lesson Player Integration
- Fully embeds Phase 4 `LessonPlayer` and `SceneCanvas`.
- Renders typed visual families (illustrations, function plots, algorithm state, etc.).
- Audio playback and synchronized captions driven by measured PCM cue timestamps.
- Video export (`.mp4`) and subtitle export (`.srt`) functional.

---

## 4. Protected Route Parity

The headless video export and frame verification routes bypass the landing page and 3D canvas entirely:
- `/render` -> `<ExportView />`
- `/render-lesson` -> `<GeneratedExportView />`
- `/render-localized` -> `<LocalizedExportView />`
- `/lesson` -> `<PreparedLessonView />`

Confirmed with Playwright: `count(.blu-hero) === 0` and `count(.blu-robot-3d) === 0`.
