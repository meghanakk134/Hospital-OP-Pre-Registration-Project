"""
pages/5_Token_Status.py
-------------------------
Live OP token / queue status: current token, estimated wait time,
patients ahead, and a live queue table for the patient's booked doctor.
"""

import os
import sys

import streamlit as st
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
import utils
import qr_generator

st.set_page_config(page_title="Token Status | City Care Hospital", page_icon="🎫", layout="wide")
db.init_db()

css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🎫 Token Status & Live Queue")

if not st.session_state.get("logged_in_patient_id"):
    st.warning("Please log in as a patient to view your token status.")
    if st.button("Go to Patient Login"):
        st.switch_page("pages/2_Patient_Login.py")
    st.stop()

patient = db.get_patient_by_id(st.session_state.logged_in_patient_id)
appointments = db.get_appointments_by_patient(patient["patient_id"])
scheduled = [a for a in appointments if a["status"] == "Scheduled"]

if not scheduled:
    st.info("You have no active tokens right now.")
    if st.button("Book an Appointment"):
        st.switch_page("pages/3_Book_Appointment.py")
    st.stop()

options = {f"{a['appointment_date']} — {a['department']} (Token #{a['token_number']})": a for a in scheduled}
selected_label = st.selectbox("Select appointment", list(options.keys()))
appointment = options[selected_label]
doctor = db.get_doctor_by_id(appointment["doctor_id"]) or {}

queue = db.get_tokens_for_doctor_date(appointment["doctor_id"], appointment["appointment_date"])
queue_sorted = sorted(queue, key=lambda a: a["token_number"])

# naive "current token" = first scheduled token in queue (smallest number still Scheduled)
active_tokens = [a for a in queue_sorted if a["status"] == "Scheduled"]
current_token = active_tokens[0]["token_number"] if active_tokens else appointment["token_number"]
patients_ahead = max(0, appointment["token_number"] - current_token)
est_wait = utils.ai_predict_wait_time(patients_ahead, appointment["department"])

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{appointment['token_number']}</div>
    <div class="kpi-label">Your Token</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{current_token}</div>
    <div class="kpi-label">Current Token</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{patients_ahead}</div>
    <div class="kpi-label">Patients Ahead</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{est_wait} min</div>
    <div class="kpi-label">Est. Wait Time</div></div>""", unsafe_allow_html=True)

st.divider()

progress = 0.0
if len(queue_sorted) > 0:
    progress = min(1.0, current_token / max(appointment["token_number"], 1))
st.progress(progress, text=f"Queue progress toward your token #{appointment['token_number']}")

st.markdown(f"""
**Doctor:** {doctor.get('full_name', appointment['doctor_id'])} &nbsp; | &nbsp;
**Hospital:** {appointment.get('hospital_name') or appointment.get('branch', '-')} &nbsp; | &nbsp;
**Department:** {appointment['department']} &nbsp; | &nbsp;
**Date:** {appointment['appointment_date']} &nbsp; | &nbsp;
**Time Slot:** {appointment['time_slot']}
""")

join_url = qr_generator.get_consultation_link(appointment["appointment_id"])
st.link_button("🎥 Join Video Consultation", join_url, use_container_width=True)

st.markdown("#### 🧾 Live Queue")
if queue_sorted:
    df = pd.DataFrame([{
        "Token #": a["token_number"],
        "Patient ID": a["patient_id"],
        "Status": utils.status_badge(a["status"]),
        "Time Slot": a["time_slot"],
    } for a in queue_sorted])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No queue data available.")

st.button("🔄 Refresh Status", on_click=st.rerun)
