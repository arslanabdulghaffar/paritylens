import html

import streamlit as st


def badges(result: dict) -> None:
    labels = (("Shape", "shape_check"), ("dtype", "dtype_check"), ("Parity", "parity_check"))
    st.markdown('<div class="checks">' + "".join(
        f'<span class="pill {result[key].lower()}">{label} {result[key]}</span>'
        for label, key in labels) + '</div>', unsafe_allow_html=True)


def timeline(stages: list[dict] | None) -> None:
    items = stages or [{"stage": name, "comparison": "NOT RUN"}
                      for name in ("decode", "geometry", "scaling", "normalization", "model_input")]
    nodes = []
    for stage in items:
        state = stage["comparison"]
        css = state.lower() if state in ("PASS", "FAIL") else "muted"
        nodes.append(f'<div class="stage {css}"><strong>{html.escape(stage["stage"])}</strong>{html.escape(state.replace("_", " "))}</div>')
    st.markdown('<div class="timeline">' + ''.join(nodes) + '</div>', unsafe_allow_html=True)


def channel_probe(stage: dict, candidate_label: str) -> None:
    panels = []
    for prefix, title in (("reference", "Reference · RGB"), ("candidate", candidate_label)):
        rows = []
        for index, value in enumerate(stage[f"{prefix}_probe"]):
            label = f"{'RGB'[index]} · slot {index + 1}" if prefix == "reference" else f"Slot {index + 1}"
            width = max(0, min(100, float(value) / 255 * 100))
            different = " different" if prefix == "candidate" and value != stage["reference_probe"][index] else ""
            rows.append(f'<div class="channel"><span>{label}</span><div class="channel-track" aria-hidden="true">'
                        f'<span class="channel-fill{different}" style="width:{width:.3f}%"></span></div>'
                        f'<span class="channel-value">{html.escape(str(value))}</span></div>')
        panels.append(f'<div class="probe-panel"><h4>{html.escape(title)}</h4>{"".join(rows)}'
                      f'<p class="probe-foot">{html.escape(str(stage[prefix + "_shape"]))} · {html.escape(stage[prefix + "_dtype"])}</p></div>')
    st.markdown('<div class="probe-grid">' + ''.join(panels) + '</div>', unsafe_allow_html=True)
    reference, candidate = stage["reference_probe"], stage["candidate_probe"]
    if reference[0] != reference[2] and candidate == list(reversed(reference)):
        st.markdown("**Channel slots 1 and 3 are swapped in this recorded probe.** Compare the same slots above.")
    else:
        st.caption("Channel slots are shown as recorded. Bar lengths use the same 0–255 scale.")


def render_trace(result: dict, candidate_label: str, stage_key: str = "stage") -> None:
    timeline(result["stages"])
    if result["shape_check"] == result["dtype_check"] == "PASS" and result["parity_check"] == "FAIL":
        st.markdown('<div class="semantic"><span class="same">SAME SHAPE · SAME DTYPE</span>'
                    '<strong>DIFFERENT SEMANTIC INPUT</strong></div>', unsafe_allow_html=True)
    elif result["parity_check"] == "PASS":
        st.success("Same shape. Same dtype. Matching values at every frozen boundary.")
    if result["first_violating_boundary"]:
        st.write("The comparator stops at the first violation. Later arrays are recorded; their parity is **NOT EVALUATED**.")
    names = [stage["stage"] for stage in result["stages"]]
    initial = names.index(result["first_violating_boundary"]) if result["first_violating_boundary"] else 0
    selected = st.selectbox("Inspect recorded stage", names, index=initial if stage_key not in st.session_state else 0, key=stage_key)
    stage = next(item for item in result["stages"] if item["stage"] == selected)
    st.caption(f"Probe pixel {result['probe_coordinate']} · {selected} · values from this execution")
    if selected in ("decode", "geometry"):
        channel_probe(stage, candidate_label)
    else:
        left, right = st.columns(2)
        for column, prefix, title in ((left, "reference", "Reference"), (right, "candidate", candidate_label)):
            with column:
                st.markdown(f"**{title}**")
                st.code(str(stage[f"{prefix}_probe"]), language=None)
                st.caption(f"Shape {stage[f'{prefix}_shape']} · {stage[f'{prefix}_dtype']}")
    maximum = stage["max_absolute_difference"]
    st.write(f"Maximum absolute difference: **{maximum:.7g}**" if maximum is not None else "Maximum difference: not comparable")
    with st.expander("Source locations and recorded measurements"):
        st.write("Classification: " + (stage["classification"] or ("none — passed" if stage["comparison"] == "PASS" else "not evaluated")))
        st.text("Reference: " + str(stage["reference_source"]))
        st.text("Candidate: " + str(stage["candidate_source"]))
        st.code("Reference probe: " + str(stage["reference_probe"]) + "\nCandidate probe: " + str(stage["candidate_probe"]), language=None)
        st.dataframe([{"Stage": item["stage"], "Frozen comparison": item["comparison"],
                       "Shape matches": item["shape_matches"], "dtype matches": item["dtype_matches"],
                       "Max |difference|": item["max_absolute_difference"]} for item in result["stages"]],
                     hide_index=True, width="stretch")
