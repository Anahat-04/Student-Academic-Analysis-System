import streamlit as st

def apply_styles():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── BASE ── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

.stApp {
    background: #0a0e1a;
    background-image:
        radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(16, 185, 129, 0.06) 0%, transparent 50%);
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #0f1320 !important;
    border-right: 1px solid rgba(99, 102, 241, 0.2) !important;
}

[data-testid="stSidebar"] .stRadio label {
    color: #94a3b8 !important;
    font-size: 14px !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}

[data-testid="stSidebar"] .stRadio label:hover {
    color: #fff !important;
    background: rgba(99, 102, 241, 0.15) !important;
}

/* ── TITLE ── */
h1 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 2rem !important;
    background: linear-gradient(135deg, #6366f1, #10b981) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    letter-spacing: -0.5px !important;
}

h2, h3 {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    letter-spacing: -0.3px !important;
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: #111827 !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
}

[data-testid="stMetric"]:hover {
    border-color: rgba(99, 102, 241, 0.5) !important;
    box-shadow: 0 4px 32px rgba(99, 102, 241, 0.15) !important;
    transform: translateY(-2px) !important;
}

[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}

[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 2rem !important;
    font-weight: 600 !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: #111827 !important;
    border: 2px dashed rgba(99, 102, 241, 0.3) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    transition: all 0.3s !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(99, 102, 241, 0.6) !important;
    background: rgba(99, 102, 241, 0.05) !important;
}

/* ── SELECTBOX ── */
[data-testid="stSelectbox"] > div > div {
    background: #111827 !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-left-width: 4px !important;
    font-size: 14px !important;
}

/* ── DIVIDER ── */
hr {
    border-color: rgba(99, 102, 241, 0.15) !important;
    margin: 24px 0 !important;
}

/* ── CAPTION ── */
[data-testid="stCaptionContainer"] {
    color: #475569 !important;
    font-size: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 12px !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.7); }
</style>
""", unsafe_allow_html=True)
