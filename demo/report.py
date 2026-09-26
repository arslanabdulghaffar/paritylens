from __future__ import annotations

import ast
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np


def source_locations(path: Path) -> dict[str, str]:
    assignments = {"decode_arr": "decode", "geometry_arr": "geometry",
                   "scaling_arr": "scaling", "norm_arr": "normalization",
                   "model_input_arr": "model_input"}
    locations = {}
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in assignments:
                    locations.setdefault(assignments[target.id], f"{path.as_posix()}:{node.lineno}")
    return locations


def stage_details(comparison, contract: dict, metadata: dict, candidate_path: Path) -> list[dict]:
    evaluated = {item.stage: item for item in comparison.stages}
    reference_locations = source_locations(Path("paritylens/pipelines/reference.py"))
    candidate_locations = source_locations(candidate_path)
    row, col = metadata["probe_coordinate"]
    stages = []
    for name, spec in contract["stages"].items():
        ref = np.load(f"evidence/reference/{name}.npy", allow_pickle=False)
        cand = np.load(f"evidence/candidate/{name}.npy", allow_pickle=False)
        result = evaluated.get(name)
        chw = spec.get("layout") == "CHW"
        probe_index = (slice(None), row, col) if chw else (row, col, slice(None))
        same_shape = ref.shape == cand.shape
        stages.append({
            "stage": name,
            "comparison": ("PASS" if result.passed else "FAIL") if result else "NOT_EVALUATED",
            "classification": result.defect_class if result else None,
            "reference_shape": list(ref.shape), "candidate_shape": list(cand.shape),
            "shape_matches": same_shape,
            "reference_dtype": str(ref.dtype), "candidate_dtype": str(cand.dtype),
            "dtype_matches": ref.dtype == cand.dtype,
            "reference_probe": ref[probe_index].tolist(),
            "candidate_probe": cand[probe_index].tolist(),
            "max_absolute_difference": float(np.max(np.abs(ref.astype(np.float64) - cand.astype(np.float64)))) if same_shape else None,
            "reference_source": reference_locations.get(name),
            "candidate_source": candidate_locations.get(name),
        })
    return stages


def build_report(before: dict, after: dict, provenance: dict) -> dict:
    if before["input_sha256"] != after["input_sha256"]:
        raise ValueError("Before and after inputs differ; rerun both comparisons.")
    return {
        "project": "ParityLens", "scenario": "RGB/BGR preprocessing handoff",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "contract_version": before["contract_version"],
        "comparison_policy": before["comparison_policy"],
        "before_commit": provenance["before_commit"],
        "repaired_commit": provenance["repaired_commit"],
        "historical_snapshot_sha256": provenance["snapshot_sha256"],
        "integrity_hash_policy": provenance["hash_policy"],
        "fixture": before["fixture"],
        "first_violating_boundary": before["first_violating_boundary"],
        "defect_classification": before["classification"],
        "before_result": before, "after_result": after,
        "verification_state": after["verification_state"],
        "repair_statement": "Repair produced during the recorded IBM Bob IDE workflow. Bob is not invoked by this application.",
        "stage_note": "The frozen comparator stops at its first failure. Later recorded stages are NOT_EVALUATED; their probe values and maximum differences are descriptive measurements only.",
    }


def report_json(before: dict, after: dict, provenance: dict) -> str:
    return json.dumps(build_report(before, after, provenance), indent=2, allow_nan=False)
