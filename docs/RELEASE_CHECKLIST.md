# Release checklist

Use at the actual release commit. Local evidence is in FINAL_VALIDATION.md; rerun after changes. Unchecked boxes are not assertions of completion.

## Repository

- [ ] Confirm clean branch and `git status --short` after the final local commit.
- [ ] Record and approve the exact release commit SHA.
- [x] Review tracked source/docs and common credential patterns; record limits in PUBLIC_RELEASE_AUDIT.md.
- [ ] Human review for secrets/PII in screenshots and Git history; confirm publication is appropriate.
- [x] No prohibited cache/venv artifacts tracked; ignore local scratch and release output.
- [x] Protected integrity passes locally.
- [x] README run instructions, scope and measured claims checked.
- [ ] Human decides project license and reviews dependency/evidence publication rights.

## Testing

- [x] Existing tests and new release-tool tests pass in a fresh environment.
- [x] Full evaluation runs twice and matches saved semantic results.
- [x] Preflight passes through the one-command final review.
- [x] Strict and portable integrity checks pass locally.
- [x] Streamlit AppTest and headless HTTP startup pass.
- [x] CI YAML and commands reviewed statically.
- [ ] GitHub CI passes remotely on the reviewed commit.

## Deployment — human steps

- [ ] Push reviewed code only after publication review.
- [ ] Run and inspect remote CI.
- [ ] Confirm platform availability, then deploy Streamlit using DEPLOYMENT.md.
- [ ] Verify the public URL in a signed-out browser.
- [ ] Smoke-test desktop/mobile layout, keyboard controls and contrast.
- [ ] Run BEFORE/AFTER and controlled cases; download and inspect the actual JSON report.

## Bob evidence

- [x] Four required original session screenshots present and hash-checked.
- [x] Bob wording attributes only the original recorded RGB/BGR repair.
- [x] No fake or remote Bob invocation added.
- [ ] Human approves screenshot privacy/rights and organizer publication requirements.

## Submission

- [x] Project-description draft, technology/Bob explanations, measured results and limitations prepared.
- [ ] Adapt text to the real form's character limits and confirm all claims.
- [ ] Public repository link approved and accessible.
- [ ] Live demo URL approved and accessible.
- [ ] Record video; review and publish approved video URL.
- [ ] Capture/review the cover image and permitted screenshots.
- [ ] Confirm technology, Bob, results and limitations wording in the final form.

## Final human checks

- [ ] Actual video is under the platform's duration limit.
- [ ] Every public link works without the author's signed-in session.
- [ ] Submission form is saved/submitted and confirmation retained.
- [ ] Final deadline and timezone checked manually against organizer instructions.

Nothing here authorizes an automated push, deployment or submission. The local ZIP is a review artifact, not a published release.
