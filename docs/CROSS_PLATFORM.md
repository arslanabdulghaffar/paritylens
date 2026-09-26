# Cross-platform and UI review

The UI findings below describe the earlier submission-preparation review. For the subsequent presentation redesign and local Chromium viewport checks, see [UI_REVIEW.md](UI_REVIEW.md). Linux execution remains pending.

## Static compatibility review

Reviewed non-protected Python source and configuration for paths, imports, process spawning, text encoding, temporary files, filename case, newlines and Git assumptions. Python sources parse successfully.

- Runtime resources resolve from `Path(__file__)` and repository-relative names. No local drive or user directory is required. Referenced filenames match their checked-in case.
- Pipeline subprocesses use the running interpreter, argument lists, explicit isolated working directories and timeouts. No `shell=True` or Windows-only shell command is used by the public app.
- Workers require the isolated-workspace marker; temporary evidence stays outside the original evidence tree. Process entry points are guarded. TemporaryDirectory handles cleanup.
- The public app uses the historical snapshot and provenance manifest without Git. Developer tests compare that snapshot to its Git blob; CI therefore uses full history. The release bundle builder also requires a Git checkout and stages new files before inclusion.
- Portable integrity permits only CRLF/LF differences in designated text. The historical snapshot remains byte-exact. Numerical evidence and image bytes are never normalized.
- Most JSON is ASCII-safe even at legacy default-encoding reads. The UI contract read and preflight captured test output are now explicitly UTF-8; no protected implementation was edited. Preflight's hosting-check import now works both as a script and as an imported module.
- Headless startup uses an ephemeral loopback port only for its local probe. A host chooses the public listening address/port. The app itself has no localhost service dependency.

## Windows execution

See FINAL_VALIDATION.md for the fresh Python 3.12 environment, exact package versions, tests, repeated matrix, integrity, AppTest and HTTP startup results. The fresh environment installs only requirements.txt and its transitive dependencies; it does not inherit system site packages.

Remote Linux execution remains pending until CI runs. Differences in native libraries or image codecs must be investigated if results differ; checks must not be weakened. No Linux execution or hosted availability is claimed.

## UI and judge-first review

The existing 1300px content cap and 1rem bold semantic message are retained. The message now permits wrapping of long content; the first-run caption explains BEFORE, decode failure and AFTER verification. The historical Bob case remains selected by default. No section, decoration, animation or feature was added.

PASS, FAIL and Not evaluated are literal labels. BEFORE has one failing decode stage and four not-evaluated stages; AFTER has five PASS labels and a success message. Status does not depend solely on color. Existing standard Streamlit buttons, selectors, radio controls, expanders and downloads remain; no custom keyboard interaction was introduced. The locked download control says exactly how to enable it.

Static CSS review confirms two timeline columns below 650px and wrapping stage names. Code uses Streamlit code blocks; detailed measurements stay in an expander. AppTest verifies behavior and repeated scenario/fixture switching, including returning to historical BEFORE/AFTER, with no exceptions or stale result leakage.

Browser inventory was empty. Desktop/mobile rendering, overflow in a real browser, tab order, screen-reader behavior and contrast were not visually verified. Human smoke tests at approximately 1440px, 1024px and 390px widths remain required; this is not an accessibility conformance claim. The 30-second introduction is a copy/flow target, not a measured usability result.

## CI static validation

The existing workflow parses with PyYAML 6.0.3 in the development environment. Reviewed triggers, read-only repository permission, Ubuntu runner, Python 3.12, full Git history, requirements installation, integrity/preflight commands and 15-minute timeout. Commands exist and require no secrets. Validation makes no deployment call. The workflow remains unchanged; action resolution and Ubuntu execution require a real remote run.

CI is prepared but not remotely validated until pushed to GitHub.
