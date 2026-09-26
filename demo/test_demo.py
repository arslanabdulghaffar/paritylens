from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from demo.report import report_json
from demo.runner import ROOT, check_integrity, provenance, run_demo


def evidence_hashes() -> dict:
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "evidence").rglob("*") if p.is_file()}


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_evidence = evidence_hashes()
        with ThreadPoolExecutor(max_workers=2) as pool:
            cls.before, cls.after = list(pool.map(run_demo, ("before", "after")))

    def test_historical_snapshot_is_git_blob(self):
        info = provenance()
        historical = subprocess.check_output(
            ["git", "show", f"{info['before_commit']}:{info['original_source']}"], cwd=ROOT)
        self.assertEqual(historical, (ROOT / "demo/candidate_before_bob.py").read_bytes())
        self.assertTrue(all(check_integrity().values()))

    def test_before_exposes_semantic_mismatch(self):
        result = self.before
        self.assertEqual((result["shape_check"], result["dtype_check"], result["parity_check"]),
                         ("PASS", "PASS", "FAIL"))
        self.assertEqual(result["first_violating_boundary"], "decode")
        self.assertEqual(result["classification"], "channel_order_mismatch")
        self.assertEqual(result["execution_exit_code"], 1)
        metadata = json.loads((ROOT / "fixtures/fixture_metadata.json").read_text())
        decode = result["stages"][0]
        self.assertEqual(decode["reference_probe"], metadata["probe_pixel_rgb"])
        self.assertEqual(decode["candidate_probe"], list(reversed(metadata["probe_pixel_rgb"])))
        self.assertTrue(all(s["comparison"] == "NOT_EVALUATED" for s in result["stages"][1:]))
        self.assertEqual(result["verification_state"], "NOT_RUN")

    def test_after_uses_full_verification(self):
        result = self.after
        self.assertEqual((result["shape_check"], result["dtype_check"], result["parity_check"]),
                         ("PASS", "PASS", "PASS"))
        self.assertEqual(result["verification_state"], "PASS")
        self.assertEqual(result["verification"]["exit_code"], 0)
        self.assertIn("--verify", result["verification"]["command"])
        self.assertEqual(len(result["stages"]), 5)
        self.assertTrue(all(s["comparison"] == "PASS" for s in result["stages"]))
        self.assertTrue(all(s["max_absolute_difference"] == 0 for s in result["stages"]))

    def test_report_and_evidence_isolation(self):
        report = json.loads(report_json(self.before, self.after, provenance()))
        self.assertEqual(report["verification_state"], "PASS")
        self.assertEqual(report["before_result"]["input_sha256"], report["after_result"]["input_sha256"])
        self.assertEqual(report["defect_classification"], "channel_order_mismatch")
        self.assertEqual(self.original_evidence, evidence_hashes())

    def test_rejects_unlisted_mode(self):
        with self.assertRaises(ValueError):
            run_demo("user-supplied-code")

    def test_ui_workflow(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("download_button")), 0)
        app.button(key="run_before").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["before"]["parity_check"], "FAIL")
        app.button(key="run_after").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["after"]["verification_state"], "PASS")
        self.assertEqual(len(app.get("download_button")), 1)
        app.radio(key="trace_mode").set_value("after").run()
        app.selectbox(key="stage").set_value("model_input").run()
        self.assertFalse(app.exception)
        self.assertEqual(self.original_evidence, evidence_hashes())


if __name__ == "__main__":
    unittest.main()
