import streamlit as st

def apply_styles():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

.stApp {
    background: #0a0e1a;
    background-image:
        radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(16, 185, 129, 0.06) 0%, transparent 50%);
}

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

[data-testid="stMetric"] {
    background: #111827 !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
    animation: popIn 0.4s ease-out;
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

[data-testid="stFileUploader"] {
    background: #111827 !important;
    border: 2px dashed rgba(99, 102, 241, 0.3) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    transition: all 0.3s !important;
    max-width: 480px !important;
    margin: 0 auto !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(99, 102, 241, 0.6) !important;
    background: rgba(99, 102, 241, 0.05) !important;
}

[data-testid="stSelectbox"] > div > div {
    background: #111827 !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-left-width: 4px !important;
    font-size: 14px !important;
}

hr {
    border-color: rgba(99, 102, 241, 0.15) !important;
    margin: 24px 0 !important;
}

[data-testid="stCaptionContainer"] {
    color: #475569 !important;
    font-size: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 12px !important;
}

[data-testid="stAppViewContainer"] {
    animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0px);  }
}

@keyframes popIn {
    from { opacity: 0; transform: scale(0.95); }
    to   { opacity: 1; transform: scale(1);    }
}

[data-testid="stPlotlyChart"] {
    animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0);    }
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.7); }

@media (max-width: 768px) {

    .block-container {
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 1rem !important;
    }

    h1 {
        font-size:clamp(1.6rem, 5vw, 2.5rem); !important;
        line-height: 1.3 !important;
        text-align: center !important;
    }

    h2 {
        font-size: 1.4rem !important;
    }

    h3 {
        font-size: 1.1rem !important;
    }

    p {
        font-size: 14px !important;
    }

    [data-testid="stMetric"] {
        padding: 14px !important;
        border-radius: 12px !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 11px !important;
    }

    [data-testid="stFileUploader"] {
        padding: 14px !important;
        max-width: 100% !important;
    }

    .stButton > button {
        width: 100% !important;
        padding: 0.8rem !important;
        font-size: 14px !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] {
        min-width: 220px !important;
    }

    iframe {
        width: 100% !important;
    }

    .stDataFrame {
        overflow-x: auto !important;
    }

}
</style>
""", unsafe_allow_html=True)
