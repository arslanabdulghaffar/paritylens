import streamlit as st


def apply_theme() -> None:
    st.markdown("""
<style>
.stApp { background: #10151e; color: #edf2fa; }
.block-container { max-width: 1280px; padding-top: 4.5rem; padding-bottom: 2rem; }
[data-testid="stAppDeployButton"] { display: none; }
.brand, .section-head, .timeline, .probe-grid { scroll-margin-top: 5rem; }
h1, h2, h3 { letter-spacing: -.035em; }
h2 { font-size: 1.8rem !important; }
h3 { font-size: 1.25rem !important; }
p, li { line-height: 1.6; }
a { color: #a9bdff; }
button, a { touch-action: manipulation; }
button:focus-visible, a:focus-visible { outline: 3px solid #a9bdff !important; outline-offset: 4px; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #b6c3d6; font-size: .875rem; }
[data-testid="stCaptionContainer"] { opacity: 1; }
[data-testid="stVerticalBlockBorderWrapper"] > div { border-color: #354155 !important; border-radius: 12px; }
[data-testid="stCode"] { max-width: 100%; overflow-x: auto; }
[data-testid="stText"] { overflow-wrap: anywhere; white-space: pre-wrap; }
[data-testid="stButton"] button { min-height: 48px; border-radius: 8px; font-weight: 650; }
[data-testid="stButton"] button[kind="primary"] { background: #a9bdff; color: #10182b; border-color: #a9bdff; }
[data-testid="stButton"] button[kind="secondary"] { border-color: #53627c; }
.brand { display: flex; align-items: center; gap: 12px; margin-bottom: 30px; }
.brand-name { font-size: 1.25rem; font-weight: 750; letter-spacing: -.045em; }
.brand-meta { color: #aab7ca; font: 600 .72rem ui-monospace, monospace; letter-spacing: .1em; margin-left: auto; }
.parity-mark { display: inline-block; width: 29px; height: 26px; position: relative; }
.parity-mark::before, .parity-mark::after { content: ''; position: absolute; width: 26px; height: 7px; border: 2px solid #a9bdff; border-radius: 8px; left: 0; }
.parity-mark::before { top: 2px; }
.parity-mark::after { bottom: 2px; width: 17px; left: 9px; }
.hero { display: grid; grid-template-columns: 1.4fr 1fr; gap: 36px; align-items: center; margin-bottom: 18px; }
.eyebrow { color: #a9bdff; font: 650 .75rem ui-monospace, monospace; letter-spacing: .11em; text-transform: uppercase; margin-bottom: 10px; }
.hero h1 { font-size: clamp(2.8rem, 4.4vw, 4.25rem); line-height: 1.06; font-weight: 750; margin: 0 0 20px; padding: 0; }
.hero h1 .hero-emphasis { color: #ffb09e; }
.hero-subtitle { color: #edf2fa; font-size: 1.13rem; max-width: 530px; margin: 0 0 8px; }
.hero-description { color: #aab7ca; font-size: .95rem; margin: 0; }
.pattern { border: 1px solid #354155; border-radius: 14px; padding: 24px; background: #161e2a; }
.pattern-title { font-size: .9rem; font-weight: 650; margin-bottom: 18px; }
.pattern-row { display: flex; justify-content: space-between; gap: 10px; padding: 13px 0; border-bottom: 1px solid #354155; font: 600 .85rem ui-monospace, monospace; }
.pattern-note { color: #aab7ca; font-size: .8rem; line-height: 1.5; margin: 16px 0 0; }
.status-pass { color: #80dcb2; }
.status-fail { color: #ffb09e; }
.evidence-link { display: inline-flex; min-height: 48px; align-items: center; font-size: .85rem; font-weight: 650; text-decoration: none; }
.section-head { margin: 38px 0 14px; border-top: 1px solid #303b4d; padding-top: 30px; }
.section-head h2 { margin: 0 0 6px; padding: 0; }
.section-head p { color: #aab7ca; margin: 0; max-width: 850px; }
.journey { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 12px; margin: 12px 0 22px; }
.journey-step { border-top: 2px solid #46536a; padding: 14px 0; }
.journey-step.active { border-color: #a9bdff; }
.journey-step.complete { border-color: #80dcb2; }
.journey-step small { display: block; color: #aab7ca; font: .75rem ui-monospace, monospace; margin-bottom: 6px; }
.journey-step strong { display: block; font-size: 1rem; }
.journey-step span { display: block; color: #aab7ca; font-size: .85rem; margin-top: 5px; }
.checks { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; }
.pill { border: 1px solid #46536a; border-radius: 6px; padding: 7px 10px; font: 600 .8rem ui-monospace, monospace; }
.pass { color: #80dcb2; background: #172c28; border-color: #366658; }
.fail { color: #ffb09e; background: #322321; border-color: #a96554; }
.muted { color: #b2bfd1; background: #18212e; }
.timeline { display: grid; grid-template-columns: repeat(5,minmax(0,1fr)); gap: 18px; margin: 22px 0; }
.stage { position: relative; border: 1px solid #46536a; border-radius: 10px; padding: 22px 14px 16px; font: 650 .83rem ui-monospace, monospace; min-width: 0; }
.stage strong { display: block; margin-bottom: 14px; overflow-wrap: anywhere; color: #edf2fa; font-size: .92rem; }
.stage:not(:last-child)::after { content: '→'; position: absolute; right: -16px; top: 40%; color: #98a8bf; }
.stage.pass { border-color: #4e927b; }
.stage.fail { border: 2px solid #ef9a83; padding: 21px 13px 15px; }
.stage.fail::before { content: 'FIRST VIOLATION'; position: absolute; top: -10px; left: 8px; padding: 2px 6px; border-radius: 4px; background: #ffb09e; color: #271913; font-size: .62rem; letter-spacing: .03em; }
.semantic { border: 1px solid #9a6457; border-left: 4px solid #ffb09e; border-radius: 10px; padding: 22px 24px; background: #292021; margin: 20px 0; }
.semantic .same { color: #dac3bd; font: 600 .85rem ui-monospace, monospace; letter-spacing: .055em; }
.semantic strong { display: block; margin-top: 8px; color: #ffe2d9; font-size: clamp(1.3rem, 2.1vw, 1.9rem); line-height: 1.25; letter-spacing: -.02em; }
.probe-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 16px; margin: 16px 0; }
.probe-panel { border: 1px solid #354155; background: #161e2a; border-radius: 10px; padding: 20px; min-width: 0; }
.probe-panel h4 { font: 650 .82rem ui-monospace, monospace; color: #d8e2f2; margin: 0 0 16px; }
.channel { display: grid; grid-template-columns: 92px 1fr 60px; gap: 10px; align-items: center; margin: 14px 0; font: .85rem ui-monospace, monospace; }
.channel-track { height: 9px; border-radius: 5px; background: #354155; overflow: hidden; }
.channel-fill { display: block; height: 100%; border-radius: 5px; background: #a9bdff; }
.channel-fill.different { background: #ffb09e; }
.channel-value { text-align: right; color: #edf2fa; font-weight: 700; }
.probe-foot { font-size: .8rem; color: #aab7ca; margin: 14px 0 0; overflow-wrap: anywhere; }
.story { display: grid; grid-template-columns: repeat(5,minmax(0,1fr)); gap: 16px; margin: 20px 0; }
.story-step { border-left: 2px solid #536992; padding: 4px 10px 8px 14px; }
.story-step small { color: #a9bdff; font: .73rem ui-monospace, monospace; }
.story-step strong { display: block; font-size: .95rem; margin: 8px 0; }
.story-step p { margin: 0; color: #aab7ca; font-size: .82rem; line-height: 1.5; }
.metric-grid { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 12px; margin: 20px 0; }
.evidence-metric { border: 1px solid #354155; border-radius: 10px; background: #161e2a; padding: 20px; min-width: 0; }
.evidence-metric strong { display: block; font-size: clamp(1.5rem,2.7vw,2.3rem); color: #d5dfff; letter-spacing: -.04em; }
.evidence-metric span { display: block; color: #becbde; margin-top: 6px; font-size: .86rem; }
.baseline { display: flex; flex-wrap: wrap; align-items: baseline; gap: 12px 20px; border: 1px solid #53627c; border-radius: 10px; padding: 18px 22px; margin-bottom: 14px; }
.baseline strong { font-size: 1.8rem; color: #edf2fa; }
.baseline p { color: #aab7ca; font-size: .85rem; margin: 0; flex-basis: 100%; }
.footer { border-top: 1px solid #354155; padding-top: 24px; margin-top: 40px; display: flex; flex-wrap: wrap; gap: 10px 25px; font-size: .8rem; color: #aab7ca; }
.footer strong { color: #edf2fa; }
@media(max-width: 900px) {
  .hero { grid-template-columns: 1.2fr 1fr; gap: 20px; }
  .pattern { padding: 18px; }
  .timeline { gap: 12px; }
  .stage { padding-left: 9px; padding-right: 9px; }
  .stage:not(:last-child)::after { right: -12px; }
  .story { grid-template-columns: repeat(3,minmax(0,1fr)); }
  .metric-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
}
@media(max-width: 650px) {
  .block-container { padding: 4rem 1.1rem 2rem; }
  .brand { margin-bottom: 24px; }
  .brand-meta { font-size: .6rem; max-width: 130px; text-align: right; }
  .hero { grid-template-columns: 1fr; }
  .hero h1 { font-size: 2.8rem; }
  .pattern { padding: 16px 18px; }
  .pattern-row { padding: 8px 0; }
  .timeline { grid-template-columns: 1fr; gap: 18px; }
  .stage { padding: 17px; display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .stage strong { margin: 0; }
  .stage.fail { padding: 16px; }
  .stage:not(:last-child)::after { content: '↓'; right: 50%; top: auto; bottom: -18px; }
  .journey { grid-template-columns: 1fr; gap: 0; }
  .journey-step { padding: 10px 0; }
  .journey-step small { display: inline; margin-right: 10px; }
  .journey-step strong { display: inline; }
  .probe-grid { grid-template-columns: 1fr; }
  .story { grid-template-columns: 1fr; gap: 12px; }
  .story-step p { margin-top: 4px; }
  .story-step strong { display: inline; margin-left: 8px; }
  .semantic { padding: 18px; }
  .metric-grid { gap: 8px; }
  .evidence-metric { padding: 16px 12px; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stColumn"] { min-width: min(100%, 300px) !important; flex: 1 1 100% !important; }
}
</style>
""", unsafe_allow_html=True)
