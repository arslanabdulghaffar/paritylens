import json
import logging

import streamlit as st

from demo.report import report_json
from demo.runner import FIXTURE, ROOT, check_integrity, provenance, run_demo
from demo.ui import badges, render_trace, timeline
from evaluation.ui import load_summary, render_controlled, render_evidence_strip, render_summary
from ui.components import bob_story, footer, hero, journey, section
from ui.theme import apply_theme


def execute(mode: str) -> None:
    st.session_state["scenario_selector"] = "historical_rgb_bgr"
    st.session_state.pop(mode, None)
    st.session_state.pop("execution_error", None)
    try:
        with st.spinner("Executing pipelines and frozen comparisons…"):
            st.session_state[mode] = run_demo(mode)
        st.session_state["trace_mode"] = mode
        st.session_state["stage"] = st.session_state[mode]["first_violating_boundary"] or "decode"
    except Exception:
        st.session_state["execution_error"] = "Execution could not complete. Check the local server log, dependencies and source integrity, then rerun."
        logging.exception("ParityLens demo failed")


def select_scenario(scenario: str) -> None:
    st.session_state["scenario_selector"] = scenario


def proof_card(mode: str, result: dict | None) -> None:
    title = "Before · hidden mismatch" if mode == "before" else "After · repaired candidate"
    if mode == "after" and result and result["verification_state"] == "PASS":
        title = "After · verified repair"
    st.markdown("### " + title)
    st.write("Exact historical candidate" if mode == "before" else "Current Bob-repaired candidate")
    if not result:
        st.info("Not run yet. Reproduce the hidden bug above." if mode == "before" else "Not run yet. Verify the repaired candidate below.")
        return
    badges(result)
    if result["first_violating_boundary"]:
        st.markdown(f"First violation: **`{result['first_violating_boundary']}`**")
        st.write("Classification: `" + str(result["classification"]) + "`")
    else:
        passed = sum(stage["comparison"] == "PASS" for stage in result["stages"])
        st.markdown(f"**{passed} / {len(result['stages'])} boundaries passed**")
    if mode == "after":
        st.write("Normal end-to-end verification: **" + result["verification_state"] + "**")
        st.caption("Intervention disabled · same frozen checks")
    st.caption("Executed " + result["executed_at"][:19].replace("T", " ") + " UTC")


def historical_demo() -> None:
    before, after = st.session_state.get("before"), st.session_state.get("after")
    section("A hidden bug. An inspectable repair.", "GUIDED DEMO / Historical RGB/BGR · Pillow reference vs OpenCV candidate", "guided-demo")
    journey(before, after)
    st.markdown("### Follow the input through the pipeline")
    available = [name for name in ("before", "after") if st.session_state.get(name)]
    if available:
        mode = st.radio("Execution", available, format_func=str.upper, horizontal=True, key="trace_mode")
        render_trace(st.session_state[mode], "Historical candidate" if mode == "before" else "Repaired candidate")
    else:
        timeline(None)
        st.info("Reproduce the hidden bug to see real stage results and channel values. No live execution has run yet.")
    bob_story()
    section("The proof is the comparison.", "Run both candidates. Keep the reference, contract, comparator, verifier and fixtures unchanged.")
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        proof_card("before", before)
    with right, st.container(border=True):
        proof_card("after", after)
        st.button("VERIFY BOB REPAIR", key="run_after", on_click=execute, args=("after",), width="stretch")
    st.caption("Shape and dtype checks cover all recorded stages, including the final model input.")


def failure_modes() -> None:
    section("Explore additional failure modes", "CONTROLLED EVALUATION / Authored scenarios, separate from the historical Bob repair.", "failure-modes")
    for column, scenario, title, description in zip(
        st.columns(2, gap="medium"), ("scaling_mismatch", "normalization_mismatch"),
        ("Scaling drift", "Normalization drift"),
        ("Correct channel order. Incorrect value scale.", "Correct early stages. Incorrect mean and standard deviation."),
    ):
        with column, st.container(border=True):
            st.markdown('<p class="supporting-note">CONTROLLED EVALUATION</p>', unsafe_allow_html=True)
            st.markdown("### " + title)
            st.write(description)
            st.button("Explore " + title.lower(), key="choose_" + scenario, on_click=select_scenario,
                      args=(scenario,), width="stretch")
    with st.expander("Scenario navigation"):
        st.selectbox("Active scenario", ("historical_rgb_bgr", "scaling_mismatch", "normalization_mismatch"),
                     format_func=lambda value: {"historical_rgb_bgr": "RGB/BGR channel order · Historical Bob case",
                                                "scaling_mismatch": "Scaling mismatch · Controlled evaluation",
                                                "normalization_mismatch": "Normalization mismatch · Controlled evaluation"}[value],
                     key="scenario_selector")
    scenario = st.session_state["scenario_selector"]
    if scenario != "historical_rgb_bgr":
        st.button("Return to the historical Bob case", key="return_historical", on_click=select_scenario,
                  args=("historical_rgb_bgr",))
        render_controlled(scenario, contract)


def technical_evidence() -> None:
    section("Evidence you can inspect.", "Provenance, unchanged artifacts and execution reports.", "technical-evidence")
    with st.expander("Technical evidence · contract, provenance and verification"):
        st.markdown(f"**Frozen contract v{contract['version']} · integrity PASS**")
        st.write("Historical BEFORE: " + manifest["before_commit"])
        st.write("Bob repair: " + manifest["repaired_commit"])
        st.caption(manifest["hash_policy"])
        st.json(manifest, expanded=False)
        st.json(integrity, expanded=False)
        st.markdown("**Original synthetic fixture**")
        st.image(str(ROOT / FIXTURE), caption="Historical RGB/BGR input · 224 × 224", width=160)
        st.markdown("**Recorded Bob session evidence**")
        st.write("Four original session summaries remain in bob_sessions/. They are not embedded here; public screenshot use requires human review.")
        st.code("\n".join(path.relative_to(ROOT).as_posix() for path in sorted((ROOT / "bob_sessions").glob("*.png"))), language=None)
        before, after = st.session_state.get("before"), st.session_state.get("after")
        if after:
            st.markdown("**Normal verification command and output**")
            st.code(after["verification"]["command"], language="bash")
            st.code(after["verification"]["stdout"], language=None)
            if after["verification"]["stderr"]:
                st.warning(after["verification"]["stderr"])
        if before and after:
            st.download_button("Download historical evidence · JSON", report_json(before, after, manifest),
                               file_name="paritylens-rgb-bgr-evidence.json", mime="application/json", width="stretch")
        else:
            st.caption("Run both historical comparisons to enable the JSON evidence download.")


st.set_page_config(page_title="ParityLens · Preprocessing parity", page_icon="◧", layout="wide")
apply_theme()
manifest = provenance()
integrity = check_integrity()
hero()
if not all(integrity.values()):
    st.error("Source integrity check failed. Restore the approved experiment before executing.")
    st.write([name for name, matches in integrity.items() if not matches])
    st.stop()
contract = json.loads((ROOT / "contract/preprocessing_contract.json").read_text(encoding="utf-8"))

primary, secondary, _ = st.columns([1.3, 1, 1.2])
with primary:
    st.button("REPRODUCE HIDDEN BUG", key="run_before", type="primary", width="stretch", on_click=execute, args=("before",))
with secondary:
    st.markdown('<a class="evidence-link" href="#evaluation-evidence" target="_self">EXPLORE EVIDENCE ↗</a>', unsafe_allow_html=True)
evaluation_summary = load_summary()
render_evidence_strip(evaluation_summary)
if st.session_state.get("execution_error"):
    st.error(st.session_state["execution_error"])
if st.session_state.get("scenario_selector", "historical_rgb_bgr") == "historical_rgb_bgr":
    historical_demo()
else:
    st.info("You're exploring a controlled evaluation below. Reproduce the hidden bug to return to the historical Bob story.")
failure_modes()
render_summary(evaluation_summary)
technical_evidence()
footer()
