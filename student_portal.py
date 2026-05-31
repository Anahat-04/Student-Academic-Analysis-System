import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from uploader import RISK_COLOR, RISK_EMOJI, SAFE_MARKS, SAFE_ATTENDANCE


def show_student_portal(df, subjects, model):
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
        search = st.button("Check My Performance", type="primary", use_container_width=True)

    if search and roll_input:
        match = df[df["Roll_No"].astype(str).str.strip() == roll_input.strip()]

        if match.empty:
            st.error(f"❌ Roll number **{roll_input}** not found. Please check and try again.")

        else:
            student = match.iloc[0]
            rl      = student["Risk_Level"]

            st.divider()

            # Welcome banner
            st.markdown(
                f"""
                <div style='
                    background: #111827;
                    border: 1px solid rgba(99,102,241,0.3);
                    border-radius: 16px;
                    padding: 20px 28px;
                    text-align: center;
                '>
                    <h3 style='color:#e2e8f0; margin:0'>Roll No: {student['Roll_No']}</h3>
                    <p style='color:{RISK_COLOR[rl]}; font-size:1.2rem; font-weight:600; margin:8px 0 0 0'>
                        {RISK_EMOJI[rl]} {rl} Student
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.divider()

            # Key metrics
            marks_cols = [f"{s}_Marks" for s in subjects]
            att_cols   = [f"{s}_Attendance" for s in subjects]
            avg_marks  = round(student[marks_cols].mean(), 1)
            avg_att    = round(student[att_cols].mean(), 1)
            pred       = model.predict([student[att_cols].values])[0]

            c1, c2, c3 = st.columns(3)
            c1.metric("Your Avg Marks",      avg_marks)
            c2.metric("Your Avg Attendance", f"{avg_att}%")
            c3.metric("Your Risk Score",     student["Risk_Score"])

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

            # Subject-wise breakdown
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
                    "Subject":         s,
                    "Your Marks":      m,
                    "Marks Gap":       m_gap,
                    "Your Attendance": a,
                    "Attendance Gap":  a_gap,
                    "Status":          status,
                    "What to do":      tip,
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

            # Bar chart
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
            fig.add_hline(
                y=SAFE_MARKS, line_dash="dash",
                line_color="#E24B4A", line_width=2,
                annotation_text=f"Target ({SAFE_MARKS})",
                annotation_position="top right"
            )
            fig.update_yaxes(range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Improvement summary
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
