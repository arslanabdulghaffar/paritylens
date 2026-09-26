# Submission facts

Project: ParityLens (NeuralFoundry).

Problem: matching tensor shape and dtype can conceal a semantically different model input.
Solution: compare recorded preprocessing boundaries, locate the first violation, show numerical/source evidence, and verify a real repair with unchanged checks.
Target user: computer-vision engineers comparing trusted and serving preprocessing paths.
Technology: Python, NumPy, Pillow, headless OpenCV, Streamlit; CPU-only and local.

## IBM Bob and provenance

The 15-image synthetic set is deterministic and contract-constrained: 224x224 RGB PNGs, a documented asymmetric probe, and no numerical resize. Five pattern families have three variants each. Four scenarios run twice in isolated workspaces. The historical RGB/BGR candidate is the genuine Git snapshot executed on additional evaluation images; the original Bob demo remains a separate original-fixture experiment. Scaling (missing division by 255) and normalization (fixed incorrect mean/std) are controlled authored variants. Clean controls run the independent current candidate. Only the original RGB/BGR repair is attributed to the recorded Bob workflow.

Bob was used for the recorded plan/contract, deterministic comparison implementation, evidence-based diagnosis, and real RGB conversion repair. The web app itself does not invoke Bob.
BEFORE commit: d0ea1fd4f967aa00b1e2113025b19d5783fc7242.
Repair commit: 334a4013230076fbca4d2e3eb86281d1cf29b0c6.
Session evidence: bob_sessions/neuralfoundry_task01_session_summary.png through task04.

## Measured results

- Fixture count: 15; cases per run: 60.
- Supported defects detected: 45/45.
- First-boundary localization: 45/45.
- Supported classification: 45/45.
- Clean controls passed: 15/15; false positives: 0.
- Two-run semantic reproducibility (including array hashes): True.
- Final shape/dtype baseline detects 0/45 defective cases; ParityLens detects 45/45.

Local runtime measurements and environment are in VALIDATION.md and evaluation/benchmark_results.json.

## Run commands

```bash
python -m pip install -r requirements.txt
streamlit run app.py
python -m demo.runner --mode both
python -m evaluation.runner
python scripts/preflight.py
```

## Data, security, and limits

Project-generated synthetic images only; no external photographs, private/client datasets, or social-media data. Bob screenshots are supplied workflow evidence and require release review.
The app runs allowlisted local code and fixtures with isolated temporary evidence. No arbitrary uploads, user shell commands, remote Bob API, or external LLM calls. See SECURITY.md for remaining resource and dependency risks.
- This is not generalization evidence for arbitrary CV stacks or a comparison with all MLOps systems.
- The baseline checks exactly final tensor shape and dtype. Its results come from recorded model-input arrays, not scenario labels.
- Scaling/normalization classifications name the first numerical boundary, not the underlying faulty operation.
- The frozen channel-swap classification is a probe heuristic: a red/blue-swapped probe with a changed green value still receives that label. An adversarial test preserves and documents this limitation.
- Fully black/gray probe pixels violate the frozen precondition. Dark/bright tests retain an admissible asymmetric probe; these are not unrestricted black-image support.

No production-readiness, universal detection, novelty, prize, or deployment claim is made. Nothing is deployed by these validation commands.
