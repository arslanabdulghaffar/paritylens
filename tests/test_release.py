import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
import zipfile

from scripts.build_release_bundle import build_bundle, collect_files, prohibited


class ReleaseTests(unittest.TestCase):
    def test_bundle_members_and_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
            (root / "README.md").write_text("Review fixture", encoding="utf-8")
            (root / "bob_sessions").mkdir()
            (root / "bob_sessions/session.png").write_bytes(b"test bytes")
            names = ["README.md", "bob_sessions/session.png", "__pycache__/test.pyc", ".env",
                     ".streamlit/secrets.toml", "dist/old.zip", "scratch/evidence.npy"]
            with patch("scripts.build_release_bundle.tracked_files", return_value=names):
                manifest = build_bundle(root / "output", root)
            self.assertEqual(manifest["included_file_count"], 2)
            with zipfile.ZipFile(root / "output/paritylens-review.zip") as archive:
                self.assertEqual(set(archive.namelist()), {"README.md", "bob_sessions/session.png", "release_manifest.json"})
                self.assertEqual(json.loads(archive.read("release_manifest.json")), manifest)
                for name, digest in manifest["files"].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
            self.assertFalse(prohibited("evaluation/results.json"))
            self.assertFalse(prohibited("evidence/candidate/decode.npy"))

    def test_embedded_credential_blocks_bundle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config.txt").write_text("sk-" + "a" * 40, encoding="utf-8")
            with patch("scripts.build_release_bundle.tracked_files", return_value=["config.txt"]):
                with self.assertRaisesRegex(ValueError, "Possible credential in config.txt"):
                    collect_files(root)

    def test_outside_path_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch("scripts.build_release_bundle.tracked_files", return_value=["../outside.txt"]):
                with self.assertRaisesRegex(ValueError, "Unsafe release path"):
                    collect_files(Path(temporary))
