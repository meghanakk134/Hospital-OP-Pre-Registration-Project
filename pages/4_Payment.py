"""
pages/4_Payment.py
--------------------
Payment module supporting Cash, UPI, Credit Card, and Insurance. Generates
a payment receipt / PDF invoice on successful payment.
"""

import os
import sys
from datetime import datetime

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import utils
import pdf_generator

st.set_page_config(page_title="Payment | City Care Hospital", page_icon="💳", layout="wide")
db.init_db()

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("💳 Payment")

if not st.session_state.get("logged_in_patient_id"):
    st.warning("Please log in as a patient to make a payment.")
    if st.button("Go to Patient Login"):
        st.switch_page("pages/2_Patient_Login.py")
    st.stop()

patient = db.get_patient_by_id(st.session_state.logged_in_patient_id)

# ------------------------------------------------------------------
# Select appointment to pay for
# ------------------------------------------------------------------
appointments = db.get_appointments_by_patient(patient["patient_id"])
unpaid = [a for a in appointments if a["status"] == "Scheduled" and not db.get_payment_by_appointment(a["appointment_id"])]

preselected_id = st.session_state.get("pending_payment_appointment_id")

if not unpaid:
    st.info("No pending payments. Book an appointment first.")
    if st.button("Book an Appointment"):
        st.switch_page("pages/3_Book_Appointment.py")
    st.stop()

options = {f"{a['appointment_id']} — {a['department']} on {a['appointment_date']}": a for a in unpaid}
default_index = 0
if preselected_id:
    for i, (label, a) in enumerate(options.items()):
        if a["appointment_id"] == preselected_id:
            default_index = i
            break

selected_label = st.selectbox("Select Appointment to Pay For", list(options.keys()), index=default_index)
appointment = options[selected_label]
doctor = db.get_doctor_by_id(appointment["doctor_id"])
fee = doctor["consultation_fee"] if doctor else 300.0

st.markdown(f"""
<div class="hospital-card">
<b>Department:</b> {appointment['department']}<br>
<b>Doctor:</b> {doctor['full_name'] if doctor else '-'}<br>
<b>Date & Time:</b> {appointment['appointment_date']} · {appointment['time_slot']}<br>
<b>Consultation Fee:</b> ₹{fee:.2f}
</div>
""", unsafe_allow_html=True)

st.divider()
payment_type = st.radio("Select Payment Method", ["Cash", "UPI", "Credit Card", "Insurance"], horizontal=True)

if payment_type == "UPI":
    st.text_input("UPI ID", placeholder="yourname@upi")
elif payment_type == "Credit Card":
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Card Number", placeholder="XXXX XXXX XXXX XXXX")
    with c2:
        st.text_input("Expiry (MM/YY)", placeholder="MM/YY")
    with c3:
        st.text_input("CVV", type="password", placeholder="***")
elif payment_type == "Insurance":
    st.text_input("Insurance Provider", value=patient.get("insurance_provider", ""))
    st.text_input("Insurance ID", value=patient.get("insurance_id", ""))

if st.button("Pay Now", type="primary", use_container_width=True):
    payment_id = utils.generate_payment_id()
    payment = {
        "payment_id": payment_id,
        "appointment_id": appointment["appointment_id"],
        "patient_id": patient["patient_id"],
        "amount": fee,
        "payment_type": payment_type,
        "status": "Paid",
        "transaction_date": datetime.now().isoformat(),
    }
    db.insert_payment(payment)

    utils.notify_patient(
        patient["patient_id"], patient["email"], patient["phone"],
        f"Payment of ₹{fee:.2f} received via {payment_type} for your appointment on "
        f"{appointment['appointment_date']}. Receipt ID: {payment_id}.",
        db,
    )

    st.success(f"✅ Payment successful! Receipt ID: {payment_id}")
    st.balloons()

    pdf_bytes = pdf_generator.generate_invoice_pdf(payment, patient, appointment)
    st.download_button(
        "⬇️ Download Invoice / Receipt (PDF)", data=pdf_bytes,
        file_name=f"invoice_{payment_id}.pdf", mime="application/pdf",
    )

    if st.button("View Token Status →"):
        st.switch_page("pages/5_Token_Status.py")
