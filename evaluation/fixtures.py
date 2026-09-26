import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = Path(__file__).parent / "fixtures"
SEED = 20260926
PATTERNS = ("gradients", "blocks", "checker", "intensity", "noise")


def generate(directory: Path = FIXTURE_DIR) -> dict:
    """Generate 15 reproducible RGB images and their measured metadata."""
    contract = json.loads((ROOT / "contract/preprocessing_contract.json").read_text())
    width, height = contract["fixture"]["size"]
    row, col = contract["fixture"]["probe_pixel"]["coordinate"]
    y, x = np.indices((height, width))
    rng = np.random.default_rng(SEED)
    directory.mkdir(parents=True, exist_ok=True)
    entries = []
    for pattern in PATTERNS:
        for variant in range(3):
            if pattern == "gradients":
                channels = ((x + 37 * variant) % 256, (2*y + x//3) % 256, (x//2 + y + 19*variant) % 256)
                pixels = np.stack(channels, axis=-1).astype(np.uint8)
            elif pattern == "blocks":
                palette = np.array([[230, 61, 15], [30, 185, 240], [81, 17, 152], [252, 230, 99]], dtype=np.uint8)
                pixels = palette[(x//(28 + 7*variant) + 2*(y//(32 + 8*variant))) % 4]
            elif pattern == "checker":
                mask = ((x//(4 + 5*variant) + y//(4 + 5*variant)) % 2)[..., None]
                pixels = np.where(mask, [9 + variant, 34, 203], [241, 189 - variant, 23]).astype(np.uint8)
            elif pattern == "intensity":
                channels = ((x + y)//(2 + variant), (3*x + 2*y) % 256, np.where(x < width//2, 5 + variant, 245 - variant))
                pixels = np.stack(channels, axis=-1).astype(np.uint8)
            else:
                pixels = rng.integers(0, 256, (height, width, 3), dtype=np.uint8)
            # Keep every probe inside the frozen contract's observable-channel precondition.
            pixels[row, col] = [210 - 11*variant, 100 + 7*variant, 20 + 9*variant]
            name = f"{pattern}_{variant + 1}.png"
            path = directory / name
            Image.fromarray(pixels).save(path)
            entries.append({
                "id": path.stem, "filename": name, "pattern": pattern, "variant": variant + 1,
                "image_size": [width, height], "probe_coordinate": [row, col],
                "probe_pixel_rgb": pixels[row, col].tolist(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "pixel_sha256": hashlib.sha256(pixels.tobytes()).hexdigest(),
            })
    manifest = {"version": "synthetic-v1", "seed": SEED, "generator": "evaluation/fixtures.py",
                "probe_policy": "The documented probe is set to asymmetric RGB values satisfying the frozen precondition.",
                "fixtures": entries}
    (directory / "metadata.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_manifest(directory: Path = FIXTURE_DIR) -> dict:
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    expected = {f"{pattern}_{variant}" for pattern in PATTERNS for variant in range(1, 4)}
    entries = manifest["fixtures"]
    if len(entries) != len(expected) or {item["id"] for item in entries} != expected:
        raise ValueError("Unsupported or duplicate fixture entries")
    for item in entries:
        if item["filename"] != item["id"] + ".png":
            raise ValueError("Unsafe evaluation fixture filename")
        if (directory / item["filename"]).resolve().parent != directory.resolve():
            raise ValueError("Evaluation fixture escapes its directory")
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise ValueError("Invalid evaluation fixture hash")
    return manifest


if __name__ == "__main__":
    print(f"Generated {len(generate()['fixtures'])} evaluation fixtures.")
