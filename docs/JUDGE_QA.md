# Judge Q&A

1. **What problem does ParityLens solve?** It finds where a serving preprocessing path first differs from a trusted reference, even when the final tensor has the expected shape and dtype.
2. **Why are shape and dtype insufficient?** Both describe structure. RGB and BGR arrays can share that structure while putting different values in each channel slot.
3. **How is this different from a normal unit test?** A well-written unit test can catch this too. ParityLens organizes comparisons across explicit boundaries and presents localization, numerical evidence, provenance and repair verification together.
4. **Why stage-by-stage comparison?** The first comparable failure narrows investigation. Downstream arrays are recorded, but parity after a first failure is labeled Not evaluated.
5. **Why trust the reference?** It is a human-approved Pillow implementation under a frozen contract. It is the experiment's ground truth, not something the tool independently proves correct.
6. **What prevents silently changing the contract?** Repository rules prohibit it; stored hashes detect changes to the contract, checks and evidence. These are review controls, not tamper-proof protection against someone replacing the whole repository.
7. **What did IBM Bob do?** The recorded IDE workflow covers the plan/contract, deterministic comparison implementation, evidence-based diagnosis and explicit BGR-to-RGB candidate repair. The four original session summaries and Git provenance support that history.
8. **Did Bob repair every scenario?** No. Only the original RGB/BGR repair is attributed to Bob. Scaling and normalization are authored controlled evaluation variants.
9. **Which scenario is historical?** The original RGB/BGR case uses the exact pre-repair candidate snapshot and the current Bob-repaired candidate on the original fixture. The matrix also runs that historical snapshot on additional synthetic inputs.
10. **Which scenarios are controlled?** Missing division by 255, incorrect normalization mean/std, and independent clean controls. A passing control is not an additional Bob repair.
11. **Why synthetic data?** It makes inputs reproducible and channel semantics observable without private image data. The fixtures deliberately meet the contract's probe precondition.
12. **Does it require model training?** No. This prototype compares preprocessing arrays before model inference.
13. **Does it require a GPU?** No. Its Python, NumPy, Pillow and OpenCV paths run on CPU.
14. **How does it know the root cause?** It localizes the first violating boundary and exposes probes and source locations. The Bob diagnosis used that evidence; boundary localization alone is not a proof of cause.
15. **What does classification mean?** Supported labels describe a channel-swap probe pattern or a first numerical failure at scaling/normalization. The frozen channel heuristic can label a red/blue-swapped probe even if green also changes.
16. **What about unsupported mismatches?** A mismatch can remain unclassified while still failing. Missing/unknown evidence and invalid inputs must fail visibly; the adapter rejects non-finite and object arrays rather than silently accepting them.
17. **Could it work with PyTorch/TensorFlow?** Potentially, with reviewed boundary instrumentation, comparable semantics and approved contracts. Those integrations are not implemented or evaluated here.
18. **What are the limitations?** A narrow synthetic set, fixed 224x224 inputs, an admissible asymmetric probe, no numerical resize, limited labels and a human-approved reference. It does not establish general production accuracy.
19. **Why not compare final tensors?** Value comparison there can detect the mismatch. Earlier comparisons tell the developer where it first appears. The measured baseline uses only final shape and dtype, not final tensor values.
20. **What are the measured results?** On 60 cases per run from 15 fixtures and four scenarios: 45/45 supported defects detected, localized and classified; 15/15 clean controls pass. See CLAIMS_AUDIT.md and VALIDATION.md.
21. **What is the false-positive result?** 0/15 clean controls in this set. This is not an estimate for all production inputs.
22. **What is the runtime overhead?** The saved local benchmark measures reference, candidate, comparison and complete scenario separately, including NPY I/O. For the historical case, complete execution is 67.578 ms median and 82.357 ms p95. Startup/imports, workspace setup, rendering and core --verify are excluded; this is not end-to-end hosted latency or a deployment overhead estimate.
23. **How reproducible is it?** Two independent matrix runs match semantic results and recorded-array hashes within the measured environment. Cross-platform bitwise equality is not promised; Linux CI remains pending.
24. **Does the public app execute arbitrary repositories?** No. It runs allowlisted local implementations and fixtures in isolated temporary workspaces. There are no repository or code uploads.
25. **Is Bob running inside Streamlit?** No. The repair was produced during the recorded IBM Bob IDE workflow. The web app executes the recorded code and does not invoke Bob.
26. **What would production use require?** Broader input/framework coverage, reviewed reference ownership, representative tolerances, dependency maintenance, resource/concurrency limits and operational/security validation. None is claimed complete here.
27. **What is the developer value?** It reduces the investigation needed to locate a hidden preprocessing mismatch and leaves inspectable proof that a repair passed unchanged checks. No time-saving or financial return has been measured.
28. **What next?** Future work could add framework adapters, real resize cases and larger representative datasets after new human-approved contracts and evidence. These are proposals, not current features.
