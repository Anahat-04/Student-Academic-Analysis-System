import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
from student_ui import apply_styles
from groq import Groq
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import streamlit.components.v1 as components

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

# CONSTANTS 

RISK_COLOR = {"Critical": "#E24B4A", "At Risk": "#EF9F27", "Safe": "#1D9E75"}
RISK_EMOJI = {"Critical": "🔴",      "At Risk": "🟡",      "Safe": "🟢"}

SAFE_MARKS      = 75
SAFE_ATTENDANCE = 75

# FUNCTIONS

def normalize_marks(df, cols, max_mark):
    for col in cols:
        df[col] = ((pd.to_numeric(df[col], errors="coerce") / max_mark) * 100).clip(0, 100)
    return df

def performance_score(row, subjects):
    marks = np.mean([row[f"{s}_Marks"] for s in subjects])
    att   = np.mean([row[f"{s}_Attendance"] for s in subjects])
    return round((marks * 0.7) + (att * 0.3), 2)

def risk_score(row, subjects):
    marks = np.mean([row[f"{s}_Marks"] for s in subjects])
    att = np.mean([row[f"{s}_Attendance"] for s in subjects])
    performance = (marks * 0.6) + (att * 0.4)
    risk = 100 - performance
    return round(risk, 2)

def classify_risk(score):
    if score >= 55:
        return "Critical"
    elif score >= 35:
        return "At Risk"
    return "Safe"

def train_lr_model(df, subjects):
    """Linear Regression: predicts Performance Score from attendance features.
    The predicted score is then used to classify risk level."""
    att_cols = [f"{s}_Attendance" for s in subjects]
    lr_feature_cols = att_cols
    X = df[lr_feature_cols]
    y = df["Score"]

    if len(df) >= 10:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        mae = round(mean_absolute_error(y_test, lr.predict(X_test)), 2)
    else:
        lr = LinearRegression()
        lr.fit(X, y)
        mae = None

    return lr, lr_feature_cols, mae


def train_rf_model(df, subjects):
    """Random Forest: used ONLY for feature importance extraction.
    Identifies which marks/attendance features most influence risk."""
    all_feature_cols = [f"{s}_Marks" for s in subjects] + [f"{s}_Attendance" for s in subjects]
    X = df[all_feature_cols]
    y = df["Risk_Level"]

    rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    rf.fit(X, y)

    importances = pd.Series(rf.feature_importances_, index=all_feature_cols).sort_values(ascending=False)
    return rf, all_feature_cols, importances

def highlight_risk(val):
    return {
        "Critical": "background-color:#fde8e8;color:#A32D2D;font-weight:600",
        "At Risk":  "background-color:#fef3d0;color:#854F0B;font-weight:600",
        "Safe":     "background-color:#eaf3de;color:#3B6D11;font-weight:600",
    }.get(val, "")

def validate(df, subjects):
    errors, warnings = [], []
    if not subjects:
        errors.append("No subject columns detected.")
    for s in subjects:
        mc, ac = f"{s}_Marks", f"{s}_Attendance"
        if df[mc].isna().all(): errors.append(f"{mc} is empty.")
        if df[ac].isna().all(): errors.append(f"{ac} is empty.")
        if df[mc].max() > 100:
            warnings.append(f"{mc} clipped to 100.")
            df[mc] = df[mc].clip(0, 100)
        if df[ac].max() > 100:
            warnings.append(f"{ac} clipped to 100.")
            df[ac] = df[ac].clip(0, 100)
    if df["Roll_No"].duplicated().any():
        warnings.append("Duplicate roll numbers found.")

    # Fix 1: Flag students where ALL marks are 0 — likely missing/bad data
    marks_cols_check = [f"{s}_Marks" for s in subjects]
    zero_marks_mask = (df[marks_cols_check] == 0).all(axis=1)
    if zero_marks_mask.any():
        bad_rolls = df.loc[zero_marks_mask, "Roll_No"].tolist()
        warnings.append(
            f"{len(bad_rolls)} student(s) have zero marks in all subjects "
            f"(Roll No: {', '.join(str(r) for r in bad_rolls[:5])}{'...' if len(bad_rolls) > 5 else ''}) "
            f"— these may be data entry errors and could affect risk classification."
        )

    return df, errors, warnings

def generate_pdf_report(student_id, risk_level, risk_score, report_text):
    from io import BytesIO

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(
        "<font size=20 color='#4f46e5'><b>Student Performance Report</b></font>",
        styles['Title']
    )
    elements.append(title)
    elements.append(Spacer(1, 20))

    info_data = [
        ["Student ID", student_id],
        ["Status", risk_level],
        ["Score", f"{risk_score}/100"],
    ]

    table = Table(info_data, colWidths=[150, 300])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#4f46e5")),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#f3f4f6")),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#d1d5db")),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 25))

    formatted_report = report_text.replace("\n", "<br/>")

    report_paragraph = Paragraph(
        f"<font size=11>{formatted_report}</font>",
        styles['BodyText']
    )

    elements.append(report_paragraph)
    elements.append(Spacer(1, 30))

    footer = Paragraph(
        "<font size=9 color='gray'>Generated by AI Student Analytics System</font>",
        styles['Normal']
    )

    elements.append(footer)

    doc.build(elements)

    buffer.seek(0)

    return buffer

# SIDEBAR

page = st.sidebar.radio("Navigation", [
    "Class Overview",
    "Students at Risk",
    "Student Portal",
    "AI Report"
])

file     = st.file_uploader("Upload current dataset", type=["csv", "xlsx"])
file_prev = st.file_uploader("Upload previous dataset (optional — for trend comparison)", type=["csv", "xlsx"])

if file:
    df_raw = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df_raw.columns = df_raw.columns.str.strip().str.replace(" ", "_")
    all_cols = df_raw.columns.tolist()

    already_standard = any("_Marks" in c for c in all_cols) or st.session_state.get("mapping_confirmed", False)

    if already_standard and not st.session_state.get("mapping_confirmed", False):
        df       = df_raw.copy()
        subjects = [c.replace("_Marks", "") for c in df.columns if "_Marks" in c]
        for col in df.columns:
            if "roll" in col.lower():
                df.rename(columns={col: "Roll_No"}, inplace=True)
        for col in df.columns:
            if "mark" in col.lower() or "att" in col.lower():
                df[col] = df[col].astype(str).str.replace("%", "")
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df.fillna(df.mean(numeric_only=True), inplace=True)

    elif st.session_state.get("mapping_confirmed", False):
        roll_col   = st.session_state["roll_col"]
        marks_cols = st.session_state["marks_cols"]
        att_cols   = st.session_state["att_cols"]
        max_mark   = st.session_state["max_mark"]

        df = df_raw[[roll_col] + marks_cols + att_cols].copy()
        df.rename(columns={roll_col: "Roll_No"}, inplace=True)
        df = normalize_marks(df, marks_cols, max_mark)

        subjects = [
            c.replace("_score","").replace("_marks","")
             .replace("_grade","").replace("-","_")
             .strip().title().replace(" ","_")
            for c in marks_cols
        ]

        for i, s in enumerate(subjects):
            df.rename(columns={marks_cols[i]: f"{s}_Marks"}, inplace=True)
            if i < len(att_cols):
                df.rename(columns={att_cols[i]: f"{s}_Attendance"}, inplace=True)
            else:
                df[f"{s}_Attendance"] = 75

        df.fillna(df.mean(numeric_only=True), inplace=True)

    else:
        roll_col   = st.selectbox("Student ID / Roll No column", all_cols)
        marks_cols = st.multiselect("Marks columns", [c for c in all_cols if c != roll_col])
        has_att    = st.checkbox("My dataset has attendance columns", value=True)
        att_cols   = []
        if has_att:
            att_cols = st.multiselect("Attendance columns", [c for c in all_cols if c != roll_col and c not in marks_cols])
        max_mark = st.number_input("Maximum possible marks in your dataset", min_value=1, value=100)

        if not marks_cols:
            st.info("Please select at least one marks column to continue.")
            st.stop()

        if st.button("Confirm and Analyse", type="primary"):
            mapping_errors = []

            if has_att and len(att_cols) > 0:
                if len(att_cols) != len(marks_cols):
                    mapping_errors.append(
                        f"You selected {len(marks_cols)} marks column(s) "
                        f"but {len(att_cols)} attendance column(s). "
                        f"These must match — one attendance column per subject."
                    )

            overlap = set(marks_cols) & set(att_cols)
            if overlap:
                mapping_errors.append(
                    f"These columns are selected as both marks and attendance: "
                    f"{', '.join(overlap)}. Each column can only be used once."
                )

            if roll_col in marks_cols or roll_col in att_cols:
                mapping_errors.append(
                    f"Roll No column '{roll_col}' cannot also be a marks or attendance column."
                )

            suspicious = []
            for i, mc in enumerate(marks_cols):
                if i < len(att_cols):
                    ac = att_cols[i]
                    mc_subject = mc.lower().replace("_score","").replace("_marks","").replace("_grade","").strip()
                    ac_subject = ac.lower().replace("_attendance","").replace("_att","").strip()
                    if mc_subject != ac_subject:
                        suspicious.append(
                            f"'{mc}' (marks) is paired with '{ac}' (attendance) "
                            f"— these seem to be from different subjects."
                        )

            if mapping_errors:
                for err in mapping_errors:
                    st.error(f"❌ {err}")

            else:
                if suspicious:
                    st.warning(
                        "⚠️ Possible mismatch detected — please confirm these pairings are correct:\n\n"
                        + "\n".join(f"• {s}" for s in suspicious)
                    )
                    if not st.checkbox("I confirm these pairings are correct, proceed anyway"):
                        st.stop()

                st.session_state["mapping_confirmed"] = True
                st.session_state["roll_col"]          = roll_col
                st.session_state["marks_cols"]        = marks_cols
                st.session_state["att_cols"]          = att_cols
                st.session_state["max_mark"]          = max_mark

        if not st.session_state.get("mapping_confirmed"):
            st.stop()

        roll_col   = st.session_state["roll_col"]
        marks_cols = st.session_state["marks_cols"]
        att_cols   = st.session_state["att_cols"]
        max_mark   = st.session_state["max_mark"]

        df = df_raw[[roll_col] + marks_cols + att_cols].copy()
        df.rename(columns={roll_col: "Roll_No"}, inplace=True)
        df = normalize_marks(df, marks_cols, max_mark)

        subjects = [
            c.replace("_score","").replace("_marks","")
             .replace("_grade","").replace("-","_")
             .strip().title().replace(" ","_")
            for c in marks_cols
        ]

        for i, s in enumerate(subjects):
            df.rename(columns={marks_cols[i]: f"{s}_Marks"}, inplace=True)
            if i < len(att_cols):
                df.rename(columns={att_cols[i]: f"{s}_Attendance"}, inplace=True)
            else:
                df[f"{s}_Attendance"] = 75

        df.fillna(df.mean(numeric_only=True), inplace=True)

    # VALIDATE 
    if "Roll_No" not in df.columns:
        st.error("No Roll / Student ID column found.")
        st.stop()

    df, errors, warnings = validate(df, subjects)

    if errors:
        for e in errors: st.error(f"❌ {e}")
        st.stop()

    if warnings:
        with st.expander("⚠️ Data quality warnings"):
            for w in warnings: st.warning(w)

    # COMPUTE
    
    df["Score"]      = df.apply(lambda x: performance_score(x, subjects), axis=1)
    df["Risk_Score"] = df.apply(lambda x: risk_score(x, subjects), axis=1)
    df["Risk_Level"] = df["Risk_Score"].apply(classify_risk)

    cache_key = f"model_{file.name}_{len(df)}"
    if st.session_state.get("model_cache_key") != cache_key:
        # Linear Regression — classifies risk via predicted performance score
        lr_model, lr_feature_cols, lr_mae = train_lr_model(df, subjects)
        # Random Forest — feature importance only (drives Top 5 focus areas)
        rf_model, rf_feature_cols, feature_importances = train_rf_model(df, subjects)

        st.session_state["model_cache_key"]     = cache_key
        st.session_state["lr_model"]            = lr_model
        st.session_state["lr_feature_cols"]     = lr_feature_cols
        st.session_state["lr_mae"]              = lr_mae
        st.session_state["rf_model"]            = rf_model
        st.session_state["rf_feature_cols"]     = rf_feature_cols
        st.session_state["feature_importances"] = feature_importances
    else:
        lr_model            = st.session_state["lr_model"]
        lr_feature_cols     = st.session_state["lr_feature_cols"]
        lr_mae              = st.session_state["lr_mae"]
        rf_model            = st.session_state["rf_model"]
        rf_feature_cols     = st.session_state["rf_feature_cols"]
        feature_importances = st.session_state["feature_importances"]

    # Use LR to classify risk: predict score → apply classify_risk threshold
    df["LR_Predicted_Score"] = lr_model.predict(df[lr_feature_cols]).clip(0, 100)
    df["Risk_Level"] = df["LR_Predicted_Score"].apply(lambda s: classify_risk(100 - s))

    n_critical = (df["Risk_Level"] == "Critical").sum()
    n_at_risk  = (df["Risk_Level"] == "At Risk").sum()
    n_safe     = (df["Risk_Level"] == "Safe").sum()

    # Fix 3: Process previous dataset for trend comparison
    df_prev = None
    if file_prev:
        try:
            df_prev_raw = pd.read_csv(file_prev) if file_prev.name.endswith(".csv") else pd.read_excel(file_prev)
            df_prev_raw.columns = df_prev_raw.columns.str.strip().str.replace(" ", "_")

            # Rename Roll_No
            for col in df_prev_raw.columns:
                if "roll" in col.lower():
                    df_prev_raw.rename(columns={col: "Roll_No"}, inplace=True)

            # Strip % and convert numeric cols
            for col in df_prev_raw.columns:
                if "mark" in col.lower() or "att" in col.lower() or "score" in col.lower():
                    df_prev_raw[col] = pd.to_numeric(
                        df_prev_raw[col].astype(str).str.replace("%", ""), errors="coerce"
                    )

            # Detect subjects — support both _Marks and _score naming
            if any("_Marks" in c for c in df_prev_raw.columns):
                prev_subjects = [c.replace("_Marks", "") for c in df_prev_raw.columns if "_Marks" in c]
            else:
                # Map _score -> _Marks, _attendance -> _Attendance to match current format
                prev_subjects = [c.replace("_score", "") for c in df_prev_raw.columns if c.endswith("_score")]
                for s in prev_subjects:
                    if f"{s}_score" in df_prev_raw.columns:
                        df_prev_raw.rename(columns={f"{s}_score": f"{s}_Marks"}, inplace=True)
                    if f"{s}_attendance" in df_prev_raw.columns:
                        df_prev_raw.rename(columns={f"{s}_attendance": f"{s}_Attendance"}, inplace=True)

            if prev_subjects and "Roll_No" in df_prev_raw.columns:
                # Clip to 100 and fill NaN
                for s in prev_subjects:
                    for suffix in ("_Marks", "_Attendance"):
                        c = f"{s}{suffix}"
                        if c in df_prev_raw.columns:
                            df_prev_raw[c] = df_prev_raw[c].clip(0, 100)
                df_prev_raw.fillna(df_prev_raw.mean(numeric_only=True), inplace=True)
                df_prev_raw["Risk_Score"] = df_prev_raw.apply(lambda x: risk_score(x, prev_subjects), axis=1)
                df_prev_raw["Risk_Level"] = df_prev_raw["Risk_Score"].apply(classify_risk)
                # Normalize Roll_No to str to match current df pipeline
                df_prev_raw["Roll_No"] = df_prev_raw["Roll_No"].astype(str).str.strip()
                df_prev = df_prev_raw
        except Exception as e:
            st.warning(f"⚠️ Could not process previous dataset: {e}")
            df_prev = None

    # CLASS OVERVIEW

    if page == "Class Overview":
        st.subheader("Class Overview")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Students",  len(df))
        c2.metric("Avg Score", round(df["Score"].mean(), 2))
        c3.metric("Top Score", round(df["Score"].max(), 2))
        c4.metric("Critical",  int(n_critical))
        c5.metric("At Risk",   int(n_at_risk))

        st.divider()

        if n_critical > 0:
            st.error(f"⚠️ {n_critical} student(s) Critical — check At-Risk Detection.")
        elif n_at_risk > 0:
            st.warning(f"ℹ️ {n_at_risk} student(s) flagged At Risk.")

        st.subheader("Top Students")
        st.dataframe(
            df.sort_values("Score", ascending=False)
              .head(5)[["Roll_No", "Score", "Risk_Level"]],
            use_container_width=True
        )

        st.divider()

        avg = df[[c for c in df.columns if "_Marks" in c]].mean().reset_index()
        avg.columns = ["Subject", "Marks"]
        avg["Subject"] = avg["Subject"].str.replace("_Marks", "")

        fig = px.bar(avg, x="Subject", y="Marks",
                     title="Subject Performance", template="plotly_dark")
        fig.update_yaxes(range=[0, 100])
        
        if len(avg) == 1:
            fig.update_traces(width=0.3)
            
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10),transition_duration=500)
        st.plotly_chart(fig, use_container_width=True)

        # Fix 3: Trend comparison table
        if df_prev is not None:
            st.divider()
            st.subheader("Month-on-Month Progress")

            df_curr_trend = df[["Roll_No", "Risk_Score", "Risk_Level"]].copy()
            df_curr_trend["Roll_No"] = df_curr_trend["Roll_No"].astype(str).str.strip()
            df_prev_trend = df_prev[["Roll_No", "Risk_Score", "Risk_Level"]].copy()
            df_prev_trend["Roll_No"] = df_prev_trend["Roll_No"].astype(str).str.strip()
            merged = df_curr_trend.merge(
                df_prev_trend.rename(
                    columns={"Risk_Score": "Prev_Risk_Score", "Risk_Level": "Prev_Risk_Level"}
                ),
                on="Roll_No", how="inner"
            )
            merged["Change"] = (merged["Risk_Score"] - merged["Prev_Risk_Score"]).round(1)
            merged["Trend"]  = merged["Change"].apply(
                lambda x: "📉 Worsened" if x > 2 else ("📈 Improved" if x < -2 else "➡️ Stable")
            )

            worsened = (merged["Trend"] == "📉 Worsened").sum()
            improved = (merged["Trend"] == "📈 Improved").sum()
            stable   = (merged["Trend"] == "➡️ Stable").sum()
            tc1, tc2, tc3 = st.columns(3)
            tc1.metric("Improved",  int(improved),  delta=f"-{improved} risk",  delta_color="normal")
            tc2.metric("Worsened",  int(worsened),  delta=f"+{worsened} risk",  delta_color="inverse")
            tc3.metric("Stable",    int(stable))

            st.dataframe(
                merged[["Roll_No", "Prev_Risk_Level", "Risk_Level", "Prev_Risk_Score", "Risk_Score", "Change", "Trend"]]
                .rename(columns={
                    "Prev_Risk_Level":  "Previous Status",
                    "Risk_Level":       "Current Status",
                    "Prev_Risk_Score":  "Previous Score",
                    "Risk_Score":       "Current Score",
                })
                .sort_values("Change", ascending=False)
                .style.map(highlight_risk, subset=["Previous Status", "Current Status"])
                .format(precision=1, subset=["Previous Score", "Current Score", "Change"]),
                use_container_width=True
            )


    # AT-RISK DETECTION

    elif page == "Students at Risk":
        st.subheader("Students at Risk")

        fig_donut = px.pie(
            pd.DataFrame({"Status": ["Critical","At Risk","Safe"],
                          "Count":  [n_critical, n_at_risk, n_safe]}),
            names="Status", values="Count", hole=0.55,
            color="Status",
            color_discrete_map={"Critical":"#E24B4A","At Risk":"#EF9F27","Safe":"#1D9E75"},
            title="Risk Distribution", template="plotly_dark"
        )
        fig_donut.update_traces(textposition="inside", textinfo="percent+label", rotation=90)
        fig_donut.update_layout(transition=dict(duration=700, easing="cubic-in-out"))
        st.plotly_chart(fig_donut, use_container_width=True)

        st.divider()

        filter_level = st.selectbox("Filter by status level",
                                    ["All","Critical","At Risk","Safe"])

        display_cols = (["Roll_No","Risk_Level","Risk_Score"]
                        + [f"{s}_Marks" for s in subjects]
                        + [f"{s}_Attendance" for s in subjects])

        filtered = df if filter_level == "All" else df[df["Risk_Level"] == filter_level]
        filtered = filtered.sort_values("Risk_Score", ascending=False)
        st.caption("Sorted by highest risk first")

        st.dataframe(
            filtered[display_cols]
            .style.map(highlight_risk, subset=["Risk_Level"])
            .format(precision=1),
            use_container_width=True
        )
    
    # STUDENT PORTAL

    elif page == "Student Portal":
        st.markdown("""
        <div style='text-align:center; padding: 20px 0 10px 0;'>
            <h2 style='color:#6366f1; font-size:1.8rem;'>Student Academic Performance Portal</h2>
            <p style='color:#94a3b8; font-size:14px;'>
                Enter your roll number to view your personal performance report
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            roll_input = st.text_input(
                "Enter Your Roll Number",
                placeholder="e.g. 1 / STU001",
                label_visibility="visible"
            )
            search = st.button("Check My Performance", type="primary",
                               use_container_width=True)

        if search and roll_input:
            # Fix 9: normalize both sides — strip whitespace, lowercase, try numeric fallback
            def normalize_roll(val):
                v = str(val).strip().lower()
                try:
                    return str(int(float(v)))
                except (ValueError, TypeError):
                    return v

            roll_normalized = normalize_roll(roll_input)
            match = df[df["Roll_No"].apply(normalize_roll) == roll_normalized]

            if match.empty:
                st.error(f"❌ Roll number **{roll_input}** not found. Please check and try again.")
            else:
                student = match.iloc[0]
                rl      = student["Risk_Level"]

                st.divider()

                st.markdown(
                    f"""
                    <div style='
                        background: #111827;
                        border: 1px solid rgba(99,102,241,0.3);
                        border-radius: 16px;
                        padding: 20px 28px;
                        text-align: center;
                    '>
                        <h3 style='color:#e2e8f0; margin:0'>
                            Roll No: {student['Roll_No']}
                        </h3>
                        <p style='color:{RISK_COLOR[rl]}; font-size:1.2rem;
                                  font-weight:600; margin:8px 0 0 0'>
                            {RISK_EMOJI[rl]} {rl} Student
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.divider()

                marks_cols_list = [f"{s}_Marks" for s in subjects]
                att_cols_list   = [f"{s}_Attendance" for s in subjects]
                avg_marks  = round(student[marks_cols_list].mean(), 1)
                avg_att    = round(student[att_cols_list].mean(), 1)

                c1, c2, c3 = st.columns(3)
                c1.metric("Your Avg Marks",      avg_marks)
                c2.metric("Your Avg Attendance", f"{avg_att}%")
                c3.metric("Risk Score (↓ lower is better)", student["Risk_Score"])

                fi_series = feature_importances.copy()
                personal_impact = {}
                for feat, imp in fi_series.items():
                    val = student[feat]
                    target = SAFE_MARKS if "_Marks" in feat else SAFE_ATTENDANCE
                    gap = max(target - val, 0)
                    # Only include features where student is below target
                    if gap > 0:
                        personal_impact[feat] = imp * (1 + gap / 100)

                top5 = sorted(personal_impact.items(), key=lambda x: x[1], reverse=True)[:5]
                top5_parts = []
                for rank, (feat, gap_val) in enumerate(top5, 1):
                    val    = round(student[feat], 1)
                    target = SAFE_MARKS if "_Marks" in feat else SAFE_ATTENDANCE
                    gap    = round(max(target - val, 0), 1)
                    label  = feat.replace("_Marks", " Marks").replace("_Attendance", " Attendance")
                    icon   = "📚" if "_Marks" in feat else "📅"
                    gap_txt = f"<span style=\"color:#E24B4A;font-weight:600\">↑ {gap} needed</span>"
                    top5_parts.append(
                        f"<div style=\"display:flex;justify-content:space-between;align-items:center;"
                        f"padding:8px 0;border-bottom:1px solid #1e293b\">"
                        f"<div style=\"display:flex;align-items:center;gap:8px\">"
                        f"<span style=\"color:#475569;font-size:12px;font-weight:700;width:16px\">{rank}</span>"
                        f"<span style=\"font-size:1rem\">{icon}</span>"
                        f"<span style=\"color:#e2e8f0;font-size:13px\">{label}</span>"
                        f"</div>"
                        f"<span style=\"color:#94a3b8;font-size:12px\">{val} &nbsp;{gap_txt}</span>"
                        f"</div>"
                    )

                if top5_parts:
                    top5_html = "".join(top5_parts)
                    st.markdown(
                        "<div style=\"background:#111827;border:1px solid rgba(99,102,241,0.3);"
                        "border-left:4px solid #6366f1;border-radius:12px;padding:18px 24px;margin:12px 0\">"
                        "<div style=\"color:#94a3b8;font-size:11px;text-transform:uppercase;"
                        "letter-spacing:1.2px;margin-bottom:10px\">🎯 Your Top 5 Focus Areas</div>"
                        + top5_html +
                        "</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.success("🎯 All subjects are on target — nothing needs improvement right now!")

                if rl == "Critical":
                    st.error(
                        "🚨 Your academic status is Critical. "
                        "Immediate improvement in both marks and attendance is required. "
                        "Please meet your teacher as soon as possible."
                    )
                elif rl == "At Risk":
                    st.warning(
                        "⚠️ You are At Risk. "
                        "You need to improve your marks and attendance "
                        "to reach Safe status. Check your subject details below."
                    )
                else:
                    st.success(
                        "✅ You are performing well and are in Safe status. "
                        "Keep it up and maintain your current effort!"
                    )

                st.divider()

                st.subheader("Your Subject-wise Performance")

                rows = []
                for s in subjects:
                    m     = round(student[f"{s}_Marks"], 1)
                    a     = round(student[f"{s}_Attendance"], 1)
                    m_gap = max(round(SAFE_MARKS - m, 1), 0)
                    a_gap = max(round(SAFE_ATTENDANCE - a, 1), 0)

                    if m < SAFE_MARKS and a < SAFE_ATTENDANCE:
                        status = "⚠️ Needs Attention"
                        tip    = "Improve both marks and attendance"
                    elif m < SAFE_MARKS:
                        status = "📚 Low Marks"
                        tip    = "Focus on improving marks"
                    elif a < SAFE_ATTENDANCE:
                        status = "📅 Low Attendance"
                        tip    = "Attend more classes"
                    else:
                        status = "✅ On Track"
                        tip    = "Keep it up"

                    rows.append({
                        "Subject":          s,
                        "Your Marks":       m,
                        "Marks Gap":        m_gap,
                        "Your Attendance":  a,
                        "Attendance Gap":   a_gap,
                        "Status":           status,
                        "What to do":       tip,
                    })

                portal_df = pd.DataFrame(rows)

                def color_status(val):
                    if "✅" in str(val): return "color:#1D9E75;font-weight:600"
                    if "⚠️" in str(val): return "color:#E24B4A;font-weight:600"
                    return "color:#EF9F27;font-weight:600"

                def color_gap(val):
                    if val <= 0:   return "color:#1D9E75;font-weight:600"
                    elif val < 10: return "color:#EF9F27;font-weight:600"
                    return "color:#E24B4A;font-weight:600"

                st.dataframe(
                    portal_df.style
                    .map(color_status, subset=["Status"])
                    .map(color_gap, subset=["Marks Gap", "Attendance Gap"])
                    .format(precision=1, subset=[
                        "Your Marks", "Marks Gap",
                        "Your Attendance", "Attendance Gap"
                    ]),
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()

                st.subheader("Your Marks vs Attendance")

                chart_df = pd.DataFrame({
                    "Subject": subjects * 2,
                    "Value":   [student[f"{s}_Marks"] for s in subjects] +
                               [student[f"{s}_Attendance"] for s in subjects],
                    "Type":    ["Your Marks"] * len(subjects) +
                               ["Your Attendance"] * len(subjects),
                })

                fig = px.bar(
                    chart_df, x="Subject", y="Value",
                    color="Type", barmode="group",
                    title="Your Marks and Attendance per Subject",
                    template="plotly_dark",
                    color_discrete_map={
                        "Your Marks":      "#6366f1",
                        "Your Attendance": "#10b981",
                    }
                )
                
                if len(subjects) == 1:
                    fig.update_traces(width=0.3)
                    fig.update_layout(bargap=0.8)
                    
                fig.add_hline(
                    y=SAFE_MARKS, line_dash="dash",
                    line_color="#E24B4A", line_width=2,
                    annotation_text=f"Target ({SAFE_MARKS})",
                    annotation_position="top right"
                )
                fig.update_yaxes(range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

                st.divider()

                if rl != "Safe":
                    st.subheader("What You Need to Reach Safe Status")

                    current_avg_marks = np.mean([student[f"{s}_Marks"] for s in subjects])
                    current_avg_att   = np.mean([student[f"{s}_Attendance"] for s in subjects])
                    marks_gap_overall = max(round(SAFE_MARKS - current_avg_marks, 1), 0)
                    att_gap_overall   = max(round(SAFE_ATTENDANCE - current_avg_att, 1), 0)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 🎯 Marks Target")
                        st.metric("You need to score at least", f"{SAFE_MARKS}/100")
                        st.metric("You need to improve by",     f"+{marks_gap_overall} points")

                    with c2:
                        st.markdown("### 📅 Attendance Target")
                        st.metric("You need at least",      f"{SAFE_ATTENDANCE}%")
                        st.metric("You need to improve by", f"+{att_gap_overall}%")

        elif search and not roll_input:
            st.warning("Please enter your roll number first.")

    # AI REPORT

    elif page == "AI Report":
        st.subheader("AI Generated Student Report")


        roll    = st.selectbox("Select Student", sorted(df["Roll_No"].astype(str), key=lambda x: int(x) if x.isdigit() else x))
        student = df[df["Roll_No"].astype(str) == roll].iloc[0]

        # Risk level is now derived from LR model prediction (consistent everywhere)
        assigned_rl = student["Risk_Level"]

        # Look up trend data for this student if previous dataset is loaded
        trend_context = ""
        if df_prev is not None:
            prev_match = df_prev[df_prev["Roll_No"].astype(str).str.strip() == str(roll).strip()]
            if not prev_match.empty:
                prev_student    = prev_match.iloc[0]
                prev_risk_score = prev_student["Risk_Score"]
                prev_risk_level = prev_student["Risk_Level"]
                change          = round(student["Risk_Score"] - prev_risk_score, 1)
                if change > 2:
                    trend_word = "declined"
                elif change < -2:
                    trend_word = "improved"
                else:
                    trend_word = "stable"
                trend_context = (
                    f"\nTrend vs Previous Month:\n"
                    f"- Previous Status : {prev_risk_level} (Risk Score: {round(prev_risk_score,1)})"
                    f"\n- Current Status  : {assigned_rl} (Risk Score: {student['Risk_Score']})"
                    f"\n- Change          : {'+' if change > 0 else ''}{change} points ({trend_word})"
                )

        st.markdown(
            f"**Assigned Status:** "
            f"<span style='color:{RISK_COLOR.get(assigned_rl, '#e2e8f0')};font-weight:600'>"
            f"{RISK_EMOJI.get(assigned_rl, '')} {assigned_rl}</span> &nbsp;|&nbsp; "
            f"**Risk Score:** {student['Risk_Score']}",
            unsafe_allow_html=True,
        )

        st.divider()

        subject_details = ""
        for s in subjects:
            m     = round(student[f"{s}_Marks"], 1)
            a     = round(student[f"{s}_Attendance"], 1)
            m_gap = max(round(SAFE_MARKS - m, 1), 0)
            a_gap = max(round(SAFE_ATTENDANCE - a, 1), 0)
            subject_details += (
                f"- {s}: Marks = {m}/100 "
                f"(gap to target: {m_gap}), "
                f"Attendance = {a}% "
                f"(gap to target: {a_gap}%)\n"
            )

        avg_marks = round(student[[f"{s}_Marks" for s in subjects]].mean(), 1)
        avg_att   = round(student[[f"{s}_Attendance" for s in subjects]].mean(), 1)

        prompt = f"""
You are an experienced academic advisor analyzing a student's performance data from a college.

Student Roll No : {roll}
Assigned Status : {assigned_rl} (Score: {student['Risk_Score']}/100)
Avg Marks       : {avg_marks} out of 100
Avg Attendance  : {avg_att}%
{trend_context}

Subject-wise breakdown:
{subject_details}

Safe target thresholds: {SAFE_MARKS} marks and {SAFE_ATTENDANCE}% attendance in every subject.

Write a professional and personalized academic performance report covering these sections:

1. Overall Assessment — summarize the student's current academic standing. If trend data is provided, mention whether the student has improved, declined, or stayed stable compared to last month.
2. Strong Areas — mention subjects where the student is doing well with specific numbers
3. Areas of Concern — mention weak subjects with specific marks and attendance numbers and explain the impact
4. Attendance Analysis — analyze the attendance pattern and its effect on performance
5. Specific Recommendations — give 3 to 5 concrete actionable steps the student should take
6. Predicted Outcome — what will happen if current trend continues vs if student improves

Important instructions:
- Be specific with numbers throughout the report
- Write in a professional but supportive tone
- Use bullet points and small paragraph at end when explaining predicted outcomes
- Keep the total report under 350 words
- Address the student directly as "you" throughout
- Do not use markdown and ** Symbols
- Use plain highlighted headings only
"""

        if st.button("Generate AI Report", type="primary"):
            with st.spinner("Generating personalized report..."):
                try:
                    from groq import Groq

                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1024,
                        temperature=0.7,
                    )

                    report = response.choices[0].message.content

                    st.divider()

                    st.markdown(
                        f"""
                        <div style='
                            background: #111827;
                            border: 1px solid rgba(99, 102, 241, 0.3);
                            border-radius: 16px;
                            padding: 28px 32px;
                            line-height: 1.9;
                            color: #e2e8f0;
                            font-size: 15px;
                            font-family: Space Grotesk, sans-serif;
                        '>
                        {report.replace(chr(10), "<br>")}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.divider()
                    pdf_file = generate_pdf_report(
                    student_id=roll,
                    risk_level=assigned_rl,
                    risk_score=student["Risk_Score"],
                    report_text=report
                   )

                    st.download_button(
                        label="⬇️ Download Report",
                        data=pdf_file,
                        file_name=f"student_report_{roll}.pdf",
                        mime="application/pdf"
                    )

                except Exception as e:
                    st.error(f"❌ Error generating report: {e}")

        else:
            st.info("👆 Select a student and click Generate AI Report to create their personalized report.")

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
