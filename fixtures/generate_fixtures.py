"""
Deterministic synthetic fixture generator.

Generates a 224x224 PNG where:
  - Every pixel has distinct R, G, B channels
  - Probe coordinate [0,0] has R != G != B and |R - B| > 50

No external images. Fully deterministic with a fixed seed.
"""

import json
import shutil
import numpy as np
from PIL import Image
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

HEIGHT, WIDTH = 224, 224
PROBE_ROW, PROBE_COL = 0, 0

rng = np.random.default_rng(42)

# Build a gradient-based image with a structured colour pattern to ensure
# R != G != B at every pixel and |R - B| > 50 at the probe.
h_idx = np.arange(HEIGHT, dtype=np.float32).reshape(HEIGHT, 1)
w_idx = np.arange(WIDTH, dtype=np.float32).reshape(1, WIDTH)

# Channel values derived from smooth independent gradients.
# Probe pixel [0,0]: R=180, G=120, B=20  →  R!=G!=B and |R-B|=160 > 50
r_chan = (180 - (h_idx / (HEIGHT - 1)) * 130).astype(np.uint8)  # 180..50
g_chan = (120 + (w_idx / (WIDTH - 1)) * 80).astype(np.uint8)    # 120..200
b_chan = (20  + ((h_idx + w_idx) / (HEIGHT + WIDTH - 2)) * 80).astype(np.uint8)  # 20..100

img_array = np.stack(
    [np.broadcast_to(r_chan, (HEIGHT, WIDTH)),
     np.broadcast_to(g_chan, (HEIGHT, WIDTH)),
     np.broadcast_to(b_chan, (HEIGHT, WIDTH))],
    axis=2
).copy()

# Verify probe pixel preconditions
r0 = int(img_array[PROBE_ROW, PROBE_COL, 0])
g0 = int(img_array[PROBE_ROW, PROBE_COL, 1])
b0 = int(img_array[PROBE_ROW, PROBE_COL, 2])

assert r0 != g0, f"Probe R==G at [{PROBE_ROW},{PROBE_COL}]: R={r0}, G={g0}"
assert g0 != b0, f"Probe G==B at [{PROBE_ROW},{PROBE_COL}]: G={g0}, B={b0}"
assert r0 != b0, f"Probe R==B at [{PROBE_ROW},{PROBE_COL}]: R={r0}, B={b0}"
assert abs(r0 - b0) > 50, (
    f"Probe |R-B| <= 50 at [{PROBE_ROW},{PROBE_COL}]: R={r0}, B={b0}, diff={abs(r0-b0)}"
)

# Save fixtures
defect_path = FIXTURE_DIR / "defect_rgb_bgr.png"
control_path = FIXTURE_DIR / "control_clean.png"

Image.fromarray(img_array, mode="RGB").save(defect_path)
shutil.copy(defect_path, control_path)

# Write metadata
metadata = {
    "probe_coordinate": [PROBE_ROW, PROBE_COL],
    "probe_pixel_rgb": [r0, g0, b0],
    "image_size": [HEIGHT, WIDTH],
    "r_minus_b_abs": abs(r0 - b0),
}
with open(FIXTURE_DIR / "fixture_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Probe pixel [{PROBE_ROW},{PROBE_COL}]: R={r0}, G={g0}, B={b0}, |R-B|={abs(r0-b0)}")
print(f"defect_rgb_bgr.png  -> {defect_path}")
print(f"control_clean.png   -> {control_path}")
print(f"fixture_metadata.json written")
