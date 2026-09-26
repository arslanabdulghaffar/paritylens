"""
ParityLens CLI entry point.

Usage:
  python -m paritylens --fixture <path>
      Run reference pipeline and candidate pipeline on <path>,
      compare with contract, report first failure.

  python -m paritylens --fixture <path> --use-reference-as-candidate
      Run the reference pipeline twice (once as reference, once as candidate).
      Used for the clean control experiment.

  python -m paritylens --fixture <path> --verify
      Run candidate pipeline end-to-end (no patching), compare with reference.

Exit codes:
  0  All stages pass
  1  Defect detected
  2  Error (import failure, missing file, invalid args, etc.)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from paritylens import comparator

CONTRACT_PATH = Path("contract/preprocessing_contract.json")
METADATA_PATH = Path("fixtures/fixture_metadata.json")
REF_EVIDENCE_DIR = Path("evidence/reference")
CAND_EVIDENCE_DIR = Path("evidence/candidate")


def _clear_evidence_dirs() -> None:
    """Remove and recreate evidence directories before each run."""
    for d in (REF_EVIDENCE_DIR, CAND_EVIDENCE_DIR):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)


def _print_report(report: comparator.ComparisonReport) -> None:
    for s in report.stages:
        status = "PASS" if s.passed else f"FAIL [{s.defect_class}]"
        print(f"  stage={s.stage:<14}  {status}")
    if report.first_failure:
        print()
        print(f"FAIL  stage={report.first_failure.stage}  "
              f"defect={report.first_failure.defect_class}")
    else:
        print()
        print("PASS  all stages")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m paritylens",
        description="ParityLens — preprocessing pipeline comparator",
    )
    parser.add_argument(
        "--fixture", required=True,
        help="Path to input PNG fixture",
    )
    parser.add_argument(
        "--use-reference-as-candidate", action="store_true",
        help="Run reference pipeline as both reference and candidate (clean control)",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Run candidate pipeline end-to-end and verify (no patching)",
    )
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    if not fixture_path.exists():
        print(f"ERROR: fixture not found: {fixture_path}", file=sys.stderr)
        return 2

    _clear_evidence_dirs()

    # ------------------------------------------------------------------
    # Mode: clean control (reference used as both pipelines)
    # ------------------------------------------------------------------
    if args.use_reference_as_candidate:
        try:
            from paritylens.pipelines import reference
        except ImportError as exc:
            print(f"ERROR: import failed: {exc}", file=sys.stderr)
            return 2

        print("ParityLens - clean control run")
        print(f"Fixture: {fixture_path}")
        print(f"Mode: reference-as-candidate")
        print()

        # Run reference pipeline into reference evidence dir
        reference.run(fixture_path)

        # Copy reference evidence to candidate evidence dir (same pipeline, same arrays)
        for npy_file in REF_EVIDENCE_DIR.glob("*.npy"):
            import shutil as _shutil
            _shutil.copy(npy_file, CAND_EVIDENCE_DIR / npy_file.name)

        report = comparator.compare(
            contract_path=CONTRACT_PATH,
            metadata_path=METADATA_PATH,
            ref_dir=REF_EVIDENCE_DIR,
            cand_dir=CAND_EVIDENCE_DIR,
        )
        _print_report(report)
        return 0 if report.passed else 1

    # ------------------------------------------------------------------
    # Mode: verify (run candidate end-to-end, no patching)
    # ------------------------------------------------------------------
    if args.verify:
        try:
            from paritylens import verifier
        except ImportError as exc:
            print(f"ERROR: import failed: {exc}", file=sys.stderr)
            return 2

        print("ParityLens - verify mode")
        print(f"Fixture: {fixture_path}")
        print()

        report = verifier.verify(fixture_path)
        _print_report(report)
        return 0 if report.passed else 1

    # ------------------------------------------------------------------
    # Mode: default (run reference + candidate, compare)
    # ------------------------------------------------------------------
    try:
        from paritylens.pipelines import reference
    except ImportError as exc:
        print(f"ERROR: import failed: {exc}", file=sys.stderr)
        return 2

    try:
        from paritylens.pipelines import candidate
    except ImportError as exc:
        print(f"ERROR: cv2 not available - install opencv-python: {exc}", file=sys.stderr)
        return 2

    print("ParityLens - defect detection run")
    print(f"Fixture: {fixture_path}")
    print()

    reference.run(fixture_path)
    candidate.run(fixture_path)

    report = comparator.compare(
        contract_path=CONTRACT_PATH,
        metadata_path=METADATA_PATH,
        ref_dir=REF_EVIDENCE_DIR,
        cand_dir=CAND_EVIDENCE_DIR,
    )
    _print_report(report)
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
