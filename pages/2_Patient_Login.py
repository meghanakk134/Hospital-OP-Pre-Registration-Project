"""
pages/2_Patient_Login.py
-------------------------
Patient login via Patient ID or Phone Number + simulated OTP, followed by
a personal dashboard: details, upcoming appointments, medical history,
previous visits, prescription downloads, and QR code.
"""

import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import auth
import utils
import qr_generator
import pdf_generator

st.set_page_config(page_title="Patient Login | City Care Hospital", page_icon="🔐", layout="wide")
db.init_db()

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🔐 Patient Login")

if "logged_in_patient_id" not in st.session_state:
    st.session_state.logged_in_patient_id = None
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = None
if "otp_target_patient" not in st.session_state:
    st.session_state.otp_target_patient = None

# ------------------------------------------------------------------
# Already logged in -> show dashboard
# ------------------------------------------------------------------
if st.session_state.logged_in_patient_id:
    patient = db.get_patient_by_id(st.session_state.logged_in_patient_id)
    if not patient:
        st.session_state.logged_in_patient_id = None
        st.rerun()

    top = st.columns([3, 1])
    with top[0]:
        st.subheader(f"Welcome, {patient['full_name']} 👋")
        st.caption(f"Patient ID: {patient['patient_id']}")
    with top[1]:
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in_patient_id = None
            st.rerun()

    tabs = st.tabs(["👤 Personal Details", "📅 Upcoming Appointments", "🧾 Medical History",
                     "🕘 Previous Visits", "💊 Prescriptions", "📱 QR Code"])

    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="hospital-card">
            <b>Full Name:</b> {patient['full_name']}<br>
            <b>Gender:</b> {patient['gender']}<br>
            <b>Date of Birth:</b> {patient['dob']}<br>
            <b>Age:</b> {patient['age']}<br>
            <b>Blood Group:</b> {patient['blood_group']}<br>
            <b>Phone:</b> {patient['phone']}<br>
            <b>Email:</b> {patient['email'] or '-'}
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="hospital-card">
            <b>Address:</b> {patient['address']}<br>
            <b>City/State/PIN:</b> {patient['city']}, {patient['state']} - {patient['pincode']}<br>
            <b>Emergency Contact:</b> {patient['emergency_contact']}<br>
            <b>Insurance Provider:</b> {patient['insurance_provider'] or 'N/A'}<br>
            <b>Insurance ID:</b> {patient['insurance_id'] or 'N/A'}
            </div>
            """, unsafe_allow_html=True)
        if patient.get("photo_path") and os.path.exists(patient["photo_path"]):
            st.image(patient["photo_path"], width=150, caption="Profile Photo")

    with tabs[1]:
        appts = db.get_appointments_by_patient(patient["patient_id"])
        upcoming = [a for a in appts if a["status"] == "Scheduled"]
        if upcoming:
            for a in upcoming:
                doctor = db.get_doctor_by_id(a["doctor_id"]) or {}
                hosp_line = f"🏥 {a['hospital_name']}<br>" if a.get("hospital_name") else ""
                st.markdown(f"""
                <div class="hospital-card">
                {hosp_line}<b>{a['department']}</b> — {doctor.get('full_name', a['doctor_id'])}<br>
                📅 {a['appointment_date']} 🕐 {a['time_slot']}<br>
                🎫 Token #{a['token_number']} &nbsp;|&nbsp;
                <span class="badge badge-warning">{a['status']}</span>
                </div>
                """, unsafe_allow_html=True)
                join_url = qr_generator.get_consultation_link(a["appointment_id"])
                st.link_button(
                    "🎥 Join Video Consultation",
                    join_url
                )
                st.write("")
        else:
            st.info("No upcoming appointments.")
        if st.button("📅 Book a New Appointment"):
            st.switch_page("pages/3_Book_Appointment.py")

    with tabs[2]:
        st.markdown(f"""
        <div class="hospital-card">
        {patient['medical_history'] or 'No medical history recorded.'}
        </div>
        """, unsafe_allow_html=True)
        records = db.get_medical_records_for_patient(patient["patient_id"])
        if records:
            st.markdown("#### Diagnoses on File")
            for r in records:
                st.markdown(f"- **{r['visit_date']}** — {r['diagnosis']}")

    with tabs[3]:
        appts = db.get_appointments_by_patient(patient["patient_id"])
        completed = [a for a in appts if a["status"] == "Completed"]
        cancelled = [a for a in appts if a["status"] == "Cancelled"]
        if completed or cancelled:
            import pandas as pd
            df = pd.DataFrame(appts)
            st.dataframe(
                df[["appointment_date", "department", "doctor_id", "time_slot", "status"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("No previous visits yet.")

    with tabs[4]:
        records = db.get_medical_records_for_patient(patient["patient_id"])
        if records:
            for r in records:
                doctor = db.get_doctor_by_id(r["doctor_id"]) or {}
                st.markdown(f"**{r['visit_date']}** — {doctor.get('full_name', '-')} ({r.get('diagnosis','-')})")
                pdf_bytes = pdf_generator.generate_prescription_pdf(
                    patient, doctor, r["diagnosis"], r["prescription"], r["visit_date"]
                )
                st.download_button(
                    "⬇️ Download Prescription", data=pdf_bytes,
                    file_name=f"prescription_{r['record_id']}.pdf", mime="application/pdf",
                    key=f"presc_{r['record_id']}",
                )
        else:
            st.info("No prescriptions available yet.")

    with tabs[5]:
        qr_bytes = qr_generator.generate_patient_qr(patient["patient_id"], patient["full_name"])
        st.image(qr_bytes, width=220, caption="Show this QR code at the hospital reception")

    st.stop()

# ------------------------------------------------------------------
# Login form
# ------------------------------------------------------------------
login_method = st.radio("Login using:", ["Patient ID", "Phone Number"], horizontal=True)

with st.form("login_form"):
    if login_method == "Patient ID":
        identifier = st.text_input("Enter your Patient ID")
    else:
        identifier = st.text_input("Enter your registered Phone Number")
    request_otp = st.form_submit_button("Send OTP", use_container_width=True)

if request_otp:
    patient = (
        db.get_patient_by_id(identifier.strip()) if login_method == "Patient ID"
        else db.get_patient_by_phone(identifier.strip())
    )
    if not patient:
        st.error("No patient found with the given details. Please register first.")
    else:
        otp = auth.generate_otp()
        st.session_state.otp_sent = otp
        st.session_state.otp_target_patient = patient["patient_id"]
        # Simulated OTP delivery
        utils.send_sms_notification(patient["phone"], f"Your OTP is {otp}")
        st.success(f"OTP sent to registered mobile number ending in {patient['phone'][-4:]}.")
        st.info(f"🧪 Demo mode — your OTP is **{otp}** (in production this would be sent via SMS).")

if st.session_state.otp_sent and st.session_state.otp_target_patient:
    with st.form("otp_form"):
        entered_otp = st.text_input("Enter the 6-digit OTP")
        verify = st.form_submit_button("Verify & Login", use_container_width=True)
    if verify:
        if entered_otp.strip() == st.session_state.otp_sent:
            st.session_state.logged_in_patient_id = st.session_state.otp_target_patient
            st.session_state.otp_sent = None
            st.session_state.otp_target_patient = None
            auth.touch_session(st.session_state)
            st.rerun()
        else:
            st.error("Incorrect OTP. Please try again.")

st.divider()
st.caption("New patient? ")
if st.button("Go to Registration"):
    st.switch_page("pages/1_Patient_Registration.py")
