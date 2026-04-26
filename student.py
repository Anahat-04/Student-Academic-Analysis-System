import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import numpy as np

st.set_page_config(page_title="AI Student Analytics", layout="wide")
st.title("AI Student Performance System")


#  CLEAN DATA 
    
def clean_data(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    for col in df.columns:
        if "roll" in col.lower():
            df.rename(columns={col: "Roll_No"}, inplace=True)
    for col in df.columns:
        if "mark" in col.lower() or "att" in col.lower():
            df[col] = df[col].astype(str).str.replace("%", "")
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.fillna(df.mean(numeric_only=True), inplace=True)
    return df


#  DETECT SUBJECTS

def detect_subjects(df):
    return [col.replace("_Marks", "") for col in df.columns if "_Marks" in col]


#  PERFORMANCE SCORE 

def performance_score(row, subjects):
    marks = np.mean([row[f"{s}_Marks"] for s in subjects])
    att   = np.mean([row[f"{s}_Attendance"] for s in subjects])
    return (marks * 0.7) + (att * 0.3)


#  AT-RISK SCORE & CLASSIFICATION 

def risk_score(row, subjects):
    avg_marks = np.mean([row[f"{s}_Marks"] for s in subjects])
    avg_att   = np.mean([row[f"{s}_Attendance"] for s in subjects])
    return round((avg_marks * 0.6) + (avg_att * 0.4), 2)


def classify_risk(score):
    if score < 45:
        return "Critical"
    elif score < 65:
        return "At Risk"
    return "Safe"


RISK_COLOR = {
    "Critical": "#E24B4A",
    "At Risk":  "#EF9F27",
    "Safe":     "#1D9E75",
}

RISK_EMOJI = {
    "Critical": "🔴",
    "At Risk":  "🟡",
    "Safe":     "🟢",
}


#  PREDICTION MODEL 

def train_model(df, subjects):
    X = df[[f"{s}_Attendance" for s in subjects]]
    y = df[[f"{s}_Marks" for s in subjects]].mean(axis=1)
    model = LinearRegression()
    model.fit(X, y)
    return model


#  SIDEBAR 

page = st.sidebar.radio("Navigation", [
    "Dashboard",
    "Student Analysis",
    "At-Risk Detection",
    "AI Insights",
])

file = st.file_uploader("Upload dataset", type=["csv", "xlsx"])

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df = clean_data(df)
    subjects = detect_subjects(df)

    if "Roll_No" not in df.columns:
        st.error("No Roll column found in dataset!")
        st.stop()

    df["Score"]      = df.apply(lambda x: performance_score(x, subjects), axis=1)
    df["Risk_Score"] = df.apply(lambda x: risk_score(x, subjects), axis=1)
    df["Risk_Level"] = df["Risk_Score"].apply(classify_risk)

    model = train_model(df, subjects)

    n_critical = (df["Risk_Level"] == "Critical").sum()
    n_at_risk  = (df["Risk_Level"] == "At Risk").sum()
    n_safe     = (df["Risk_Level"] == "Safe").sum()


  
    # DASHBOARD
   

    if page == "Dashboard":
        st.subheader("Overview")

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Students",  len(df))
        col2.metric("Avg Score", round(df["Score"].mean(), 2))
        col3.metric("Top Score", round(df["Score"].max(), 2))
        col4.metric("Critical",  int(n_critical))
        col5.metric("At Risk",   int(n_at_risk))

        st.divider()

        if n_critical > 0:
            st.error(
                f"⚠️ {n_critical} student(s) are in **Critical** status. "
                "Go to At-Risk Detection for details."
            )
        elif n_at_risk > 0:
            st.warning(f"ℹ️ {n_at_risk} student(s) are flagged as **At Risk**.")

        st.subheader("Top Students")
        top_df = df.sort_values("Score", ascending=False).head(5)
        st.dataframe(top_df[["Roll_No", "Score", "Risk_Level"]])

        marks_cols = [col for col in df.columns if "_Marks" in col]
        avg = df[marks_cols].mean().reset_index()
        avg.columns = ["Subject", "Marks"]
        fig = px.bar(avg, x="Subject", y="Marks", title="Subject Performance")
        st.plotly_chart(fig, use_container_width=True)


     
    # STUDENT ANALYSIS
     

    elif page == "Student Analysis":
        roll    = st.selectbox("Select Student", df["Roll_No"])
        student = df[df["Roll_No"] == roll].iloc[0]

        marks_cols = [f"{s}_Marks" for s in subjects]
        att_cols   = [f"{s}_Attendance" for s in subjects]

        avg_marks = student[marks_cols].mean()
        avg_att   = student[att_cols].mean()
        pred      = model.predict([student[att_cols]])[0]

        rl = student["Risk_Level"]
        st.markdown(
            f"**Risk status:** "
            f"<span style='color:{RISK_COLOR[rl]};font-weight:600'>"
            f"{RISK_EMOJI[rl]} {rl}</span>",
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Marks",       round(avg_marks, 1))
        col2.metric("Attendance",      round(avg_att, 1))
        col3.metric("Predicted Marks", round(pred, 1))
        col4.metric("Risk Score",      student["Risk_Score"])

        if avg_att < 50:
            st.error("🚨 Very low attendance!")

        st.divider()

        radar = pd.DataFrame({
            "Subject": subjects,
            "Marks":   [student[f"{s}_Marks"] for s in subjects],
        })
        fig = px.line_polar(radar, r="Marks", theta="Subject", line_close=True)
        fig.update_traces(fill="toself")
        st.plotly_chart(fig, use_container_width=True)

        month_cols = [c for c in df.columns if "Attendance_" in c]
        if month_cols:
            monthly_data = pd.DataFrame({
                "Month":      month_cols,
                "Attendance": [student[c] for c in month_cols],
            })
            fig2 = px.line(monthly_data, x="Month", y="Attendance",
                           markers=True, title="Monthly Attendance")
            st.plotly_chart(fig2, use_container_width=True)


     
    # AT-RISK DETECTION
     

    elif page == "At-Risk Detection":
        st.subheader("At-Risk Student Detection")
        st.caption(
            "Risk score = (avg marks × 0.6) + (avg attendance × 0.4). "
            "Critical < 45 · At Risk 45–65 · Safe > 65"
        )

        # Summary cards
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Critical", int(n_critical))
        c2.metric("🟡 At Risk",  int(n_at_risk))
        c3.metric("🟢 Safe",     int(n_safe))

        st.divider()

        # Donut chart
        donut_df = pd.DataFrame({
            "Status": ["Critical", "At Risk", "Safe"],
            "Count":  [n_critical, n_at_risk, n_safe],
        })
        fig_donut = px.pie(
            donut_df,
            names="Status",
            values="Count",
            hole=0.55,
            color="Status",
            color_discrete_map={
                "Critical": "#E24B4A",
                "At Risk":  "#EF9F27",
                "Safe":     "#1D9E75",
            },
            title="Risk Distribution",
        )
        fig_donut.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_donut, use_container_width=True)

        st.divider()

        # Filtered colour-coded table
        filter_level = st.selectbox(
            "Filter by risk level",
            ["All", "Critical", "At Risk", "Safe"],
        )

        display_cols = (
            ["Roll_No", "Risk_Level", "Risk_Score"]
            + [f"{s}_Marks" for s in subjects]
            + [f"{s}_Attendance" for s in subjects]
        )

        filtered = df if filter_level == "All" else df[df["Risk_Level"] == filter_level]
        filtered = filtered.sort_values("Risk_Score")

        def highlight_risk(val):
            colors = {
                "Critical": "background-color:#fde8e8;color:#A32D2D;font-weight:600",
                "At Risk":  "background-color:#fef3d0;color:#854F0B;font-weight:600",
                "Safe":     "background-color:#eaf3de;color:#3B6D11;font-weight:600",
            }
            return colors.get(val, "")

        styled = (
            filtered[display_cols]
            .style
            .map(highlight_risk, subset=["Risk_Level"])
            .format(precision=1)
        )
        st.dataframe(styled, use_container_width=True)


   
    # AI INSIGHTS
     

    elif page == "AI Insights":
        st.subheader("Smart Insights")

        roll    = st.selectbox("Select Student", df["Roll_No"])
        student = df[df["Roll_No"] == roll].iloc[0]
        rl      = student["Risk_Level"]

        st.markdown(
            f"**Risk status:** "
            f"<span style='color:{RISK_COLOR[rl]};font-weight:600'>"
            f"{RISK_EMOJI[rl]} {rl}</span>",
            unsafe_allow_html=True,
        )

        tips = []
        for s in subjects:
            if student[f"{s}_Marks"] < 50:
                tips.append(f"Improve {s} marks")
            if student[f"{s}_Attendance"] < 60:
                tips.append(f"Attend more {s} classes")

        if not tips:
            tips.append("Doing great 👍")

        for t in tips:
            st.success(t)

else:
    st.info("👆 Upload a dataset to begin")
