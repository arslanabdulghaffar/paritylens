import json
from pathlib import Path

from evaluation.fixtures import load_manifest
from evaluation.scenarios import SCENARIOS
from evaluation.worker import execute_case


def main() -> None:
    request = json.loads(Path("benchmark_request.json").read_text())
    contract = json.loads(Path("contract/preprocessing_contract.json").read_text())
    fixture = load_manifest()["fixtures"][0]
    records = []
    for scenario_id in SCENARIOS:
        samples = []
        for iteration in range(request["warmup"] + request["runs"]):
            timings = {}
            result = execute_case(scenario_id, fixture, contract, timings)
            if not result["expectation_met"]:
                raise ValueError("Benchmark scenario produced an unexpected result")
            if iteration >= request["warmup"]:
                samples.append(timings)
        records.append({"scenario": scenario_id, "fixture": fixture["id"], "samples": samples})
    Path("benchmark_samples.json").write_text(json.dumps(records), encoding="utf-8")


if __name__ == "__main__":
    main()
