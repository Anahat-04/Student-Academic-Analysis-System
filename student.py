import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

st.set_page_config(page_title="AI Student Analytics", layout="wide")

st.title("🤖 AI Student Performance System")


# CLEAN DATA

def clean_data(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace(" ", "_")

    # 🔥 Auto-detect Roll column
    for col in df.columns:
        if "roll" in col.lower():
            df.rename(columns={col: "Roll_No"}, inplace=True)

    # 🔥 Convert marks & attendance
    for col in df.columns:
        if "mark" in col.lower() or "att" in col.lower():
            df[col] = df[col].astype(str).str.replace("%", "")
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.fillna(df.mean(numeric_only=True), inplace=True)
    return df


# DETECT SUBJECTS

def detect_subjects(df):
    subjects = []
    for col in df.columns:
        if "_Marks" in col:
            subjects.append(col.replace("_Marks", ""))
    return subjects


# PERFORMANCE SCORE

def performance_score(row, subjects):
    marks = np.mean([row[f"{s}_Marks"] for s in subjects])
    att = np.mean([row[f"{s}_Attendance"] for s in subjects])
    return (marks * 0.7) + (att * 0.3)



# PREDICTION MODEL

def train_model(df, subjects):
    X = df[[f"{s}_Attendance" for s in subjects]]
    y = df[[f"{s}_Marks" for s in subjects]].mean(axis=1)

    model = LinearRegression()
    model.fit(X, y)
    return model



# SIDEBAR

page = st.sidebar.radio("📌 Navigation", [
    "Dashboard",
    "Student Analysis",
    "AI Insights"
])

file = st.file_uploader("📂 Upload dataset", type=["csv", "xlsx"])

if file:

    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df = clean_data(df)

    # Detect subjects automatically
    subjects = detect_subjects(df)

    # Safety check
    if "Roll_No" not in df.columns:
        st.error("❌ No Roll column found in dataset!")
        st.stop()

    # Add score
    df["Score"] = df.apply(lambda x: performance_score(x, subjects), axis=1)

    # Train model
    model = train_model(df, subjects)

    
    # DASHBOARD
   
    if page == "Dashboard":

        st.subheader("📊 Overview")

        col1, col2, col3 = st.columns(3)
        col1.metric("Students", len(df))
        col2.metric("Avg Score", round(df["Score"].mean(), 2))
        col3.metric("Top Score", round(df["Score"].max(), 2))

        st.divider()

        # 🏆 Leaderboard
        st.subheader("🏆 Top Students")
        top_df = df.sort_values("Score", ascending=False).head(5)
        st.dataframe(top_df[["Roll_No", "Score"]])

        # 📊 Subject Performance
        marks_cols = [col for col in df.columns if "_Marks" in col]

        avg = df[marks_cols].mean().reset_index()
        avg.columns = ["Subject", "Marks"]

        fig = px.bar(avg, x="Subject", y="Marks", title="📚 Subject Performance")
        st.plotly_chart(fig, use_container_width=True)

   
    # STUDENT ANALYSIS
   
    elif page == "Student Analysis":

        roll = st.selectbox("Select Student", df["Roll_No"])
        student = df[df["Roll_No"] == roll].iloc[0]

        marks_cols = [f"{s}_Marks" for s in subjects]
        att_cols = [f"{s}_Attendance" for s in subjects]

        avg_marks = student[marks_cols].mean()
        avg_att = student[att_cols].mean()

        pred = model.predict([student[att_cols]])[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Avg Marks", round(avg_marks, 1))
        col2.metric("Attendance", round(avg_att, 1))
        col3.metric("Predicted Marks", round(pred, 1))

        # 🚨 ALERT
        if avg_att < 50:
            st.error("🚨 Very low attendance!")

        st.divider()

        # 🎯 Radar Chart
        radar = pd.DataFrame({
            "Subject": subjects,
            "Marks": [student[f"{s}_Marks"] for s in subjects]
        })

        fig = px.line_polar(radar, r="Marks", theta="Subject", line_close=True)
        fig.update_traces(fill='toself')
        st.plotly_chart(fig, use_container_width=True)

        # 📅 Monthly Attendance (if exists)
        month_cols = [c for c in df.columns if "Attendance_" in c]

        if month_cols:
            monthly_data = pd.DataFrame({
                "Month": month_cols,
                "Attendance": [student[c] for c in month_cols]
            })

            fig2 = px.line(monthly_data, x="Month", y="Attendance", markers=True,
                           title="📅 Monthly Attendance")
            st.plotly_chart(fig2, use_container_width=True)

   
    # AI INSIGHTS
   
    elif page == "AI Insights":

        st.subheader("🤖 Smart Insights")

        roll = st.selectbox("Select Student", df["Roll_No"])
        student = df[df["Roll_No"] == roll].iloc[0]

        tips = []

        for s in subjects:
            if student[f"{s}_Marks"] < 50:
                tips.append(f"Improve {s}")
            if student[f"{s}_Attendance"] < 60:
                tips.append(f"Attend more {s}")

        if not tips:
            tips.append("Doing great 👍")

        for t in tips:
            st.success(t)

else:
    st.info("👆 Upload dataset to begin")