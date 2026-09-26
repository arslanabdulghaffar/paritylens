# Final local validation

Final-submission preparation on Windows, 2026-09-27. Starting commit: `79f37de`; branch: `feature/final-submission-prep`. The recorded hardening results in ENVIRONMENT.json and PREFLIGHT.json remain historical evidence. No evaluation or benchmark measurement artifact was rewritten for submission preparation.

## Environment and execution

Fresh temporary venv created with system site packages disabled. Installed only `requirements.txt` and its transitive dependencies, using the venv interpreter for execution. Python 3.12.10; NumPy 2.5.3; Pillow 12.3.0; opencv-python-headless 5.0.0.93 (cv2 5.0.0); Streamlit 1.64.0. `pip check` reports no broken requirements.

Run `python scripts/final_review.py --json-output dist/final_review.json` for the current executable record. This calls preflight once; tests, matrix and startup are not rerun as redundant top-level steps. Tests contain their own independent regression checks by design.

| Check | Local result |
|---|---|
| Unit/integration suite | 23 tests pass: all 20 existing tests plus three release-bundle tests |
| Historical BEFORE | Shape/dtype PASS; decode FAIL; channel_order_mismatch; four downstream stages Not evaluated |
| Historical AFTER | Normal candidate --verify execution; all five stages PASS |
| Controlled matrix | 60 cases per run, twice; exact match to saved semantic results and array hashes |
| Detection/localization/classification | 45/45 for each supported metric |
| Clean controls / false positives | 15/15 PASS; 0/15 false positives |
| Final shape/dtype-only baseline | 0/45 defective cases detected; measured from actual arrays |
| Protected integrity | Strict and portable checks pass; 32 checks each |
| UI switching | Three additional AppTest cycles through controlled scenarios, controls, fixtures and historical BEFORE/AFTER; no exceptions or stale fixture timeline |
| Headless Streamlit | Local health and page HTTP 200; executed scenario behavior covered separately by AppTest |
| Claims | Generated results/docs agree; benchmark median/p95 recomputed from saved samples; README metric phrases agree |
| Bundle | Temporary ZIP members, per-file hashes, embedded manifest and required original evidence checked |
| CI | YAML parsed locally; commands/configuration reviewed; remote run pending |

Release-tool tests exercise exclusions (including secrets/cache/dist/scratch), inclusion of evidence, manifest membership/hashes, rejection of an embedded credential pattern and rejection of an outside path. They do not weaken core tests or alter protected evidence.

## Scope limits and human work

No browser is available to this agent. AppTest checks widget behavior and rendered content, not real viewport layout, tab order, screen-reader behavior or contrast. Human desktop/mobile smoke tests remain pending. No Linux run, external CI execution, deployed app or published screenshot/video is claimed.

The saved benchmark remains the earlier local measurement; this run verifies its inputs and arithmetic without claiming a new timing experiment. Original protected files, fixtures, Bob evidence and the historical candidate snapshot remain byte-for-byte unchanged from task start. See PUBLIC_RELEASE_AUDIT.md for historical bytecode, author metadata, screenshot and license review items.

After committing, rebuild `dist/paritylens-review.zip`; its external/embedded manifest records the final commit and whether the checkout was dirty. The ZIP and latest machine-readable final-review output are local ignored artifacts, not committed evidence or public uploads.
