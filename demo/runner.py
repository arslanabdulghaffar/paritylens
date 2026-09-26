from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = "fixtures/defect_rgb_bgr.png"
SCENARIO = "RGB/BGR preprocessing handoff"


def provenance() -> dict:
    return json.loads((ROOT / "demo/provenance.json").read_text(encoding="utf-8"))


def file_hash(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix in {".py", ".json"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def check_integrity(root: Path = ROOT) -> dict[str, bool]:
    manifest = provenance()
    checks = {
        name: (root / name).is_file() and file_hash(root / name) == expected
        for name, expected in manifest["repaired_file_sha256"].items()
    }
    snapshot = root / "demo/candidate_before_bob.py"
    checks["demo/candidate_before_bob.py"] = (
        snapshot.is_file()
        and hashlib.sha256(snapshot.read_bytes()).hexdigest() == manifest["snapshot_sha256"]
    )
    for folder in ("contract", "fixtures"):
        actual = {p.relative_to(root).as_posix() for p in (root / folder).rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts}
        expected = {p for p in checks if p.startswith(folder + "/")}
        checks[folder + "/file_set"] = actual == expected
    return checks


def run_demo(mode: str) -> dict:
    """Execute one allowlisted scenario in a disposable working directory."""
    if mode not in {"before", "after"}:
        raise ValueError("Only before and after modes are supported.")
    checks = check_integrity()
    if not all(checks.values()):
        raise RuntimeError("Source integrity check failed; restore the approved experiment.")
    with tempfile.TemporaryDirectory(prefix="paritylens-demo-") as temporary:
        workspace = Path(temporary)
        for name in provenance()["repaired_file_sha256"]:
            target = workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        (workspace / "demo").mkdir()
        for name in ("__init__.py", "candidate_before_bob.py", "worker.py", "report.py"):
            shutil.copyfile(ROOT / "demo" / name, workspace / "demo" / name)
        if not all(check_integrity(workspace).values()):
            raise RuntimeError("Isolated copy failed the source integrity check.")
        (workspace / ".demo-workspace").touch()
        process = subprocess.run(
            [sys.executable, "-B", "-m", "demo.worker", mode],
            cwd=workspace, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60, shell=False,
        )
        if process.returncode not in (0, 1) or not (workspace / "result.json").exists():
            print(process.stderr, file=sys.stderr)
            raise RuntimeError("Demo execution failed; no verification result was produced.")
        result = json.loads((workspace / "result.json").read_text(encoding="utf-8"))
        result["integrity"] = checks
        result["input_sha256"] = {
            name: hashlib.sha256((workspace / name).read_bytes()).hexdigest()
            for name in provenance()["repaired_file_sha256"]
        }
        result["execution_exit_code"] = process.returncode
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the isolated ParityLens demo.")
    parser.add_argument("--mode", choices=("before", "after", "both"), default="both")
    args = parser.parse_args()
    try:
        if args.mode == "both":
            from demo.report import build_report
            before, after = run_demo("before"), run_demo("after")
            print(json.dumps(build_report(before, after, provenance()), indent=2))
            return 0 if after["verification_state"] == "PASS" else 1
        result = run_demo(args.mode)
        print(json.dumps(result, indent=2))
        return result["execution_exit_code"]
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
