import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
from student_ui import apply_styles


# CONFIG

st.set_page_config(page_title="AI Student Analytics", layout="wide")
st.title("AI Student Performance System")
apply_styles()


# CONSTANTS 

RISK_COLOR = {"Critical": "#E24B4A", "At Risk": "#EF9F27", "Safe": "#1D9E75"}
RISK_EMOJI = {"Critical": "🔴",      "At Risk": "🟡",      "Safe": "🟢"}

SAFE_MARKS      = 75
SAFE_ATTENDANCE = 75


# FUNCTIONS

def convert_attendance(df, cols):
    for col in cols:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.lower().str.strip().map({
                "present": 100, "absent": 0,
                "yes": 100,     "no": 0,
                "p": 100,       "a": 0,
            })
    return df


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
    att   = np.mean([row[f"{s}_Attendance"] for s in subjects])
    return round((marks * 0.6) + (att * 0.4), 2)


def classify_risk(score):
    if score < 45:   return "Critical"
    elif score < 65: return "At Risk"
    return "Safe"


def train_model(df, subjects):
    X = df[[f"{s}_Attendance" for s in subjects]]
    y = df[[f"{s}_Marks" for s in subjects]].mean(axis=1)
    m = LinearRegression()
    m.fit(X, y)
    return m


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
    return df, errors, warnings


# SIDEBAR

page = st.sidebar.radio("Navigation", [
    "Class Overview",
    "Student Analysis",
    "At-Risk Detection",
    "Improvement Planner",
])

file = st.file_uploader("Upload dataset", type=["csv", "xlsx"])


if file:
    df_raw = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df_raw.columns = df_raw.columns.str.strip().str.replace(" ", "_")
    all_cols = df_raw.columns.tolist()

    already_standard = any("_Marks" in c for c in all_cols)

    if already_standard:
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

    else:
        st.subheader("Map Your Dataset Columns")
        st.caption("Your dataset doesn't follow the standard format. Tell us which columns are which.")

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
        df = convert_attendance(df, att_cols)
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
    model            = train_model(df, subjects)

    n_critical = (df["Risk_Level"] == "Critical").sum()
    n_at_risk  = (df["Risk_Level"] == "At Risk").sum()
    n_safe     = (df["Risk_Level"] == "Safe").sum()

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
        fig.update_layout(transition_duration=500)
        st.plotly_chart(fig, use_container_width=True)

    # STUDENT ANALYSIS

    elif page == "Student Analysis":
        roll    = st.selectbox("Select Student", sorted(df["Roll_No"].astype(str)))
        student = df[df["Roll_No"].astype(str) == roll].iloc[0]

        marks_cols = [f"{s}_Marks" for s in subjects]
        att_cols   = [f"{s}_Attendance" for s in subjects]
        avg_marks  = student[marks_cols].mean()
        avg_att    = student[att_cols].mean()
        pred       = model.predict([student[att_cols].values])[0]
        rl         = student["Risk_Level"]

        st.markdown(
            f"**Risk Status:** "
            f"<span style='color:{RISK_COLOR[rl]};font-weight:600'>"
            f"{RISK_EMOJI[rl]} {rl}</span>",
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Marks",       round(avg_marks, 1))
        c2.metric("Avg Attendance",  round(avg_att, 1))
        c3.metric("Predicted Marks", round(pred, 1))
        c4.metric("Risk Score",      student["Risk_Score"])

        if avg_att < 50:
            st.error("🚨 Very low attendance!")

        st.divider()
        st.subheader("Subject-wise Breakdown")

        breakdown_melted = pd.DataFrame({
            "Subject":    subjects * 2,
            "Value":      [round(student[f"{s}_Marks"], 1) for s in subjects] +
                          [round(student[f"{s}_Attendance"], 1) for s in subjects],
            "Type":       ["Marks"] * len(subjects) + ["Attendance"] * len(subjects),
        })

        fig = px.bar(
            breakdown_melted, x="Subject", y="Value",
            color="Type", barmode="group",
            title="Marks vs Attendance per Subject",
            template="plotly_dark",
            color_discrete_map={"Marks": "#6366f1", "Attendance": "#10b981"}
        )
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

    # AT-RISK DETECTION

    elif page == "At-Risk Detection":
        st.subheader("At-Risk Student Detection")
        st.caption("Risk Score = (Avg Marks × 0.6) + (Avg Attendance × 0.4) · Critical <45 · At Risk 45–65 · Safe >65")

        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Critical", int(n_critical))
        c2.metric("🟡 At Risk",  int(n_at_risk))
        c3.metric("🟢 Safe",     int(n_safe))

        st.divider()

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

        filter_level = st.selectbox("Filter by risk level",
                                    ["All","Critical","At Risk","Safe"])

        display_cols = (["Roll_No","Risk_Level","Risk_Score"]
                        + [f"{s}_Marks" for s in subjects]
                        + [f"{s}_Attendance" for s in subjects])

        filtered = df if filter_level == "All" else df[df["Risk_Level"] == filter_level]
        filtered = filtered.sort_values("Risk_Score")

        st.dataframe(
            filtered[display_cols]
            .style.map(highlight_risk, subset=["Risk_Level"])
            .format(precision=1),
            use_container_width=True
        )

    # IMPROVEMENT PLANNER  (merged with AI Insights)

    elif page == "Improvement Planner":
        st.subheader("Improvement Planner")
        st.caption(
            f"Target: {SAFE_MARKS}/100 marks and {SAFE_ATTENDANCE}% attendance in every subject"
        )

        roll    = st.selectbox("Select Student", sorted(df["Roll_No"].astype(str)))
        student = df[df["Roll_No"].astype(str) == roll].iloc[0]
        rl      = student["Risk_Level"]

        st.markdown(
            f"**Current Risk Status:** "
            f"<span style='color:{RISK_COLOR[rl]};font-weight:600'>"
            f"{RISK_EMOJI[rl]} {rl}</span> &nbsp;|&nbsp; "
            f"**Risk Score:** {student['Risk_Score']}",
            unsafe_allow_html=True,
        )

        st.divider()

        if rl == "Safe":
            st.success("✅ This student is already in Safe status. No improvement needed.")

        else:
            current_avg_marks = np.mean([student[f"{s}_Marks"] for s in subjects])
            current_avg_att   = np.mean([student[f"{s}_Attendance"] for s in subjects])

            # ── Paths to Safe Status ──────────────────────────────────────
            st.subheader("Paths to Safe Status")

            marks_gap_overall = max(round(SAFE_MARKS - current_avg_marks, 1), 0)
            att_gap_overall   = max(round(SAFE_ATTENDANCE - current_avg_att, 1), 0)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📚 Improve Marks")
                st.metric("Required Avg Marks",  f"{SAFE_MARKS}/100")
                st.metric("Current Avg Marks",   f"{round(current_avg_marks, 1)}/100")
                st.metric("Needs to improve by", f"+{marks_gap_overall} points")
                if marks_gap_overall == 0:
                    st.success("Marks target already met!")
                else:
                    st.warning(
                        f"Student needs to score at least **{SAFE_MARKS}** "
                        f"in every subject to meet the marks target."
                    )

            with col2:
                st.markdown("### 📅 Improve Attendance")
                st.metric("Required Avg Attendance", f"{SAFE_ATTENDANCE}%")
                st.metric("Current Avg Attendance",  f"{round(current_avg_att, 1)}%")
                st.metric("Needs to improve by",     f"+{att_gap_overall}%")
                if att_gap_overall == 0:
                    st.success("Attendance target already met!")
                else:
                    st.warning(
                        f"Student needs at least **{SAFE_ATTENDANCE}%** "
                        f"attendance in every subject to meet the attendance target."
                    )

            st.divider()

            #Subject-wise Improvement Table with AI Tips 
            st.subheader("Subject-wise Improvement Needed")
            st.caption("Red = needs urgent attention · Orange = needs improvement · Green = target met")

            rows = []
            for s in subjects:
                m         = round(student[f"{s}_Marks"], 1)
                a         = round(student[f"{s}_Attendance"], 1)
                m_gap     = max(round(SAFE_MARKS - m, 1), 0)
                a_gap     = max(round(SAFE_ATTENDANCE - a, 1), 0)

                # AI tip for this subject
                if m < SAFE_MARKS and a < SAFE_ATTENDANCE:
                    tip = f"Both marks and attendance need improvement"
                elif m < SAFE_MARKS:
                    tip = f"Focus on improving marks — attendance is fine"
                elif a < SAFE_ATTENDANCE:
                    tip = f"Attend more classes — marks are fine"
                else:
                    tip = "✅ Target met in this subject"

                rows.append({
                    "Subject":            s,
                    "Current Marks":      m,
                    "Marks Needed":       SAFE_MARKS,
                    "Marks Gap":          m_gap,
                    "Current Attendance": a,
                    "Attendance Needed":  SAFE_ATTENDANCE,
                    "Attendance Gap":     a_gap,
                    "Tip":               tip,
                })

            imp_df = pd.DataFrame(rows)

            def color_gap(val):
                if val <= 0:   return "color:#1D9E75;font-weight:600"
                elif val < 10: return "color:#EF9F27;font-weight:600"
                return "color:#E24B4A;font-weight:600"

            def color_tip(val):
                if "✅" in str(val):     return "color:#1D9E75"
                if "Both" in str(val):   return "color:#E24B4A"
                return "color:#EF9F27"

            st.dataframe(
                imp_df.style
                .map(color_gap, subset=["Marks Gap", "Attendance Gap"])
                .map(color_tip, subset=["Tip"])
                .format(precision=1, subset=[
                    "Current Marks","Marks Needed","Marks Gap",
                    "Current Attendance","Attendance Needed","Attendance Gap"
                ]),
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            # Visual gap chart
            st.subheader("Visual Gap Chart")

            gap_df = pd.DataFrame({
                "Subject": subjects * 2,
                "Value":   [student[f"{s}_Marks"] for s in subjects] +
                           [student[f"{s}_Attendance"] for s in subjects],
                "Type":    ["Marks"] * len(subjects) +
                           ["Attendance"] * len(subjects),
            })

            fig = px.bar(
                gap_df, x="Subject", y="Value",
                color="Type", barmode="group",
                title=f"Current vs Target ({SAFE_MARKS} marks / {SAFE_ATTENDANCE}% attendance)",
                template="plotly_dark",
                color_discrete_map={"Marks": "#6366f1", "Attendance": "#10b981"}
            )
            fig.add_hline(
                y=SAFE_MARKS, line_dash="dash",
                line_color="#E24B4A", line_width=2,
                annotation_text=f"Target ({SAFE_MARKS})",
                annotation_position="top right"
            )
            fig.update_yaxes(range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👆 Upload a dataset to begin")
