"""
Reference preprocessing pipeline.

Ground-truth path. Every stage output is the definition of correct.
Stages: decode, geometry, scaling, normalization, model_input.

Each stage saves its output to evidence/reference/<stage>.npy.
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from PIL import Image

EVIDENCE_DIR = Path("evidence/reference")


def run(image_path: str | Path) -> dict[str, np.ndarray]:
    """Run all reference pipeline stages and return a dict of stage arrays."""
    image_path = Path(image_path)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    stages: dict[str, np.ndarray] = {}

    # ------------------------------------------------------------------
    # Stage: decode
    # PIL.Image.open → numpy uint8 HWC, assert mode == "RGB"
    # ------------------------------------------------------------------
    pil_img = Image.open(image_path)
    assert pil_img.mode == "RGB", (
        f"Reference decode: expected RGB image, got mode={pil_img.mode!r}"
    )
    decode_arr = np.array(pil_img, dtype=np.uint8)
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
    # PIL BILINEAR resize to (224, 224) then divide by 255.0 → float32
    # The fixture is already 224x224 so resize is a no-op numerically.
    # ------------------------------------------------------------------
    pil_scaled = pil_img.resize((224, 224), Image.BILINEAR)
    scaling_arr = np.array(pil_scaled, dtype=np.float32) / 255.0
    np.save(EVIDENCE_DIR / "scaling.npy", scaling_arr)
    stages["scaling"] = scaling_arr

    # ------------------------------------------------------------------
    # Stage: normalization
    # Subtract per-channel mean, divide by std.
    # Internal arithmetic in float64; cast to float32 before save.
    # mean/std applied in RGB channel order (channel 0=R, 1=G, 2=B).
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
