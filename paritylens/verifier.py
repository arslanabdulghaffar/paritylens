"""
ParityLens Verifier.

Runs the candidate pipeline end-to-end (no patching, no cached artefacts),
then calls the comparator. Used by the --verify flag to confirm a genuine repair.

The current Milestone 1 candidate is EXPECTED to fail verification because
it contains the deliberate BGR defect. This is correct behaviour.
"""

from __future__ import annotations

from pathlib import Path

from paritylens import comparator
from paritylens.pipelines import reference, candidate


CONTRACT_PATH = Path("contract/preprocessing_contract.json")
METADATA_PATH = Path("fixtures/fixture_metadata.json")
REF_EVIDENCE_DIR = Path("evidence/reference")
CAND_EVIDENCE_DIR = Path("evidence/candidate")


def verify(image_path: str | Path) -> comparator.ComparisonReport:
    """
    Run reference pipeline, run candidate pipeline end-to-end (no patching),
    then compare. Returns a ComparisonReport.
    """
    image_path = Path(image_path)

    reference.run(image_path)
    candidate.run(image_path)

    return comparator.compare(
        contract_path=CONTRACT_PATH,
        metadata_path=METADATA_PATH,
        ref_dir=REF_EVIDENCE_DIR,
        cand_dir=CAND_EVIDENCE_DIR,
    )
