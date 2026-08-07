"""
qr_generator.py
----------------
Generates QR codes encoding patient/appointment details after a successful
registration or booking. Returns image bytes suitable for st.image() and
for embedding into the PDF invoice/receipt.
"""

import io
import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generate_qr_code(data: dict) -> bytes:
    """Build a QR code from a dict of patient/appointment info and return
    the PNG image as raw bytes."""
    lines = [f"{key}: {value}" for key, value in data.items() if value]
    payload = "\n".join(lines)

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0066CC", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_patient_qr(patient_id, name):
    return generate_qr_code({"Patient ID": patient_id, "Name": name})


def generate_appointment_qr(patient_id, name, appointment_id, doctor, department, appt_date):
    return generate_qr_code({
        "Patient ID": patient_id,
        "Name": name,
        "Appointment ID": appointment_id,
        "Doctor": doctor,
        "Department": department,
        "Date": str(appt_date),
    })


# ------------------------------------------------------------------
# Consultation QR — scanning it opens a live video-consult room directly,
# no login or app install needed for the patient or the doctor.
# ------------------------------------------------------------------

def get_consultation_link(appointment_id: str) -> str:
    """Return a unique, shareable video-consultation room URL for an
    appointment. Uses the free public Jitsi Meet service so the QR code
    works standalone, without any extra backend or account setup."""
    room_name = f"HospitalOPConsult-{appointment_id}"
    return f"https://meet.jit.si/{room_name}"


def generate_consultation_qr(appointment_id: str):
    """Generate a QR code that opens the video-consultation room directly
    when scanned. Returns (png_bytes, join_url)."""
    join_url = get_consultation_link(appointment_id)

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(join_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0066CC", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue(), join_url
