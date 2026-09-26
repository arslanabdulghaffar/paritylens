from html import escape

import streamlit as st


def section(title: str, description: str, anchor: str = "") -> None:
    st.markdown(f'<section class="section-head" id="{escape(anchor)}"><h2>{escape(title)}</h2>'
                f'<p>{escape(description)}</p></section>', unsafe_allow_html=True)


def hero() -> None:
    st.markdown("""
<div class="brand"><span class="parity-mark" aria-hidden="true"></span><span class="brand-name">ParityLens</span><span class="brand-meta">NEURALFOUNDRY / DEVELOPER TOOLS</span></div>
<div class="hero">
  <div><div class="eyebrow">Trust the input. Prove the repair.</div>
    <h1>Same shape.<br>Same dtype.<br><span class="hero-emphasis">Wrong model input.</span></h1>
    <p class="hero-subtitle">Find where the model's input changed. Then prove the repair.</p>
    <p class="hero-description">Stage-by-stage preprocessing parity for computer-vision pipelines.</p>
  </div>
  <div class="pattern"><div class="pattern-title">Historical case summary</div>
    <div class="pattern-row"><span>SHAPE</span><span class="status-pass">PASS</span></div>
    <div class="pattern-row"><span>DTYPE</span><span class="status-pass">PASS</span></div>
    <div class="pattern-row"><span>SEMANTIC PARITY</span><span class="status-fail">FAIL</span></div>
    <p class="pattern-note">Recorded RGB/BGR defect · not a live result.<br>Run the preserved historical candidate below to reproduce it.</p>
  </div>
</div>
""", unsafe_allow_html=True)


def journey(before: dict | None, after: dict | None) -> None:
    verified = after and after["verification_state"] == "PASS"
    items = (("01", "Reproduce hidden bug", "Real historical candidate", "active"),
             ("02", "Locate first bad boundary", before["first_violating_boundary"] or "No violation" if before else "Follow the recorded trace", "active" if before else ""),
             ("03", "Verify Bob repair", "Verified with unchanged checks" if verified else "Normal candidate · no intervention", "complete" if verified else "active" if before else ""))
    st.markdown('<div class="journey">' + ''.join(
        f'<div class="journey-step {state}"><small>STEP {number}</small><strong>{escape(title)}</strong><span>{escape(detail)}</span></div>'
        for number, title, detail, state in items) + '</div>', unsafe_allow_html=True)


def bob_story() -> None:
    section("One real defect. One recorded repair.", "The historical RGB/BGR case follows the recorded IBM Bob IDE workflow.")
    steps = (("Historical candidate", "OpenCV decoded BGR."), ("ParityLens evidence", "The first mismatch appeared at decode."),
             ("IBM Bob diagnosis", "Channel order explained the evidence."), ("Minimal repair", "Explicit BGR → RGB conversion."),
             ("Frozen verification", "The same checks tested the repair."))
    st.markdown('<div class="story">' + ''.join(
        f'<div class="story-step"><small>{index:02}</small><strong>{escape(title)}</strong><p>{escape(detail)}</p></div>'
        for index, (title, detail) in enumerate(steps, 1)) + '</div>', unsafe_allow_html=True)
    st.code("cv2.imread(...)\n        ↓\ncv2.cvtColor(..., cv2.COLOR_BGR2RGB)", language=None)
    st.markdown("**Repair produced during the recorded IBM Bob IDE workflow.** This app runs the recorded code; it does not invoke Bob.")


def footer() -> None:
    st.markdown('<footer class="footer"><strong>ParityLens / NeuralFoundry</strong><span>Built with IBM Bob 2.0 · recorded IDE workflow</span>'
                '<span>Deterministic local evidence</span><span>No external model API required</span></footer>', unsafe_allow_html=True)
