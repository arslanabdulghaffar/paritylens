import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_release_bundle import build_bundle, prohibited, tracked_files
from scripts.claims_audit import check_claims
from scripts.preflight import preflight

REQUIRED_DOCS = ("PUBLIC_RELEASE_AUDIT", "CROSS_PLATFORM", "CLAIMS_AUDIT", "JUDGE_QA", "SUBMISSION_DRAFT",
                 "VIDEO_SHOTLIST", "SCREENSHOT_PLAN", "RELEASE_CHECKLIST", "DEPLOYMENT", "FINAL_VALIDATION")


def release_checks() -> list[dict]:
    checks = []

    def record(name, operation):
        try:
            checks.append({"check": name, "passed": True, "detail": operation()})
        except Exception as exc:
            checks.append({"check": name, "passed": False, "detail": str(exc)})

    def hygiene():
        names = tracked_files()
        bad = [name for name in names if prohibited(name)]
        if bad:
            raise ValueError("Prohibited tracked files: " + ", ".join(bad))
        required = [f"docs/{name}.md" for name in REQUIRED_DOCS]
        required += ["app.py", "requirements.txt", ".streamlit/config.toml", ".github/workflows/ci.yml",
                     "scripts/build_release_bundle.py", "scripts/final_review.py"]
        missing = [name for name in required if name not in names or not (ROOT / name).is_file()]
        if missing:
            raise ValueError("Missing or unstaged release files: " + ", ".join(missing))
        return "Required release/runtime docs tracked; no prohibited tracked cache or secret filenames"

    def bundle():
        with tempfile.TemporaryDirectory(prefix="paritylens-review-") as temporary:
            output = Path(temporary)
            manifest = build_bundle(output)
            protected = json.loads((ROOT / "integrity/protected_manifest.json").read_text(encoding="utf-8"))
            required = set(protected["files"]) | {"evaluation/results.json", "evaluation/benchmark_results.json"}
            required |= {f"docs/{name}.md" for name in REQUIRED_DOCS}
            if not required <= manifest["files"].keys():
                raise ValueError("Bundle omits required evidence/docs")
            with zipfile.ZipFile(output / "paritylens-review.zip") as archive:
                if archive.testzip() or len(archive.namelist()) != manifest["bundle_member_count"]:
                    raise ValueError("Invalid ZIP or member count")
                for name, digest in manifest["files"].items():
                    if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                        raise ValueError("Bundle hash mismatch: " + name)
                if json.loads(archive.read("release_manifest.json")) != manifest:
                    raise ValueError("Embedded and external manifests differ")
            return f"Temporary ZIP verified: {manifest['included_file_count']} project files; original evidence included"

    record("Release files and repository hygiene", hygiene)
    record("Claims and source consistency", check_claims)
    record("Release bundle capability and hashes", bundle)
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run preflight once, then inexpensive release checks; no deployment.")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    result = preflight()
    result["checks"].extend(release_checks())
    result["passed"] = all(item["passed"] for item in result["checks"])
    for item in result["checks"]:
        print(f"{'PASS' if item['passed'] else 'FAIL'} {item['check']}: {item['detail']}")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
