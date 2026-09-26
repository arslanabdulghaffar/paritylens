import json
import logging

import streamlit as st

from demo.report import report_json
from demo.ui import badges, render_trace
from evaluation.ui import render_controlled, render_summary
from demo.runner import FIXTURE, ROOT, SCENARIO, check_integrity, provenance, run_demo

st.set_page_config(page_title="ParityLens", page_icon="◧", layout="wide")
st.markdown("""
<style>
.block-container { max-width: 1300px; padding-top: 2rem; padding-bottom: 3rem; }
h1 { letter-spacing: -.045em; padding-bottom: .15rem !important; }
h3 { letter-spacing: -.02em; }
.eyebrow { font: 600 .72rem monospace; letter-spacing: .12em; color: #758393; }
.subtitle { color: #758393; font-size: 1.08rem; margin-bottom: 1.3rem; }
.checks { display: flex; gap: 7px; flex-wrap: wrap; margin: 12px 0; }
.pill { border: 1px solid #71809655; border-radius: 5px; padding: 5px 9px;
        font: 600 .76rem monospace; }
.pass { color: #17845c; background: #17845c0d; border-color: #17845c55; }
.fail { color: #d04b42; background: #d04b420d; border-color: #d04b4255; }
.muted { color: #758393; }
.timeline { display: grid; grid-template-columns: repeat(5,minmax(0,1fr)); gap: 8px; margin: 16px 0; }
.stage { border: 1px solid #71809644; border-radius: 7px; padding: 12px 10px; font: .78rem monospace; }
.stage strong { display: block; margin-bottom: 7px; overflow-wrap: anywhere; }
.stage.pass { border-color: #17845c88; }
.stage.fail { border: 2px solid #d04b42; }
.semantic { padding: 14px 16px; border-left: 4px solid #d04b42; background: #d04b420a;
            font: 700 1rem monospace; margin: 12px 0; overflow-wrap: anywhere; }
@media(max-width: 650px) { .timeline { grid-template-columns: 1fr 1fr; } }
</style>
""", unsafe_allow_html=True)


def execute(mode: str) -> None:
    st.session_state.pop(mode, None)
    try:
        with st.spinner("Executing pipelines and frozen comparisons…"):
            st.session_state[mode] = run_demo(mode)
    except Exception:
        st.error("Execution could not complete. Check the local server log, dependencies, and source integrity, then rerun.")
        logging.exception("ParityLens demo failed")


manifest = provenance()
integrity = check_integrity()
intact = all(integrity.values())
st.markdown('<div class="eyebrow">NEURALFOUNDRY / PREPROCESSING DEBUGGER</div>', unsafe_allow_html=True)
st.title("ParityLens")
st.markdown('<div class="subtitle">Find where the model\'s input changed. Then prove the repair.</div>', unsafe_allow_html=True)
if not intact:
    st.error("Source integrity check failed. Results are unavailable until the approved experiment is restored.")
    st.write([name for name, matches in integrity.items() if not matches])
    st.stop()

contract = json.loads((ROOT / "contract/preprocessing_contract.json").read_text(encoding="utf-8"))

scenario_id = st.selectbox(
    "Scenario", ("historical_rgb_bgr", "scaling_mismatch", "normalization_mismatch"),
    format_func=lambda value: {
        "historical_rgb_bgr": "RGB/BGR channel order · Historical Bob case",
        "scaling_mismatch": "Scaling mismatch · Controlled evaluation",
        "normalization_mismatch": "Normalization mismatch · Controlled evaluation",
    }[value], key="scenario_selector",
)
if scenario_id == "historical_rgb_bgr":
    st.caption("Historical Bob case · Run BEFORE to see matching shape and dtype fail at decode. Run AFTER to verify Bob's RGB conversion with unchanged checks.")
    st.subheader("01  Compare")
    st.markdown(f"**{SCENARIO}**")
    context = st.columns(4)
    for column, label, value in zip(context,
        ("Reference pipeline", "Candidate pipeline", "Frozen contract", "Fixture"),
        ("Pillow · RGB", "OpenCV · historical / repaired", f"v{contract['version']} · human approved", "defect_rgb_bgr.png")):
        with column:
            st.caption(label)
            st.write(value)

    left, right = st.columns(2)
    for column, mode, title in ((left, "before", "BEFORE BOB REPAIR"), (right, "after", "AFTER BOB REPAIR")):
        with column, st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption("Exact historical candidate" if mode == "before" else "Current Bob-repaired candidate")
            if st.button(f"Run {title}", key=f"run_{mode}", type="primary" if mode == "before" else "secondary", width="stretch"):
                execute(mode)
            result = st.session_state.get(mode)
            if result:
                badges(result)
                if result["first_violating_boundary"]:
                    st.markdown(f"First violation: **`{result['first_violating_boundary']}`**")
                    st.caption(result["classification"])
                else:
                    st.markdown(f"**{len(result['stages'])} / {len(result['stages'])} frozen comparisons pass**")
                    st.caption("Normal candidate run · intervention disabled")
                st.caption("Executed " + result["executed_at"][:19].replace("T", " ") + " UTC")
            else:
                st.caption("Not run yet. Results appear after execution.")

    before, after = st.session_state.get("before"), st.session_state.get("after")
    st.caption("Shape and dtype badges check all recorded stages, including the final model input.")
    st.divider()
    st.subheader("02  Trace")
    image_col, trace_col = st.columns([1, 4])
    with image_col:
        st.image(str(ROOT / FIXTURE), caption="Synthetic input · 224 × 224", width="stretch")
    with trace_col:
        available = [name for name in ("before", "after") if st.session_state.get(name)]
        if not available:
            st.info("Run BEFORE to locate the first boundary where the input changes.")
            st.code("decode → geometry → scaling → normalization → model_input", language=None)
        else:
            mode = st.radio("Execution", available, format_func=lambda value: value.upper(), horizontal=True, key="trace_mode")
            result = st.session_state[mode]
            render_trace(result, "Historical candidate" if mode == "before" else "Repaired candidate")

    st.divider()
    st.subheader("03  Verify repair")
    a, b, c = st.columns(3)
    with a, st.container(border=True):
        st.caption("BEFORE")
        st.markdown("**BGR decode mismatch**")
        st.write(f"{before['parity_check']} · {before['first_violating_boundary'] or 'no violation'}" if before else "Awaiting historical execution")
    with b, st.container(border=True):
        st.caption("BOB REPAIR")
        st.markdown("**Explicit BGR → RGB conversion**")
        st.code("cv2.imread(...)\n        ↓\ncv2.cvtColor(..., cv2.COLOR_BGR2RGB)", language=None)
    with c, st.container(border=True):
        st.caption("AFTER")
        st.markdown("**" + ("All frozen checks pass" if after and after["verification_state"] == "PASS" else "Verification pending" if not after else "Verification failed") + "**")
        st.write("Final verification: " + (after["verification_state"] if after else "NOT RUN"))
    st.caption("Repair produced during the recorded IBM Bob IDE workflow. This app runs the recorded code; it does not invoke Bob.")
    st.markdown('<div class="checks">' + ''.join(f'<span class="pill pass">{label} unchanged</span>'
        for label in ("Frozen contract", "Comparator", "Verifier", "Fixtures")) + '</div>', unsafe_allow_html=True)
    with st.expander("Provenance and verification evidence"):
        st.text("Before commit: " + manifest["before_commit"])
        st.text("Repair commit: " + manifest["repaired_commit"])
        st.caption(manifest["hash_policy"])
        st.caption("The historical snapshot matches its recorded SHA-256; the current core matches the repair commit. Each run uses an isolated, byte-for-byte copy.")
        if after:
            st.code(after["verification"]["command"], language="bash")
            st.code(after["verification"]["stdout"], language=None)
            if after["verification"]["stderr"]:
                st.warning(after["verification"]["stderr"])
    if before and after:
        st.download_button("Download evidence report · JSON", report_json(before, after, manifest),
                           file_name="paritylens-rgb-bgr-evidence.json", mime="application/json", width="stretch")
    else:
        st.button("Run both comparisons to unlock the evidence report", disabled=True, width="stretch")
    st.caption("One fixture. One defect. The same frozen checks before and after.")
else:
    render_controlled(scenario_id, contract)

render_summary()
