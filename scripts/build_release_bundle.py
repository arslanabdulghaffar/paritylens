import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PARTS = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
                 ".ruff_cache", ".cache", "cache", "dist", "tmp", "scratch", "benchmark_scratch",
                 ".idea", ".vscode", "htmlcov"}
BLOCKED_SUFFIXES = {".pyc", ".pyo", ".pyd", ".log", ".tmp", ".pem", ".key", ".pfx", ".exe", ".dll"}
TEXT_SUFFIXES = {".py", ".md", ".json", ".toml", ".yml", ".yaml", ".txt"}
SECRET_PATTERNS = (
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"(?:sk-|ghp_)[A-Za-z0-9_-]{32,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb'''(?i)(?:password|api_key|access_token|client_secret)\s*[:=]\s*["'][^"'\r\n]{16,}["']'''),
)


def prohibited(name: str) -> bool:
    path = PurePosixPath(name.lower())
    return (bool(set(path.parts) & BLOCKED_PARTS) or path.suffix in BLOCKED_SUFFIXES
            or path.name.startswith(".env") or path.name in {"secrets.toml", ".ds_store", "thumbs.db", ".coverage"})


def tracked_files(root: Path = ROOT) -> list[str]:
    result = subprocess.run(["git", "ls-files", "--cached", "-z"], cwd=root,
                            capture_output=True, check=True, timeout=15)
    return sorted(set(result.stdout.decode("utf-8").rstrip("\0").split("\0")) - {""})


def collect_files(root: Path = ROOT) -> dict[str, bytes]:
    root = root.resolve()
    files = {}
    for name in tracked_files(root):
        if prohibited(name):
            continue
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Unsafe release path: {name}")
        data = path.read_bytes()
        if path.suffix.lower() in TEXT_SUFFIXES and any(pattern.search(data) for pattern in SECRET_PATTERNS):
            raise ValueError(f"Possible credential in {name}; review before bundling")
        files[name] = data
    if not files:
        raise ValueError("No tracked project files; stage reviewed additions before building")
    return files


def build_bundle(output: Path, root: Path = ROOT) -> dict:
    files = collect_files(root)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=15)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                            capture_output=True, text=True, check=True, timeout=15)
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    important = ("app.py", "requirements.txt", "demo/candidate_before_bob.py", "demo/provenance.json",
                 "integrity/protected_manifest.json", "evaluation/results.json", "evaluation/benchmark_results.json")
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(),
                "commit_sha": commit.stdout.strip() if commit.returncode == 0 else None,
                "working_tree_dirty": bool(status.stdout.strip()),
                "included_file_count": len(files), "bundle_member_count": len(files) + 1,
                "scope": "Tracked working-tree files plus this manifest; untracked additions require staging. Local review only.",
                "important_artifact_hashes": {name: hashes[name] for name in important if name in hashes},
                "files": hashes}
    output.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    with zipfile.ZipFile(output / "paritylens-review.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr("release_manifest.json", encoded)
    (output / "release_manifest.json").write_bytes(encoded)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local review ZIP from staged/tracked files; requires Git.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    manifest = build_bundle(args.output)
    print(f"Bundled {manifest['included_file_count']} project files; manifest records hashes and dirty state.")


if __name__ == "__main__":
    main()
