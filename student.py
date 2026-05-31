import streamlit as st
import streamlit.components.v1 as components
from student_ui import apply_styles
from uploader import load_and_preprocess, performance_score, risk_score, classify_risk, train_model
from class_overview import show_class_overview
from students_at_risk import show_students_at_risk
from student_portal import show_student_portal
from report_generate import show_ai_report

# CONFIG

st.set_page_config(page_title="AI Student Analytics", layout="wide")
apply_styles()

st.markdown("""
<link rel="stylesheet" 
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

<div style='padding: 8px 0 24px 0; text-align:center;'>
    <div style='display:flex; align-items:center; justify-content:center; gap:12px;'>
        <div style='
            background: linear-gradient(135deg, #6366f1, #10b981);
            border-radius: 12px;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
        '>
            <i class="fas fa-users" 
               style="color:white; font-size:22px;"></i>
        </div>
        <div>
            <div style='font-size:1.8rem; font-weight:700;
                        background:linear-gradient(135deg,#6366f1,#10b981);
                        -webkit-background-clip:text;
                        -webkit-text-fill-color:transparent'>
                Student Performance Analytics System
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# SIDEBAR

page = st.sidebar.radio("Navigation", [
    "Class Overview",
    "Students at Risk",
    "Student Portal",
    "AI Report"
])

file = st.file_uploader("Upload dataset", type=["csv", "xlsx"])

if not file:
    components.html("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <div style='display:flex; justify-content:center; gap:16px; flex-wrap:wrap; margin-top:24px; max-width:900px; margin-left:auto; margin-right:auto;'>

        <div style='background:#111827; border:1px solid rgba(99,102,241,0.2); border-radius:14px; padding:20px 24px; width:190px; text-align:center;'>
            <i class="fas fa-triangle-exclamation" style="color:#E24B4A; font-size:24px;"></i>
            <div style='color:#e2e8f0; font-weight:600; font-size:14px; margin:10px 0 6px 0'>Early Risk Alerts</div>
        </div>

        <div style='background:#111827; border:1px solid rgba(99,102,241,0.2); border-radius:14px; padding:20px 24px; width:190px; text-align:center;'>
            <i class="fas fa-list-check" style="color:#EF9F27; font-size:24px;"></i>
            <div style='color:#e2e8f0; font-weight:600; font-size:14px; margin:10px 0 6px 0'>Improvement Plan</div>
        </div>
        
        <div style='background:#111827; border:1px solid rgba(99,102,241,0.2); border-radius:14px; padding:20px 24px; width:190px; text-align:center;'>
            <i class="fas fa-file-pdf" style="color:#6366f1; font-size:24px;"></i>
            <div style='color:#e2e8f0; font-weight:600; font-size:14px; margin:10px 0 6px 0'>Individual Student Reports</div>
        </div>

    </div>
    """, height=700)
    st.stop()

# LOAD & COMPUTE

df, subjects = load_and_preprocess(file)

df["Score"]      = df.apply(lambda x: performance_score(x, subjects), axis=1)
df["Risk_Score"] = df.apply(lambda x: risk_score(x, subjects), axis=1)
df["Risk_Level"] = df["Risk_Score"].apply(classify_risk)
model            = train_model(df, subjects)

n_critical = (df["Risk_Level"] == "Critical").sum()
n_at_risk  = (df["Risk_Level"] == "At Risk").sum()
n_safe     = (df["Risk_Level"] == "Safe").sum()

# ROUTING

if page == "Class Overview":
    show_class_overview(df, subjects, n_critical, n_at_risk)

elif page == "Students at Risk":
    show_students_at_risk(df, subjects, n_critical, n_at_risk, n_safe)

elif page == "Student Portal":
    show_student_portal(df, subjects, model)

elif page == "AI Report":
    show_ai_report(df, subjects)
