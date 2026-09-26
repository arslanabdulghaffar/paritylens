# Technical validation

Generated from evaluation/results.json and evaluation/benchmark_results.json.
Evaluation measured: 2026-09-26T17:53:15.414152+00:00. Benchmark measured: 2026-09-26T17:53:22.274577+00:00.

## Design

The 15-image synthetic set is deterministic and contract-constrained: 224x224 RGB PNGs, a documented asymmetric probe, and no numerical resize. Five pattern families have three variants each. Four scenarios run twice in isolated workspaces. The historical RGB/BGR candidate is the genuine Git snapshot executed on additional evaluation images; the original Bob demo remains a separate original-fixture experiment. Scaling (missing division by 255) and normalization (fixed incorrect mean/std) are controlled authored variants. Clean controls run the independent current candidate. Only the original RGB/BGR repair is attributed to the recorded Bob workflow.

## Measured results

- Fixture count: 15; cases per run: 60.
- Supported defects detected: 45/45.
- First-boundary localization: 45/45.
- Supported classification: 45/45.
- Clean controls passed: 15/15; false positives: 0.
- Two-run semantic reproducibility (including array hashes): True.
- Final shape/dtype baseline detects 0/45 defective cases; ParityLens detects 45/45.

Evaluation environment: `{"python": "3.12.10", "platform": "Windows", "numpy": "2.5.3", "pillow": "12.3.0", "streamlit": "1.64.0", "opencv": "5.0.0"}`.

## Local runtime

Local development-machine measurements, not universal performance guarantees. One gradients_1 fixture per scenario; 224x224 RGB. Includes NPY disk I/O. Comparison includes adapter validation and first-failure stopping. Complete execution includes fixture validation, evidence cleanup, both pipelines, comparison, and report measurements/hashes. Excludes process startup, imports, workspace setup, Streamlit rendering and core --verify invocation. p95 uses NumPy's linear percentile; samples are not independent deployment estimates.

20 measured repetitions after 3 warmups for each scenario.

| Scenario | Reference median/p95 ms | Candidate median/p95 ms | Comparison median/p95 ms | Complete median/p95 ms |
|---|---:|---:|---:|---:|
| historical_rgb_bgr | 7.792 / 8.720 | 7.193 / 8.711 | 35.558 / 51.911 | 67.578 / 82.357 |
| scaling_mismatch | 7.709 / 8.290 | 7.167 / 7.496 | 37.544 / 46.628 | 68.065 / 75.432 |
| normalization_mismatch | 7.544 / 8.151 | 7.065 / 7.372 | 40.088 / 46.600 | 69.312 / 76.243 |
| clean_control | 7.530 / 12.473 | 7.052 / 7.465 | 40.429 / 50.869 | 70.634 / 82.041 |

Benchmark environment: `{"python": "3.12.10", "platform": "Windows", "machine": "AMD64", "processor": "Intel64 Family 6 Model 183 Stepping 1, GenuineIntel", "numpy": "2.5.3", "opencv": "5.0.0"}`.

## Adversarial coverage and limits

- This is not generalization evidence for arbitrary CV stacks or a comparison with all MLOps systems.
- The baseline checks exactly final tensor shape and dtype. Its results come from recorded model-input arrays, not scenario labels.
- Scaling/normalization classifications name the first numerical boundary, not the underlying faulty operation.
- The frozen channel-swap classification is a probe heuristic: a red/blue-swapped probe with a changed green value still receives that label. An adversarial test preserves and documents this limitation.
- Fully black/gray probe pixels violate the frozen precondition. Dark/bright tests retain an admissible asymmetric probe; these are not unrestricted black-image support.
- Integer comparison is exact. Float tolerance-neighbor tests use the contract values; no policy was relaxed.
- Missing evidence fails visibly; the adapter additionally rejects unknown stages and non-finite/object arrays. Downstream stages after a first failure remain NOT_EVALUATED.
- Repeatability was measured within each environment. Cross-platform/native-library changes may require investigation; the suite does not silently accept a changed artifact.

## Reproduce

```bash
python -m unittest discover -v
python -m evaluation.runner
python -m evaluation.benchmark
python -m integrity.check_integrity
python scripts/preflight.py
python scripts/validation_docs.py
```

Default integrity checking is byte-exact for this baseline checkout. Use --portable on other checkouts to allow only CRLF/LF text differences; the historical snapshot remains byte-exact.
