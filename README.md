# ParityLens

ParityLens compares a trusted computer-vision preprocessing pipeline with a
serving candidate and finds the first violating comparable boundary. Matching
tensor shape and dtype can hide different channel meanings or numerical values.
The trace shows measured probes, differences, and source locations.

## Historical Bob workflow

The recorded IBM Bob IDE workflow established the contract, implemented the
comparison core, diagnosed an RGB/BGR decode mismatch, and repaired it with an
explicit `cv2.cvtColor(..., cv2.COLOR_BGR2RGB)` conversion. Session evidence is
preserved in `bob_sessions/`.

- BEFORE: exact candidate snapshot from `d0ea1fd4f967aa00b1e2113025b19d5783fc7242`.
- AFTER: current candidate checked against repair `334a4013230076fbca4d2e3eb86281d1cf29b0c6`.

The web app does not invoke Bob. The original historical demonstration still
uses the original fixture, frozen checks, and normal `--verify` CLI for AFTER.
The historical source is never recreated or rewritten at runtime.

## Install and run

Use a fresh Python 3.12 environment, then run from the repository root:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Dependencies are NumPy, Pillow, headless OpenCV, and Streamlit. Headless OpenCV
provides `cv2` without desktop GUI dependencies; do not install both OpenCV
distributions in the same environment. No secrets, external APIs, or GPU are
required. Usage statistics are disabled in `.streamlit/config.toml`.

The historical case is selected by default. Run BEFORE and AFTER, inspect the
trace, then download the JSON evidence report. Select a controlled scenario to
run its defect and a clean candidate on the same synthetic fixture.

## CLI and verification

```bash
# Isolated historical BEFORE: exit 1, decode/channel_order_mismatch
python -m demo.runner --mode before

# Isolated actual repair verification: exit 0 when all five stages pass
python -m demo.runner --mode after

# Both executions and their combined JSON evidence report
python -m demo.runner --mode both

# Original core commands (these overwrite the repository evidence/ arrays)
python -m paritylens --fixture fixtures/defect_rgb_bgr.png
python -m paritylens --fixture fixtures/defect_rgb_bgr.png --verify
```

The current core candidate is repaired, so both core commands now pass. Prefer
the isolated demo commands to preserve existing evidence. They execute fresh
pipelines in disposable directories; no cached evidence or runtime patching is
used. Core/demo single-run exit codes: 0 pass, 1 detected defect, 2 error.

## Controlled evaluation

| Scenario | Origin | Candidate behavior | Expected first boundary |
|---|---|---|---|
| `historical_rgb_bgr` | Historical source | Exact pre-repair candidate on additional synthetic images | `decode` |
| `scaling_mismatch` | Controlled evaluation | Keeps 0..255 float32 values instead of dividing by 255 | `scaling` |
| `normalization_mismatch` | Controlled evaluation | Fixed incorrect mean and std, both `[0.5, 0.5, 0.5]` | `normalization` |
| `clean_control` | Controlled evaluation | Independent Pillow reference and current RGB-correct OpenCV candidate | None |

The new defects are authored evaluation variants, not historical Bob repairs.
They live outside the frozen core. The adapter delegates acceptance decisions
to the unchanged comparator: exact integer equality, contract tolerances for
floats, recorded arrays compared as-is, and stop at the first failure. It adds
boundary-based labels for numerical scaling/normalization failures without
inferring which operation caused them or changing any acceptance decision.

```bash
# Run all 60 cases twice; write evaluation/results.json and results.md
python -m evaluation.runner

# Run one case and print its JSON report (expected defect exits 1)
python -m evaluation.runner --scenario scaling_mismatch --fixture gradients_1

# Regenerate the versioned synthetic set deterministically
python -m evaluation.fixtures

# Historical, evaluation, isolation, report, and Streamlit interaction tests
python -m unittest discover -v
```

The set has 15 RGB PNGs spanning gradients, blocks, checkers, intensity regions,
and seeded noise. Generation metadata, probe values, and hashes are stored in
`evaluation/fixtures/metadata.json`. Probes deliberately satisfy the frozen
contract's channel-observability precondition; the remaining pixels vary.

The artifact contains both full runs, per-stage measurements, array hashes,
source/fixture fingerprints, dependency versions, and measured metrics. Timing
metadata is outside the equality comparison. Matrix exit 0 means all expected
outcomes occurred and both runs matched; exit 1 means an unexpected outcome or
reproducibility failure; exit 2 means execution failed. Defective cases remain
parity FAIL even when the evaluation expectation is met.

The UI reads metrics from this artifact and warns when input fingerprints are
stale. Regenerate after changing evaluation code or fixtures. The matrix never
writes to the protected fixtures or existing evidence directories.

## Limits and deployment status

- This is a deterministic synthetic evaluation, not evidence of general
  production detection accuracy or production readiness.
- Only RGB/BGR, the controlled scaling defect, and the controlled normalization
  defect are covered. Classification metrics apply to these supported cases.
- Inputs are contract-admissible 224×224 RGB PNGs with an asymmetric probe.
  Resize is a numerical no-op; cross-library interpolation drift is untested.
- New labels describe the first numerical boundary, not an automatic root-cause
  diagnosis. Later stages are recorded but marked NOT_EVALUATED after failure.
- Repeatability is tested within the reported environment; cross-platform and
  cross-version bitwise reproducibility are not promised.
- A clean control is a comparison, not a new Bob repair or repair verification.
- Only allowlisted local scenarios and fixtures run. There are no code uploads,
  repository inputs, user shell commands, or remote agent calls.

The repository is prepared for a Streamlit entry point at `app.py`, with no
deployment performed. Review the local UI and artifact before publishing.
The frozen experiment, protected source files, and Bob session evidence remain
unchanged; changes to those require human approval.
