"""
Streamlit UI for the Atrium family-office RAG.

Presentation only: secrets bridge, answer/decline states, and source cards
with per-record confidence. Retrieval and grounding live in engine.py.
"""

import os
import html
import streamlit as st

st.set_page_config(
    page_title="Atrium — Family Office Intelligence",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Bridge Streamlit Cloud secrets into os.environ so engine.py can stay unchanged.
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

import engine  # noqa: E402

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

#MainMenu, footer, header, [data-testid="stStatusWidget"] {visibility:hidden}
.stApp {
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, #E8E4D8 0%, transparent 55%),
    #F6F4EE;
}
.block-container {max-width:760px; padding-top:2.75rem; padding-bottom:3.5rem}
html, body, [class*="css"] {font-family:'Inter',system-ui,sans-serif; color:#16211C}

/* —— Header —— */
.atrium-head {margin-bottom:1.75rem}
.atrium-head .brand {
  display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;
}
.atrium-head h1 {
  font-family:'Fraunces',serif; font-weight:600; font-size:34px;
  color:#1F4438; margin:0; letter-spacing:-0.02em; line-height:1.15;
}
.atrium-head .tag {
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  letter-spacing:.14em; text-transform:uppercase; color:#9A7B4F;
}
.atrium-head p {
  color:#5C6660; font-size:15px; line-height:1.55;
  margin:10px 0 0; max-width:52ch;
}

/* —— Search —— */
div[data-testid="stForm"] {
  background:#fff; border:1px solid #E4DFD3; border-radius:16px;
  padding:18px 18px 14px; margin-bottom:10px;
  box-shadow:0 1px 0 rgba(31,68,56,.04);
}
div[data-testid="stForm"] [data-testid="stTextInput"] > div > div {
  background:#F9F7F2 !important; border-radius:10px !important;
}
div[data-testid="stForm"] input {
  font-size:16px !important; color:#16211C !important;
  caret-color:#1F4438;
}
div[data-testid="stForm"] input::placeholder {color:#8A8A82 !important}
.stButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
  background:#1F4438 !important; border-color:#1F4438 !important;
  color:#fff !important; font-weight:500 !important;
  border-radius:10px !important; min-height:42px !important;
  padding:0 22px !important; letter-spacing:.01em;
  transition:background .15s ease, transform .12s ease !important;
}
.stButton > button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
  background:#16352B !important; border-color:#16352B !important;
  transform:translateY(-1px);
}

/* —— Example chips —— */
.atrium-hints {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  letter-spacing:.12em; text-transform:uppercase; color:#8A8A82;
  margin:18px 0 10px;
}
div[data-testid="stHorizontalBlock"] button[kind="secondary"],
div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-secondary"] {
  background:#fff !important; border:1px solid #E4DFD3 !important;
  color:#3D4A44 !important; font-size:13px !important; font-weight:400 !important;
  border-radius:10px !important; min-height:36px !important;
  padding:6px 14px !important; white-space:normal !important;
  line-height:1.35 !important; text-align:left !important;
  transition:border-color .15s ease, background .15s ease, color .15s ease !important;
}
div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover,
div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-secondary"]:hover {
  border-color:#1F4438 !important; background:#F0EEE6 !important; color:#1F4438 !important;
}

/* —— Result —— */
.atrium-asked {
  font-family:'IBM Plex Mono',monospace; font-size:12px; color:#5C6660;
  margin:28px 0 12px; line-height:1.45;
  animation:atrium-in .35s ease both;
}
.atrium-asked strong {color:#1F4438; font-weight:500}
.atrium-answer {
  background:#fff; border:1px solid #E4DFD3; border-radius:14px;
  padding:24px 26px; border-left:3px solid #1F4438; margin-top:4px;
  animation:atrium-in .4s ease both;
}
.atrium-answer.declined {border-left-color:#9A7B4F}
.atrium-answer .eyebrow {
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  letter-spacing:.14em; text-transform:uppercase; color:#9A7B4F;
  margin-bottom:12px; display:flex; align-items:center; gap:8px;
}
.atrium-answer .eyebrow .dot {
  width:6px; height:6px; border-radius:50%; background:#9A7B4F; flex-shrink:0;
}
.atrium-answer:not(.declined) .eyebrow .dot {background:#2E7D5B}
.atrium-answer .body {
  font-family:'Fraunces',serif; font-size:20px; line-height:1.55; color:#16211C;
}
.atrium-answer.declined .body {
  font-family:'Inter',sans-serif; font-size:15.5px; line-height:1.6; color:#5C6660;
}

.atrium-srch {
  font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.14em;
  text-transform:uppercase; color:#5C6660; margin:28px 0 12px;
  animation:atrium-in .45s ease both;
}
.atrium-source {
  background:#fff; border:1px solid #E4DFD3; border-radius:12px;
  padding:15px 17px; margin-bottom:10px;
  animation:atrium-in .5s ease both;
  transition:border-color .15s ease;
}
.atrium-source:hover {border-color:#C9C2B4}
.atrium-source .top {
  display:flex; justify-content:space-between; align-items:center;
  gap:14px; margin-bottom:6px; flex-wrap:wrap;
}
.atrium-source .entity {
  font-family:'Inter',sans-serif; font-size:13px; font-weight:600;
  color:#1F4438; letter-spacing:-0.01em;
}
.atrium-source .meta {
  display:flex; align-items:center; gap:12px; flex-wrap:wrap;
}
.atrium-source .lbl {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  letter-spacing:.1em; text-transform:uppercase;
}
.atrium-source .conf {display:flex; align-items:center; gap:9px}
.atrium-source .bar {
  width:70px; height:5px; border-radius:3px; background:#E4DFD3; overflow:hidden;
}
.atrium-source .bar i {display:block; height:100%; border-radius:3px}
.atrium-source .val {
  font-family:'IBM Plex Mono',monospace; font-size:12px;
  color:#5C6660; min-width:34px; text-align:right;
}
.atrium-source .txt {
  font-size:14.5px; color:#3D4A44; line-height:1.55; margin-top:8px;
}

.atrium-foot {
  margin-top:40px; padding-top:18px; border-top:1px solid #E4DFD3;
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  letter-spacing:.06em; color:#8A8A82; line-height:1.5;
}

@keyframes atrium-in {
  from {opacity:0; transform:translateY(8px)}
  to {opacity:1; transform:translateY(0)}
}

@media (max-width:640px) {
  .atrium-head h1 {font-size:28px}
  .atrium-answer .body {font-size:18px}
  .block-container {padding-top:1.75rem}
}
</style>
"""

EXAMPLES = [
    "Which family offices invest in biotech or life sciences?",
    "Single-family offices focused on real estate",
    "Who backs healthcare startups?",
]


def _band(score):
    if score >= 0.5:
        return "#2E7D5B", "Strong match"
    if score >= 0.29:
        return "#B5852F", "Moderate match"
    return "#8A8A82", "Weak match"


def render_result(question: str, data: dict):
    e = html.escape
    st.markdown(
        f'<div class="atrium-asked">Asked · <strong>{e(question)}</strong></div>',
        unsafe_allow_html=True,
    )

    cls = "atrium-answer" if data["answered"] else "atrium-answer declined"
    eyebrow = "Answer" if data["answered"] else "Insufficient evidence"
    st.markdown(
        f'<div class="{cls}">'
        f'<div class="eyebrow"><span class="dot"></span>{eyebrow}</div>'
        f'<div class="body">{e(data["text"])}</div></div>',
        unsafe_allow_html=True,
    )

    if not data["sources"]:
        return

    st.markdown(
        f'<div class="atrium-srch">Source records · {len(data["sources"])}</div>',
        unsafe_allow_html=True,
    )
    for i, s in enumerate(data["sources"]):
        color, label = _band(s["score"])
        pct = max(4, round(s["score"] * 100))
        entity = e(s.get("entity") or f"Record {i + 1}")
        delay = 0.05 * i
        st.markdown(
            f'<div class="atrium-source" style="animation-delay:{delay:.2f}s">'
            f'<div class="top">'
            f'<span class="entity">{entity}</span>'
            f'<span class="meta">'
            f'<span class="lbl" style="color:{color}">{label}</span>'
            f'<span class="conf"><span class="bar">'
            f'<i style="width:{pct}%;background:{color}"></i></span>'
            f'<span class="val">{s["score"]:.2f}</span></span>'
            f'</span></div>'
            f'<div class="txt">{e(s["text"])}</div></div>',
            unsafe_allow_html=True,
        )


# —— Page ——
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    '<div class="atrium-head">'
    '<div class="brand"><h1>Atrium</h1>'
    '<span class="tag">Family Office Intelligence</span></div>'
    '<p>Ask in plain language. Every answer is drawn only from verified records '
    '— and when the evidence is thin, we say so rather than guess.</p></div>',
    unsafe_allow_html=True,
)

for key, default in (
    ("pending_example", None),
    ("last_result", None),
    ("last_question", None),
    ("query_input", ""),
):
    if key not in st.session_state:
        st.session_state[key] = default

# Example chip: fill the input and search on this run.
auto_question = None
if st.session_state.pending_example:
    auto_question = st.session_state.pending_example
    st.session_state.query_input = auto_question
    st.session_state.pending_example = None

with st.form("search", clear_on_submit=False):
    q = st.text_input(
        "Question",
        label_visibility="collapsed",
        placeholder="Ask about investment focus, location, or family office type…",
        key="query_input",
    )
    submitted = st.form_submit_button("Search", type="primary")

st.markdown('<div class="atrium-hints">Try an example</div>', unsafe_allow_html=True)
cols = st.columns(len(EXAMPLES), gap="small")
for i, (col, ex) in enumerate(zip(cols, EXAMPLES)):
    with col:
        if st.button(ex, use_container_width=True, key=f"ex_{i}"):
            st.session_state.pending_example = ex
            st.rerun()

question = None
if submitted and q.strip():
    question = q.strip()
elif auto_question:
    question = auto_question

if question:
    with st.spinner("Searching verified records…"):
        data = engine.answer_question(question)
    st.session_state.last_question = question
    st.session_state.last_result = data
    render_result(question, data)
elif st.session_state.last_result and st.session_state.last_question:
    render_result(st.session_state.last_question, st.session_state.last_result)

st.markdown(
    '<div class="atrium-foot">'
    "50 verified single-family offices · answers grounded in source records · "
    "weak matches are declined, not guessed"
    "</div>",
    unsafe_allow_html=True,
)
