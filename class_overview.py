import streamlit as st
import plotly.express as px
from uploader import RISK_COLOR, RISK_EMOJI


def show_class_overview(df, subjects, n_critical, n_at_risk):
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
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    avg = df[[c for c in df.columns if "_Marks" in c]].mean().reset_index()
    avg.columns = ["Subject", "Marks"]
    avg["Subject"] = avg["Subject"].str.replace("_Marks", "")

    fig = px.bar(avg, x="Subject", y="Marks",
                 title="Subject Performance", template="plotly_dark")
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), transition_duration=500)
    st.plotly_chart(fig, use_container_width=True)
