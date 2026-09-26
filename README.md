# ParityLens

A narrow debugging workflow for computer-vision engineers. ParityLens takes a
single input image, runs it through two independently-written preprocessing
pipelines (reference and candidate/serving), and uses a stage-by-stage contract
comparison to surface the first location where the outputs diverge in a
semantically meaningful way — even when shape and dtype are identical.

## Usage

```
# Run defect experiment (exits 1, reports decode/channel_order_mismatch)
python -m paritylens --fixture fixtures/defect_rgb_bgr.png

# Run clean control (exits 0, all stages pass)
python -m paritylens --fixture fixtures/control_clean.png --use-reference-as-candidate

# Verify a repaired candidate end-to-end
python -m paritylens --fixture fixtures/defect_rgb_bgr.png --verify
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All stages pass |
| 1 | Defect detected |
| 2 | Error (import failure, missing file, etc.) |

## Requirements

```
pip install -r requirements.txt
```
