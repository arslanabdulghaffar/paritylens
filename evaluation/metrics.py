import hashlib
import json


def semantic_digest(cases: list[dict]) -> str:
    payload = json.dumps(cases, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def summarize(cases: list[dict], repeated: list[dict]) -> dict:
    defects = [case for case in cases if case["expected_first_boundary"] is not None]
    controls = [case for case in cases if case["expected_first_boundary"] is None]
    localized = sum(c["observed_first_boundary"] == c["expected_first_boundary"] for c in defects)
    classified = sum(c["observed_classification"] == c["expected_classification"] for c in defects)
    return {
        "cases_evaluated": len(cases), "defect_cases": len(defects), "clean_cases": len(controls),
        "clean_controls_passed": sum(c["parity_check"] == "PASS" for c in controls),
        "defects_detected": sum(c["parity_check"] == "FAIL" for c in defects),
        "boundary_localization": {"correct": localized, "total": len(defects),
                                  "accuracy": localized / len(defects) if defects else None},
        "supported_classification": {"correct": classified, "total": len(defects),
                                     "accuracy": classified / len(defects) if defects else None},
        "clean_false_positives": sum(c["parity_check"] == "FAIL" for c in controls),
        "expectations_met": sum(c["expectation_met"] for c in cases),
        "reproducibility": {"runs": 2, "matched": cases == repeated,
                            "first_digest": semantic_digest(cases), "second_digest": semantic_digest(repeated)},
    }
