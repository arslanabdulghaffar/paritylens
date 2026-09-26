import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from demo.report import report_json
from demo.runner import provenance, run_demo
from evaluation.report import case_report, validate_suite
from evaluation.runner import input_fingerprint, run_evaluation
from integrity.check_integrity import check
from hosting_check import check_startup


def preflight() -> dict:
    checks = []

    def record(name, operation):
        try:
            detail = operation()
            checks.append({"check": name, "passed": True, "detail": detail})
        except Exception as exc:
            checks.append({"check": name, "passed": False, "detail": str(exc)})

    def integrity():
        statuses = check(portable=True)
        if not all(statuses.values()):
            raise ValueError("Changed/missing: " + ", ".join(k for k, v in statuses.items() if not v))
        return f"{len(statuses)} portable integrity checks; original snapshot remains byte-exact"

    record("Protected integrity and Bob evidence", integrity)
    if not checks[-1]["passed"]:
        return {"passed": False, "checks": checks}

    def required_files():
        names = ("app.py", "requirements.txt", "demo/provenance.json", "evaluation/fixtures/metadata.json",
                 "evaluation/results.json", "evaluation/results.md", "evaluation/benchmark_results.json",
                 "docs/SECURITY.md", "docs/VALIDATION.md", "docs/ARCHITECTURE.md", "docs/DEMO_SCRIPT.md",
                 "docs/SUBMISSION_FACTS.md", "docs/DATA_AND_DEPENDENCIES.md")
        missing = [name for name in names if not (ROOT / name).is_file()]
        if missing:
            raise ValueError("Missing required files: " + ", ".join(missing))
        return f"{len(names)} required files present"

    record("Required project files", required_files)
    historical = {}

    def historical_run(mode):
        result = run_demo(mode)
        historical[mode] = result
        if result["shape_check"] != "PASS" or result["dtype_check"] != "PASS":
            raise ValueError("Historical structural regression")
        if mode == "before":
            if (result["parity_check"], result["first_violating_boundary"], result["classification"]) != (
                    "FAIL", "decode", "channel_order_mismatch"):
                raise ValueError("Historical BEFORE regression")
            return "decode / channel_order_mismatch; shape and dtype PASS"
        if result["verification_state"] != "PASS" or any(s["comparison"] != "PASS" for s in result["stages"]):
            raise ValueError("Repaired candidate verification failed")
        return "Normal --verify CLI: all five stages PASS"

    record("Historical BEFORE", lambda: historical_run("before"))
    record("Bob-repaired AFTER", lambda: historical_run("after"))
    fresh = {}

    def evaluation():
        suite = run_evaluation()
        fresh.update(suite)
        metrics = suite["metrics"]
        if metrics["expectations_met"] != metrics["cases_evaluated"] or not metrics["reproducibility"]["matched"]:
            raise ValueError("Evaluation outcome or reproducibility regression")
        return f"{metrics['cases_evaluated']} cases twice; scaling/normalization localized; clean controls PASS"

    record("Full controlled matrix and reproducibility", evaluation)

    def artifacts():
        saved = json.loads((ROOT / "evaluation/results.json").read_text(encoding="utf-8"))
        validate_suite(saved)
        if saved["inputs"] != input_fingerprint():
            raise ValueError("Stale evaluation artifact; run python -m evaluation.runner")
        if saved["cases"] != fresh["cases"] or saved["metrics"] != fresh["metrics"]:
            raise ValueError("Saved evaluation differs from fresh execution")
        benchmark = json.loads((ROOT / "evaluation/benchmark_results.json").read_text(encoding="utf-8"))
        if benchmark["inputs"] != input_fingerprint():
            raise ValueError("Stale benchmark; run python -m evaluation.benchmark")
        return "Stored evaluation matches fresh cases and baseline; benchmark inputs current"

    record("Evaluation and benchmark artifact consistency", artifacts)

    def reports():
        combined = json.loads(report_json(historical["before"], historical["after"], provenance()))
        if combined["verification_state"] != "PASS":
            raise ValueError("Historical report verification missing")
        for case in fresh["cases"]:
            report = case_report(case, fresh["inputs"], provenance())
            json.dumps(report, allow_nan=False)
            if report["scenario_origin"] == "controlled_evaluation" and "historical_provenance" in report:
                raise ValueError("Controlled report incorrectly claims historical provenance")
        return "Historical and all scenario reports serialize with correct origins"

    record("Evidence exports", reports)

    def tests():
        result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-v"], cwd=ROOT,
                                capture_output=True, text=True, timeout=240)
        if result.returncode:
            raise ValueError(result.stdout + result.stderr)
        return " / ".join(line for line in result.stderr.splitlines() if line.startswith("Ran ") or line == "OK")

    record("Automated tests including Streamlit", tests)
    record("Headless Streamlit startup", lambda: check_startup())
    record("Post-execution protected integrity", integrity)
    return {"generated_at": datetime.now(timezone.utc).isoformat(),
            "passed": all(item["passed"] for item in checks), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only project validation; no artifact regeneration or deployment.")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    result = preflight()
    for item in result["checks"]:
        print(f"{'PASS' if item['passed'] else 'FAIL'} {item['check']}: {item['detail']}")
    if args.json_output:
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
