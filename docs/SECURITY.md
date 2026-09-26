# Public demo security review

Scope: local source review and automated negative tests, not a penetration test
or formal security certification.

## Threat surface and controls

- The UI exposes fixed scenario IDs, fixed synthetic fixture IDs, run buttons,
  trace selection, and JSON downloads. There are no uploads, repository inputs,
  user code, shell inputs, credential fields, or external model/API calls.
- Subprocess commands are fixed argument lists using the current Python
  interpreter. No shell is used. Each execution has a timeout and a disposable
  working directory; public execution does not write frozen repository evidence.
- Fixture manifests enforce the fixed 15 identifiers, exact PNG filenames,
  directory containment, hashes, and contract preconditions. Traversal strings,
  unexpected IDs, duplicates, and unsupported evidence fail visibly.
- Workers reject direct invocation in the repository. These guards prevent
  accidental writes; they are not a sandbox for untrusted local code.
- Recorded arrays are loaded with `allow_pickle=False` in the demo/evaluation
  layer. The frozen comparator uses NumPy's default pickle-disabled load; only
  trusted, freshly generated arrays reach it. Object-array rejection is tested.
- No runtime `eval`/`exec`, user-controlled subprocess program, environment dump,
  or external network request is present in the application execution path.
  Test-only `python -c` snippets are fixed repository-authored test code.
- Errors shown in the UI are generic; detailed exceptions go to local server
  logs. Repository paths in reports are relative. Streamlit telemetry is disabled.
- Integrity checking covers 28 frozen files and four directory inventories,
  including Bob screenshots and original NPY evidence. The manifest is tracked
  evidence, not a cryptographic signature or defense against a malicious maintainer.

## Findings and remaining limits

This pass added worker guards and fixture-manifest path validation, and moved
contract parsing after the UI's integrity check. It also tightened artifact
validation to reject contradictory summaries and stage sequences.

No secret or arbitrary-code input surface was found in the reviewed source.
This is not a dependency vulnerability scan. Streamlit and its dependencies
remain part of the trust boundary. Installation requires package-registry access;
normal scenario execution requires no application-level network calls.

There is no authentication, per-user quota, or global concurrency/rate limit.
Repeated run requests can consume CPU, disk, and memory. Hosting resource limits
must be reviewed before a public release. A trusted checkout and writable OS
temporary directory are required. Concurrent source edits during execution are
not a supported deployment mode.

There is no client/private or social-media dataset in the preprocessing inputs.
Bob screenshots are user-supplied IDE workflow evidence; review their visible
content before public release. The app does not invoke Bob remotely.
