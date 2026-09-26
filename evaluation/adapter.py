from dataclasses import replace
import json
from pathlib import Path

import numpy as np
from PIL import Image

from paritylens import comparator


def validate_fixture(image_path: Path, metadata: dict, contract: dict) -> None:
    if list(contract["stages"]) != comparator.STAGE_ORDER:
        raise ValueError("Unsupported or ambiguous contract stage map")
    coordinate = contract["fixture"]["probe_pixel"]["coordinate"]
    if metadata["probe_coordinate"] != coordinate:
        raise ValueError("Fixture probe coordinate violates contract")
    row, col = coordinate
    with Image.open(image_path) as image:
        if image.mode != "RGB" or image.format != "PNG" or list(image.size) != contract["fixture"]["size"]:
            raise ValueError("Fixture format, mode, or dimensions violate contract")
        probe = list(image.getpixel((col, row)))
    if probe != metadata["probe_pixel_rgb"] or len(set(probe)) != 3 or abs(probe[0] - probe[2]) <= 50:
        raise ValueError("Fixture probe violates the frozen observable-channel precondition")


def compare(contract_path: Path, metadata_path: Path):
    """Keep frozen acceptance decisions; annotate supported numerical boundaries."""
    contract = json.loads(contract_path.read_text())
    if list(contract["stages"]) != comparator.STAGE_ORDER:
        raise ValueError("Unsupported or ambiguous contract stage map")
    for side in ("reference", "candidate"):
        directory = Path("evidence") / side
        if {p.stem for p in directory.glob("*.npy")} != set(comparator.STAGE_ORDER):
            raise ValueError("Missing or ambiguous recorded stages")
        for path in directory.glob("*.npy"):
            if not np.isfinite(np.load(path, allow_pickle=False)).all():
                raise ValueError("Non-finite recorded values are unsupported")
    report = comparator.compare(contract_path, metadata_path, "evidence/reference", "evidence/candidate")
    failure = report.first_failure
    core_class = failure.defect_class if failure else None
    if failure and core_class == "numerical_mismatch" and failure.stage in {"scaling", "normalization"}:
        classified = replace(failure, defect_class=f"{failure.stage}_mismatch",
                             message=f"Numerical mismatch first observed at {failure.stage}; root cause not inferred.")
        report.stages[-1] = classified
        report.first_failure = classified
    return report, core_class
