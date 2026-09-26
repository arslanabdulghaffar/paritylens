import json

from evaluation.metrics import summarize
from evaluation.scenarios import SCENARIOS
from paritylens.comparator import STAGE_ORDER

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
             f"Final shape/dtype baseline detects {metrics['final_shape_dtype_baseline']['naive_defects_detected']}/"
             f"{metrics['defect_cases']} defects; ParityLens detects {metrics['defects_detected']}/{metrics['defect_cases']}.",
             "This baseline represents only final tensor shape and dtype checks.", "",
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
    expected_keys = {(scenario, fixture) for scenario in SCENARIOS for fixture in {c["fixture"] for c in cases}}
    for run in (cases, suite["repeated_cases"]):
        seen = set()
        for case in run:
            key = (case["scenario"]["id"], case["fixture"])
            if key in seen or key not in expected_keys:
                raise ValueError("Duplicate or unsupported evaluation case")
            seen.add(key)
            scenario = SCENARIOS[key[0]]
            if (case["scenario"] != scenario.metadata()
                    or case["expected_first_boundary"] != scenario.expected_first_boundary
                    or case["expected_classification"] != scenario.expected_classification):
                raise ValueError("Evaluation expectations differ from scenario definitions")
            stages = case["stages"]
            if [s["stage"] for s in stages] != STAGE_ORDER:
                raise ValueError("Incomplete or reordered stage evidence")
            failed = next((s for s in stages if s["comparison"] == "FAIL"), None)
            boundary = failed["stage"] if failed else None
            classification = failed["classification"] if failed else None
            expected_states = ["PASS"] * len(stages)
            if failed:
                index = STAGE_ORDER.index(boundary)
                expected_states[index:] = ["FAIL"] + ["NOT_EVALUATED"] * (len(stages) - index - 1)
            if [s["comparison"] for s in stages] != expected_states:
                raise ValueError("Invalid first-failure stage sequence")
            if (case["observed_first_boundary"] != boundary or case["observed_classification"] != classification
                    or case["parity_check"] != ("FAIL" if failed else "PASS")):
                raise ValueError("Case summary disagrees with stage evidence")
            for field, flag in (("shape_check", "shape_matches"), ("dtype_check", "dtype_matches")):
                if case[field] != ("PASS" if all(s[flag] for s in stages) else "FAIL"):
                    raise ValueError("Structural summary disagrees with stages")
            final = stages[-1]
            naive = case["naive_structural_check"]
            if (naive["passed"] != (final["shape_matches"] and final["dtype_matches"])
                    or naive["reference_shape"] != final["reference_shape"]
                    or naive["candidate_shape"] != final["candidate_shape"]
                    or naive["reference_dtype"] != final["reference_dtype"]
                    or naive["candidate_dtype"] != final["candidate_dtype"]):
                raise ValueError("Final baseline disagrees with model input evidence")
            if case["expectation_met"] != (boundary == scenario.expected_first_boundary and classification == scenario.expected_classification):
                raise ValueError("Incorrect evaluation expectation status")
        if seen != expected_keys:
            raise ValueError("Incomplete repeated matrix")
    json.dumps(suite, allow_nan=False)
