import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from demo.runner import ROOT, check_integrity, file_hash, provenance
from evaluation.fixtures import FIXTURE_DIR, load_manifest
from evaluation.metrics import summarize
from evaluation.report import DISCLAIMER, case_report, markdown_report, validate_suite
from evaluation.scenarios import SCENARIOS, get_scenario

EXECUTION_FILES = ("__init__.py", "adapter.py", "candidates.py", "fixtures.py", "metrics.py",
                   "report.py", "runner.py", "scenarios.py", "worker.py")


def input_fingerprint() -> dict:
    contract_path = ROOT / "contract/preprocessing_contract.json"
    contract = json.loads(contract_path.read_text())
    names = list(provenance()["repaired_file_sha256"])
    names += ["demo/candidate_before_bob.py", "demo/report.py"]
    names += [f"evaluation/{name}" for name in EXECUTION_FILES]
    names += ["evaluation/fixtures/metadata.json"]
    names += [f"evaluation/fixtures/{f['filename']}" for f in load_manifest()["fixtures"]]
    return {"contract_version": contract["version"], "contract_sha256": file_hash(contract_path),
            "comparison_policy": contract["comparison"]["comparator_policy"],
            "hash_policy": "SHA-256, CRLF normalized to LF for Python/JSON; other files hashed as bytes.",
            "files": {name: file_hash(ROOT / name) for name in names}}


def run_cases(scenario_ids: list[str] | None = None, fixture_ids: list[str] | None = None) -> list[dict]:
    scenario_ids = list(SCENARIOS) if scenario_ids is None else scenario_ids
    manifest = load_manifest()
    available = {item["id"] for item in manifest["fixtures"]}
    fixture_ids = [item["id"] for item in manifest["fixtures"]] if fixture_ids is None else fixture_ids
    for scenario_id in scenario_ids:
        get_scenario(scenario_id)
    if not scenario_ids or not fixture_ids or not set(fixture_ids) <= available:
        raise ValueError("Select an allowlisted scenario and evaluation fixture")
    if len(set(scenario_ids)) != len(scenario_ids) or len(set(fixture_ids)) != len(fixture_ids):
        raise ValueError("Duplicate evaluation selection")
    if not all(check_integrity().values()):
        raise RuntimeError("Frozen source integrity check failed")
    with tempfile.TemporaryDirectory(prefix="paritylens-evaluation-") as temporary:
        workspace = Path(temporary)
        names = list(provenance()["repaired_file_sha256"])
        names += ["demo/__init__.py", "demo/candidate_before_bob.py", "demo/report.py"]
        names += [f"evaluation/{name}" for name in EXECUTION_FILES]
        names += ["evaluation/fixtures/metadata.json"]
        names += [f"evaluation/fixtures/{f['filename']}" for f in manifest["fixtures"]]
        for name in names:
            destination = workspace / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        if not all(check_integrity(workspace).values()):
            raise RuntimeError("Isolated source integrity check failed")
        (workspace / ".evaluation-workspace").touch()
        (workspace / "request.json").write_text(json.dumps({"scenarios": scenario_ids, "fixtures": fixture_ids}))
        process = subprocess.run([sys.executable, "-B", "-m", "evaluation.worker"], cwd=workspace,
                                 capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        if process.returncode:
            print(process.stderr, file=sys.stderr)
            raise RuntimeError("Evaluation execution failed; no passing result is inferred")
        return json.loads((workspace / "cases.json").read_text(encoding="utf-8"))


def run_scenario(scenario_id: str, fixture_id: str) -> dict:
    inputs = input_fingerprint()
    case = run_cases([scenario_id], [fixture_id])[0]
    if inputs != input_fingerprint():
        raise RuntimeError("Evaluation inputs changed during execution")
    return case_report(case, inputs, provenance())


def run_evaluation() -> dict:
    inputs = input_fingerprint()
    first = run_cases()
    second = run_cases()
    if inputs != input_fingerprint():
        raise RuntimeError("Evaluation inputs changed between runs")
    versions = {name: importlib.metadata.version(name) for name in ("numpy", "pillow", "streamlit")}
    import cv2
    versions["opencv"] = cv2.__version__
    result = {
        "schema_version": "1.0", "project": "ParityLens", "evaluation": "Deterministic synthetic evaluation",
        "generated_at": datetime.now(timezone.utc).isoformat(), "fixture_set": load_manifest()["version"],
        "fixture_count": len(load_manifest()["fixtures"]), "scenarios": [s.metadata() for s in SCENARIOS.values()],
        "inputs": inputs, "environment": {"python": platform.python_version(), "platform": platform.system(), **versions},
        "metrics": summarize(first, second), "cases": first, "repeated_cases": second,
        "disclaimer": DISCLAIMER,
        "classification_policy": "Frozen comparator decides parity. Evaluation adapter labels numerical failures at scaling/normalization by boundary; it does not infer the faulty operation.",
        "historical_provenance": {key: provenance()[key] for key in ("before_commit", "repaired_commit", "snapshot_sha256")},
        "historical_scope": "Historical candidate executed on additional synthetic inputs; the original recorded Bob case remains in demo/.",
    }
    validate_suite(result)
    return result


def save_evaluation(result: dict, directory: Path = ROOT / "evaluation") -> None:
    validate_suite(result)
    for name, payload in (("results.json", json.dumps(result, indent=2, allow_nan=False) + "\n"),
                          ("results.md", markdown_report(result))):
        target = directory / name
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as handle:
            handle.write(payload)
            temporary = Path(handle.name)
        temporary.replace(target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic synthetic evaluation twice.")
    parser.add_argument("--scenario", choices=list(SCENARIOS))
    parser.add_argument("--fixture", choices=[f["id"] for f in load_manifest()["fixtures"]])
    args = parser.parse_args()
    try:
        if args.scenario:
            report = run_scenario(args.scenario, args.fixture or load_manifest()["fixtures"][0]["id"])
            print(json.dumps(report, indent=2, allow_nan=False))
            return 0 if report["result"]["parity_check"] == "PASS" else 1
        if args.fixture:
            parser.error("--fixture requires --scenario")
        result = run_evaluation()
        save_evaluation(result)
        print(json.dumps(result["metrics"], indent=2))
        return 0 if (result["metrics"]["expectations_met"] == len(result["cases"])
                     and result["metrics"]["reproducibility"]["matched"]) else 1
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
