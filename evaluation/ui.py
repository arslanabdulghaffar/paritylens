import json
import logging
from html import escape

import streamlit as st

from demo.runner import ROOT
from demo.ui import badges, render_trace
from evaluation.fixtures import load_manifest
from evaluation.report import validate_suite
from evaluation.runner import input_fingerprint, run_scenario
from evaluation.scenarios import get_scenario
from ui.components import section


def render_controlled(scenario_id: str, contract: dict) -> None:
    scenario = get_scenario(scenario_id)
    st.markdown('<p class="supporting-note">Controlled evaluation scenario</p>', unsafe_allow_html=True)
    st.subheader(scenario.title)
    st.write(scenario.description)
    fixtures = {item["id"]: item for item in load_manifest()["fixtures"]}
    fixture_id = st.selectbox("Evaluation fixture", list(fixtures), key="evaluation_fixture")
    fixture = fixtures[fixture_id]
    st.caption(f"Pillow RGB reference · controlled OpenCV candidate · frozen contract v{contract['version']}")
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
                    st.session_state[f"evaluation_trace_{selection}"] = mode
                    st.session_state[f"evaluation_stage_{selection}"] = selected[mode]["result"]["observed_first_boundary"] or "decode"
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
    st.subheader("Controlled pipeline trace")
    available = [mode for mode in ("defect", "control") if mode in selected]
    report = None
    with st.container():
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
    st.subheader("Controlled result")
    st.markdown('<p class="supporting-note">Controlled ParityLens evaluation scenario. These runs are not historical repairs.</p>', unsafe_allow_html=True)
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
    with st.expander("Controlled fixture and contract"):
        st.image(str(ROOT / "evaluation/fixtures" / fixture["filename"]),
                 caption=f"{fixture['pattern']} · {fixture['image_size'][0]} × {fixture['image_size'][1]}", width=160)
        st.json(fixture, expanded=False)
        st.caption(f"Frozen contract v{contract['version']} · no Bob repair is claimed for this scenario")


def load_summary() -> dict | None:
    try:
        suite = json.loads((ROOT / "evaluation/results.json").read_text(encoding="utf-8"))
        validate_suite(suite)
        if suite["inputs"] != input_fingerprint():
            st.warning("Evaluation artifact is stale. Run python -m evaluation.runner to refresh measured results.")
            return
    except (OSError, ValueError, KeyError, TypeError):
        st.warning("Evaluation summary is unavailable. Generate it with python -m evaluation.runner.")
        return
    return suite


def render_evidence_strip(suite: dict | None) -> None:
    if suite is None:
        return
    metrics = suite["metrics"]
    baseline = metrics["final_shape_dtype_baseline"]
    items = (
        ("ParityLens", f"{metrics['defects_detected']}/{metrics['defect_cases']}", "supported defects detected"),
        ("Final shape/dtype-only baseline", f"{baseline['naive_defects_detected']}/{baseline['defective_cases']}", "detected"),
        ("Clean controls", f"{metrics['clean_false_positives']}/{metrics['clean_cases']}", "false positives"),
    )
    st.markdown('<div class="evidence-strip">' + ''.join(
        f'<div><span>{escape(label)}</span><p><strong>{escape(value)}</strong> {escape(detail)}</p></div>'
        for label, value, detail in items) + '</div>'
        '<p class="evidence-strip-note">Saved synthetic evaluation · the baseline checks final tensor structure, not all ML monitoring tools.</p>',
        unsafe_allow_html=True)


def render_summary(suite: dict | None) -> None:
    section("Evidence at a glance", "Deterministic synthetic evaluation. Measured results, with their scope kept visible.", "evaluation-evidence")
    if suite is None:
        return
    metrics = suite["metrics"]
    values = (
        ("Supported defects detected", f"{metrics['defects_detected']}/{metrics['defect_cases']}"),
        ("First boundaries localized", f"{metrics['boundary_localization']['correct']}/{metrics['boundary_localization']['total']}"),
        ("Clean false positives", f"{metrics['clean_false_positives']}/{metrics['clean_cases']}"),
        ("Reproducibility", "MATCH" if metrics["reproducibility"]["matched"] else "DIFFERS"),
    )
    st.markdown('<div class="metric-grid">' + ''.join(
        f'<div class="evidence-metric"><strong>{escape(value)}</strong><span>{escape(label)}</span></div>'
        for label, value in values) + '</div>', unsafe_allow_html=True)
    baseline = metrics["final_shape_dtype_baseline"]
    st.markdown('<div class="baseline">'
                f'<div class="detection-pair"><div><span>ParityLens detection</span><strong>{metrics["defects_detected"]}/{metrics["defect_cases"]}</strong></div>'
                f'<div><span>Final shape/dtype-only baseline</span><strong>{baseline["naive_defects_detected"]}/{baseline["defective_cases"]}</strong></div></div>'
                '<p>Supported defects detected on the same evaluated cases. The baseline checks final tensor structure only; it does not represent all tests or ML monitoring tools.</p></div>', unsafe_allow_html=True)
    st.write(f"**{metrics['cases_evaluated']} cases per run** · {suite['fixture_count']} synthetic images · "
             f"{len(suite['scenarios'])} scenarios · {metrics['reproducibility']['runs']} independent runs")
    st.caption(f"Supported classifications: {metrics['supported_classification']['correct']}/{metrics['supported_classification']['total']} · "
               f"Clean controls passed: {metrics['clean_controls_passed']}/{metrics['clean_cases']} · Measured {suite['generated_at'][:10]}")
    st.caption(suite["disclaimer"])
