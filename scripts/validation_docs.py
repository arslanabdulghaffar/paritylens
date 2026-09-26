import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    suite = json.loads((ROOT / "evaluation/results.json").read_text(encoding="utf-8"))
    benchmark = json.loads((ROOT / "evaluation/benchmark_results.json").read_text(encoding="utf-8"))
    metrics = suite["metrics"]
    baseline = metrics["final_shape_dtype_baseline"]
    measured = [
        f"- Fixture count: {suite['fixture_count']}; cases per run: {metrics['cases_evaluated']}.",
        f"- Supported defects detected: {metrics['defects_detected']}/{metrics['defect_cases']}.",
        f"- First-boundary localization: {metrics['boundary_localization']['correct']}/{metrics['boundary_localization']['total']}.",
        f"- Supported classification: {metrics['supported_classification']['correct']}/{metrics['supported_classification']['total']}.",
        f"- Clean controls passed: {metrics['clean_controls_passed']}/{metrics['clean_cases']}; false positives: {metrics['clean_false_positives']}.",
        f"- Two-run semantic reproducibility (including array hashes): {metrics['reproducibility']['matched']}.",
        f"- Final shape/dtype baseline detects {baseline['naive_defects_detected']}/{baseline['defective_cases']} defective cases; ParityLens detects {baseline['paritylens_defects_detected']}/{baseline['defective_cases']}.",
    ]
    design = ("The 15-image synthetic set is deterministic and contract-constrained: 224x224 RGB PNGs, "
              "a documented asymmetric probe, and no numerical resize. Five pattern families have three variants each. "
              "Four scenarios run twice in isolated workspaces. The historical RGB/BGR candidate is the genuine Git snapshot "
              "executed on additional evaluation images; the original Bob demo remains a separate original-fixture experiment. "
              "Scaling (missing division by 255) and normalization (fixed incorrect mean/std) are controlled authored variants. "
              "Clean controls run the independent current candidate. Only the original RGB/BGR repair is attributed to the recorded Bob workflow.")
    limits = [
        "This is not generalization evidence for arbitrary CV stacks or a comparison with all MLOps systems.",
        "The baseline checks exactly final tensor shape and dtype. Its results come from recorded model-input arrays, not scenario labels.",
        "Scaling/normalization classifications name the first numerical boundary, not the underlying faulty operation.",
        "The frozen channel-swap classification is a probe heuristic: a red/blue-swapped probe with a changed green value still receives that label. An adversarial test preserves and documents this limitation.",
        "Fully black/gray probe pixels violate the frozen precondition. Dark/bright tests retain an admissible asymmetric probe; these are not unrestricted black-image support.",
        "Integer comparison is exact. Float tolerance-neighbor tests use the contract values; no policy was relaxed.",
        "Missing evidence fails visibly; the adapter additionally rejects unknown stages and non-finite/object arrays. Downstream stages after a first failure remain NOT_EVALUATED.",
        "Repeatability was measured within each environment. Cross-platform/native-library changes may require investigation; the suite does not silently accept a changed artifact.",
    ]
    lines = ["# Technical validation", "", "Generated from evaluation/results.json and evaluation/benchmark_results.json.",
             f"Evaluation measured: {suite['generated_at']}. Benchmark measured: {benchmark['generated_at']}.", "",
             "## Design", "", design, "", "## Measured results", "", *measured, "",
             "Evaluation environment: `" + json.dumps(suite["environment"]) + "`.", "",
             "## Local runtime", "", benchmark["scope"], "",
             f"{benchmark['runs_per_scenario']} measured repetitions after {benchmark['warmup_per_scenario']} warmups for each scenario.", "",
             "| Scenario | Reference median/p95 ms | Candidate median/p95 ms | Comparison median/p95 ms | Complete median/p95 ms |",
             "|---|---:|---:|---:|---:|"]
    for record in benchmark["records"]:
        values = [f"{record['summary'][key]['median_ms']:.3f} / {record['summary'][key]['p95_ms']:.3f}"
                  for key in ("reference_ms", "candidate_ms", "comparison_ms", "complete_scenario_ms")]
        lines.append("| " + record["scenario"] + " | " + " | ".join(values) + " |")
    lines += ["", "Benchmark environment: `" + json.dumps(benchmark["environment"]) + "`.", "",
              "## Adversarial coverage and limits", "", *["- " + value for value in limits], "",
              "## Reproduce", "", "```bash", "python -m unittest discover -v", "python -m evaluation.runner",
              "python -m evaluation.benchmark", "python -m integrity.check_integrity", "python scripts/preflight.py",
              "python scripts/validation_docs.py", "```", "",
              "Default integrity checking is byte-exact for this baseline checkout. Use --portable on other checkouts to allow only CRLF/LF text differences; the historical snapshot remains byte-exact.", ""]
    (ROOT / "docs/VALIDATION.md").write_text("\n".join(lines), encoding="utf-8")
    facts = ["# Submission facts", "", "Project: ParityLens (NeuralFoundry).", "",
             "Problem: matching tensor shape and dtype can conceal a semantically different model input.",
             "Solution: compare recorded preprocessing boundaries, locate the first violation, show numerical/source evidence, and verify a real repair with unchanged checks.",
             "Target user: computer-vision engineers comparing trusted and serving preprocessing paths.",
             "Technology: Python, NumPy, Pillow, headless OpenCV, Streamlit; CPU-only and local.", "",
             "## IBM Bob and provenance", "", design, "",
             "Bob was used for the recorded plan/contract, deterministic comparison implementation, evidence-based diagnosis, and real RGB conversion repair. The web app itself does not invoke Bob.",
             "BEFORE commit: d0ea1fd4f967aa00b1e2113025b19d5783fc7242.",
             "Repair commit: 334a4013230076fbca4d2e3eb86281d1cf29b0c6.",
             "Session evidence: bob_sessions/neuralfoundry_task01_session_summary.png through task04.", "",
             "## Measured results", "", *measured, "", "Local runtime measurements and environment are in VALIDATION.md and evaluation/benchmark_results.json.", "",
             "## Run commands", "", "```bash", "python -m pip install -r requirements.txt", "streamlit run app.py",
             "python -m demo.runner --mode both", "python -m evaluation.runner", "python scripts/preflight.py", "```", "",
             "## Data, security, and limits", "",
             "Project-generated synthetic images only; no external photographs, private/client datasets, or social-media data. Bob screenshots are supplied workflow evidence and require release review.",
             "The app runs allowlisted local code and fixtures with isolated temporary evidence. No arbitrary uploads, user shell commands, remote Bob API, or external LLM calls. See SECURITY.md for remaining resource and dependency risks.",
             *["- " + value for value in limits[:5]], "",
             "No production-readiness, universal detection, novelty, prize, or deployment claim is made. Nothing is deployed by these validation commands.", ""]
    (ROOT / "docs/SUBMISSION_FACTS.md").write_text("\n".join(facts), encoding="utf-8")


if __name__ == "__main__":
    main()
