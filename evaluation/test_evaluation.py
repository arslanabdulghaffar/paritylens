import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from demo.runner import ROOT, provenance
from evaluation.fixtures import generate, load_manifest
from evaluation.report import case_report, validate_suite
from evaluation.runner import run_cases, run_evaluation


def protected_hashes() -> dict:
    paths = [ROOT / name for name in ("AGENTS.md", "paritylens-plan.md")]
    for folder in ("contract", "fixtures", "paritylens", "bob_sessions", "evidence"):
        paths.extend(p for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protected_before = protected_hashes()
        cls.suite = run_evaluation()

    def test_matrix_localizes_each_family(self):
        self.assertEqual(self.suite["fixture_count"], 15)
        self.assertEqual(len(self.suite["cases"]), 60)
        expected = {"historical_rgb_bgr": "decode", "scaling_mismatch": "scaling",
                    "normalization_mismatch": "normalization", "clean_control": None}
        for case in self.suite["cases"]:
            with self.subTest(scenario=case["scenario"]["id"], fixture=case["fixture"]):
                boundary = expected[case["scenario"]["id"]]
                self.assertEqual(case["observed_first_boundary"], boundary)
                self.assertEqual(case["shape_check"], "PASS")
                self.assertEqual(case["dtype_check"], "PASS")
                self.assertTrue(case["expectation_met"])
                statuses = [s["comparison"] for s in case["stages"]]
                if boundary:
                    index = [s["stage"] for s in case["stages"]].index(boundary)
                    self.assertEqual(statuses[:index], ["PASS"] * index)
                    self.assertEqual(statuses[index], "FAIL")
                    self.assertEqual(statuses[index+1:], ["NOT_EVALUATED"] * (4-index))
                else:
                    self.assertEqual(statuses, ["PASS"] * 5)

    def test_reproducibility_and_metrics(self):
        self.assertEqual(self.suite["cases"], self.suite["repeated_cases"])
        metrics = self.suite["metrics"]
        self.assertTrue(metrics["reproducibility"]["matched"])
        self.assertEqual(metrics["defects_detected"], 45)
        self.assertEqual(metrics["clean_controls_passed"], 15)
        self.assertEqual(metrics["clean_false_positives"], 0)
        self.assertEqual(metrics["boundary_localization"]["correct"], 45)
        self.assertEqual(metrics["supported_classification"]["correct"], 45)

    def test_fixture_generation_is_repeatable(self):
        with tempfile.TemporaryDirectory(prefix="paritylens-fixture-test-") as directory:
            generated = generate(Path(directory))
            self.assertEqual(generated, load_manifest())
            self.assertEqual(len({f["pixel_sha256"] for f in generated["fixtures"]}), 15)

    def test_reports_preserve_origin_and_schema(self):
        validate_suite(json.loads(json.dumps(self.suite)))
        for case in self.suite["cases"]:
            report = case_report(case, self.suite["inputs"], provenance())
            self.assertEqual(report["scenario_id"], case["scenario"]["id"])
            if case["scenario"]["origin"] == "controlled_evaluation":
                self.assertNotIn("historical_provenance", report)
                self.assertNotIn("repair_statement", report)
            else:
                self.assertEqual(report["historical_provenance"]["before_commit"], provenance()["before_commit"])
        invalid = copy.deepcopy(self.suite)
        invalid["metrics"]["defects_detected"] = 0
        with self.assertRaises(ValueError):
            validate_suite(invalid)

    def test_execution_preserves_protected_files(self):
        self.assertEqual(self.protected_before, protected_hashes())

    def test_unlisted_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            run_cases(["arbitrary_source"], ["gradients_1"])
        with self.assertRaises(ValueError):
            run_cases(["clean_control"], ["../../fixtures/defect_rgb_bgr.png"])

    def test_adapter_keeps_frozen_acceptance_and_rejects_ambiguity(self):
        script = r'''
import json
from pathlib import Path
import numpy as np
from evaluation.adapter import compare, validate_fixture
from demo.runner import ROOT
contract_path = ROOT / 'contract/preprocessing_contract.json'
metadata_path = ROOT / 'fixtures/fixture_metadata.json'
contract = json.loads(contract_path.read_text())
for side in ('reference', 'candidate'):
    folder = Path('evidence') / side
    folder.mkdir(parents=True)
    for stage in contract['stages']:
        dtype = np.uint8 if stage in ('decode', 'geometry') else np.float32
        shape = (3,224,224) if stage == 'model_input' else (224,224,3)
        np.save(folder / f'{stage}.npy', np.ones(shape, dtype=dtype))
def change(stage, value, dtype=np.float32):
    np.save(f'evidence/candidate/{stage}.npy', np.full((224,224,3), value, dtype=dtype))
change('scaling', 1 + contract['comparison']['atol']/10)
assert compare(contract_path, metadata_path)[0].passed
change('scaling', 1.1)
report, core = compare(contract_path, metadata_path)
assert not report.passed and report.first_failure.defect_class == 'scaling_mismatch'
assert core == 'numerical_mismatch'
change('scaling', 1, np.float64)
assert compare(contract_path, metadata_path)[0].first_failure.defect_class == 'dtype_mismatch'
change('scaling', 1)
change('decode', 2, np.uint8)
assert compare(contract_path, metadata_path)[0].first_failure.stage == 'decode'
change('decode', 1, np.uint8)
change('normalization', np.nan)
try:
    compare(contract_path, metadata_path)
except ValueError:
    pass
else:
    raise AssertionError('Non-finite data accepted')
change('normalization', 1)
np.save('evidence/candidate/unknown.npy', np.ones(1))
try:
    compare(contract_path, metadata_path)
except ValueError:
    pass
else:
    raise AssertionError('Unknown stage accepted')
bad_metadata = json.loads(metadata_path.read_text())
bad_metadata['probe_pixel_rgb'] = [1,1,1]
try:
    validate_fixture(ROOT / 'fixtures/defect_rgb_bgr.png', bad_metadata, contract)
except ValueError:
    pass
else:
    raise AssertionError('Invalid probe accepted')
'''
        with tempfile.TemporaryDirectory(prefix="paritylens-adapter-test-") as directory:
            env = {**os.environ, "PYTHONPATH": str(ROOT)}
            result = subprocess.run([sys.executable, "-B", "-c", script], cwd=directory,
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_controlled_ui_states_and_switching(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        for scenario, boundary in (("scaling_mismatch", "scaling"), ("normalization_mismatch", "normalization")):
            app.selectbox(key="scenario_selector").set_value(scenario).run()
            self.assertFalse(app.exception)
            self.assertFalse(any("Repair produced during" in c.value for c in app.caption))
            app.button(key="eval_run_defect").click().run()
            self.assertFalse(app.exception)
            timeline = next(m.value for m in app.markdown if '<div class="timeline">' in m.value)
            self.assertIn(f'<strong>{boundary}</strong>FAIL', timeline)
            app.button(key="eval_run_control").click().run()
            app.radio(key=f"evaluation_trace_{scenario}:gradients_1").set_value("control").run()
            self.assertFalse(app.exception)
            timeline = next(m.value for m in app.markdown if '<div class="timeline">' in m.value)
            self.assertEqual(timeline.count('class="stage pass"'), 5)
            app.selectbox(key="evaluation_fixture").set_value("blocks_1").run()
            self.assertFalse(app.exception)
            self.assertFalse(any('<div class="timeline">' in m.value for m in app.markdown))
            app.selectbox(key="evaluation_fixture").set_value("gradients_1").run()
        app.selectbox(key="scenario_selector").set_value("historical_rgb_bgr").run()
        app.button(key="run_after").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["after"]["verification_state"], "PASS")
        self.assertEqual(self.protected_before, protected_hashes())


if __name__ == "__main__":
    unittest.main()
