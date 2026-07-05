# app.py
import re
import streamlit as st
from src.vector_db import initialize_database, query_relevant_rules
from src.ai_client import review_code_with_rag

st.set_page_config(
    page_title="RAG Code Review Console",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Data setup
# ----------------------------------------------------------------------------

@st.cache_resource
def setup_db():
    return initialize_database()

collection = setup_db()
try:
    RULE_COUNT = collection.count()
except Exception:
    RULE_COUNT = 0

if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_rules" not in st.session_state:
    st.session_state.last_rules = []

# ----------------------------------------------------------------------------
# Style system
# ----------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

:root{
    --bg:#070913;
    --panel:#0d1120;
    --panel-2:#121626;
    --line:rgba(255,255,255,0.07);
    --line-strong:rgba(255,255,255,0.14);
    --text:#f3f4f7;
    --muted:#7c8496;
    --muted-2:#565d70;
    --crimson:#B80F20;
    --crimson-bright:#e8324a;
    --amber:#e8a33d;
    --green:#31b978;
    --mono: 'JetBrains Mono', ui-monospace, monospace;
    --sans: 'Inter', -apple-system, sans-serif;
}

html, body, [data-testid="stAppViewContainer"]{
    background:
        radial-gradient(ellipse 900px 500px at 15% -10%, rgba(184,15,32,0.10), transparent 60%),
        radial-gradient(ellipse 700px 500px at 100% 0%, rgba(184,15,32,0.05), transparent 55%),
        var(--bg);
    font-family: var(--sans);
    color: var(--text);
}

[data-testid="stHeader"]{ background: transparent; }
.block-container{ padding-top: 2.2rem; max-width: 1180px; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"]{
    background: linear-gradient(180deg, var(--panel) 0%, var(--bg) 100%);
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] .block-container{ padding-top: 2rem; }

.brand{
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    color: var(--crimson-bright);
    text-transform: uppercase;
    margin-bottom: 0.3rem;
    display:flex; align-items:center; gap:8px;
}
.brand-dot{
    width:7px; height:7px; border-radius:50%;
    background: var(--green);
    box-shadow: 0 0 0 3px rgba(49,185,120,0.15);
    animation: pulse 2.2s ease-in-out infinite;
    flex-shrink:0;
}
@keyframes pulse{
    0%,100%{ box-shadow: 0 0 0 3px rgba(49,185,120,0.15); }
    50%{ box-shadow: 0 0 0 6px rgba(49,185,120,0.06); }
}
.sidebar-title{
    font-family: var(--mono); font-weight: 700; font-size: 1.05rem;
    color: var(--text); margin-bottom: 1.6rem; line-height:1.4;
}

.pipeline{ margin: 0.4rem 0 1.8rem 0; }
.pipe-step{
    display:flex; gap:12px; position:relative; padding-bottom: 22px;
}
.pipe-step:last-child{ padding-bottom:0; }
.pipe-step .rail{
    display:flex; flex-direction:column; align-items:center;
}
.pipe-step .node{
    width:22px; height:22px; border-radius:6px;
    border:1px solid var(--line-strong);
    background: var(--panel-2);
    display:flex; align-items:center; justify-content:center;
    font-family: var(--mono); font-size:0.62rem; color: var(--muted);
    flex-shrink:0;
}
.pipe-step.active .node{
    border-color: var(--crimson); color: var(--crimson-bright);
    background: rgba(184,15,32,0.12);
}
.pipe-step .stem{
    width:1px; flex:1; background: var(--line-strong); margin-top:4px;
}
.pipe-step:last-child .stem{ display:none; }
.pipe-step .body{ padding-top:1px; }
.pipe-step .label{
    font-family: var(--mono); font-size:0.76rem; font-weight:600;
    color: var(--text); letter-spacing:0.03em;
}
.pipe-step .desc{
    font-size:0.74rem; color: var(--muted); margin-top:2px; line-height:1.4;
}

.meta-card{
    border:1px solid var(--line); background: var(--panel-2);
    border-radius:10px; padding:12px 14px; margin-bottom:10px;
}
.meta-row{
    display:flex; justify-content:space-between; align-items:center;
    font-family: var(--mono); font-size:0.72rem; padding: 3px 0;
}
.meta-row .k{ color: var(--muted); }
.meta-row .v{ color: var(--text); font-weight:600; }

.foot-note{
    font-family: var(--mono); font-size:0.66rem; color: var(--muted-2);
    margin-top: 2rem; line-height:1.6;
}

/* ---------- Header ---------- */
.eyebrow{
    font-family: var(--mono); font-size:0.74rem; letter-spacing:0.18em;
    color: var(--crimson-bright); text-transform:uppercase; margin-bottom:0.6rem;
}
.masthead{
    font-family: var(--mono); font-weight:800; font-size:2.35rem;
    letter-spacing:-0.02em; color: var(--text); margin:0; line-height:1.15;
}
.masthead span{ color: var(--crimson-bright); }
.subhead{
    font-family: var(--sans); color: var(--muted); font-size:0.98rem;
    margin-top:0.55rem; max-width:640px; line-height:1.55;
}
.chips-row{ display:flex; gap:8px; margin-top:1.1rem; flex-wrap:wrap; }
.tech-chip{
    font-family: var(--mono); font-size:0.68rem; padding:5px 10px;
    border:1px solid var(--line-strong); border-radius:20px; color:var(--muted);
    background: var(--panel-2);
}
hr.rule{
    border:none; border-top:1px solid var(--line); margin: 1.7rem 0 1.5rem 0;
}

/* ---------- Window chrome ---------- */
.win{
    border:1px solid var(--line); border-radius:12px; overflow:hidden;
    background: var(--panel); margin-bottom: 0.9rem;
}
.win-bar{
    display:flex; align-items:center; justify-content:space-between;
    padding: 9px 14px; background: var(--panel-2); border-bottom:1px solid var(--line);
}
.win-dots{ display:flex; gap:6px; }
.win-dots span{ width:9px; height:9px; border-radius:50%; display:inline-block; }
.d1{ background:#e8586a; } .d2{ background:#e8a33d; } .d3{ background:#31b978; }
.win-name{
    font-family: var(--mono); font-size:0.72rem; color: var(--muted); letter-spacing:0.02em;
}
.win-tag{
    font-family: var(--mono); font-size:0.64rem; color: var(--muted-2);
}
.win-body{ padding: 14px 16px 6px 16px; }

/* ---------- Textarea styling (code input) ---------- */
[data-testid="stTextArea"] textarea{
    background: var(--bg) !important;
    color: #dfe3ee !important;
    font-family: var(--mono) !important;
    font-size: 0.86rem !important;
    border: none !important;
    border-radius: 6px !important;
    line-height: 1.55 !important;
}
[data-testid="stTextArea"] textarea:focus{
    box-shadow: 0 0 0 1px var(--crimson) inset !important;
}
[data-testid="stTextArea"]{ margin-bottom: -0.2rem; }

/* ---------- Slider ---------- */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"]{
    background-color: var(--crimson) !important;
    border-color: var(--crimson) !important;
}
[data-testid="stSlider"] label p{
    font-family: var(--mono) !important; font-size: 0.76rem !important;
    color: var(--muted) !important; text-transform: uppercase; letter-spacing:0.04em;
}

/* ---------- Button ---------- */
[data-testid="stButton"] button{
    background: linear-gradient(135deg, var(--crimson) 0%, #8c0c19 100%) !important;
    color: #fff !important; border: none !important;
    font-family: var(--mono) !important; font-weight:700 !important;
    letter-spacing: 0.04em !important; text-transform: uppercase; font-size: 0.82rem !important;
    border-radius: 8px !important; padding: 0.65rem 1rem !important;
    box-shadow: 0 6px 18px rgba(184,15,32,0.28) !important;
    transition: transform 0.12s ease, box-shadow 0.12s ease !important;
}
[data-testid="stButton"] button:hover{
    transform: translateY(-1px);
    box-shadow: 0 8px 22px rgba(184,15,32,0.4) !important;
}
[data-testid="stButton"] button p{ font-family: var(--mono) !important; }

/* ---------- Rule chips ---------- */
.rule-chip{
    display:inline-flex; align-items:baseline; gap:6px;
    font-family: var(--mono); font-size:0.72rem;
    background: rgba(184,15,32,0.10); border:1px solid rgba(184,15,32,0.35);
    color:#f0a9ae; padding:5px 10px; border-radius:6px; margin: 0 6px 8px 0;
}
.rule-chip b{ color: var(--crimson-bright); }
.rule-label{
    font-family: var(--mono); font-size:0.7rem; color: var(--muted);
    text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;
}

/* ---------- Output / empty state ---------- */
.empty-state{
    border: 1px dashed var(--line-strong); border-radius:10px;
    padding: 2.6rem 1.4rem; text-align:center; color: var(--muted);
    font-family: var(--mono); font-size:0.82rem; margin: 0.4rem 0 1rem 0;
    background: repeating-linear-gradient(135deg, rgba(255,255,255,0.012) 0px, rgba(255,255,255,0.012) 10px, transparent 10px, transparent 20px);
}
.empty-state .big{ font-size:1.5rem; color: var(--muted-2); margin-bottom:0.5rem; }

.status-line{
    font-family: var(--mono); font-size:0.72rem; color: var(--green);
    display:flex; align-items:center; gap:7px; margin-bottom:10px;
}
.status-dot{ width:7px; height:7px; border-radius:50%; background: var(--green); }

[data-testid="stVerticalBlock"] h1, [data-testid="stVerticalBlock"] h2, [data-testid="stVerticalBlock"] h3{
    font-family: var(--mono) !important;
}

::-webkit-scrollbar{ width:8px; height:8px; }
::-webkit-scrollbar-thumb{ background: var(--line-strong); border-radius:4px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Sidebar — pipeline rail + system info
# ----------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div class="brand"><span class="brand-dot"></span>SYSTEM ONLINE</div>
    <div class="sidebar-title">Retrieval Pipeline</div>
    """, unsafe_allow_html=True)

    steps = [
        ("01", "RETRIEVE", "Embed the snippet and pull the nearest style-guide rules from ChromaDB."),
        ("02", "AUGMENT", "Fold matched rules into the review prompt as required context."),
        ("03", "GENERATE", "Gemini 2.5 Flash drafts the review against your code and those rules."),
    ]
    rail_html = '<div class="pipeline">'
    for num, label, desc in steps:
        rail_html += f'''
        <div class="pipe-step active">
            <div class="rail"><div class="node">{num}</div><div class="stem"></div></div>
            <div class="body"><div class="label">{label}</div><div class="desc">{desc}</div></div>
        </div>'''
    rail_html += '</div>'
    st.markdown(rail_html, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="meta-card">
        <div class="meta-row"><span class="k">MODEL</span><span class="v">gemini-2.5-flash</span></div>
        <div class="meta-row"><span class="k">VECTOR STORE</span><span class="v">ChromaDB</span></div>
        <div class="meta-row"><span class="k">RULES INDEXED</span><span class="v">{RULE_COUNT}</span></div>
        <div class="meta-row"><span class="k">REVIEWS THIS SESSION</span><span class="v">{len(st.session_state.history)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="foot-note">
    // guidelines are retrieved by semantic similarity,<br>
    // not keyword match — results vary with n.
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------

st.markdown("""
<div class="eyebrow">// Retrieval-Augmented Static Analysis</div>
<h1 class="masthead">Code Review <span>Console</span></h1>
<p class="subhead">
Paste a snippet, retrieve the corporate style rules closest to it in embedding space,
and let Gemini write the review with those rules pinned to the prompt.
</p>
<div class="chips-row">
    <span class="tech-chip">ChromaDB · vector search</span>
    <span class="tech-chip">Gemini 2.5 Flash</span>
    <span class="tech-chip">Custom style guide</span>
</div>
<hr class="rule">
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Main panels
# ----------------------------------------------------------------------------

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown("""
    <div class="win">
        <div class="win-bar">
            <div class="win-dots"><span class="d1"></span><span class="d2"></span><span class="d3"></span></div>
            <div class="win-name">source.py</div>
            <div class="win-tag">input</div>
        </div>
        <div class="win-body">
    """, unsafe_allow_html=True)

    user_code = st.text_area(
        "code_input",
        height=340,
        placeholder="def handle_response(payload):\n    try:\n        ...\n    except:\n        pass",
        label_visibility="collapsed",
    )

    lines = len(user_code.splitlines())
    chars = len(user_code)
    st.markdown(f"""
        <div class="win-tag" style="padding: 4px 2px 10px 2px;">{lines} lines · {chars} chars</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    num_rules = st.slider("Guidelines to retrieve", min_value=1, max_value=3, value=2)
    submit_button = st.button("Analyze Code →", type="primary", use_container_width=True)

with col2:
    st.markdown("""
    <div class="win">
        <div class="win-bar">
            <div class="win-dots"><span class="d1"></span><span class="d2"></span><span class="d3"></span></div>
            <div class="win-name">review.md</div>
            <div class="win-tag">output</div>
        </div>
        <div class="win-body">
    """, unsafe_allow_html=True)

    if submit_button:
        if not user_code.strip():
            st.warning("Paste some code on the left before analyzing.")
        else:
            with st.spinner("Retrieving guidelines and generating review…"):
                retrieved_rules = query_relevant_rules(user_code, n_results=num_rules)
                review_result = review_code_with_rag(user_code, retrieved_rules)

            rule_lines = [r for r in retrieved_rules.split("\n") if r.strip()]
            st.session_state.last_rules = rule_lines
            st.session_state.last_result = review_result
            st.session_state.history.append(review_result)

    if st.session_state.last_result:
        if st.session_state.last_rules:
            chips = ""
            for r in st.session_state.last_rules:
                m = re.match(r"\[RULE\s*(\d+)\]\s*(.*)", r.strip())
                if m:
                    chips += f'<span class="rule-chip"><b>RULE {m.group(1)}</b> {m.group(2)}</span>'
                else:
                    chips += f'<span class="rule-chip">{r.strip()}</span>'
            st.markdown('<div class="rule-label">Matched guidelines</div>', unsafe_allow_html=True)
            st.markdown(chips, unsafe_allow_html=True)

        st.markdown("""
        <div class="status-line"><span class="status-dot"></span>ANALYSIS COMPLETE</div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.last_result)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="big">◈</div>
            Ready when you are.<br>Paste code on the left, then run <b>Analyze Code</b>.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)