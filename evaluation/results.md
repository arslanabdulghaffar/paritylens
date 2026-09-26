# ParityLens deterministic synthetic evaluation

Deterministic synthetic evaluation on contract-admissible 224x224 RGB PNGs. Results do not establish accuracy on arbitrary production pipelines. Scaling and normalization labels identify the first numerical boundary, not an inferred root cause.

Fixture set: synthetic-v1 (15 images).
Cases: 60 per run; two independent executions.
Detected defects: 45/45.
Boundary localization: 45/45.
Supported classification: 45/45.
Clean controls passed: 15/15.
Clean false positives: 0.
Reproducible: True.

| Scenario | Fixture | Expected boundary | Observed boundary | Class | Parity |
|---|---|---|---|---|---|
| historical_rgb_bgr | gradients_1.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | gradients_2.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | gradients_3.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | blocks_1.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | blocks_2.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | blocks_3.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | checker_1.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | checker_2.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | checker_3.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | intensity_1.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | intensity_2.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | intensity_3.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | noise_1.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | noise_2.png | decode | decode | channel_order_mismatch | FAIL |
| historical_rgb_bgr | noise_3.png | decode | decode | channel_order_mismatch | FAIL |
| scaling_mismatch | gradients_1.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | gradients_2.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | gradients_3.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | blocks_1.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | blocks_2.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | blocks_3.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | checker_1.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | checker_2.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | checker_3.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | intensity_1.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | intensity_2.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | intensity_3.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | noise_1.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | noise_2.png | scaling | scaling | scaling_mismatch | FAIL |
| scaling_mismatch | noise_3.png | scaling | scaling | scaling_mismatch | FAIL |
| normalization_mismatch | gradients_1.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | gradients_2.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | gradients_3.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | blocks_1.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | blocks_2.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | blocks_3.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | checker_1.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | checker_2.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | checker_3.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | intensity_1.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | intensity_2.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | intensity_3.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | noise_1.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | noise_2.png | normalization | normalization | normalization_mismatch | FAIL |
| normalization_mismatch | noise_3.png | normalization | normalization | normalization_mismatch | FAIL |
| clean_control | gradients_1.png | none | none | none | PASS |
| clean_control | gradients_2.png | none | none | none | PASS |
| clean_control | gradients_3.png | none | none | none | PASS |
| clean_control | blocks_1.png | none | none | none | PASS |
| clean_control | blocks_2.png | none | none | none | PASS |
| clean_control | blocks_3.png | none | none | none | PASS |
| clean_control | checker_1.png | none | none | none | PASS |
| clean_control | checker_2.png | none | none | none | PASS |
| clean_control | checker_3.png | none | none | none | PASS |
| clean_control | intensity_1.png | none | none | none | PASS |
| clean_control | intensity_2.png | none | none | none | PASS |
| clean_control | intensity_3.png | none | none | none | PASS |
| clean_control | noise_1.png | none | none | none | PASS |
| clean_control | noise_2.png | none | none | none | PASS |
| clean_control | noise_3.png | none | none | none | PASS |
