# Demo script — 4 minutes 50 seconds

Before presenting: run `python scripts/preflight.py`, start `streamlit run app.py`,
and open the historical scenario. Keep the Bob Task 03/04 screenshots available.
Use the measured artifacts if performance or evaluation questions arise.

| Time | Action and explanation |
|---|---|
| 0:00–0:25 | “A serving pipeline can produce the expected tensor shape and dtype while changing what the channels mean. ParityLens compares preprocessing boundaries to show where that happened.” |
| 0:25–1:15 | Run historical BEFORE. Point to shape PASS, dtype PASS, parity FAIL. Explain that this is the actual pre-repair candidate from Git, not a recreated presentation bug. |
| 1:15–2:05 | Inspect decode. Read the measured reference and candidate probe values. Show the first red boundary, source location, and downstream NOT_EVALUATED labels. The comparator stops at the first failure. |
| 2:05–2:50 | Show recorded Bob diagnosis/repair evidence. Explain the actual `cv2.imread` BGR output and explicit `cv2.cvtColor(..., cv2.COLOR_BGR2RGB)` repair. State that Bob was used in the IDE workflow; this web app does not invoke Bob. |
| 2:50–3:25 | Run AFTER, select AFTER in Trace, and show all five PASS stages. Expand verification evidence: the normal CLI executed with unchanged checks. Download the evidence JSON. |
| 3:25–4:05 | Select controlled scaling, run its defect, show earlier PASS stages and scaling FAIL. Repeat for normalization. Say explicitly that these are authored controlled evaluations, not additional historical Bob repairs. |
| 4:05–4:30 | Show the measured 60-case summary. Refer to VALIDATION.md for the final shape/dtype baseline and local runtime timings. These numbers describe this synthetic set only. |
| 4:30–4:50 | “The value is localizing a hidden semantic mismatch and verifying the repair under unchanged checks. This is a narrow, deterministic prototype, not universal preprocessing detection.” Point to the repository and preflight command. |

Do not imitate live Bob activity or invent a dialogue. If execution fails, show
the error and investigation evidence rather than substituting prerecorded PASS
states. Leave benchmark results explicitly tied to their recorded environment.
