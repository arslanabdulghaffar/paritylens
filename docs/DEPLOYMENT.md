# Deployment preflight (no deployment performed)

Entry point: `app.py`. Supported/tested interpreter: Python 3.12. Install only
`requirements.txt` into a fresh environment. No secrets, system shell programs,
GUI libraries, GPU, external data, or remote Bob/LLM API are required by runtime.
Headless OpenCV supplies the needed `cv2` functionality.

Repository-relative paths are derived from source locations. Fixed Python
subprocesses execute allowlisted modules in temporary working directories. The
public UI has no arbitrary path input. Normal execution does not write protected
evidence or code. Python bytecode caches are optional, not a required write path.

The exact historical candidate is included in the repository and integrity
checked. A test runs the original BEFORE/AFTER demo from a copy without `.git`;
Git history is not a public runtime dependency. The Git-blob provenance test
does need a full development checkout, so CI requests full history.

Committed `evaluation/results.json`, synthetic PNGs/metadata, and provenance
must be present. Artifact fingerprints detect stale code or fixture content.
Do not regenerate results at app startup. A fresh writable OS temporary
directory is required for individual runs.

Local preflight includes headless startup and HTTP health/page checks. AppTest
executes historical and controlled UI interactions. These are not browser visual
inspection or a hosted deployment test. Fresh-environment details are recorded
in ENVIRONMENT.json; command results are in PREFLIGHT.json.

CI is prepared for Ubuntu/Python 3.12, installing requirements and running
portable integrity plus the full preflight. No deployment job or secrets are
configured. The workflow has not been run on GitHub because nothing was pushed.
Official action usage: [checkout](https://github.com/actions/checkout) and
[setup-python](https://github.com/actions/setup-python).

Before publishing, review screenshot contents and publication rights, choose
hosting resource/concurrency limits, and run the first Linux CI job. This session
validated Windows locally; it does not claim a completed Linux/cloud validation.
Unpinned top-level packages may change over time; recorded versions identify the
tested environment, and failed future comparisons should be investigated rather
than automatically accepting new artifacts.
