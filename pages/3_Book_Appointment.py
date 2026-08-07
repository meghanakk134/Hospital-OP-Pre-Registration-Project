"""
pages/3_Book_Appointment.py
-----------------------------
OP appointment booking, two steps:
  1. Pick one of 10-15 multi-speciality hospitals from a grid.
  2. Pick department, doctor, date, time slot, reason, language, payment type
     for that specific hospital.

Generates a token, prevents duplicate bookings, shows an AI-estimated
waiting time, and — after booking — issues a QR code that opens a live
video consultation with the doctor directly when scanned.
"""

import os
import sys
from datetime import date, timedelta, datetime

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import utils
import qr_generator

st.set_page_config(page_title="Book Appointment | City Care Hospital", page_icon="📅", layout="wide")
db.init_db()

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📅 Book an OP Appointment")

if not st.session_state.get("logged_in_patient_id"):
    st.warning("Please log in as a patient first to book an appointment.")
    if st.button("Go to Patient Login"):
        st.switch_page("pages/2_Patient_Login.py")
    st.stop()

patient = db.get_patient_by_id(st.session_state.logged_in_patient_id)
st.caption(f"Booking for: **{patient['full_name']}** ({patient['patient_id']})")

if "booking_hospital_id" not in st.session_state:
    st.session_state.booking_hospital_id = None

# ------------------------------------------------------------------
# STEP 1 — Choose a hospital from the grid
# ------------------------------------------------------------------
if not st.session_state.booking_hospital_id:
    st.markdown("### 🏥 Step 1 — Choose a Hospital")
    st.caption("Select one of our multi-speciality hospitals to see its doctors and available slots.")

    hospitals = db.get_all_hospitals()

    if not hospitals:
        st.error("No hospitals configured yet. Please contact the administrator.")
        st.stop()

    cols_per_row = 5
    for row_start in range(0, len(hospitals), cols_per_row):
        row = hospitals[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row, gap="medium")
        for col, hosp in zip(cols, row):
            with col:
                stars = "⭐" * int(round(hosp["rating"]))
                st.markdown(f"""
                <div class="hosp-pick-card">
                    <div class="hosp-icon">{hosp['icon']}</div>
                    <h4>{hosp['name']}</h4>
                    <div class="hosp-loc">📍 {hosp['city']}</div>
                    <div class="hosp-rating">{stars} {hosp['rating']}</div>
                    <div style="font-size:12px;color:#5d6b87;">{hosp['specialties']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Select Hospital", key=f"pick_{hosp['hospital_id']}", use_container_width=True):
                    st.session_state.booking_hospital_id = hosp["hospital_id"]
                    st.rerun()
    st.stop()

# ------------------------------------------------------------------
# STEP 2 — Book with the selected hospital
# ------------------------------------------------------------------
hospital = db.get_hospital_by_id(st.session_state.booking_hospital_id)
if not hospital:
    st.session_state.booking_hospital_id = None
    st.rerun()

top_l, top_r = st.columns([4, 1])
with top_l:
    st.markdown(f"""
    <div class="hosp-selected-banner">
    {hospital['icon']} <b>{hospital['name']}</b> &nbsp;|&nbsp; 📍 {hospital['address']}, {hospital['city']}
    &nbsp;|&nbsp; ⭐ {hospital['rating']} &nbsp;|&nbsp; 📞 {hospital['phone']}
    </div>
    """, unsafe_allow_html=True)
with top_r:
    if st.button("🔁 Change Hospital", use_container_width=True):
        st.session_state.booking_hospital_id = None
        st.rerun()

st.markdown("### 📝 Step 2 — Appointment Details")

# ------------------------------------------------------------------
# AI Symptom Checker (optional helper before booking)
# ------------------------------------------------------------------
with st.expander("🤖 AI Symptom Checker (optional) — not a medical diagnosis"):
    symptoms = st.text_input("Describe your symptoms briefly", placeholder="e.g. chest pain and dizziness")
    if symptoms:
        suggested_dept = utils.ai_suggest_department(symptoms)
        st.info(f"Based on your symptoms, we suggest visiting: **{suggested_dept}**. "
                "This is a demo suggestion only — please consult General Medicine if unsure.")

st.divider()

departments = db.get_all_departments()
dept_names = [d["name"] for d in departments]

col1, col2 = st.columns(2)
with col1:
    department = st.selectbox("Department *", dept_names)
with col2:
    doctors = db.get_doctors_by_hospital_department(hospital["hospital_id"], department)
    doctor_options = {f"{d['full_name']} (Fee: ₹{d['consultation_fee']:.0f})": d for d in doctors}
    if not doctor_options:
        st.warning("No doctors currently available in this department at this hospital.")
        doctor_choice = None
    else:
        doctor_choice_label = st.selectbox("Doctor *", list(doctor_options.keys()))
        doctor_choice = doctor_options[doctor_choice_label]

# AI doctor recommendation
if doctors:
    recommended = utils.ai_recommend_doctor(department, doctors)
    if recommended:
        st.caption(f"🤖 AI Recommendation: **{recommended['full_name']}** has the shortest expected wait today.")

col4, col5 = st.columns(2)
with col4:
    appt_date = st.date_input("Appointment Date *", value=date.today() + timedelta(days=1),
                               min_value=date.today(), max_value=date.today() + timedelta(days=30))
with col5:
    time_slot = st.selectbox("Available Time Slot *", utils.generate_time_slots())

reason = st.text_area("Reason for Visit *", placeholder="Briefly describe your reason for the visit")

col6, col7 = st.columns(2)
with col6:
    preferred_language = st.selectbox("Preferred Language", ["English", "Hindi", "Telugu"])
with col7:
    payment_type = st.selectbox("Payment Type *", ["Cash", "UPI", "Credit Card", "Insurance"])

if doctor_choice:
    patients_ahead = len(db.get_appointments_by_doctor_date(doctor_choice["doctor_id"], str(appt_date)))
    est_wait = utils.ai_predict_wait_time(patients_ahead, department)
    st.markdown(f"""
    <div class="hospital-card">
    🧑‍🤝‍🧑 Patients ahead of you (est.): <b>{patients_ahead}</b><br>
    ⏱️ AI-estimated waiting time: <b>{est_wait} minutes</b>
    </div>
    """, unsafe_allow_html=True)

st.divider()

if st.button("Confirm Booking", type="primary", use_container_width=True, disabled=(not doctor_choice)):
    if not reason.strip():
        st.error("Please enter a reason for your visit.")
    elif db.check_duplicate_booking(patient["patient_id"], doctor_choice["doctor_id"], str(appt_date)):
        st.error("You already have an appointment with this doctor on this date. "
                 "Please choose a different date or check your Token Status page.")
    else:
        token_number = db.get_next_token_number(doctor_choice["doctor_id"], str(appt_date))
        appointment_id = utils.generate_appointment_id()
        appointment = {
            "appointment_id": appointment_id,
            "patient_id": patient["patient_id"],
            "doctor_id": doctor_choice["doctor_id"],
            "department": department,
            "branch": hospital["name"],
            "hospital_id": hospital["hospital_id"],
            "hospital_name": hospital["name"],
            "appointment_date": str(appt_date),
            "time_slot": time_slot,
            "reason": reason.strip(),
            "preferred_language": preferred_language,
            "payment_type": payment_type,
            "status": "Scheduled",
            "token_number": token_number,
            "created_at": datetime.now().isoformat(),
        }
        db.insert_appointment(appointment)
        db.insert_token(appointment_id, token_number, department, str(appt_date))

        utils.notify_patient(
            patient["patient_id"], patient["email"], patient["phone"],
            f"Appointment confirmed at {hospital['name']} with {doctor_choice['full_name']} on "
            f"{appt_date} at {time_slot}. Your token number is {token_number}.",
            db,
        )

        st.session_state.last_booked_appointment = appointment
        st.success(f"✅ Appointment booked at **{hospital['name']}**! Your OP Token Number is **{token_number}**.")
        st.balloons()

        qr_bytes, join_url = qr_generator.generate_consultation_qr(appointment_id)

        c1, c2 = st.columns([1, 1.4])
        with c1:
            st.markdown('<div class="consult-qr-card">', unsafe_allow_html=True)
            st.image(qr_bytes, caption="📱 Scan to consult your doctor directly", width=220)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            **Hospital:** {hospital['name']}  
            **Appointment ID:** {appointment_id}  
            **Doctor:** {doctor_choice['full_name']}  
            **Department:** {department}  
            **Date & Time:** {appt_date} · {time_slot}  
            **Token Number:** {token_number}
            """)
            st.info("Scanning this QR code opens a live video consultation room instantly — "
                    "no login or app install needed. It works for both you and your doctor.")
            st.link_button("🎥 Join Video Consultation Now", join_url, use_container_width=True)
            if st.button("Proceed to Payment →", use_container_width=True):
                st.session_state.pending_payment_appointment_id = appointment_id
                st.switch_page("pages/4_Payment.py")
