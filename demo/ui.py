import html

import streamlit as st


def badges(result: dict) -> None:
    labels = (("Shape", "shape_check"), ("dtype", "dtype_check"), ("Parity", "parity_check"))
    st.markdown('<div class="checks">' + "".join(
        f'<span class="pill {result[key].lower()}">{label} {result[key]}</span>'
        for label, key in labels) + '</div>', unsafe_allow_html=True)


def render_trace(result: dict, candidate_label: str, stage_key: str = "stage") -> None:
    timeline = []
    for stage in result["stages"]:
        state = stage["comparison"]
        label = "Not evaluated" if state == "NOT_EVALUATED" else state
        css = state.lower() if state != "NOT_EVALUATED" else "muted"
        timeline.append(f'<div class="stage {css}"><strong>{html.escape(stage["stage"])}</strong>{label}</div>')
    st.markdown('<div class="timeline">' + ''.join(timeline) + '</div>', unsafe_allow_html=True)
    if result["shape_check"] == result["dtype_check"] == "PASS" and result["parity_check"] == "FAIL":
        st.markdown('<div class="semantic">SAME SHAPE · SAME DTYPE · DIFFERENT SEMANTIC INPUT</div>', unsafe_allow_html=True)
    elif result["parity_check"] == "PASS":
        st.success("Same shape. Same dtype. Matching values at every frozen boundary.")
    if result["first_violating_boundary"]:
        st.caption("The comparator stops at the first violation. Later arrays were recorded; their parity was not evaluated.")
    names = [s["stage"] for s in result["stages"]]
    initial = names.index(result["first_violating_boundary"]) if result["first_violating_boundary"] else 0
    selected = st.selectbox("Inspect recorded stage", names, index=initial, key=stage_key)
    stage = next(s for s in result["stages"] if s["stage"] == selected)
    st.caption(f"Probe pixel {result['probe_coordinate']} · channel slots shown as recorded")
    a, b = st.columns(2)
    for column, prefix, title in ((a, "reference", "Reference"), (b, "candidate", candidate_label)):
        with column:
            st.markdown(f"**{title}**")
            st.code(str(stage[f"{prefix}_probe"]), language=None)
            st.caption(f"Shape {stage[f'{prefix}_shape']} · {stage[f'{prefix}_dtype']}")
    maximum = stage["max_absolute_difference"]
    st.markdown(f"Maximum absolute difference: **{maximum:.7g}**" if maximum is not None else "Maximum difference: not comparable")
    st.caption("Classification: " + (stage["classification"] or ("none — passed" if stage["comparison"] == "PASS" else "not evaluated")))
    with st.expander("Source locations and recorded measurements"):
        st.text("Reference: " + str(stage["reference_source"]))
        st.text("Candidate: " + str(stage["candidate_source"]))
        st.dataframe([{"Stage": s["stage"], "Frozen comparison": s["comparison"],
                       "Shape matches": s["shape_matches"], "dtype matches": s["dtype_matches"],
                       "Max |difference|": s["max_absolute_difference"]} for s in result["stages"]],
                     hide_index=True, width="stretch")
