from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile

import cv2
import numpy as np

from demo.runner import ROOT, check_integrity
from evaluation.runner import input_fingerprint, prepare_workspace


def run_benchmark(runs: int = 20, warmup: int = 3) -> dict:
    if runs < 2 or warmup < 1:
        raise ValueError("Use at least two measurements and one warmup")
    if not all(check_integrity().values()):
        raise ValueError("Frozen source integrity check failed")
    inputs = input_fingerprint()
    with tempfile.TemporaryDirectory(prefix="paritylens-benchmark-") as temporary:
        workspace = Path(temporary)
        prepare_workspace(workspace)
        (workspace / "benchmark_request.json").write_text(json.dumps({"runs": runs, "warmup": warmup}))
        result = subprocess.run([sys.executable, "-B", "-m", "evaluation.benchmark_worker"], cwd=workspace,
                                capture_output=True, text=True, timeout=180)
        if result.returncode:
            raise RuntimeError("Benchmark failed: " + result.stderr)
        records = json.loads((workspace / "benchmark_samples.json").read_text())
    if inputs != input_fingerprint():
        raise ValueError("Benchmark inputs changed during execution")
    for record in records:
        record["summary"] = {field: {"median_ms": round(statistics.median(s[field] for s in record["samples"]), 3),
                                     "p95_ms": round(float(np.percentile([s[field] for s in record["samples"]], 95)), 3)}
                             for field in record["samples"][0]}
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "runs_per_scenario": runs,
            "warmup_per_scenario": warmup, "inputs": inputs, "records": records,
            "environment": {"python": platform.python_version(), "platform": platform.system(),
                            "machine": platform.machine(), "processor": platform.processor(),
                            "numpy": np.__version__, "opencv": cv2.__version__},
            "scope": "Local development-machine measurements, not universal performance guarantees. "
                     "One gradients_1 fixture per scenario; 224x224 RGB. Includes NPY disk I/O. "
                     "Comparison includes adapter validation and first-failure stopping. Complete execution includes "
                     "fixture validation, evidence cleanup, both pipelines, comparison, and report measurements/hashes. "
                     "Excludes process startup, imports, workspace setup, Streamlit rendering and core --verify invocation. "
                     "p95 uses NumPy's linear percentile; samples are not independent deployment estimates."}


def markdown(result: dict) -> str:
    lines = ["# Local runtime benchmark", "", result["scope"], "",
             f"{result['runs_per_scenario']} measured runs and {result['warmup_per_scenario']} warmups per scenario.", "",
             "| Scenario | Component | Median ms | p95 ms |", "|---|---|---:|---:|"]
    for record in result["records"]:
        for component, metrics in record["summary"].items():
            lines.append(f"| {record['scenario']} | {component} | {metrics['median_ms']:.3f} | {metrics['p95_ms']:.3f} |")
    lines += ["", "Environment: `" + json.dumps(result["environment"]) + "`.", ""]
    return "\n".join(lines)


def main() -> None:
    result = run_benchmark()
    (ROOT / "evaluation/benchmark_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (ROOT / "evaluation/benchmark_results.md").write_text(markdown(result), encoding="utf-8")
    print(markdown(result))


if __name__ == "__main__":
    main()
