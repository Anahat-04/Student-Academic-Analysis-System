import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# ── CONSTANTS ──────────────────────────────────────────────────────────────────

RISK_COLOR = {"Critical": "#E24B4A", "At Risk": "#EF9F27", "Safe": "#1D9E75"}
RISK_EMOJI = {"Critical": "🔴",      "At Risk": "🟡",      "Safe": "🟢"}

SAFE_MARKS      = 75
SAFE_ATTENDANCE = 75


# ── SHARED FUNCTIONS ───────────────────────────────────────────────────────────

def normalize_marks(df, cols, max_mark):
    for col in cols:
        df[col] = ((pd.to_numeric(df[col], errors="coerce") / max_mark) * 100).clip(0, 100)
    return df


def performance_score(row, subjects):
    marks = np.mean([row[f"{s}_Marks"] for s in subjects])
    att   = np.mean([row[f"{s}_Attendance"] for s in subjects])
    return round((marks * 0.7) + (att * 0.3), 2)


def risk_score(row, subjects):
    marks       = np.mean([row[f"{s}_Marks"] for s in subjects])
    att         = np.mean([row[f"{s}_Attendance"] for s in subjects])
    performance = (marks * 0.6) + (att * 0.4)
    return round(100 - performance, 2)


def classify_risk(score):
    if score >= 55:
        return "Critical"
    elif score >= 35:
        return "At Risk"
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


# ── FILE UPLOAD & PREPROCESSING ────────────────────────────────────────────────

def load_and_preprocess(file):
    """
    Handles file upload, column mapping, normalization, and validation.
    Returns (df, subjects) or stops execution on error.
    """
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
        # Manual column mapping UI
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

    # Validate
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

    return df, subjects
