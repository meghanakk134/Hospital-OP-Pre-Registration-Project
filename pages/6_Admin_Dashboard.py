"""
pages/6_Admin_Dashboard.py
-----------------------------
Professional admin dashboard: KPI cards, Plotly charts (pie/line/bar),
search module, and downloadable PDF/CSV reports (daily/weekly/monthly/
department/doctor/patient).
"""

import os
import sys
from datetime import datetime, date, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import auth
import pdf_generator

st.set_page_config(page_title="Admin Dashboard | City Care Hospital", page_icon="📊", layout="wide")
db.init_db()

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

PRIMARY = "#0066CC"
SECONDARY = "#00B894"
CHART_COLORS = [PRIMARY, SECONDARY, "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899",
                "#14B8A6", "#F97316", "#6366F1", "#84CC16", "#06B6D4"]

st.title("📊 Admin Dashboard")

# ------------------------------------------------------------------
# Admin login gate
# ------------------------------------------------------------------
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.info("🔐 Admin access only. Please log in.")
    with st.form("admin_login_form"):
        username = st.text_input("Username", value="")
        password = st.text_input("Password", type="password")
        st.caption("Demo credentials → username: `admin`, password: `admin123`")
        submitted = st.form_submit_button("Login", use_container_width=True)
    if submitted:
        admin = auth.authenticate_admin(username.strip(), password)
        if admin:
            st.session_state.admin_logged_in = True
            st.session_state.admin_username = admin["username"]
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.stop()

top = st.columns([4, 1])
with top[1]:
    if st.button("Logout", use_container_width=True):
        st.session_state.admin_logged_in = False
        st.rerun()

# ------------------------------------------------------------------
# Load data
# ------------------------------------------------------------------
patients = db.get_all_patients()
appointments = db.get_all_appointments()
payments = db.get_all_payments()
doctors = db.get_all_doctors()

df_patients = pd.DataFrame(patients) if patients else pd.DataFrame()
df_appointments = pd.DataFrame(appointments) if appointments else pd.DataFrame()
df_payments = pd.DataFrame(payments) if payments else pd.DataFrame()
df_doctors = pd.DataFrame(doctors) if doctors else pd.DataFrame()

today_str = date.today().isoformat()

today_registrations = 0
if not df_patients.empty:
    today_registrations = df_patients["created_at"].astype(str).str.startswith(today_str).sum()

today_appointments = 0
if not df_appointments.empty:
    today_appointments = (df_appointments["appointment_date"] == today_str).sum()

total_revenue = df_payments["amount"].sum() if not df_payments.empty else 0
doctors_available = (df_doctors["available"] == 1).sum() if not df_doctors.empty else 0

patients_waiting = 0
if not df_appointments.empty:
    patients_waiting = ((df_appointments["appointment_date"] == today_str) &
                         (df_appointments["status"] == "Scheduled")).sum()

cancelled_count = 0
if not df_appointments.empty:
    cancelled_count = (df_appointments["status"] == "Cancelled").sum()

# ------------------------------------------------------------------
# KPI Cards
# ------------------------------------------------------------------
st.markdown("### Overview")
k1, k2, k3, k4, k5, k6 = st.columns(6)
kpis = [
    (k1, today_registrations, "Today's Registrations"),
    (k2, today_appointments, "Today's Appointments"),
    (k3, f"₹{total_revenue:,.0f}", "Total Revenue"),
    (k4, doctors_available, "Doctors Available"),
    (k5, patients_waiting, "Patients Waiting"),
    (k6, cancelled_count, "Cancelled Appointments"),
]
for col, value, label in kpis:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ------------------------------------------------------------------
# Charts
# ------------------------------------------------------------------
st.markdown("### Analytics")
chart_row1 = st.columns(2)

with chart_row1[0]:
    st.markdown("#### Department-Wise Patients")
    if not df_appointments.empty:
        dept_counts = df_appointments["department"].value_counts().reset_index()
        dept_counts.columns = ["Department", "Count"]
        fig = px.pie(dept_counts, names="Department", values="Count", hole=0.45,
                     color_discrete_sequence=CHART_COLORS)
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No appointment data yet.")

with chart_row1[1]:
    st.markdown("#### Most Visited Departments (Bar)")
    if not df_appointments.empty:
        dept_counts = df_appointments["department"].value_counts().reset_index()
        dept_counts.columns = ["Department", "Visits"]
        fig = px.bar(dept_counts, x="Department", y="Visits", color="Department",
                     color_discrete_sequence=CHART_COLORS)
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No appointment data yet.")

chart_row2 = st.columns(2)
with chart_row2[0]:
    st.markdown("#### Monthly Registrations")
    if not df_patients.empty:
        dfp = df_patients.copy()
        dfp["created_at"] = pd.to_datetime(dfp["created_at"], errors="coerce")
        dfp["month"] = dfp["created_at"].dt.to_period("M").astype(str)
        monthly = dfp.groupby("month").size().reset_index(name="Registrations")
        fig = px.line(monthly, x="month", y="Registrations", markers=True,
                       color_discrete_sequence=[PRIMARY])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No patient data yet.")

with chart_row2[1]:
    st.markdown("#### Revenue Analysis")
    if not df_payments.empty:
        dfpay = df_payments.copy()
        dfpay["transaction_date"] = pd.to_datetime(dfpay["transaction_date"], errors="coerce")
        dfpay["day"] = dfpay["transaction_date"].dt.date.astype(str)
        rev = dfpay.groupby("day")["amount"].sum().reset_index()
        fig = px.bar(rev, x="day", y="amount", color_discrete_sequence=[SECONDARY])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), yaxis_title="Revenue (₹)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No payment data yet.")

st.markdown("#### Doctor Performance (Consultations Handled)")
if not df_appointments.empty:
    doc_counts = df_appointments["doctor_id"].value_counts().reset_index()
    doc_counts.columns = ["doctor_id", "Consultations"]
    if not df_doctors.empty:
        doc_counts = doc_counts.merge(df_doctors[["doctor_id", "full_name"]], on="doctor_id", how="left")
    fig = px.bar(doc_counts, x="full_name" if "full_name" in doc_counts else "doctor_id",
                 y="Consultations", color_discrete_sequence=CHART_COLORS)
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="Doctor")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No appointment data yet.")

st.divider()

# ------------------------------------------------------------------
# Search module
# ------------------------------------------------------------------
st.markdown("### 🔍 Search")
search_cols = st.columns([3, 1])
with search_cols[0]:
    search_term = st.text_input("Search by Patient ID, Phone Number, Doctor, Department, or Date")
with search_cols[1]:
    search_btn = st.button("Search", use_container_width=True)

if search_btn and search_term.strip():
    term = search_term.strip()
    st.markdown("**Matching Patients**")
    matched_patients = db.search_patients(term)
    if matched_patients:
        st.dataframe(pd.DataFrame(matched_patients)[
            ["patient_id", "full_name", "phone", "email", "city"]
        ], use_container_width=True, hide_index=True)
    else:
        st.caption("No matching patients.")

    st.markdown("**Matching Appointments**")
    if not df_appointments.empty:
        mask = (
            df_appointments["patient_id"].astype(str).str.contains(term, case=False, na=False) |
            df_appointments["doctor_id"].astype(str).str.contains(term, case=False, na=False) |
            df_appointments["department"].astype(str).str.contains(term, case=False, na=False) |
            df_appointments["appointment_date"].astype(str).str.contains(term, case=False, na=False)
        )
        matched_appts = df_appointments[mask]
        if not matched_appts.empty:
            st.dataframe(matched_appts, use_container_width=True, hide_index=True)
        else:
            st.caption("No matching appointments.")

st.divider()

# ------------------------------------------------------------------
# Tables
# ------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["👥 Patients", "📅 Appointments", "💳 Payments", "🩺 Doctors"])
with tab1:
    st.dataframe(df_patients, use_container_width=True, hide_index=True) if not df_patients.empty else st.info("No patients yet.")
with tab2:
    st.dataframe(df_appointments, use_container_width=True, hide_index=True) if not df_appointments.empty else st.info("No appointments yet.")
with tab3:
    st.dataframe(df_payments, use_container_width=True, hide_index=True) if not df_payments.empty else st.info("No payments yet.")
with tab4:
    st.dataframe(df_doctors, use_container_width=True, hide_index=True) if not df_doctors.empty else st.info("No doctors yet.")

st.divider()

# ------------------------------------------------------------------
# Reports
# ------------------------------------------------------------------
st.markdown("### 📑 Reports")
report_type = st.selectbox(
    "Report Type",
    ["Daily Report", "Weekly Report", "Monthly Report", "Department Report",
     "Doctor Report", "Patient Report"],
)

report_df = pd.DataFrame()
if not df_appointments.empty:
    dfa = df_appointments.copy()
    dfa["appointment_date"] = pd.to_datetime(dfa["appointment_date"], errors="coerce")
    today_ts = pd.Timestamp(date.today())

    if report_type == "Daily Report":
        report_df = dfa[dfa["appointment_date"] == today_ts]
    elif report_type == "Weekly Report":
        report_df = dfa[dfa["appointment_date"] >= today_ts - pd.Timedelta(days=7)]
    elif report_type == "Monthly Report":
        report_df = dfa[dfa["appointment_date"] >= today_ts - pd.Timedelta(days=30)]
    elif report_type == "Department Report":
        report_df = dfa.groupby("department").size().reset_index(name="Total Appointments")
    elif report_type == "Doctor Report":
        report_df = dfa.groupby("doctor_id").size().reset_index(name="Total Appointments")
    elif report_type == "Patient Report":
        report_df = dfa.groupby("patient_id").size().reset_index(name="Total Appointments")

if not report_df.empty:
    st.dataframe(report_df, use_container_width=True, hide_index=True)

    csv_bytes = report_df.to_csv(index=False).encode("utf-8")
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button("⬇️ Export CSV", data=csv_bytes,
                            file_name=f"{report_type.replace(' ', '_').lower()}.csv", mime="text/csv",
                            use_container_width=True)
    with dl_col2:
        headers = list(report_df.columns.astype(str))
        rows = report_df.astype(str).values.tolist()
        pdf_bytes = pdf_generator.generate_report_pdf(report_type, headers, rows)
        st.download_button("⬇️ Export PDF", data=pdf_bytes,
                            file_name=f"{report_type.replace(' ', '_').lower()}.pdf", mime="application/pdf",
                            use_container_width=True)
else:
    st.info("No data available for this report yet.")
