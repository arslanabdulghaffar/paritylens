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

## Public RGB/BGR demo

Run `streamlit run app.py`, then run **BEFORE BOB REPAIR** and **AFTER BOB REPAIR**
to inspect the trace and download a JSON evidence report. Bob is not invoked by
the app; the repair was produced during the recorded IBM Bob IDE workflow.

`python -m demo.runner --mode both` also prints the report. The historical
candidate is an exact Git snapshot from `d0ea1fd`; AFTER uses the current candidate,
checked against repair commit `334a401`. Both run in disposable directories;
repository evidence is untouched. AFTER executes the normal core `--verify` CLI.
The current repaired candidate passes the original CLI example above; use the
demo's BEFORE mode to execute the genuine historical defect (exit code 1).

Run `python -m unittest demo.test_demo` for demo execution and UI checks.
