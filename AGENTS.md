# AGENTS.md — ParityLens Immutability Rules

## Purpose

This file encodes the rules that govern how Bob and any automated agent must
behave when working inside the ParityLens repository. These rules exist to
ensure that a verified repair is meaningful and that evidence cannot be
fabricated by relaxing constraints.

---

## Rule 1 — Reference behaviour is human-approved

The reference pipeline (`paritylens/pipelines/reference.py`) and every stage
it contains represent the ground truth for correct preprocessing.

**Agents must not modify any file in `paritylens/pipelines/reference.py`.**

A change to the reference pipeline is not a repair. It is a redefinition of
correctness. Any such change requires explicit human approval and a new
contract version.

---

## Rule 2 — Candidate code cannot redefine the expected result

When a defect is detected, the fix must be applied to the candidate pipeline
(`paritylens/pipelines/candidate.py`). The fix must bring the candidate output
into alignment with the reference output.

**Agents must not modify the reference pipeline to match the candidate output.**

---

## Rule 3 — Comparison policy cannot be modified during repair

The contract file (`contract/preprocessing_contract.json`) and the comparator
(`paritylens/comparator.py`) define what counts as a passing result.

**Agents must not modify `contract/preprocessing_contract.json` or
`paritylens/comparator.py` during a repair cycle.**

Widening tolerances, removing stages from the stage map, or disabling checks
to make a repair pass is forbidden without a new human-approved contract
version.

The `comparator_policy` field in the contract is an explicit human-readable
reminder: `compare_recorded_arrays_as_is__no_channel_reorder__no_value_transform`.
The comparator must never reorder channels, transpose arrays, renormalize values,
or otherwise alter either the reference or candidate arrays before comparison.

---

## Rule 4 — Fixtures cannot be changed to make a repair pass

Synthetic fixtures (`fixtures/`) are fixed inputs. Their pixel values are
part of the experiment definition.

**Agents must not modify or replace fixture files during a repair cycle.**

If a fixture is genuinely incorrect, that is a separate human-approved action
that produces a new fixture version with a documented rationale.

---

## Rule 5 — The verifier cannot be weakened during repair

The verification script (`paritylens/verifier.py`) checks that a normal
candidate run, with no diagnostic intervention, produces output that satisfies
the contract.

**Agents must not modify `paritylens/verifier.py` during a repair cycle.**

---

## Rule 6 — Diagnostic replay is not equivalent to verified repair

Running the comparator against saved `.npy` artefacts (replay mode) is a
diagnostic tool. It does not constitute a verified repair.

**A repair is only verified when `python -m paritylens --verify` runs the full
candidate pipeline end-to-end (no cached artefacts) and the comparator passes
all stages.**

---

## Rule 7 — Verified repair requires a normal candidate run with intervention disabled

The `--verify` flag runs the candidate pipeline without any patching, monkey-
patching, or stage injection. The candidate code must be genuinely fixed.

**Agents must not use runtime patching to pass verification.**

---

## Rule 8 — Unsupported or ambiguous cases must remain visible

If the comparator encounters a stage that is not in the approved stage map, or
a fixture that violates a contract precondition, it must emit a visible warning
and exit with a non-zero code.

**Agents must not silently skip ambiguous stages or suppress warnings to
produce a clean run.**

---

## Scope of agent autonomy

Bob may:
- Read all files in the repository.
- Propose changes to `paritylens/pipelines/candidate.py`.
- Run `python -m paritylens` and `python -m paritylens --verify`.
- Inspect evidence artefacts in `evidence/`.

Bob must not (without explicit human approval):
- Modify the reference pipeline.
- Modify the contract file.
- Modify the comparator or verifier.
- Modify fixtures.
- Modify this AGENTS.md file.
