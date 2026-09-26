import json
import logging

import streamlit as st

from demo.runner import ROOT
from demo.ui import badges, render_trace
from evaluation.fixtures import load_manifest
from evaluation.report import validate_suite
from evaluation.runner import input_fingerprint, run_scenario
from evaluation.scenarios import get_scenario


def render_controlled(scenario_id: str, contract: dict) -> None:
    scenario = get_scenario(scenario_id)
    st.caption("Controlled evaluation scenario")
    st.subheader("01  Compare")
    st.markdown(f"**{scenario.title}**")
    st.write(scenario.description)
    fixtures = {item["id"]: item for item in load_manifest()["fixtures"]}
    fixture_id = st.selectbox("Evaluation fixture", list(fixtures), key="evaluation_fixture")
    fixture = fixtures[fixture_id]
    context = st.columns(3)
    for column, label, value in zip(context, ("Reference", "Candidate", "Frozen contract"),
                                     ("Pillow · RGB", "Controlled OpenCV variant", f"v{contract['version']} · unchanged")):
        column.caption(label)
        column.write(value)
    results = st.session_state.setdefault("evaluation_runs", {})
    selection = f"{scenario_id}:{fixture_id}"
    selected = results.setdefault(selection, {})
    for column, mode, title, run_id in zip(st.columns(2), ("defect", "control"),
                                          ("CONTROLLED DEFECT", "CLEAN CONTROL"), (scenario_id, "clean_control")):
        with column, st.container(border=True):
            st.markdown(f"**{title}**")
            if st.button(f"Run {title}", key=f"eval_run_{mode}", width="stretch",
                         type="primary" if mode == "defect" else "secondary"):
                selected.pop(mode, None)
                try:
                    with st.spinner("Executing the selected evaluation case…"):
                        selected[mode] = run_scenario(run_id, fixture_id)
                except Exception:
                    st.error("Evaluation could not complete. Check the local server log; no result is inferred.")
                    logging.exception("Controlled evaluation failed")
            report = selected.get(mode)
            if report:
                case = report["result"]
                badges(case)
                st.write("First violation: " + (case["observed_first_boundary"] or "none"))
                st.caption(case["observed_classification"] or "All five frozen comparisons pass")
            else:
                st.caption("Not run yet. Results appear after execution.")
    st.caption("Shape and dtype checks cover all recorded stages. Clean control runs the independent RGB-correct candidate.")
    st.divider()
    st.subheader("02  Trace")
    image_col, trace_col = st.columns([1, 4])
    with image_col:
        st.image(str(ROOT / "evaluation/fixtures" / fixture["filename"]),
                 caption=f"{fixture['pattern']} · {fixture['image_size'][0]} × {fixture['image_size'][1]}", width="stretch")
    available = [mode for mode in ("defect", "control") if mode in selected]
    report = None
    with trace_col:
        if not available:
            st.info("Run the controlled defect to inspect its first violating boundary.")
        else:
            mode = st.radio("Execution", available, horizontal=True,
                            format_func=lambda value: "DEFECT" if value == "defect" else "CLEAN CONTROL",
                            key=f"evaluation_trace_{selection}")
            report = selected[mode]
            case = report["result"]
            st.caption(f"Expected boundary: {case['expected_first_boundary'] or 'none'} · "
                       f"Observed boundary: {case['observed_first_boundary'] or 'none'}")
            render_trace({**case, "first_violating_boundary": case["observed_first_boundary"]},
                         "Controlled candidate" if mode == "defect" else "Clean candidate",
                         stage_key=f"evaluation_stage_{selection}")
    st.divider()
    st.subheader("03  Result")
    st.caption("Controlled ParityLens evaluation scenario. These runs are not historical repairs.")
    if report:
        case = report["result"]
        if case["expectation_met"]:
            st.success("Observed result matches this evaluation scenario's expectation.")
        else:
            st.error("Unexpected evaluation result. The comparison policy has not been changed.")
        st.caption("Scaling and normalization classifications name the first numerical boundary; they do not infer a root cause.")
        st.download_button("Download scenario evidence · JSON", json.dumps(report, indent=2, allow_nan=False),
                           file_name=f"paritylens-{case['scenario']['id']}-{fixture_id}.json", mime="application/json",
                           key="evaluation_report", width="stretch")
    else:
        st.caption("Awaiting execution.")


def render_summary() -> None:
    st.divider()
    st.subheader("Deterministic synthetic evaluation")
    try:
        suite = json.loads((ROOT / "evaluation/results.json").read_text(encoding="utf-8"))
        validate_suite(suite)
        if suite["inputs"] != input_fingerprint():
            st.warning("Evaluation artifact is stale. Run python -m evaluation.runner to refresh measured results.")
            return
    except (OSError, ValueError, KeyError, TypeError):
        st.warning("Evaluation summary is unavailable. Generate it with python -m evaluation.runner.")
        return
    metrics = suite["metrics"]
    values = (
        ("Cases evaluated", str(metrics["cases_evaluated"])),
        ("Defects detected", f"{metrics['defects_detected']}/{metrics['defect_cases']}"),
        ("Boundary localization", f"{metrics['boundary_localization']['correct']}/{metrics['boundary_localization']['total']}"),
        ("Classification", f"{metrics['supported_classification']['correct']}/{metrics['supported_classification']['total']}"),
        ("Clean false positives", f"{metrics['clean_false_positives']}/{metrics['clean_cases']}"),
        ("Reproducibility", "MATCH" if metrics["reproducibility"]["matched"] else "DIFFERS"),
    )
    for column, (label, value) in zip(st.columns(6), values):
        column.metric(label, value)
    st.caption(f"{suite['fixture_count']} synthetic images · {len(suite['scenarios'])} scenarios · two independent runs. "
               f"Measured {suite['generated_at'][:10]}. {metrics['clean_controls_passed']}/{metrics['clean_cases']} clean controls pass.")
    st.caption(suite["disclaimer"])
