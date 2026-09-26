import hashlib
import json
from pathlib import Path
import shutil
import sys

from demo import candidate_before_bob
from demo.report import stage_details
from paritylens.pipelines import candidate, reference
from evaluation import adapter, candidates
from evaluation.fixtures import load_manifest
from evaluation.scenarios import get_scenario


def execute_case(scenario_id: str, fixture: dict, contract: dict) -> dict:
    scenario = get_scenario(scenario_id)
    image_path = Path("evaluation/fixtures") / fixture["filename"]
    if hashlib.sha256(image_path.read_bytes()).hexdigest() != fixture["sha256"]:
        raise ValueError("Evaluation fixture hash mismatch")
    adapter.validate_fixture(image_path, fixture, contract)
    evidence = Path("evidence").resolve()
    if evidence.parent != Path.cwd().resolve():
        raise ValueError("Evidence path must stay inside the disposable workspace")
    if evidence.exists():
        shutil.rmtree(evidence)
    reference.run(image_path)
    if scenario_id == "historical_rgb_bgr":
        candidate_before_bob.run(image_path)
    elif scenario_id == "clean_control":
        candidate.run(image_path)
    else:
        candidates.run(image_path, scenario_id, contract)
    metadata_path = Path("evaluation_metadata.json")
    metadata_path.write_text(json.dumps(fixture), encoding="utf-8")
    comparison, core_class = adapter.compare(Path("contract/preprocessing_contract.json"), metadata_path)
    stages = stage_details(comparison, contract, fixture, Path(scenario.candidate_implementation))
    failure = comparison.first_failure
    failed_stage = next((stage for stage in stages if stage["comparison"] == "FAIL"), None)
    boundary = failure.stage if failure else None
    classification = failure.defect_class if failure else None
    return {
        "scenario": scenario.metadata(), "fixture": image_path.as_posix(),
        "fixture_sha256": fixture["sha256"], "probe_coordinate": fixture["probe_coordinate"],
        "expected_first_boundary": scenario.expected_first_boundary, "observed_first_boundary": boundary,
        "expected_classification": scenario.expected_classification, "observed_classification": classification,
        "core_classification": core_class, "parity_check": "PASS" if comparison.passed else "FAIL",
        "shape_check": "PASS" if all(s["shape_matches"] for s in stages) else "FAIL",
        "dtype_check": "PASS" if all(s["dtype_matches"] for s in stages) else "FAIL",
        "max_absolute_difference_at_failure": failed_stage["max_absolute_difference"] if failed_stage else None,
        "expectation_met": (comparison.passed == (scenario.expected_first_boundary is None)
                            and boundary == scenario.expected_first_boundary
                            and classification == scenario.expected_classification),
        "stages": stages,
        "recorded_array_sha256": {path.relative_to(evidence).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in sorted(evidence.rglob("*.npy"))},
    }


def main() -> int:
    request = json.loads(Path("request.json").read_text())
    contract = json.loads(Path("contract/preprocessing_contract.json").read_text())
    fixtures = {item["id"]: item for item in load_manifest()["fixtures"]}
    cases = []
    for scenario_id in request["scenarios"]:
        get_scenario(scenario_id)
        for fixture_id in request["fixtures"]:
            if fixture_id not in fixtures:
                raise ValueError("Unsupported evaluation fixture")
            cases.append(execute_case(scenario_id, fixtures[fixture_id], contract))
    Path("cases.json").write_text(json.dumps(cases, indent=2, allow_nan=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    if not Path(".evaluation-workspace").is_file():
        print("ERROR: evaluation worker requires a disposable workspace", file=sys.stderr)
        raise SystemExit(2)
    try:
        raise SystemExit(main())
    except (ValueError, OSError, AssertionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
