# ParityLens — Milestone 1 Plan

## Top-Level Overview

ParityLens is a narrow debugging workflow for computer-vision engineers. It
takes a single input image, runs it through two independently-written
preprocessing pipelines (reference and candidate/serving), and uses a
stage-by-stage contract comparison to surface the first location where the
outputs diverge in a semantically meaningful way — even when shape and dtype
are identical.

**Milestone 1 scope (only):**

- One synthetic PNG fixture (clean RGB image, known pixel values)
- One clean control fixture (identical pipeline, must pass)
- A deterministic Python reference preprocessing pipeline
- A deterministic Python candidate preprocessing pipeline with a single
  deliberate RGB→BGR channel-order defect
- A machine-readable preprocessing contract (JSON)
- A stage comparator that reads the contract and catches the defect
- A CLI entry point (`python -m paritylens`)
- Reproducible evidence artefacts (numpy arrays saved to disk)
- An AGENTS.md that encodes all immutability rules

**Non-goals for Milestone 1:**

- Web UI or visualisation dashboard
- General MLOps platform features
- Model inference
- Batched or streaming inputs
- Any pipeline defect other than channel-order mismatch

---

## A. Reference Pipeline

The reference pipeline is the human-approved, ground-truth path. Every stage
output is the definition of correct.

**Fixture precondition:** The input PNG is already exactly 224×224 pixels.
Resizing is therefore a no-op numerically, but the bilinear configuration is
kept explicit so the contract accurately describes what would happen on a
differently-sized input.

| Stage | Operation | Notes |
|---|---|---|
| `decode` | `PIL.Image.open` → `numpy.array(dtype=uint8)` → assert `mode == "RGB"` | Explicit RGB assertion; saves HWC uint8 array |
| `geometry` | No-op stub — returns the `decode` array unchanged | Reserved for crop/pad; always passes in Milestone 1 |
| `scaling` | `PIL.Image.resize((224, 224), PIL.Image.BILINEAR)` → `numpy.array(dtype=float32)` → **divide by 255.0** | Output value range `[0.0, 1.0]`; bilinear is explicit but irrelevant on a 224×224 input |
| `normalization` | Subtract per-channel mean `[0.485, 0.456, 0.406]`, divide by std `[0.229, 0.224, 0.225]` | Applied in RGB channel order (channel 0 = R, 1 = G, 2 = B); internal arithmetic in float64, cast to float32 before save |
| `model_input` | `np.transpose(array, (2, 0, 1))` → shape `(3, 224, 224)`, dtype `float32` | CHW layout, no batch dimension |

Each stage saves its output array to `evidence/reference/<stage>.npy`.

---

## B. Candidate (Serving) Pipeline

The candidate pipeline is independently written to simulate a realistic serving
implementation. It contains **exactly one deliberate semantic defect**: the
channel-order swap introduced by `cv2.imread`.

**Fixture precondition:** Same 224×224 PNG as the reference run.

| Stage | Operation | Defect |
|---|---|---|
| `decode` | `cv2.imread(path)` → array is `(H, W, 3)` **BGR** uint8 | **The only deliberate defect.** `cv2.imread` returns BGR by default; the array is stored and saved as-is without conversion |
| `geometry` | No-op stub — returns the `decode` array unchanged | No defect |
| `scaling` | `cv2.resize(array, (224, 224), interpolation=cv2.INTER_LINEAR)` → `float32` → **divide by 255.0** | No value-range defect — scaling is semantically identical to reference; value range is `[0.0, 1.0]`; the channel order defect propagates transparently |
| `normalization` | Subtract `[0.485, 0.456, 0.406]`, divide by `[0.229, 0.224, 0.225]` | **No additional defect introduced here.** The same constants are applied to channel 0, 1, 2 — but channel 0 is Blue (not Red), so the wrong normalisation is applied per channel. This is a consequence of the decode defect, not a second independent defect |
| `model_input` | `np.transpose(array, (2, 0, 1))` → shape `(3, 224, 224)`, dtype `float32` | Shape and dtype match reference; defect is invisible to naïve shape/dtype checks |

Each stage saves its output array to `evidence/candidate/<stage>.npy`.

The defect is realistic: `cv2.imread` is the most common OpenCV entry point in
serving stacks, and its BGR default is a well-known production footgun.

---

## C. Approved Contract Proposal

Stored at `contract/preprocessing_contract.json`.

```json
{
  "version": "1.0",
  "approved_by": "HUMAN",
  "fixture": {
    "size": [224, 224],
    "format": "PNG",
    "probe_pixel": {
      "coordinate": [0, 0],
      "comment": "Top-left pixel. R != G != B and |R - B| > 50 in uint8 space. Documented in fixture README."
    }
  },
  "stages": {
    "decode": {
      "channel_order": "RGB",
      "dtype": "uint8",
      "layout": "HWC"
    },
    "geometry": {
      "no_op": true
    },
    "scaling": {
      "target_size": [224, 224],
      "resample": "bilinear",
      "divide_by": 255.0,
      "value_range": [0.0, 1.0],
      "dtype": "float32",
      "layout": "HWC"
    },
    "normalization": {
      "mean": [0.485, 0.456, 0.406],
      "std": [0.229, 0.224, 0.225],
      "channel_order": "RGB",
      "internal_precision": "float64",
      "output_dtype": "float32",
      "layout": "HWC"
    },
    "model_input": {
      "shape": [3, 224, 224],
      "dtype": "float32",
      "layout": "CHW",
      "channel_order": "RGB"
    }
  },
  "comparison": {
    "atol": 1e-5,
    "rtol": 1e-5,
    "enforce_channel_order": true,
    "comparator_policy": "compare_recorded_arrays_as_is__no_channel_reorder__no_value_transform"
  }
}
```

**Key contract decisions (all human-approved):**

- `channel_order: "RGB"` is the approved semantic at every stage where colour
  order is observable.
- `scaling.divide_by: 255.0` is now **explicit** in the contract. Both
  reference and candidate must divide by 255 after the resize. This removes the
  accidental 0–255 vs 0–1 ambiguity that existed in the previous plan.
- `fixture.size: [224, 224]` is contractually required. The resize step is a
  no-op on Milestone 1 fixtures; cross-library resampling differences cannot
  obscure the channel-order defect.
- `fixture.probe_pixel` documents the coordinate and requirement used by the
  comparator's channel-order classification step.
- `internal_precision: "float64"` at normalization prevents float32 rounding
  from exceeding `atol=1e-5` on the clean control path.
- `atol/rtol: 1e-5` tolerates float32 rounding but firmly rejects channel-swap
  magnitudes (~0.06–0.40 in normalised space).
- `comparator_policy` is a human-readable reminder that the comparator must
  never silently reorder, renormalize, or transpose arrays before comparison.
- The contract file is immutable during a repair cycle.

---

## D. Comparable Stage Map

Only stages where a meaningful comparison can be drawn are listed. The
comparator reads this map at runtime.

| Stage | Reference output | Candidate output | Comparable? | Primary check | Classification step |
|---|---|---|---|---|---|
| `decode` | `(224,224,3)` uint8 RGB | `(224,224,3)` uint8 BGR | **YES** | `np.allclose(ref, cand, atol, rtol)` → **FAIL** | If allclose fails: read probe pixel at documented coordinate; if `cand[r,c,0] ≈ ref[r,c,2]` and `cand[r,c,2] ≈ ref[r,c,0]` → classify `channel_order_mismatch` |
| `geometry` | `(224,224,3)` uint8 (passthrough) | `(224,224,3)` uint8 (passthrough) | YES | `np.array_equal(ref, cand)` → PASS | n/a (no-op) |
| `scaling` | `(224,224,3)` float32 [0,1] | `(224,224,3)` float32 [0,1] | YES | `np.allclose(ref, cand, atol, rtol)` → **FAIL** | Same probe test as decode; confirms channel-order propagation |
| `normalization` | `(224,224,3)` float32 normalised | `(224,224,3)` float32 normalised | YES | `np.allclose(ref, cand, atol, rtol)` → **FAIL** | Numerical divergence exceeds atol |
| `model_input` | `(3,224,224)` float32 CHW | `(3,224,224)` float32 CHW | YES | `np.allclose(ref, cand, atol, rtol)` → **FAIL** | Shape/dtype match; allclose fails |

**Comparable stage design rules:**

1. Two stages are comparable only if both produce an array covering the same
   semantic content (same image, same geometric extent, same value domain).
2. `geometry` is comparable because both are no-ops; if they diverge in future,
   a human must re-approve comparability.
3. The comparator reports the **first** failing stage and stops. It does not
   cascade through subsequent stages after the first failure.
4. **The comparator never modifies arrays before comparison.** No channel
   reordering, no re-normalisation, no transposition — only safe dtype
   conversion (e.g. float32 → float64) for the purpose of computing the
   numerical error. Recorded arrays are compared as recorded.
5. The known-pixel probe is used **only to classify** the type of defect after
   a numerical failure is established. It cannot make a failing comparison pass.

**Detection sequence on the defect fixture:**

The comparator iterates stages in contract order. `decode` is stage 1. The
numerical comparison (`np.allclose`) fails immediately because `cv2.imread`
produced a BGR array. The probe classification then confirms the swap pattern.
The comparator exits with code 1 and reports `decode` as the first failing
stage with defect class `channel_order_mismatch`. Subsequent stages are not
evaluated.

---

## E. Resolved Decisions and Remaining Uncertainties

### Resolved (human-approved)

| # | Decision | Resolution |
|---|---|---|
| E1 | **Resample filter parity** | Fixture is exactly 224×224. Resize is a no-op. PIL BILINEAR vs cv2 INTER_LINEAR difference cannot appear. Bilinear config remains explicit in both pipelines. |
| E2 | **Channel-order proof method** | **Approved: option (a) — known-pixel probe at a fixed coordinate.** Fixture must have R≠G≠B and \|R−B\| > 50 in uint8 at the documented probe coordinate (top-left pixel `[0,0]`). Probe is used for classification only; it cannot override the primary numerical comparison. |
| E3 | **`atol` and `rtol`** | **Approved: 1e-5 for both.** Valid for PNG-only, deterministic pipelines. Must be re-approved if fixture format changes. |
| E4 | **Evidence format** | **Approved: `.npy` per stage.** One file per stage per pipeline. No NPZ packaging in Milestone 1. Archive format may be added later without changing the comparison engine. |
| E5 | **Geometry stage** | **Approved: include as an explicit no-op stub.** Contract schema is forward-compatible. |
| E6 | **Batch dimension** | **Approved: no batch dimension.** `model_input` shape is `(3, 224, 224)`. |

### Remaining uncertainty requiring implementation-time attention

| # | Uncertainty | Impact | Mitigation already in plan |
|---|---|---|---|
| R1 | **float32 rounding on clean control** | If float32 intermediate arithmetic in normalisation exceeds `atol=1e-5` between the two reference runs (in the clean control), the control will emit a false positive. | Both pipelines use float64 internally in the normalisation stage and cast to float32 only at `model_input`. Verify with clean control before declaring the defect experiment valid. |
| R2 | **Probe coordinate assumption** | The probe is documented as `[0, 0]` (top-left pixel). If the fixture generator does not guarantee the top-left pixel satisfies R≠G≠B and \|R−B\| > 50, the classification step will silently produce an inconclusive result. | Fixture generator must write a companion `fixtures/fixture_metadata.json` documenting the probe pixel coordinate and its exact R, G, B values, so the comparator can assert the precondition at startup. |

---

## F. Proposed AGENTS.md

```markdown
# AGENTS.md — ParityLens Immutability Rules

## Purpose

This file encodes the rules that govern how Bob and any automated agent must
behave when working inside the ParityLens repository. These rules exist to
ensure that a verified repair is meaningful and that evidence cannot be
fabricated by relaxing constraints.

---

## Rule 1 — Reference behaviour is human-approved

The reference pipeline (`paritylens/pipelines/reference.py`) and every stage
it contains represent the ground truth for correct preprocessing.

**Agents must not modify any file in `paritylens/pipelines/reference.py`.**

A change to the reference pipeline is not a repair. It is a redefinition of
correctness. Any such change requires explicit human approval and a new
contract version.

---

## Rule 2 — Candidate code cannot redefine the expected result

When a defect is detected, the fix must be applied to the candidate pipeline
(`paritylens/pipelines/candidate.py`). The fix must bring the candidate output
into alignment with the reference output.

**Agents must not modify the reference pipeline to match the candidate output.**

---

## Rule 3 — Comparison policy cannot be modified during repair

The contract file (`contract/preprocessing_contract.json`) and the comparator
(`paritylens/comparator.py`) define what counts as a passing result.

**Agents must not modify `contract/preprocessing_contract.json` or
`paritylens/comparator.py` during a repair cycle.**

Widening tolerances, removing stages from the stage map, or disabling checks
to make a repair pass is forbidden without a new human-approved contract
version.

---

## Rule 4 — Fixtures cannot be changed to make a repair pass

Synthetic fixtures (`fixtures/`) are fixed inputs. Their pixel values are
part of the experiment definition.

**Agents must not modify or replace fixture files during a repair cycle.**

If a fixture is genuinely incorrect, that is a separate human-approved action
that produces a new fixture version with a documented rationale.

---

## Rule 5 — The verifier cannot be weakened during repair

The verification script (`paritylens/verifier.py`) checks that a normal
candidate run, with no diagnostic intervention, produces output that satisfies
the contract.

**Agents must not modify `paritylens/verifier.py` during a repair cycle.**

---

## Rule 6 — Diagnostic replay is not equivalent to verified repair

Running the comparator against saved `.npy` artefacts (replay mode) is a
diagnostic tool. It does not constitute a verified repair.

**A repair is only verified when `python -m paritylens --verify` runs the full
candidate pipeline end-to-end (no cached artefacts) and the comparator passes
all stages.**

---

## Rule 7 — Verified repair requires a normal candidate run with intervention disabled

The `--verify` flag runs the candidate pipeline without any patching, monkey-
patching, or stage injection. The candidate code must be genuinely fixed.

**Agents must not use runtime patching to pass verification.**

---

## Rule 8 — Unsupported or ambiguous cases must remain visible

If the comparator encounters a stage that is not in the approved stage map, or
a fixture that violates a contract precondition, it must emit a visible warning
and exit with a non-zero code.

**Agents must not silently skip ambiguous stages or suppress warnings to
produce a clean run.**

---

## Scope of agent autonomy

Bob may:
- Read all files in the repository.
- Propose changes to `paritylens/pipelines/candidate.py`.
- Run `python -m paritylens` and `python -m paritylens --verify`.
- Inspect evidence artefacts in `evidence/`.

Bob must not (without explicit human approval):
- Modify the reference pipeline.
- Modify the contract file.
- Modify the comparator or verifier.
- Modify fixtures.
- Modify this AGENTS.md file.
```

---

## G. Minimum Repository Structure

```
paritylens/
├── AGENTS.md
├── README.md
├── paritylens-plan.md          ← this file
├── contract/
│   └── preprocessing_contract.json
├── fixtures/
│   ├── defect_rgb_bgr.png      ← synthetic colour image, R≠G≠B at known pixel
│   └── control_clean.png       ← identical image; used for the clean control run
├── paritylens/
│   ├── __init__.py
│   ├── __main__.py             ← CLI entry point
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── reference.py        ← stages: decode, geometry, scaling, normalization, model_input
│   │   └── candidate.py        ← same stages; decode uses cv2.imread (BGR defect)
│   ├── comparator.py           ← reads contract; compares stage outputs; reports first failure
│   └── verifier.py             ← runs candidate end-to-end with no patching; calls comparator
├── evidence/
│   ├── reference/              ← .npy files written by reference pipeline
│   └── candidate/              ← .npy files written by candidate pipeline
└── requirements.txt            ← numpy, pillow, opencv-python
```

**File count: 14 files (including __init__.py stubs and fixtures).**

No framework, no config management library, no test runner beyond the CLI.

---

## H. First Experiment Acceptance Criteria

### Experiment 1 — Channel-order defect detected

```
SAME ORIGINAL IMAGE  (fixtures/defect_rgb_bgr.png, exactly 224x224 PNG)
         ↓
Reference pipeline   → evidence/reference/{decode,geometry,scaling,normalization,model_input}.npy
                       decode: HWC uint8 RGB, value range [0,255]
                       scaling: HWC float32 RGB, value range [0.0, 1.0] (÷255 applied)
         ↓
Candidate pipeline   → evidence/candidate/{decode,geometry,scaling,normalization,model_input}.npy
                       decode: HWC uint8 BGR (cv2.imread default — same numeric pixels, wrong channel order)
                       scaling: HWC float32 BGR, value range [0.0, 1.0] (÷255 applied — same operation, wrong order propagated)
         ↓
Naïve checks         → shape model_input (3,224,224) == (3,224,224) ✓
                       dtype float32 == float32 ✓
                       numpy.allclose → False (hidden by naïve check)
         ↓
ParityLens comparator (reads contract; iterates stages in order; compares recorded arrays as-is)
         ↓
Stage decode:  np.allclose(ref_decode, cand_decode) → FALSE
               probe pixel [0,0]: ref=(R,G,B), cand=(B,G,R) → classifies channel_order_mismatch
               STOP — first failure found
         ↓
EXIT 1   FAIL  stage=decode  defect=channel_order_mismatch
```

**Acceptance criteria (must all be true):**

- [ ] `python -m paritylens --fixture fixtures/defect_rgb_bgr.png` exits with code **1**
- [ ] stdout names the failing stage as `decode`
- [ ] stdout names the defect class as `channel_order_mismatch`
- [ ] No exception or traceback is raised
- [ ] `evidence/reference/decode.npy` and `evidence/candidate/decode.npy` exist and are loadable
- [ ] `numpy.allclose(ref_model_input, cand_model_input)` returns **False**
- [ ] Shape of `model_input.npy` is identical between reference and candidate: `(3, 224, 224)`
- [ ] dtype of `model_input.npy` is identical between reference and candidate: `float32`
- [ ] `evidence/reference/scaling.npy.max()` is ≤ 1.0 (confirms ÷255 was applied in reference)
- [ ] `evidence/candidate/scaling.npy.max()` is ≤ 1.0 (confirms ÷255 was applied in candidate)
- [ ] Comparator does **not** reorder or modify arrays before comparison (verified by code inspection)

### Experiment 2 — Clean control passes

```
SAME ORIGINAL IMAGE  (fixtures/control_clean.png, same file as defect_rgb_bgr.png for Milestone 1)
         ↓
Reference pipeline   → evidence/reference/{all stages}.npy
         ↓
Candidate pipeline   → reference pipeline used as candidate (--use-reference-as-candidate flag)
         ↓
ParityLens comparator
         ↓
All stages: np.allclose → TRUE (within atol=1e-5, rtol=1e-5)
         ↓
EXIT 0   PASS  all stages
```

**Acceptance criteria (must all be true):**

- [ ] `python -m paritylens --fixture fixtures/control_clean.png --use-reference-as-candidate` exits with code **0**
- [ ] All stage comparisons reported as PASS
- [ ] No channel-order warnings emitted
- [ ] Maximum absolute difference across all stages is below `atol=1e-5` (confirms float64 internal precision is effective)

> **Note on control design:** For Milestone 1 the clean control is implemented
> by running the reference pipeline twice (once as "reference", once as
> "candidate"). This is the minimal proof that the comparator does not produce
> false positives and that float32 rounding does not trigger a spurious failure.
> A real repaired candidate is validated during the repair cycle, not in the
> fixture definition.

---

## I. Risks That Could Invalidate the Experiment

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| I1 | **Resampling numerical mismatch** — PIL BILINEAR and cv2 INTER_LINEAR produce different subpixel values on non-224×224 images. | **Eliminated** | Fixture is required to be exactly 224×224. Resize is a no-op. This risk is mitigated by the contract fixture precondition. |
| I2 | **Fixture has equal R, G, B channels** — A greyscale or equal-channel image makes RGB/BGR swap invisible. | **Eliminated** | Contract requires probe pixel `[0,0]` to have R≠G≠B and \|R−B\| > 50. Comparator asserts this precondition at startup using `fixture_metadata.json`. |
| I3 | **Accidental 0–255 vs 0–1 value-range mismatch** — Reference missing the ÷255 step would produce a `scaling` failure before `decode` is reached. | **Eliminated** | Both pipelines now explicitly divide by 255.0 at scaling. Contract encodes `divide_by: 255.0`. Acceptance criteria check `max ≤ 1.0` on scaling evidence. |
| I4 | **cv2 not available in environment** — Import failure crashes the candidate pipeline. | Low | `requirements.txt` pins `opencv-python`; `__main__.py` catches `ImportError` and emits a clear message before exiting with code 2. |
| I5 | **Evidence directory collision** — Stale `.npy` files from a previous run contaminate a replay. | Low | Each run clears and recreates `evidence/reference/` and `evidence/candidate/` before writing. |
| I6 | **float32 rounding exceeds atol on clean control** — Normalisation rounding triggers a false positive. | Low | Both pipelines use float64 internally during normalisation; cast to float32 only at `model_input`. Clean control acceptance criterion verifies max abs diff < 1e-5. |
| I7 | **Comparator silently reorders arrays** — A well-intentioned "fix" inside the comparator masks the defect. | Low but high impact | AGENTS.md Rule 3 prohibits comparator modification. `comparator_policy` field in contract is an explicit human-readable reminder. Acceptance criteria include a code-inspection check. |
| I8 | **Probe pixel coordinate mismatch** — Fixture metadata documents `[0,0]` but the fixture generator uses a different coordinate. | Low | `fixture_metadata.json` is generated by the same script that creates the PNG; coordinate is hardcoded in both. Comparator reads and validates against metadata before running. |

---

## Sub-Tasks (for implementation phase)

Each sub-task is designed to be processed independently in Agent mode.

### Sub-task 1 — Repository scaffolding
**Intent:** Create the directory structure, empty `__init__.py` files, `requirements.txt`, and `README.md` shell.
**Status:** `[ ] pending`

### Sub-task 2 — Synthetic fixtures
**Intent:** Generate `fixtures/defect_rgb_bgr.png` (exactly 224×224, every pixel has R≠G≠B, \|R−B\| > 50, no grey pixels) and `fixtures/control_clean.png` (copy of the same image — used for the clean control run). Also write `fixtures/fixture_metadata.json` documenting the probe pixel coordinate and its exact R, G, B values.
**Status:** `[ ] pending`

### Sub-task 3 — Contract file
**Intent:** Write `contract/preprocessing_contract.json` exactly as specified in section C (revised version with `divide_by`, `internal_precision`, `comparator_policy`, and `fixture` fields).
**Status:** `[ ] pending`

### Sub-task 4 — Reference pipeline
**Intent:** Implement `paritylens/pipelines/reference.py` with all five stages. Scaling must divide by 255.0. Normalisation must use float64 internally and cast to float32 at save. Each stage saves to `evidence/reference/<stage>.npy`.
**Status:** `[ ] pending`

### Sub-task 5 — Candidate pipeline
**Intent:** Implement `paritylens/pipelines/candidate.py` with `cv2.imread` as the decode step (BGR defect). Scaling divides by 255.0 (same as reference — no second defect). Each stage saves to `evidence/candidate/<stage>.npy`.
**Status:** `[ ] pending`

### Sub-task 6 — Comparator
**Intent:** Implement `paritylens/comparator.py`. Reads contract. Validates probe pixel precondition from `fixture_metadata.json` at startup. Iterates stages in contract order. Compares recorded arrays as-is (no reorder, no transform). Uses `np.allclose` as the primary test. On failure, runs probe classification. Reports first failing stage, defect class, and evidence paths. Exits 1 on first failure.
**Status:** `[ ] pending`

### Sub-task 7 — Verifier
**Intent:** Implement `paritylens/verifier.py`. Runs the candidate pipeline end-to-end with no patching, then calls the comparator. Used by the `--verify` flag to confirm a genuine repair.
**Status:** `[ ] pending`

### Sub-task 8 — CLI entry point
**Intent:** Implement `paritylens/__main__.py`. Supports `--fixture`, `--use-reference-as-candidate`, and `--verify` flags. Clears evidence directories before each run. Catches `ImportError` for `cv2` with a clear message and exit code 2. Exits 0 on pass, 1 on defect detected, 2 on error.
**Status:** `[ ] pending`

### Sub-task 9 — AGENTS.md
**Intent:** Write `AGENTS.md` exactly as specified in section F, with Rule 3 updated to explicitly mention `comparator_policy` and the no-array-modification rule.
**Status:** `[ ] pending`

### Sub-task 10 — Acceptance test run
**Intent:** Run both experiments from section H. Confirm exit codes, stage names, defect class, evidence file existence, max scaling value ≤ 1.0, and max abs diff on clean control < 1e-5.
**Status:** `[ ] pending`
