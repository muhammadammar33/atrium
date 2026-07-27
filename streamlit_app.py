"""
Streamlit UI for the Atrium family-office RAG.

Presentation only: secrets bridge, answer/decline states, and source cards
with per-record confidence. Retrieval and grounding live in engine.py.
"""

import os
import html
import streamlit as st

st.set_page_config(page_title="Atrium — Family Office Intelligence",
                   page_icon="🏛️", layout="centered")

# Bridge Streamlit Cloud secrets into os.environ so engine.py can stay unchanged.
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

import engine  # noqa: E402  (import after the secret bridge)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500&family=IBM+Plex+Mono:wght@400;500&display=swap');
#MainMenu, footer, header {visibility:hidden}
.stApp {background:#F6F4EE}
.block-container {max-width:780px; padding-top:2.5rem}
html, body, [class*="css"] {font-family:'Inter',system-ui,sans-serif}
.atrium-head h1{font-family:'Fraunces',serif;font-weight:600;font-size:30px;
  color:#1F4438;margin:0;display:inline}
.atrium-head .tag{font-family:'IBM Plex Mono',monospace;font-size:11px;
  letter-spacing:.14em;text-transform:uppercase;color:#9A7B4F;margin-left:10px}
.atrium-head p{color:#5C6660;font-size:15px;margin:8px 0 22px;max-width:56ch}
.atrium-answer{background:#fff;border:1px solid #E4DFD3;border-radius:14px;
  padding:24px 26px;border-left:3px solid #1F4438;margin-top:8px}
.atrium-answer.declined{border-left-color:#9A7B4F}
.atrium-answer .eyebrow{font-family:'IBM Plex Mono',monospace;font-size:11px;
  letter-spacing:.14em;text-transform:uppercase;color:#9A7B4F;margin-bottom:12px}
.atrium-answer .body{font-family:'Fraunces',serif;font-size:20px;line-height:1.5;color:#16211C}
.atrium-answer.declined .body{font-family:'Inter',sans-serif;font-size:16px;color:#5C6660}
.atrium-srch{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:#5C6660;margin:26px 0 12px}
.atrium-source{background:#fff;border:1px solid #E4DFD3;border-radius:12px;
  padding:15px 17px;margin-bottom:10px}
.atrium-source .top{display:flex;justify-content:space-between;align-items:center;
  gap:14px;margin-bottom:8px}
.atrium-source .lbl{font-family:'IBM Plex Mono',monospace;font-size:10px;
  letter-spacing:.1em;text-transform:uppercase}
.atrium-source .conf{display:flex;align-items:center;gap:9px}
.atrium-source .bar{width:70px;height:5px;border-radius:3px;background:#E4DFD3;overflow:hidden}
.atrium-source .bar i{display:block;height:100%;border-radius:3px}
.atrium-source .val{font-family:'IBM Plex Mono',monospace;font-size:12px;color:#5C6660;min-width:34px;text-align:right}
.atrium-source .txt{font-size:15px;color:#16211C;line-height:1.55}
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {
  background: #1F4438 !important;
  border-color: #1F4438 !important;
}
</style>
"""


def _band(score):
    if score >= 0.5:
        return "#2E7D5B", "Strong match"
    if score >= 0.29:
        return "#B5852F", "Moderate match"
    return "#8A8A82", "Weak match"


def render_html(data):
    e = html.escape
    cls = "atrium-answer" if data["answered"] else "atrium-answer declined"
    eyebrow = "Answer" if data["answered"] else "Insufficient evidence"
    out = (f'<div class="{cls}"><div class="eyebrow">{eyebrow}</div>'
           f'<div class="body">{e(data["text"])}</div></div>')
    if data["sources"]:
        out += '<div class="atrium-srch">Source records</div>'
        for s in data["sources"]:
            color, label = _band(s["score"])
            pct = max(4, round(s["score"] * 100))
            out += (
                f'<div class="atrium-source"><div class="top">'
                f'<span class="lbl" style="color:{color}">{label}</span>'
                f'<span class="conf"><span class="bar">'
                f'<i style="width:{pct}%;background:{color}"></i></span>'
                f'<span class="val">{s["score"]:.2f}</span></span></div>'
                f'<div class="txt">{e(s["text"])}</div></div>'
            )
    return out


st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    '<div class="atrium-head"><h1>Atrium</h1>'
    '<span class="tag">Family Office Intelligence</span>'
    '<p>Ask in plain language. Every answer is drawn only from verified records '
    '— and when the evidence is thin, we say so rather than guess.</p></div>',
    unsafe_allow_html=True,
)

with st.form("search", clear_on_submit=False):
    q = st.text_input("Question", label_visibility="collapsed",
                      placeholder="e.g. Which single-family offices invest in biotech?")
    submitted = st.form_submit_button("Search", type="primary")

EXAMPLES = [
    "Which family offices invest in biotech or life sciences?",
    "Single-family offices focused on real estate",
    "Who backs healthcare startups?",
]
cols = st.columns(len(EXAMPLES))
example_clicked = None
for col, ex in zip(cols, EXAMPLES):
    if col.button(ex, use_container_width=True):
        example_clicked = ex

question = None
if submitted and q.strip():
    question = q.strip()
elif example_clicked:
    question = example_clicked

if question:
    with st.spinner("Searching the dataset…"):
        data = engine.answer_question(question)
    st.markdown(render_html(data), unsafe_allow_html=True)
