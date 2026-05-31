import streamlit as st
from io import BytesIO
from groq import Groq
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from uploader import RISK_COLOR, RISK_EMOJI, SAFE_MARKS, SAFE_ATTENDANCE


def show_ai_report(df, subjects):
    st.subheader("AI Generated Student Report")
    st.caption("Powered by Groq AI — generates a personalized academic report for each student")

    roll    = st.selectbox(
        "Select Student",
        sorted(df["Roll_No"].astype(str), key=lambda x: int(x) if x.isdigit() else x)
    )
    student = df[df["Roll_No"].astype(str) == roll].iloc[0]
    rl      = student["Risk_Level"]

    st.markdown(
        f"**Risk Status:** "
        f"<span style='color:{RISK_COLOR[rl]};font-weight:600'>"
        f"{RISK_EMOJI[rl]} {rl}</span> &nbsp;|&nbsp; "
        f"**Risk Score:** {student['Risk_Score']}",
        unsafe_allow_html=True,
    )

    st.divider()

    # Build prompt
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
Risk Level      : {rl}
Risk Score      : {student['Risk_Score']} out of 100
Avg Marks       : {avg_marks} out of 100
Avg Attendance  : {avg_att}%

Subject-wise breakdown:
{subject_details}

Safe target thresholds: {SAFE_MARKS} marks and {SAFE_ATTENDANCE}% attendance in every subject.

Write a professional and personalized academic performance report covering these sections:

1. Overall Assessment — summarize the student's current academic standing clearly
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

                pdf_file = _generate_pdf(
                    student_id=roll,
                    risk_level=rl,
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


def _generate_pdf(student_id, risk_level, risk_score, report_text):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40,   bottomMargin=30
    )

    styles   = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        "<font size=20 color='#4f46e5'><b>Student Performance Report</b></font>",
        styles['Title']
    ))
    elements.append(Spacer(1, 20))

    info_data = [
        ["Student ID", student_id],
        ["Risk Level", risk_level],
        ["Risk Score", f"{risk_score}/100"],
    ]
    table = Table(info_data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#4f46e5")),
        ('TEXTCOLOR',  (0, 0), (0, -1), colors.white),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#f3f4f6")),
        ('TEXTCOLOR',  (1, 0), (1, -1), colors.black),
        ('FONTNAME',   (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#d1d5db")),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 25))

    elements.append(Paragraph(
        f"<font size=11>{report_text.replace(chr(10), '<br/>')}</font>",
        styles['BodyText']
    ))
    elements.append(Spacer(1, 30))

    elements.append(Paragraph(
        "<font size=9 color='gray'>Generated by AI Student Analytics System</font>",
        styles['Normal']
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
