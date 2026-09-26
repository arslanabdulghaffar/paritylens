import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from demo.runner import ROOT
from evaluation.baseline import naive_structural_check
from evaluation.fixtures import load_manifest
from integrity.check_integrity import check


def adversarial_checks() -> None:
    from PIL import Image
    from evaluation.adapter import compare, validate_fixture
    from evaluation.candidates import run
    from paritylens import comparator
    from paritylens.pipelines import candidate, reference
    contract_path = ROOT / "contract/preprocessing_contract.json"
    contract = json.loads(contract_path.read_text())
    metadata = json.loads((ROOT / "fixtures/fixture_metadata.json").read_text())
    metadata_path = Path("metadata.json")
    metadata_path.write_text(json.dumps(metadata))
    rng = np.random.default_rng(20260927)
    patterns = {
        "dark": np.full((224, 224, 3), 3, dtype=np.uint8),
        "bright": np.full((224, 224, 3), 252, dtype=np.uint8),
        "red": np.full((224, 224, 3), [245, 12, 24], dtype=np.uint8),
        "green": np.full((224, 224, 3), [19, 243, 35], dtype=np.uint8),
        "blue": np.full((224, 224, 3), [11, 28, 239], dtype=np.uint8),
        "asymmetric_noise": rng.integers(0, 256, (224, 224, 3), dtype=np.uint8),
    }
    for name, pixels in patterns.items():
        pixels[0, 0] = metadata["probe_pixel_rgb"]
        image = Path(name + ".png")
        Image.fromarray(pixels).save(image)
        validate_fixture(image, metadata, contract)
        reference.run(image)
        candidate.run(image)
        assert compare(contract_path, metadata_path)[0].passed, name
        for scenario, boundary in (("scaling_mismatch", "scaling"), ("normalization_mismatch", "normalization")):
            run(image, scenario, contract)
            result = compare(contract_path, metadata_path)[0]
            assert result.first_failure.stage == boundary, (name, scenario)
        candidate.run(image)
    ref_path = Path("evidence/reference/scaling.npy")
    cand_path = Path("evidence/candidate/scaling.npy")
    ref = np.zeros((224, 224, 3), dtype=np.float32)
    np.save(ref_path, ref)
    atol, rtol = contract["comparison"]["atol"], contract["comparison"]["rtol"]
    threshold = atol / (1 - rtol)
    below = np.nextafter(np.float32(threshold), np.float32(0))
    above = np.nextafter(np.float32(threshold), np.float32(np.inf))
    np.save(cand_path, np.full_like(ref, below))
    assert compare(contract_path, metadata_path)[0].passed
    np.save(cand_path, np.full_like(ref, above))
    assert compare(contract_path, metadata_path)[0].first_failure.stage == "scaling"
    np.save(cand_path, ref.astype(np.float64))
    assert compare(contract_path, metadata_path)[0].first_failure.defect_class == "dtype_mismatch"
    np.save(cand_path, ref[:1])
    assert compare(contract_path, metadata_path)[0].first_failure.defect_class == "shape_mismatch"
    cand_path.unlink()
    assert comparator.compare(contract_path, metadata_path, "evidence/reference", "evidence/candidate").first_failure.defect_class == "missing_evidence"
    try:
        compare(contract_path, metadata_path)
    except ValueError:
        pass
    else:
        raise AssertionError("Adapter accepted missing evidence")
    np.save(cand_path, np.array([{"unsafe": "object"}], dtype=object))
    try:
        compare(contract_path, metadata_path)
    except ValueError:
        pass
    else:
        raise AssertionError("Object/pickle evidence accepted")
    Image.fromarray(np.zeros((224,224,3), dtype=np.uint8)).save("black.png")
    try:
        validate_fixture(Path("black.png"), metadata, contract)
    except ValueError:
        pass
    else:
        raise AssertionError("Non-observable black probe accepted")
    # The frozen swap classifier is a probe heuristic, not full causal proof.
    reference.run(ROOT / "fixtures/defect_rgb_bgr.png")
    candidate.run(ROOT / "fixtures/defect_rgb_bgr.png")
    arr = np.load("evidence/candidate/decode.npy", allow_pickle=False)
    arr[0, 0] = [20, 99, 180]
    np.save("evidence/candidate/decode.npy", arr)
    report, _ = compare(contract_path, metadata_path)
    assert report.first_failure.defect_class == "channel_order_mismatch"
    print("18 pattern executions; tolerance neighbors; shape/dtype; missing/pickle; invalid probe; heuristic limitation: PASS")


class HardeningTests(unittest.TestCase):
    def test_final_structural_baseline_detects_only_structure(self):
        ref = np.zeros((3, 224, 224), dtype=np.float32)
        self.assertTrue(naive_structural_check(ref, ref + 9)["passed"])
        self.assertFalse(naive_structural_check(ref, ref[:, :1])["passed"])
        self.assertFalse(naive_structural_check(ref, ref.astype(np.float64))["passed"])

    def test_adversarial_patterns_and_comparison_boundaries(self):
        with tempfile.TemporaryDirectory(prefix="paritylens-property-") as folder:
            result = subprocess.run([sys.executable, "-B", "-c", "from tests.test_hardening import adversarial_checks; adversarial_checks()"],
                                    cwd=folder, env={**os.environ, "PYTHONPATH": str(ROOT)},
                                    capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_workers_reject_repository_execution(self):
        for module, extra in (("demo.worker", ["before"]), ("evaluation.worker", [])):
            result = subprocess.run([sys.executable, "-B", "-m", module, *extra], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
        self.assertTrue(all(check(portable=True).values()))

    def test_fixture_manifest_rejects_paths_and_duplicates(self):
        manifest = load_manifest()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "metadata.json"
            for filename in ("../outside.png", "C:\\outside.png", "/tmp/outside.png", "sub/file.png"):
                invalid = copy.deepcopy(manifest)
                invalid["fixtures"][0]["filename"] = filename
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):
                    load_manifest(Path(folder))
            invalid = copy.deepcopy(manifest)
            invalid["fixtures"][-1] = invalid["fixtures"][0]
            path.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                load_manifest(Path(folder))

    def test_integrity_detects_missing_changed_and_extra_files(self):
        manifest = json.loads((ROOT / "integrity/protected_manifest.json").read_text())
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder)
            for name in manifest["files"]:
                path = clone / name
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, path)
            self.assertTrue(all(check(clone, portable=True).values()))
            target = clone / "bob_sessions/index.md"
            target.write_bytes(target.read_bytes() + b"changed")
            self.assertFalse(check(clone, portable=True)["bob_sessions/index.md"])
            target.unlink()
            self.assertFalse(check(clone, portable=True)["bob_sessions/index.md"])
            (clone / "fixtures/extra.txt").write_text("extra")
            self.assertFalse(check(clone, portable=True)["fixtures/file_set"])

    def test_runtime_without_git_history(self):
        with tempfile.TemporaryDirectory(prefix="paritylens-no-git-") as folder:
            clone = Path(folder)
            for directory in ("demo", "evaluation", "paritylens", "fixtures", "contract"):
                shutil.copytree(ROOT / directory, clone / directory, ignore=shutil.ignore_patterns("__pycache__"))
            result = subprocess.run([sys.executable, "-B", "-m", "demo.runner", "--mode", "both"], cwd=clone,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["verification_state"], "PASS")


if __name__ == "__main__":
    unittest.main()
