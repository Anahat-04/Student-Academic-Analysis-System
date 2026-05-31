import streamlit as st
import pandas as pd
import plotly.express as px
from uploader import highlight_risk


def show_students_at_risk(df, subjects, n_critical, n_at_risk, n_safe):
    st.subheader("Students at Risk")
    st.caption("Risk Score = (Avg Marks × 0.6) + (Avg Attendance × 0.4) · Critical <45 · At Risk 45–65 · Safe >65")

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Critical", int(n_critical))
    c2.metric("🟡 At Risk",  int(n_at_risk))
    c3.metric("🟢 Safe",     int(n_safe))

    st.divider()

    fig_donut = px.pie(
        pd.DataFrame({"Status": ["Critical", "At Risk", "Safe"],
                      "Count":  [n_critical, n_at_risk, n_safe]}),
        names="Status", values="Count", hole=0.55,
        color="Status",
        color_discrete_map={"Critical": "#E24B4A", "At Risk": "#EF9F27", "Safe": "#1D9E75"},
        title="Risk Distribution", template="plotly_dark"
    )
    fig_donut.update_traces(textposition="inside", textinfo="percent+label", rotation=90)
    fig_donut.update_layout(transition=dict(duration=700, easing="cubic-in-out"))
    st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()

    filter_level = st.selectbox("Filter by risk level", ["All", "Critical", "At Risk", "Safe"])

    display_cols = (
        ["Roll_No", "Risk_Level", "Risk_Score"]
        + [f"{s}_Marks" for s in subjects]
        + [f"{s}_Attendance" for s in subjects]
    )

    filtered = df if filter_level == "All" else df[df["Risk_Level"] == filter_level]
    filtered = filtered.sort_values("Risk_Score")

    st.dataframe(
        filtered[display_cols]
        .style.map(highlight_risk, subset=["Risk_Level"])
        .format(precision=1),
        use_container_width=True
    )
