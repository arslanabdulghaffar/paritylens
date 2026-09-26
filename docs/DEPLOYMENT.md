# Deployment guide

Human-operated guide; no deployment has been performed. Confirm account access, organizer rules and platform availability before proceeding. Do not assume a live URL exists.

## Review locally first

Use Python 3.12 in an isolated environment and a full reviewed Git checkout:

```bash
python -m pip install -r requirements.txt
python scripts/final_review.py --json-output dist/final_review.json
python -m streamlit run app.py
```

Final review calls preflight once, including tests, a two-run evaluation, provenance, integrity and headless startup, then checks docs/claims/hygiene and a temporary ZIP. It does not deploy. Git is needed for developer history tests and bundle tooling; the app runtime uses local snapshots/manifests and needs no Git history. Portable integrity tolerates designated text newline differences; use the strict checker to compare this checkout byte-for-byte.

## Streamlit Community Cloud

1. Complete RELEASE_CHECKLIST.md publication review, choose the exact commit, then manually push the reviewed repository and inspect remote CI. No push is performed by these scripts.
2. In the hosting account, create an app and select the human-confirmed GitHub owner/repository for **ParityLens**. This guide intentionally does not invent a public repository URL.
3. Select the reviewed **feature/final-submission-prep** branch, or a separately approved release branch containing the same reviewed changes. Entry point: **app.py** at repository root.
4. In Advanced settings, choose **Python 3.12** if offered. If unavailable, stop and validate another supported version before changing that expectation. Root **requirements.txt** declares NumPy, Pillow, opencv-python-headless and Streamlit. No credentials or secrets are required; leave secrets empty. Preserve `.streamlit/config.toml`.
5. Deploy only after human approval, inspect build logs and record the actual commit, dependency versions and public URL. Requirements use ranges rather than a full lockfile; future installs may resolve differently.

Repository, branch, entry-point and Python selection follow the [official Streamlit deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). Check the current UI and available versions at deployment time.

On an equivalent Python host, install requirements in an isolated environment, start `python -m streamlit run app.py --server.headless true`, and configure the required public address/port through hosting settings. Keep temporary storage writable and respect resource limits. Do not expose arbitrary shell commands or add credentials for this demo.

## Post-deployment smoke test

- Open the public URL signed out. Confirm historical RGB/BGR is default and controlled scenarios are explicitly labeled.
- Run BEFORE: shape/dtype PASS, parity FAIL, first boundary decode, channel_order_mismatch; four downstream stages Not evaluated.
- Run AFTER and select AFTER in Trace: five PASS stages, success message and actual normal --verify output. Check the recorded-IDE-workflow/no-Bob-in-app wording.
- Download JSON; inspect provenance, contract hash, BEFORE failure and AFTER verification. Test scaling/normalization and clean controls; switch scenarios/fixtures repeatedly.
- Confirm the artifact-backed summary matches CLAIMS_AUDIT.md. Review desktop/mobile layout, keyboard navigation, code overflow and readable status text. Inspect logs without posting private log content.

## Rollback

Record the last known-good commit and hosting configuration before an update. If deployment fails, stop sharing the failing URL and inspect logs. A human can deploy a reviewed rollback branch at that commit or use a normal revert commit on the deployment branch, then rerun CI and smoke tests. Do not rewrite history, alter frozen checks, or reuse a stale PASS screenshot as evidence. Roll back application code and matching artifacts together.

## Local review bundle

Stage reviewed new files before packaging; the builder uses Git's tracked-file inventory and working-tree bytes, not only committed bytes. It records whether the tree is dirty. Run:

```bash
python scripts/build_release_bundle.py
```

Outputs: `dist/paritylens-review.zip` and `dist/release_manifest.json`. The manifest records timestamp, commit if available, per-file SHA-256 and important artifact hashes. File count excludes the embedded manifest; member count includes it. Rebuild after the final commit so provenance identifies it. Both outputs are ignored. Original Bob evidence is included for local review; publication still requires human approval.

The ZIP is a source/evidence review bundle without Git history. It can run the app after installing requirements, but history-based developer tests/final review must run from the Git checkout. No hosted, remote-CI or Linux success is inferred from local Windows checks.
