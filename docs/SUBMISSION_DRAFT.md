# Submission draft

Draft for human adaptation to the actual form and organizer limits. No submission or publication has occurred.

## Project name

ParityLens — NeuralFoundry

## Tagline

Same shape. Same dtype. Wrong model input.

## Short description

ParityLens compares computer-vision preprocessing stages to locate semantic input mismatches that shape and dtype checks miss. It shows a recorded IBM Bob RGB/BGR repair and verifies the repaired candidate against unchanged reference checks.

## Medium description

ParityLens finds the first preprocessing boundary where a serving candidate differs from a trusted reference. Its Streamlit demo exposes an RGB/BGR mismatch despite matching shape and dtype, shows the repair produced during the recorded IBM Bob IDE workflow, and verifies the real candidate with unchanged checks. A separate deterministic synthetic evaluation covers controlled scaling and normalization errors. The app runs local recorded code; it does not invoke Bob or accept arbitrary repositories.

## Full description

A computer-vision service can accept a tensor with the expected shape and dtype while receiving the wrong channel meanings or numerical values. ParityLens makes that preprocessing mismatch inspectable. It runs a human-approved reference and a candidate, compares recorded arrays at five agreed boundaries, and identifies the first violation with probes, differences and source locations.

The main demo preserves a genuine RGB/BGR defect and its repair from a recorded IBM Bob IDE workflow. BEFORE executes the exact historical candidate: structure passes, but decode fails. Bob diagnosed the channel-order mismatch and added an explicit BGR-to-RGB conversion. AFTER runs the repaired candidate end to end with intervention disabled. All five stages pass under the same frozen contract, comparator, verifier and fixtures. The Streamlit app executes recorded code; it does not invoke Bob.

A separate synthetic evaluation runs 15 deterministic fixtures across four scenarios, twice. It detects, localizes and classifies all 45 supported defective cases, passes all 15 clean controls, and reproduces semantic results and array hashes. A final shape/dtype-only baseline detects none of those 45 defects. Scaling and normalization cases are authored controlled variants, not additional historical Bob repairs.

The prototype uses Python, NumPy, Pillow, headless OpenCV and Streamlit on CPU. It needs no training or private dataset. Its value is focused debugging evidence and verification under unchanged checks. Results apply to a narrow, contract-constrained synthetic set; framework integrations, real resize drift and production validation remain future work.

## Problem

Structural tensor checks can pass while preprocessing changes what the model receives. A final output mismatch alone does not reveal the first stage responsible.

## Solution

Record comparable boundaries, compare their arrays as-is under the approved contract, inspect the first failure and verify a genuine candidate repair through a normal end-to-end run.

## How IBM Bob was used

The recorded IDE workflow produced planning/contract work, deterministic comparison implementation, diagnosis from measured evidence and the original RGB conversion repair. Git provenance and four original session summaries preserve that history. The web app does not invoke Bob. Controlled post-Bob scaling and normalization evaluations are separate authored cases.

## Technical implementation

Python with NumPy, Pillow reference preprocessing, an OpenCV candidate and Streamlit. Isolated temporary workspaces preserve original evidence. SHA-256 provenance and integrity checks protect the approved experiment. JSON reports expose measurements and origins. No training, GPU or arbitrary repository execution is required.

## Measured results

The saved matrix has 60 cases per run: 45/45 supported defects detected, 45/45 first boundaries localized, 45/45 supported classifications, 15/15 clean controls passed and 0/15 clean false positives. Two runs match, including array hashes. The final shape/dtype-only baseline detects 0/45 defects. Benchmark scope and exact local values are in VALIDATION.md; these are synthetic-set results, not production accuracy claims.

## Originality / differentiation

The prototype brings first-boundary localization, numerical/source evidence, preserved historical repair provenance and unchanged-check verification into one small reviewable workflow. It makes no claim to invent array comparison or outperform all testing or MLOps tools.

## Business / developer value

Engineers can see where preprocessing diverges and what evidence supports the repair. Reduced debugging time is an intended benefit, not a measured productivity or revenue result.

## Data used

Project-generated synthetic RGB PNGs with documented dimensions, probes and hashes. No external photographs or private/customer dataset. Original Bob session screenshots provide workflow evidence and require human publication review.

## Security/privacy

Only allowlisted local scenarios and fixtures execute. No upload, user shell command, remote Bob API or external LLM call is exposed. Human reviewers must approve screenshot publication, Git metadata and the project license. See PUBLIC_RELEASE_AUDIT.md and SECURITY.md.

## Limitations

Fixed 224x224 contract-admissible inputs, asymmetric probe requirements, no numerical resize and a limited classifier. The reference is human-approved. Labels do not prove root cause; downstream parity is not evaluated after the first failure. Linux CI and hosted behavior remain pending.

## Repository run instructions

In a Python 3.12 virtual environment, from a full reviewed Git checkout:

```bash
python -m pip install -r requirements.txt
python scripts/final_review.py
python -m streamlit run app.py
```

The public app runtime does not require Git history. Developer provenance tests and release packaging do. Use RELEASE_CHECKLIST.md before publishing; no live URL is claimed yet.

## Demo instructions

Keep the default Historical Bob case. Run BEFORE and inspect decode; shape/dtype pass while parity fails. Show the actual recorded Bob diagnosis/repair evidence. Run AFTER, select AFTER in Trace and show five PASS stages, then download the JSON report. Show scaling/normalization as controlled evaluations and finish with the measured summary. Follow VIDEO_SHOTLIST.md for the recording plan.
