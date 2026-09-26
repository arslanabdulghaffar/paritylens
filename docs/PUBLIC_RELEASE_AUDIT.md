# Public release audit

Local review on 2026-09-27, starting from `79f37de` on `feature/final-submission-prep`. This is a repository readiness review, not a formal security audit or certification.

## Scope and findings

| Check | Finding |
|---|---|
| Current tracked text/source | Reviewed the initial 97-file inventory, Python syntax, docs, configuration and result artifacts. No common credential-pattern matches or hard-coded user/workspace paths found. New release files receive the same pattern check when bundled. |
| Reachable Git history | Scanned 81 historical text blobs for common API-key, private-key and quoted credential patterns; no matches. Binary contents were not secret-scanned. |
| Private endpoints and localhost | No private service endpoint found in runtime code. The loopback address in hosting_check.py is intentional for a local health check. It is not a hosting requirement. |
| Personal information | Git author identities are present. Historical bytecode may embed build-machine paths. Do not assume absence of PII from a text-pattern scan. |
| Cache and temporary artifacts | No cache, bytecode, venv, editor state or scratch output tracked in the current tree. Seven unique old bytecode paths remain in Git history. No history rewrite performed. |
| Logs, debug output and notes | Runtime exceptions go to server logs; the UI gives a concise error. Original evidence and the protected project plan are intentional project material. No additional private notes found. |
| Public claims | Synthetic-set results are qualified; controlled cases are distinct from the original Bob repair. See CLAIMS_AUDIT.md for source checks and limitations. |
| Bob screenshots | Four original session images and their index are present and hash-protected. Their contents were not transcribed, altered, or republished in these documents. Visual privacy/publication review remains human work. |

## Safe fixes

- Expanded ignore rules for environments, caches, logs, scratch output, editor metadata, local secrets and `dist/`. Committed fixtures, results and original evidence remain included.
- Added a local bundle builder that selects tracked working-tree files, excludes prohibited artifact names, checks common credential patterns in text and rejects unsafe paths. Required evidence inclusion and ZIP hashes are checked by final review.
- Made the preflight import reusable and its captured test output explicitly UTF-8. The UI contract read is explicitly UTF-8.
- Added release, deployment, claims and submission review documents without changing the frozen experiment.

## Human review before publication

- Review the four Bob images in their original location for account names, paths, private content and publication rights. Human must confirm organizer/platform screenshot publication requirements.
- Review Git author metadata and the seven historical bytecode paths before making the full history public. The local ZIP excludes Git history; publishing a repository exposes more than publishing that ZIP.
- Decide the project's license. Dependency metadata in DATA_AND_DEPENDENCIES.md does not grant a license to the project or authorize screenshot publication.
- Confirm organizer rules, platform availability, public repository/URLs, deadline and final submission text. No credentials are needed by the current app.

Pattern scanning can miss secrets and contextual private information. No dependency vulnerability assessment, screenshot OCR, penetration test or external-service audit was performed. The local review ZIP contains the requested original Bob evidence; creating it is not publication approval.
