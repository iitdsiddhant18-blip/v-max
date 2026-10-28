# Visual DSL v2

Phase 4 adds a semantic sidecar. Existing `Lesson`, `Scene`, sample timelines and
their IDs are preserved. The authoritative contract is
`backend/app/visual_schema.py`; `frontend/src/visuals/contracts.ts` is generated
from its JSON schema. No model JSON contains geometry, executable code, URLs,
CSS, SVG paths or independent animation clocks.

## Envelope and identity

`VisualPlan = {visual_schema_version:2, source_lesson_id:64hex, scenes:VisualScene[]}`.
There are exactly 3–6 scenes, one per source scene, in identical index order.
Every source English narrated beat must have an action. Titles have one beat;
other scenes retain explicit label/fact pairs. Structured teaching drafts are
normalized into the existing `Short label :: spoken fact` representation.
Each source fact also names its `source_label`, `relation_label`, and
`target_label`. These semantic relationships are validated and cached alongside
the canonical source, then own node IDs, edge IDs and per-beat reference counts.
The visual model cannot silently drop a source relationship or narrated beat.

New draft decoding asks for a three-step worked example: a concrete case or
changed condition, its result, then why. Qualitative predictions are permitted;
invented measurements are not. A bounded local factual critique can request one
source repair. This model check is supplementary evidence, not human fact QA.
Critique failures and raw replies are retained by the real matrix harness.

`VisualScene` contains `scene_index`, `family`, nullable installed `template_id`,
1–12 `entities`, 0–16 `relationships`, 1–64 `display_text_en` entries,
1–32 `beat_actions` and a discriminated typed `data` object. All models forbid
unknown fields and assignment after construction. Containers are serialized and
revalidated at persistence boundaries; callers must not mutate nested dictionaries.
IDs match `^[a-z][a-z0-9_]{0,39}$`. Labels are 1–180 characters; translated labels
are nonempty and at most 240 characters. No markup or remote URL is accepted.

Entities have `id`, semantic `role`, `label_key`, optional validated `anchor_id`.
Relationships have existing `source`, `target`, a known kind (`flow`, `causes`,
`sequence`, `contains`, `exchange`, `comparison`) and translatable `label_key`.
Self edges and dangling references are rejected. Tree layouts reject cycles.
Actions have a valid `beat_index`, closed `op`, existing `target_ids`, optional
bounded `state_index` or numeric `value`. Incompatible family/action pairs fail.

The stored envelope records `visual_source:llm|fallback`, fallback reason,
renderer revision, validated plan and SHA-256 visual ID. The canonical hash is
sorted UTF-8 JSON over the exact plan plus renderer/asset revision. The sidecar
lives in `backend/cache/visuals/<English ID>/current.json`, written atomically.
Every read revalidates the plan, source linkage and hash; corruption cannot turn
a directory into a ready visual. Existing audio caches are never deleted for a
visual update. Invalid localized audio caches are preserved under `.invalid-*`
before a rebuilt version is atomically published.

## Families and typed payloads

| Family | Payload and numeric rules |
|---|---|
| concept_map / flow_process / generic_diagram | `layout:row|tree|cycle`; explicit labeled entities/edges, no invented anatomy. |
| labelled_illustration | Installed `template_id` and known entity anchors; `zoom:none|focused_part`. |
| function_plot | `function:polynomial|reciprocal|absolute|exponential|sine|cosine`; ascending polynomial coefficients (degree ≤4), bounded scale/frequency/shift/offset, increasing finite x/y windows, x/y/curve label keys, ≤6 marked x values, optional tangent/secant x and shaded interval. |
| number_line | Increasing finite minimum/maximum, ≤8 points, ≤3 intervals with explicit open/closed endpoints, axis text key. |
| data_chart | bar/line/pie, ≤8 categories, ≤3 equal-length series, axis and series label keys; bars start at zero; pie has one nonnegative positive-total series. |
| force_motion | force/motion/circuit/wave; positive mass/time/resistance/voltage/amplitude/frequency, ≤6 finite named vectors with units N, m/s, m, m/s²; all annotations use keys. |
| formula / equation_balance | expression and step text keys; optional typed `[a,b,c]` for `a*x+b=c`, with nonzero `a`; trusted code computes solution steps. |
| reaction_equation | ≤4 species on each side, explicit coefficients/states and label keys; bounded elemental formula syntax; atom counts must balance. Unsupported grouped/charged formula syntax is rejected. |
| lab_process | 2–4 known apparatus shapes; bounded capacity/volume/solute amounts; source/target IDs and transfer amount; no overflow or negative remaining volume. Symbolic educational transfer, not a protocol. |
| code_trace | Exact source code (≤12 lines/1200 chars), bounded or honest explanation mode; translated variable/output/status labels; no execution through Python eval/exec. |
| algorithm_state | hanoi with 2–4 disks, or binary_search with ≤12 distinct sorted bounded integers; pointer/state label keys. Trusted states, monotonic narrated state groups, required correct final state. |
| timeline | 2–8 known entity events with unique increasing order and translated time-label keys. Ordering does not invent dates. |
| comparison / table | 2–3 translated columns, 1–5 equal-width rows of text keys. |

All ordinary numeric fields are finite and bounded to ±10000. Positive quantities
must be positive. Plot windows are bounded to ±100 in x with nonzero width.
Numerical evaluation has at most 241 samples. Undefined reciprocal points split
paths; plots are clipped to their axes. Model-provided y coordinates are not
accepted: trusted code computes values and derivatives. There is no string
expression evaluator or mathjs dependency.

## Illustration catalog

Locally authored schematic geometry has stable, code-owned anchors:

- human_digestive_system: mouth, esophagus, stomach, small_intestine,
  large_intestine, villi (supported schematic inset), bloodstream.
- human_heart: right_atrium, right_ventricle, left_atrium, left_ventricle,
  lungs, body. This is a flow schematic, not a diagnostic/anatomically scaled image.
- plant_cell: cell_wall, membrane, nucleus, cytoplasm, chloroplast, vacuole,
  mitochondrion.
- animal_cell: membrane, nucleus, cytoplasm, mitochondrion.
- leaf_photosynthesis: leaf, chloroplast, roots, stem, air, sugar, oxygen.

An unsupported structure must use a relevant relationship diagram. No anchor is
created by matching English or translated topic words in the rich renderer.
Unanchored context nodes may accompany an illustration, but are drawn as abstract
off-object nodes. At least one installed anchor is required. An anchored label
must name that actual part; a broad stomach anchor cannot be relabeled as a
precise unsupported sphincter or liver.

## Trusted computations and code

Hanoi states are generated by a trusted solver; n=3 has seven legal moves ending
with all disks on C. Narrated move groups traverse intermediate states directly
from progress. Binary search derives low/mid/high and termination from sorted
input. Model-created move lists or output tables are not accepted.

The trace interpreter reads Python AST data. Allowed: bounded literal integer,
string and list values; assignments; integer arithmetic/comparisons; a simple if;
bounded for over a small literal list or constant range; print. Limits: 40 states,
150 AST nodes, 500 expression operations, 12 list/range elements, 100000 integer
magnitude and 80-character strings. Imports, attributes, while, comprehensions,
arbitrary functions, files, network, recursion, classes and execution primitives
are rejected. Unsupported programs remain explicitly annotated explanations.

## Localization and deterministic time

English semantic IDs, anchors, actions, graph coefficients, units and code are
identical across EN/HI/KN. Only `visual_labels[scene][key]` changes. IndicTrans2
translates visual strings through the existing local adapter. Empty/missing/extra
keys or unprotected English-only labels in Indic output fail closed. Code tokens,
mathematical symbols, standard units and supported proper names stay protected.
The overlay is hashed and cached independently of audio.

For target-language scene-local time `t`, choose the actual recorded PCM cue `k`.
`p=clamp((t-cue[k].start)/(cue[k].end-cue[k].start),0,1)`. Prior actions are complete,
the current action interpolates with `p`, future actions are hidden. State is a
pure function of plan, overlay, computed trusted values, `k` and `p`. During the
0.5s pause `p=1`, so scene contents freeze. There are no lesson-owned animation
timers, counters or effects. The player alone samples the native audio clock.

Fonts are explicitly loaded from bundled Noto assets before render readiness;
canvas measurement wraps whole Unicode grapheme clusters. No required label is
ellipsized. The caption band remains reserved at y=579–720. Both player and
`/render-lesson` / `/render-localized` use `VisualDispatcher` through SceneCanvas.

The render hash includes semantic visual revision and localized label overlay.
Rich exports use `<audio-id>.<render-id>.mp4`; revision-qualified URLs avoid stale
diagrams and rendering fails if the sidecar changes mid-export. The first export
may create a non-overwriting canonical alias for older verification tools. Old
MP4s and legacy routes remain accessible; absent sidecars use the old renderer.

## Fixtures and unsupported cases

Executable, validated example JSON for every family is generated from
`backend/tests/test_visual_schema.py::scene_for` and saved with the QA snapshots.
These are controlled test fixtures, not model-generation evidence. See the QA
report for genuinely generated topics and fallback counts. Generic visual fallback
uses actual lesson labels and honest explanation ordering; it never asserts an
invented causal relationship. Failed source planning remains a clearly identified
outline rather than a fabricated completed lesson.
When structured source relationships are available, generic fallback draws those
actual directed labeled relationships. Older source lessons without this sidecar
use explicitly labeled explanation ordering. Partial visual failures are recovered
scene by scene and report `scene_sources`; they are not counted as all-rich success.

Unsupported physiology precision, advanced math, arbitrary code and hazardous
real-lab instructions are not simulated. Factual/translation review remains
separate from schema validity and deterministic rendering.

## Owner-feedback correction revision

Renderer `rich-svg-2.2` implements a clipped magnified view of the selected named
part. After a model selects an installed illustration, trusted normalization adds
only installed part names actually present in that source beat. These additions
use stable IDs and the ordinary translation dictionary. It cannot select a
template, invent relationships, or assign a different name to an anatomical
anchor. Digestive catalog anchors include pancreas; villi contain a schematic
epithelial outline and capillary. This is an educational schematic, not a clinical
anatomical atlas. The active relationship alone gets its moving marker and label.

Old renderer envelopes migrate only after their stored revision/hash/source
validate; prior envelopes are archived, and audio is reused. The new render hash
changes, preserving old videos. Trusted plot normalization reconstructs bounded
numeric parameters from an explicit source equation and independently checks
fractional sample points; JSON never executes an expression.

Newly synthesized English uses the already installed English `af_heart` preset
at speed 1.0. Older generated caches and the fixed English/Hindi samples retain
their original voices and files. Facts are complete sentence-sized PCM segments;
cues are measured from those samples. The installed Kokoro graph exposes audio
only, so this is **beat alignment, not word alignment** or a forced aligner.
The hook is one visual cue even if it contains two sentences. Browser and export
fonts load before frames become ready. Source rewrites create distinct lesson IDs.
