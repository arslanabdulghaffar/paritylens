import numpy as np


def naive_structural_check(reference: np.ndarray, candidate: np.ndarray) -> dict:
    shape_matches = reference.shape == candidate.shape
    dtype_matches = reference.dtype == candidate.dtype
    return {"name": "Final shape/dtype baseline", "stage": "model_input",
            "reference_shape": list(reference.shape), "candidate_shape": list(candidate.shape),
            "reference_dtype": str(reference.dtype), "candidate_dtype": str(candidate.dtype),
            "shape_matches": shape_matches, "dtype_matches": dtype_matches,
            "passed": shape_matches and dtype_matches}


def summarize_baseline(cases: list[dict]) -> dict:
    defects = [case for case in cases if case["expected_first_boundary"] is not None]
    controls = [case for case in cases if case["expected_first_boundary"] is None]
    return {"name": "Final shape/dtype baseline", "defective_cases": len(defects),
            "naive_defects_detected": sum(not c["naive_structural_check"]["passed"] for c in defects),
            "paritylens_defects_detected": sum(c["parity_check"] == "FAIL" for c in defects),
            "naive_clean_false_positives": sum(not c["naive_structural_check"]["passed"] for c in controls),
            "scope": "Only final tensor shape and dtype; not a comparison with general ML monitoring systems."}
