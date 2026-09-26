import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("protected_manifest.json")


def check(root: Path = ROOT, portable: bool = False) -> dict[str, bool]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    results = {}
    for name, expected in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            results[name] = False
            continue
        data = path.read_bytes()
        if portable and path.suffix in {".py", ".md", ".json"} and name != "demo/candidate_before_bob.py":
            data = data.replace(b"\r\n", b"\n")
        key = "portable_sha256" if portable else "sha256"
        results[name] = hashlib.sha256(data).hexdigest() == expected[key]
    for folder in ("contract", "fixtures", "bob_sessions", "evidence"):
        actual = {p.relative_to(root).as_posix() for p in (root / folder).rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts}
        expected = {name for name in manifest["files"] if name.startswith(folder + "/")}
        results[folder + "/file_set"] = actual == expected
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Check protected artifacts without modifying them.")
    parser.add_argument("--portable", action="store_true", help="Allow checkout CRLF/LF differences in text files")
    args = parser.parse_args()
    results = check(portable=args.portable)
    for name, passed in results.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"{sum(results.values())}/{len(results)} checks passed ({'portable text' if args.portable else 'byte-exact'}).")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
