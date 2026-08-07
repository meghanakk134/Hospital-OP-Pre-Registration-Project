"""
pages/1_Patient_Registration.py
--------------------------------
New patient registration form with validation, SQLite storage,
automatic Patient ID generation, and QR code + PDF confirmation.
"""

import os
import sys
from datetime import date, datetime

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import utils
import auth
import qr_generator
import pdf_generator

st.set_page_config(page_title="Patient Registration | City Care Hospital", page_icon="📝", layout="wide")
db.init_db()

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📝 Patient Registration")
st.caption("Please fill in accurate details — this information will be used for your OP records.")

if "registered_patient" in st.session_state:
    patient = st.session_state.registered_patient
    st.success(f"✅ Registration successful! Your Patient ID is **{patient['patient_id']}**")

    col1, col2 = st.columns([1, 1])
    with col1:
        qr_bytes = qr_generator.generate_patient_qr(patient["patient_id"], patient["full_name"])
        st.image(qr_bytes, caption="Your Patient QR Code", width=200)
    with col2:
        pdf_bytes = pdf_generator.generate_registration_pdf(patient, qr_bytes)
        st.download_button(
            "⬇️ Download Registration Confirmation (PDF)",
            data=pdf_bytes,
            file_name=f"{patient['patient_id']}_registration.pdf",
            mime="application/pdf",
        )
        if st.button("Book an Appointment now →"):
            st.session_state.logged_in_patient_id = patient["patient_id"]
            st.switch_page("pages/3_Book_Appointment.py")
        if st.button("Register another patient"):
            del st.session_state["registered_patient"]
            st.rerun()
    st.stop()

with st.form("registration_form", clear_on_submit=False):
    st.subheader("Personal Details")
    c1, c2, c3 = st.columns(3)
    with c1:
        full_name = st.text_input("Full Name *")
        gender = st.selectbox("Gender *", ["Male", "Female", "Other"])
    with c2:
        dob = st.date_input(
            "Date of Birth *", value=date(1995, 1, 1),
            min_value=date(1900, 1, 1), max_value=date.today(),
        )
        blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])
    with c3:
        age = utils.calculate_age(dob)
        st.number_input("Age (auto-calculated)", value=age, disabled=True)
        phone = st.text_input("Phone Number *", placeholder="10-digit mobile number")

    c4, c5 = st.columns(2)
    with c4:
        email = st.text_input("Email", placeholder="optional")
    with c5:
        aadhaar = st.text_input("Aadhaar Number", placeholder="12-digit (optional)")

    st.subheader("Address")
    address = st.text_area("Address *")
    c6, c7, c8 = st.columns(3)
    with c6:
        city = st.text_input("City *")
    with c7:
        state = st.text_input("State *")
    with c8:
        pincode = st.text_input("PIN Code *")

    st.subheader("Emergency & Medical Info")
    emergency_contact = st.text_input("Emergency Contact Number *")
    medical_history = st.text_area("Medical History", placeholder="Any known conditions, allergies, past surgeries...")

    st.subheader("Insurance Details (Optional)")
    c9, c10 = st.columns(2)
    with c9:
        insurance_provider = st.text_input("Insurance Provider")
    with c10:
        insurance_id = st.text_input("Insurance ID")

    st.subheader("Profile Photo")
    photo = st.file_uploader("Upload Profile Photo", type=["png", "jpg", "jpeg"])

    st.subheader("Account Security")
    c11, c12 = st.columns(2)
    with c11:
        password = st.text_input("Create Password *", type="password")
    with c12:
        confirm_password = st.text_input("Confirm Password *", type="password")

    submitted = st.form_submit_button("Register", use_container_width=True)

if submitted:
    errors = []
    if not full_name.strip():
        errors.append("Full name is required.")
    if not utils.is_valid_phone(phone):
        errors.append("Enter a valid 10-digit Indian mobile number starting with 6-9.")
    if not utils.is_valid_email(email):
        errors.append("Enter a valid email address.")
    if not utils.is_valid_aadhaar(aadhaar):
        errors.append("Aadhaar number must be exactly 12 digits.")
    if not address.strip():
        errors.append("Address is required.")
    if not city.strip() or not state.strip():
        errors.append("City and State are required.")
    if not utils.is_valid_pincode(pincode):
        errors.append("PIN code must be exactly 6 digits.")
    if not utils.is_valid_phone(emergency_contact):
        errors.append("Enter a valid 10-digit emergency contact number.")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if db.get_patient_by_phone(phone):
        errors.append("A patient with this phone number is already registered. Please login instead.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        photo_path = None
        if photo is not None:
            upload_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "patient_photos"
            )
            os.makedirs(upload_dir, exist_ok=True)
            patient_id_temp = utils.generate_patient_id()
            photo_path = os.path.join(upload_dir, f"{patient_id_temp}_{photo.name}")
            with open(photo_path, "wb") as f:
                f.write(photo.getbuffer())
        else:
            patient_id_temp = utils.generate_patient_id()

        new_patient = {
            "patient_id": patient_id_temp,
            "full_name": full_name.strip(),
            "gender": gender,
            "dob": str(dob),
            "age": age,
            "blood_group": blood_group,
            "phone": phone.strip(),
            "email": email.strip(),
            "aadhaar": aadhaar.strip(),
            "address": address.strip(),
            "city": city.strip(),
            "state": state.strip(),
            "pincode": pincode.strip(),
            "emergency_contact": emergency_contact.strip(),
            "medical_history": medical_history.strip(),
            "insurance_provider": insurance_provider.strip(),
            "insurance_id": insurance_id.strip(),
            "photo_path": photo_path,
            "password_hash": auth.hash_password(password),
            "created_at": datetime.now().isoformat(),
        }
        db.insert_patient(new_patient)
        utils.notify_patient(
            new_patient["patient_id"], new_patient["email"], new_patient["phone"],
            f"Welcome to City Care Hospital! Your Patient ID is {new_patient['patient_id']}.",
            db,
        )
        st.session_state.registered_patient = new_patient
        st.balloons()
        st.rerun()
