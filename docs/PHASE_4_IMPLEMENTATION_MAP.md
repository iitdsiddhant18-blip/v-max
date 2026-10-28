# Phase 4 implementation map — 2026-10-28

Starting HEAD: `91f7798`. Part 3b is present as owner-owned uncommitted work.
Initial status is saved verbatim in `outputs/phase4-evidence/initial-status.txt`.
Preserve those changes, the ZIPs, models, environments, existing media and caches.
The plan was located and read at `C:/Users/Siddh/Downloads/BLU_VISUAL_TEACHER_PLAN.md`.

## Exact planned paths

| Paths | Purpose / gate |
|---|---|
| backend/app/localized_media.py; backend/tests/test_visual_cache.py | Shared full cache validation, corruption regression, safe replacement (0). |
| backend/app/visual_schema.py; backend/app/visual_validate.py; backend/app/visual_cache.py | Strict versioned semantic contract, numeric/relationship/action validators and separate sidecar namespace (1). |
| backend/app/algorithm_trace.py | Bounded trusted Hanoi/binary-search/AST-data interpreter and plot evaluator (1,3). |
| backend/app/lesson_complexity.py; backend/app/visual_planner.py | Evidence-based auto rubric and local structured semantic planning (2). |
| backend/app/schema.py; backend/app/planner.py; backend/app/live.py; backend/app/generic_fallback.py | Backward-compatible duration marker, generalized teaching, measured speech, relevant fallback (2). |
| backend/app/visual_localize.py; backend/app/translated_lesson.py; backend/app/main.py | Stable display-text overlays, sidecar attachment and existing endpoint integration (4). |
| backend/app/live_export.py; backend/app/localized_export.py | Strict duration and visual revision integrity, preserve old files/routes (4). |
| frontend/src/visuals/contracts.ts; layout.ts; animation.ts; textLayout.ts | Exact contract types, deterministic layout/state and bundled-font measurement (3). |
| frontend/src/visuals/VisualDispatcher.tsx; Primitives.tsx; Illustrations.tsx; NumericScenes.tsx; StructuralScenes.tsx | Group related families into implemented reusable SVG components; avoid empty per-family placeholders (3). |
| frontend/src/types.ts; DynamicSceneContent.tsx; SceneCanvas.tsx; LessonPlayer.tsx | Optional sidecar and per-language cues, pure renderer dispatch, preserve legacy (3,4). |
| frontend/src/App.tsx | Only add Auto(default)/manual duration selection (2). |
| backend/tests/test_visual_schema.py; test_visual_planner.py; test_visual_cache.py; test_auto_duration.py; test_visual_localization.py; test_algorithm_trace.py | Positive, hostile, numeric, state, cache and compatibility coverage (0–4). |
| backend/scripts/visual_qa_matrix.py; frontend/src/visuals/tests/visual_qa.py | Real diverse generation/media harness and deterministic browser fixtures (5). |
| backend/scripts/visual_media_qa.py | Sequential delivery/revalidation of recorded real lessons, 3-language PCM/SRT, revision-aware export and frame evidence (4,5). |
| docs/VISUAL_DSL.md; docs/GENERALIZATION_QA.md; docs/PHASE_4_VERIFICATION_REPORT.md; README.md | Contracts, empirical results, raw evidence and truthful usage (5). |
| docs/visual_schema.json; docs/visual_examples.json | Exact machine-readable contract and validated per-family example payloads supporting DSL documentation. |
| docs/LICENSES.md (append only); docs/phase4-assets/* | Provenance for newly authored SVG code and clearly labeled verification screenshots. Existing licence audit remains intact. |

No dependency installation is planned. Use a small bounded typed numerical evaluator,
not mathjs or arbitrary expression evaluation. Author all geometry locally; no remote assets.
One existing assertion in `backend/tests/test_live.py` will be updated from its old
subject-specific exactly-five-scene grammar expectation to the explicitly required
subject-neutral 3–6 grammar. Other legacy assertions remain intact.
`backend/tests/test_localized_media.py::test_api_endpoints_safety` must use a
production-valid 30–90s synthetic fixture for its HTTP success case. Short PCM
fixtures remain supported only through explicitly isolated internal calls.
If a supporting path becomes necessary, record it here before creating it.

## Protected paths

LandingHero.tsx, RobotMascot.tsx, landing.css, SamplePlayer.tsx, old sample fixtures,
media.py/exporter.py, .gitignore, environment/model binaries and original user artifacts.
Do not stage or commit pre-existing Part 3b changes as if authored in Phase 4.

## Gate checkpoints

Supporting evidence tool `backend/scripts/visual_artifact_check.py` independently
reads actual manifests, WAV, exported MP4 and SRT; it does not generate lesson
content. Primary-test review also added presence/absence and structural-part
grounding checks in `visual_validate.py` before processing the owner holdouts.
`backend/scripts/export_visual_contract.py` regenerates the canonical TypeScript
mirror and JSON-schema/example documentation from the validated backend contract.
`LessonPlayer.tsx` adds a narrow-screen enlarge/scroll control plus the existing
caption/label text fallback, so the fixed 720p diagram remains readable on phones.
This changes player accessibility, not the landing page or export geometry.

Owner rejection of the first real digestive lesson triggered a correction pass:
`live.py` now uses an installed native English voice for newly synthesized lessons
(existing cached audio and fixed sample voices remain valid); hook cue cardinality
matches the one-beat visual contract. `visual_validate.py` grounds parts only after
a model selects an installed illustration, and `Illustrations.tsx` implements a
cue-driven magnified view. `visual_localize.py` prevents prose hyphenated labels
being mistaken for code. Supporting `indic_translator.py` changes batch size from
4 to 1 after a real CUDA out-of-memory failure on this 4 GB device. No dependency,
weight, hardware setting or old binary cache is changed by these corrections.

Each gate records tests, diff audit and evidence before advancing. Human physical
offline and native-language checks remain explicitly unverified until observed.
