"""
Candidate (serving) preprocessing pipeline.

Independently written using OpenCV. The BGR channel-order defect has been
repaired: cv2.imread output is converted to RGB immediately after decode.

Each stage saves its output to evidence/candidate/<stage>.npy.
"""

from __future__ import annotations

import numpy as np
from pathlib import Path

EVIDENCE_DIR = Path("evidence/candidate")


def run(image_path: str | Path) -> dict[str, np.ndarray]:
    """Run all candidate pipeline stages and return a dict of stage arrays."""
    import cv2  # imported here so ImportError is catchable at CLI level

    image_path = Path(image_path)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    stages: dict[str, np.ndarray] = {}

    # ------------------------------------------------------------------
    # Stage: decode
    # cv2.imread returns BGR uint8 HWC; convert to RGB per contract.
    # ------------------------------------------------------------------
    decode_arr = cv2.imread(str(image_path))
    if decode_arr is None:
        raise FileNotFoundError(f"cv2.imread could not load: {image_path}")
    decode_arr = cv2.cvtColor(decode_arr, cv2.COLOR_BGR2RGB)
    # decode_arr is now (H, W, 3) uint8, channel order RGB
    np.save(EVIDENCE_DIR / "decode.npy", decode_arr)
    stages["decode"] = decode_arr

    # ------------------------------------------------------------------
    # Stage: geometry
    # No-op stub. Returns decode array unchanged.
    # ------------------------------------------------------------------
    geometry_arr = decode_arr
    np.save(EVIDENCE_DIR / "geometry.npy", geometry_arr)
    stages["geometry"] = geometry_arr

    # ------------------------------------------------------------------
    # Stage: scaling
    # cv2 INTER_LINEAR resize to (224, 224) then divide by 255.0 → float32.
    # Note: cv2.resize takes (width, height) not (height, width).
    # The fixture is already 224x224 so resize is a no-op numerically.
    # ------------------------------------------------------------------
    resized = cv2.resize(geometry_arr, (224, 224), interpolation=cv2.INTER_LINEAR)
    scaling_arr = resized.astype(np.float32) / 255.0
    np.save(EVIDENCE_DIR / "scaling.npy", scaling_arr)
    stages["scaling"] = scaling_arr

    # ------------------------------------------------------------------
    # Stage: normalization
    # Same constants as reference. Internal arithmetic in float64;
    # cast to float32 before save. Channel 0 is now Red (RGB order).
    # ------------------------------------------------------------------
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float64)
    std  = np.array([0.229, 0.224, 0.225], dtype=np.float64)
    norm_f64 = (scaling_arr.astype(np.float64) - mean) / std
    norm_arr = norm_f64.astype(np.float32)
    np.save(EVIDENCE_DIR / "normalization.npy", norm_arr)
    stages["normalization"] = norm_arr

    # ------------------------------------------------------------------
    # Stage: model_input
    # HWC → CHW via np.transpose. Shape (3,224,224), dtype float32.
    # ------------------------------------------------------------------
    model_input_arr = np.transpose(norm_arr, (2, 0, 1))
    np.save(EVIDENCE_DIR / "model_input.npy", model_input_arr)
    stages["model_input"] = model_input_arr

    return stages
