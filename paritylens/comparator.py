"""
ParityLens Comparator.

Reads the preprocessing contract, validates preconditions, then compares
reference and candidate stage outputs array-by-array.

Policy (human-approved):
  - Compare recorded arrays as-is.
  - Never reorder channels.
  - Never transpose arrays.
  - Never renormalize either side.
  - Never alter candidate values.
  - Use exact equality (np.array_equal) for integer stages.
  - Use tolerance (np.allclose, atol=1e-5, rtol=1e-5) for floating stages.
  - Stop at the first violating comparable stage.
  - Use the known-pixel probe ONLY AFTER failure to classify the defect type.
"""

from __future__ import annotations

import json
import sys
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    stage: str
    passed: bool
    defect_class: Optional[str] = None
    message: str = ""
    ref_path: Optional[str] = None
    cand_path: Optional[str] = None


@dataclass
class ComparisonReport:
    passed: bool
    stages: list[StageResult] = field(default_factory=list)
    first_failure: Optional[StageResult] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Integer stages — exact comparison
# ---------------------------------------------------------------------------
INTEGER_STAGES = {"decode", "geometry"}

# ---------------------------------------------------------------------------
# Stage order (contract-defined evaluation order)
# ---------------------------------------------------------------------------
STAGE_ORDER = ["decode", "geometry", "scaling", "normalization", "model_input"]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compare(
    contract_path: str | Path,
    metadata_path: str | Path,
    ref_dir: str | Path,
    cand_dir: str | Path,
) -> ComparisonReport:
    """
    Load evidence from ref_dir and cand_dir, compare per the contract.

    Returns a ComparisonReport.
    """
    contract_path = Path(contract_path)
    metadata_path = Path(metadata_path)
    ref_dir = Path(ref_dir)
    cand_dir = Path(cand_dir)

    # ------------------------------------------------------------------
    # Load contract
    # ------------------------------------------------------------------
    with open(contract_path) as f:
        contract = json.load(f)

    atol = float(contract["comparison"]["atol"])
    rtol = float(contract["comparison"]["rtol"])

    # ------------------------------------------------------------------
    # Load fixture metadata and validate probe precondition
    # ------------------------------------------------------------------
    with open(metadata_path) as f:
        metadata = json.load(f)

    probe_row, probe_col = metadata["probe_coordinate"]
    probe_r, probe_g, probe_b = metadata["probe_pixel_rgb"]

    assert probe_r != probe_g, "Fixture precondition violated: probe R==G"
    assert probe_g != probe_b, "Fixture precondition violated: probe G==B"
    assert probe_r != probe_b, "Fixture precondition violated: probe R==B"
    assert abs(probe_r - probe_b) > 50, (
        f"Fixture precondition violated: |R-B| <= 50 "
        f"(R={probe_r}, B={probe_b}, diff={abs(probe_r-probe_b)})"
    )

    # ------------------------------------------------------------------
    # Iterate stages in contract order
    # ------------------------------------------------------------------
    report = ComparisonReport(passed=True)

    for stage in STAGE_ORDER:
        ref_path = ref_dir / f"{stage}.npy"
        cand_path = cand_dir / f"{stage}.npy"

        # Both files must exist
        if not ref_path.exists():
            result = StageResult(
                stage=stage, passed=False,
                defect_class="missing_evidence",
                message=f"Reference evidence missing: {ref_path}",
            )
            report.stages.append(result)
            report.passed = False
            report.first_failure = result
            return report

        if not cand_path.exists():
            result = StageResult(
                stage=stage, passed=False,
                defect_class="missing_evidence",
                message=f"Candidate evidence missing: {cand_path}",
            )
            report.stages.append(result)
            report.passed = False
            report.first_failure = result
            return report

        ref_arr = np.load(ref_path)
        cand_arr = np.load(cand_path)

        # Shape check
        if ref_arr.shape != cand_arr.shape:
            result = StageResult(
                stage=stage, passed=False,
                defect_class="shape_mismatch",
                message=(
                    f"Shape mismatch: ref={ref_arr.shape} cand={cand_arr.shape}"
                ),
                ref_path=str(ref_path),
                cand_path=str(cand_path),
            )
            report.stages.append(result)
            report.passed = False
            report.first_failure = result
            return report

        # dtype check
        if ref_arr.dtype != cand_arr.dtype:
            result = StageResult(
                stage=stage, passed=False,
                defect_class="dtype_mismatch",
                message=(
                    f"dtype mismatch: ref={ref_arr.dtype} cand={cand_arr.dtype}"
                ),
                ref_path=str(ref_path),
                cand_path=str(cand_path),
            )
            report.stages.append(result)
            report.passed = False
            report.first_failure = result
            return report

        # Primary numerical comparison
        # Integer stages: exact equality
        # Floating stages: allclose with contract tolerances
        if stage in INTEGER_STAGES:
            arrays_match = np.array_equal(ref_arr, cand_arr)
        else:
            arrays_match = np.allclose(
                ref_arr.astype(np.float64),
                cand_arr.astype(np.float64),
                atol=atol,
                rtol=rtol,
            )

        if arrays_match:
            result = StageResult(
                stage=stage, passed=True,
                message="PASS",
                ref_path=str(ref_path),
                cand_path=str(cand_path),
            )
            report.stages.append(result)
            continue

        # ------------------------------------------------------------------
        # Numerical comparison failed — classify the defect using probe pixel
        # (only if stage has HWC layout with 3 channels at this pixel index)
        # ------------------------------------------------------------------
        defect_class = _classify_defect(
            ref_arr, cand_arr,
            probe_row, probe_col,
            probe_r, probe_b,
            stage,
        )

        result = StageResult(
            stage=stage, passed=False,
            defect_class=defect_class,
            message=f"FAIL — {defect_class}",
            ref_path=str(ref_path),
            cand_path=str(cand_path),
        )
        report.stages.append(result)
        report.passed = False
        report.first_failure = result
        # Stop at first failure
        return report

    # All stages passed
    return report


def _classify_defect(
    ref_arr: np.ndarray,
    cand_arr: np.ndarray,
    probe_row: int,
    probe_col: int,
    probe_r: int,
    probe_b: int,
    stage: str,
) -> str:
    """
    Use the known probe pixel to classify whether the failure is a
    channel-order mismatch (BGR vs RGB swap).

    Only callable AFTER a numerical mismatch has been established.
    Never modifies either array.
    """
    # Probe classification only applies to HWC stages with 3 spatial channels
    if ref_arr.ndim != 3 or ref_arr.shape[2] != 3:
        return "numerical_mismatch"
    if cand_arr.ndim != 3 or cand_arr.shape[2] != 3:
        return "numerical_mismatch"

    ref_ch0 = float(ref_arr[probe_row, probe_col, 0])
    ref_ch2 = float(ref_arr[probe_row, probe_col, 2])
    cand_ch0 = float(cand_arr[probe_row, probe_col, 0])
    cand_ch2 = float(cand_arr[probe_row, probe_col, 2])

    # For uint8 stages: exact match
    # For float stages: allow small tolerance (the swap will differ by
    # large amounts >> 1e-5 so the threshold is generous)
    tolerance = 1e-3

    ch0_swapped = abs(cand_ch0 - ref_ch2) < tolerance
    ch2_swapped = abs(cand_ch2 - ref_ch0) < tolerance

    if ch0_swapped and ch2_swapped:
        return "channel_order_mismatch"

    return "numerical_mismatch"
