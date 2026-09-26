# Architecture

```text
Allowlisted image
   |                         |
Pillow reference        OpenCV candidate
   |                         |
decode -> geometry -> scaling -> normalization -> model_input
   |                         |
   +---- recorded NPY arrays-+
                |
        frozen comparator
                |
      first violating boundary
                |
      probes, differences, source locations

Historical repair: current candidate -> normal core --verify -> all stages PASS
```

## Frozen Bob-verified core

`contract/`, `fixtures/`, the reference/candidate pipelines, comparator, verifier,
and Bob session evidence are protected. The current candidate contains the real
recorded Bob repair. `demo/candidate_before_bob.py` is the exact historical Git
blob. It is shipped with the app; runtime does not retrieve Git history.

The comparator compares arrays as recorded, checks shape/dtype, uses exact
integer equality and contract float tolerances, and stops at the first failure.
Its probe-based RGB/BGR classification is a heuristic. It does not establish
full causal equivalence or independently diagnose every possible defect.

## Public demo and evaluation layer

`demo/runner.py` copies approved files into a temporary workspace and starts a
fixed subprocess. AFTER invokes the original CLI with `--verify`; replay alone
is not presented as repair verification.

`evaluation/` owns the two controlled candidate variants and 15 synthetic
fixtures. It reuses the frozen comparator; the adapter validates inputs and
labels numerical scaling/normalization failures by their first boundary. These
labels do not change pass/fail decisions. Clean controls run the independent
current candidate, not a reference substitution.

The matrix runs twice. Each case retains stage data, source locations, NPY
hashes, and a final shape/dtype baseline measured from actual model-input arrays.
The UI reads stored summary metrics and detects stale source/fixture fingerprints.
Uncompared downstream stages remain visibly NOT_EVALUATED.

## Engineering tools

- `integrity/`: read-only byte-exact and portable text-content checks.
- `scripts/preflight.py`: integrity, fresh historical/evaluation runs, artifact
  consistency, exports, required evidence, tests, and final integrity.
- `evaluation/benchmark.py`: warmups and repeated local timings, stored separately
  from deterministic semantic results. NPY I/O is included; process startup is not.
- `tests/`: test-only adversarial conditions; no extra public scenarios.

All pipeline evidence writes are confined to temporary workspaces. Explicit developer
commands regenerate evaluation/benchmark artifacts; the UI never rewrites code
or frozen inputs. No database, remote agent, GPU, or model inference is involved.
