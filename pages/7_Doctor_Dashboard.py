"""
pages/7_Doctor_Dashboard.py
------------------------------
Doctor consultation dashboard: today's patients, upcoming patients,
completed consultations, cancel appointment, patient details/search,
and prescription upload/entry.
"""

import os
import sys
from datetime import date, datetime

import streamlit as st
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import auth
import utils
import qr_generator

st.set_page_config(page_title="Doctor Dashboard | City Care Hospital", page_icon="🩺", layout="wide")
db.init_db()

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🩺 Doctor Dashboard")

if "doctor_logged_in_id" not in st.session_state:
    st.session_state.doctor_logged_in_id = None

# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------
if not st.session_state.doctor_logged_in_id:
    st.info("🔐 Doctor access only. Please log in.")
    doctors = db.get_all_doctors()
    doctor_ids = [d["doctor_id"] for d in doctors]
    with st.form("doctor_login_form"):
        doctor_id = st.selectbox("Doctor ID", doctor_ids)
        password = st.text_input("Password", type="password")
        st.caption("Demo password for all doctors: `doctor123`")
        submitted = st.form_submit_button("Login", use_container_width=True)
    if submitted:
        doctor = auth.authenticate_doctor(doctor_id, password)
        if doctor:
            st.session_state.doctor_logged_in_id = doctor_id
            st.rerun()
        else:
            st.error("Invalid Doctor ID or password.")
    st.stop()

doctor = db.get_doctor_by_id(st.session_state.doctor_logged_in_id)

top = st.columns([3, 1])
with top[0]:
    st.subheader(f"Welcome, {doctor['full_name']} 👋")
    st.caption(f"{doctor['department']} · {doctor['branch']}")
with top[1]:
    if st.button("Logout", use_container_width=True):
        st.session_state.doctor_logged_in_id = None
        st.rerun()

today_str = date.today().isoformat()
all_appts = db.get_appointments_by_doctor_date(doctor["doctor_id"], today_str)

tabs = st.tabs(["📋 Today's Patients", "📅 Upcoming Patients", "✅ Completed",
                 "🔍 Search Patient", "💊 Prescription Upload"])

# ---------------- Today's Patients ----------------
with tabs[0]:
    today_patients = [a for a in all_appts if a["status"] == "Scheduled"]
    if today_patients:
        for a in today_patients:
            patient = db.get_patient_by_id(a["patient_id"]) or {}
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
                <div class="hospital-card">
                🎫 Token #{a['token_number']} — <b>{patient.get('full_name', a['patient_id'])}</b><br>
                📞 {patient.get('phone', '-')} &nbsp; | &nbsp; 🕐 {a['time_slot']}<br>
                <b>Reason:</b> {a['reason']}
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("Mark Completed", key=f"complete_{a['appointment_id']}", use_container_width=True):
                    db.update_appointment_status(a["appointment_id"], "Completed")
                    st.rerun()
                if st.button("Cancel", key=f"cancel_{a['appointment_id']}", use_container_width=True):
                    db.update_appointment_status(a["appointment_id"], "Cancelled")
                    if patient:
                        utils.notify_patient(
                            patient["patient_id"], patient.get("email"), patient.get("phone"),
                            f"Your appointment with {doctor['full_name']} on {a['appointment_date']} "
                            "has been cancelled by the doctor. Please rebook if needed.",
                            db,
                        )
                    st.rerun()
                join_url = qr_generator.get_consultation_link(a["appointment_id"])
                st.link_button("🎥 Join Consultation", join_url, key=f"docjoin_{a['appointment_id']}",
                                use_container_width=True)
    else:
        st.info("No patients scheduled for today.")

# ---------------- Upcoming Patients ----------------
with tabs[1]:
    all_doctor_appts = db.run_query(
        "SELECT * FROM Appointments WHERE doctor_id = ? AND appointment_date > ? AND status = 'Scheduled' "
        "ORDER BY appointment_date, token_number",
        (doctor["doctor_id"], today_str), fetch=True,
    )
    if all_doctor_appts:
        df = pd.DataFrame(all_doctor_appts)
        st.dataframe(
            df[["appointment_date", "time_slot", "token_number", "patient_id", "reason"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No upcoming patients beyond today.")

# ---------------- Completed ----------------
with tabs[2]:
    completed = db.run_query(
        "SELECT * FROM Appointments WHERE doctor_id = ? AND status = 'Completed' "
        "ORDER BY appointment_date DESC", (doctor["doctor_id"],), fetch=True,
    )
    if completed:
        df = pd.DataFrame(completed)
        st.dataframe(
            df[["appointment_date", "time_slot", "token_number", "patient_id"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No completed consultations yet.")

# ---------------- Search Patient ----------------
with tabs[3]:
    term = st.text_input("Search patient by ID, name, or phone")
    if term:
        results = db.search_patients(term)
        if results:
            for p in results:
                st.markdown(f"""
                <div class="hospital-card">
                <b>{p['full_name']}</b> ({p['patient_id']})<br>
                📞 {p['phone']} &nbsp; | &nbsp; 🩸 {p['blood_group']} &nbsp; | &nbsp; 🎂 Age {p['age']}<br>
                <b>Medical History:</b> {p['medical_history'] or 'None recorded'}
                </div><br>
                """, unsafe_allow_html=True)
        else:
            st.warning("No matching patients found.")

# ---------------- Prescription Upload ----------------
with tabs[4]:
    completed_or_today = [a for a in all_appts]
    all_patient_appts = db.run_query(
        "SELECT * FROM Appointments WHERE doctor_id = ? ORDER BY appointment_date DESC",
        (doctor["doctor_id"],), fetch=True,
    )
    if all_patient_appts:
        options = {
            f"{a['appointment_id']} — {a['patient_id']} on {a['appointment_date']}": a
            for a in all_patient_appts
        }
        selected_label = st.selectbox("Select Appointment", list(options.keys()))
        selected_appt = options[selected_label]
        patient = db.get_patient_by_id(selected_appt["patient_id"])

        with st.form("prescription_form"):
            diagnosis = st.text_area("Diagnosis")
            prescription_text = st.text_area("Prescription (one instruction per line)",
                                              placeholder="e.g. Paracetamol 500mg - twice daily for 3 days")
            prescription_file = st.file_uploader("Upload Prescription File (optional)", type=["pdf", "png", "jpg", "jpeg"])
            submit_presc = st.form_submit_button("Save Prescription", use_container_width=True)

        if submit_presc:
            file_path = None
            if prescription_file is not None:
                upload_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "prescriptions"
                )
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, f"{selected_appt['appointment_id']}_{prescription_file.name}")
                with open(file_path, "wb") as f:
                    f.write(prescription_file.getbuffer())

            record = {
                "patient_id": selected_appt["patient_id"],
                "appointment_id": selected_appt["appointment_id"],
                "doctor_id": doctor["doctor_id"],
                "diagnosis": diagnosis.strip(),
                "prescription": prescription_text.strip(),
                "prescription_file": file_path,
                "visit_date": datetime.now().isoformat()[:10],
            }
            db.insert_medical_record(record)

            if patient:
                utils.notify_patient(
                    patient["patient_id"], patient.get("email"), patient.get("phone"),
                    f"Dr. {doctor['full_name']} has uploaded your prescription. "
                    "Please check your patient dashboard.",
                    db,
                )
            st.success("✅ Prescription saved successfully.")
    else:
        st.info("No appointments found to attach a prescription to.")
