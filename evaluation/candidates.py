from pathlib import Path

import cv2
import numpy as np


def run(image_path: Path, scenario_id: str, contract: dict) -> dict:
    if scenario_id not in {"scaling_mismatch", "normalization_mismatch"}:
        raise ValueError("Unsupported controlled candidate")
    stages = {}
    decode_arr = cv2.imread(str(image_path))
    if decode_arr is None:
        raise ValueError("Could not decode evaluation fixture")
    decode_arr = cv2.cvtColor(decode_arr, cv2.COLOR_BGR2RGB)
    stages["decode"] = decode_arr
    geometry_arr = decode_arr
    stages["geometry"] = geometry_arr
    scaling_spec = contract["stages"]["scaling"]
    resized = cv2.resize(geometry_arr, tuple(scaling_spec["target_size"]), interpolation=cv2.INTER_LINEAR)
    scaling_arr = resized.astype(np.float32)
    if scenario_id != "scaling_mismatch":
        scaling_arr = scaling_arr / scaling_spec["divide_by"]
    stages["scaling"] = scaling_arr
    norm_spec = contract["stages"]["normalization"]
    mean = np.array(norm_spec["mean"], dtype=np.float64)
    std = np.array(norm_spec["std"], dtype=np.float64)
    if scenario_id == "normalization_mismatch":
        mean = np.array([0.5, 0.5, 0.5], dtype=np.float64)
        std = np.array([0.5, 0.5, 0.5], dtype=np.float64)
    norm_arr = ((scaling_arr.astype(np.float64) - mean) / std).astype(np.float32)
    stages["normalization"] = norm_arr
    model_input_arr = np.transpose(norm_arr, (2, 0, 1))
    stages["model_input"] = model_input_arr
    output = Path("evidence/candidate")
    output.mkdir(parents=True, exist_ok=True)
    for stage, array in stages.items():
        np.save(output / f"{stage}.npy", array)
    return stages
