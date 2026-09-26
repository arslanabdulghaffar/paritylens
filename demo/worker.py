from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

from paritylens import comparator
from demo.report import stage_details


def main() -> int:
    if not Path(".demo-workspace").is_file() or Path.cwd().resolve() != Path(__file__).resolve().parents[1]:
        raise ValueError("Demo execution requires an isolated workspace")
    mode = sys.argv[1]
    if mode not in {"before", "after"}:
        raise ValueError("Unsupported demo mode")
    fixture = "fixtures/defect_rgb_bgr.png"
    contract = json.loads(Path("contract/preprocessing_contract.json").read_text())
    metadata = json.loads(Path("fixtures/fixture_metadata.json").read_text())
    if list(contract["stages"]) != comparator.STAGE_ORDER:
        raise ValueError("Unsupported or ambiguous contract stage map")
    with Image.open(fixture) as img:
        if img.mode != "RGB" or img.format != "PNG" or list(img.size) != contract["fixture"]["size"]:
            raise ValueError("Fixture violates the approved image preconditions")
        row, col = metadata["probe_coordinate"]
        if (metadata["probe_coordinate"] != contract["fixture"]["probe_pixel"]["coordinate"]
                or list(img.getpixel((col, row))) != metadata["probe_pixel_rgb"]):
            raise ValueError("Fixture probe does not match the frozen metadata")
    verification = None
    if mode == "before":
        from paritylens.pipelines import reference
        from demo import candidate_before_bob
        reference.run(fixture)
        candidate_before_bob.run(fixture)
        candidate_path = Path("demo/candidate_before_bob.py")
    else:
        command = [sys.executable, "-B", "-m", "paritylens", "--fixture", fixture, "--verify"]
        process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
        verification = {"command": "python -m paritylens --fixture " + fixture + " --verify",
                        "exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr}
        if process.returncode not in (0, 1):
            raise RuntimeError("Core verifier could not complete")
        candidate_path = Path("paritylens/pipelines/candidate.py")
    comparison = comparator.compare("contract/preprocessing_contract.json", "fixtures/fixture_metadata.json",
                                    "evidence/reference", "evidence/candidate")
    stages = stage_details(comparison, contract, metadata, candidate_path)
    failure = comparison.first_failure
    result = {
        "mode": mode, "executed_at": datetime.now(timezone.utc).isoformat(),
        "fixture": fixture, "contract_version": contract["version"],
        "comparison_policy": contract["comparison"]["comparator_policy"],
        "candidate_source": candidate_path.as_posix(),
        "probe_coordinate": metadata["probe_coordinate"],
        "shape_check": "PASS" if all(s["shape_matches"] for s in stages) else "FAIL",
        "dtype_check": "PASS" if all(s["dtype_matches"] for s in stages) else "FAIL",
        "parity_check": "PASS" if comparison.passed else "FAIL",
        "first_violating_boundary": failure.stage if failure else None,
        "classification": failure.defect_class if failure else None,
        "stages": stages,
        "verification_state": ("PASS" if comparison.passed and verification["exit_code"] == 0 else "FAIL") if verification else "NOT_RUN",
        "verification": verification,
    }
    Path("result.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    return 0 if comparison.passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, AssertionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
