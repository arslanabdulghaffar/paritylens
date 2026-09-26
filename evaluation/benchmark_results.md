# Local runtime benchmark

Local development-machine measurements, not universal performance guarantees. One gradients_1 fixture per scenario; 224x224 RGB. Includes NPY disk I/O. Comparison includes adapter validation and first-failure stopping. Complete execution includes fixture validation, evidence cleanup, both pipelines, comparison, and report measurements/hashes. Excludes process startup, imports, workspace setup, Streamlit rendering and core --verify invocation. p95 uses NumPy's linear percentile; samples are not independent deployment estimates.

20 measured runs and 3 warmups per scenario.

| Scenario | Component | Median ms | p95 ms |
|---|---|---:|---:|
| historical_rgb_bgr | reference_ms | 7.792 | 8.720 |
| historical_rgb_bgr | candidate_ms | 7.193 | 8.711 |
| historical_rgb_bgr | comparison_ms | 35.558 | 51.911 |
| historical_rgb_bgr | complete_scenario_ms | 67.578 | 82.357 |
| scaling_mismatch | reference_ms | 7.709 | 8.290 |
| scaling_mismatch | candidate_ms | 7.167 | 7.496 |
| scaling_mismatch | comparison_ms | 37.544 | 46.628 |
| scaling_mismatch | complete_scenario_ms | 68.065 | 75.432 |
| normalization_mismatch | reference_ms | 7.544 | 8.151 |
| normalization_mismatch | candidate_ms | 7.065 | 7.372 |
| normalization_mismatch | comparison_ms | 40.088 | 46.600 |
| normalization_mismatch | complete_scenario_ms | 69.312 | 76.243 |
| clean_control | reference_ms | 7.530 | 12.473 |
| clean_control | candidate_ms | 7.052 | 7.465 |
| clean_control | comparison_ms | 40.429 | 50.869 |
| clean_control | complete_scenario_ms | 70.634 | 82.041 |

Environment: `{"python": "3.12.10", "platform": "Windows", "machine": "AMD64", "processor": "Intel64 Family 6 Model 183 Stepping 1, GenuineIntel", "numpy": "2.5.3", "opencv": "5.0.0"}`.
