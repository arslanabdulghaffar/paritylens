import json

from evaluation.metrics import summarize

DISCLAIMER = ("Deterministic synthetic evaluation on contract-admissible 224x224 RGB PNGs. "
              "Results do not establish accuracy on arbitrary production pipelines. "
              "Scaling and normalization labels identify the first numerical boundary, not an inferred root cause.")


def case_report(case: dict, inputs: dict, provenance: dict) -> dict:
    report = {
        "project": "ParityLens", "scenario_id": case["scenario"]["id"],
        "scenario_origin": case["scenario"]["origin"], "scenario": case["scenario"],
        "contract_version": inputs["contract_version"], "contract_sha256": inputs["contract_sha256"],
        "hash_policy": inputs["hash_policy"], "input_fingerprint": inputs,
        "result": case, "evaluation_disclaimer": DISCLAIMER,
        "execution_kind": "Fresh pipeline execution followed by frozen comparison; not a repair verification.",
    }
    if case["scenario"]["origin"] == "historical":
        report["historical_provenance"] = {
            "before_commit": provenance["before_commit"], "repaired_commit": provenance["repaired_commit"],
            "snapshot_sha256": provenance["snapshot_sha256"],
            "statement": "Historical code executed on new evaluation fixtures; this is not the original recorded experiment or a new Bob repair.",
        }
    return report


def markdown_report(suite: dict) -> str:
    metrics = suite["metrics"]
    lines = ["# ParityLens deterministic synthetic evaluation", "", DISCLAIMER, "",
             f"Fixture set: {suite['fixture_set']} ({suite['fixture_count']} images).",
             f"Cases: {metrics['cases_evaluated']} per run; two independent executions.",
             f"Detected defects: {metrics['defects_detected']}/{metrics['defect_cases']}.",
             f"Boundary localization: {metrics['boundary_localization']['correct']}/{metrics['boundary_localization']['total']}.",
             f"Supported classification: {metrics['supported_classification']['correct']}/{metrics['supported_classification']['total']}.",
             f"Clean controls passed: {metrics['clean_controls_passed']}/{metrics['clean_cases']}.",
             f"Clean false positives: {metrics['clean_false_positives']}.",
             f"Reproducible: {metrics['reproducibility']['matched']}.", "",
             "| Scenario | Fixture | Expected boundary | Observed boundary | Class | Parity |",
             "|---|---|---|---|---|---|"]
    for case in suite["cases"]:
        lines.append(f"| {case['scenario']['id']} | {case['fixture'].split('/')[-1]} | "
                     f"{case['expected_first_boundary'] or 'none'} | {case['observed_first_boundary'] or 'none'} | "
                     f"{case['observed_classification'] or 'none'} | {case['parity_check']} |")
    return "\n".join(lines) + "\n"


def validate_suite(suite: dict) -> None:
    if suite.get("schema_version") != "1.0" or not suite.get("cases"):
        raise ValueError("Unsupported or empty evaluation artifact")
    cases = suite["cases"]
    if suite["metrics"]["cases_evaluated"] != len(cases):
        raise ValueError("Evaluation case count does not match metrics")
    if suite["metrics"] != summarize(cases, suite["repeated_cases"]):
        raise ValueError("Evaluation metrics disagree with recorded case results")
    if len(cases) != suite["fixture_count"] * len(suite["scenarios"]):
        raise ValueError("Incomplete evaluation matrix")
    seen = set()
    for case in cases:
        key = (case["scenario"]["id"], case["fixture"])
        if key in seen:
            raise ValueError("Duplicate evaluation case")
        seen.add(key)
        for field in ("parity_check", "shape_check", "dtype_check"):
            if case[field] not in {"PASS", "FAIL"}:
                raise ValueError("Invalid evaluation status")
        if len(case["stages"]) != 5:
            raise ValueError("Incomplete stage evidence")
    json.dumps(suite, allow_nan=False)
