"""
utils.py
--------
Shared utility functions: ID generation, input validation, waiting-time
estimation, AI symptom-checker demo, doctor recommendation, and simulated
email/SMS notification senders.
"""

import re
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, date


# ------------------------------------------------------------------
# ID Generators
# ------------------------------------------------------------------

def generate_patient_id():
    """PT + YYMMDD + 4 random digits, e.g. PT2507150001-like uniqueness."""
    stamp = datetime.now().strftime("%y%m%d%H%M%S")
    return f"PT{stamp}{random.randint(10, 99)}"


def generate_appointment_id():
    stamp = datetime.now().strftime("%y%m%d%H%M%S")
    return f"AP{stamp}{random.randint(10, 99)}"


def generate_payment_id():
    stamp = datetime.now().strftime("%y%m%d%H%M%S")
    return f"PAY{stamp}{random.randint(10, 99)}"


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------

def is_valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"[6-9]\d{9}", phone.strip()))


def is_valid_email(email: str) -> bool:
    if not email:
        return True  # email optional
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


def is_valid_aadhaar(aadhaar: str) -> bool:
    if not aadhaar:
        return True  # optional
    return bool(re.fullmatch(r"\d{12}", aadhaar.strip()))


def is_valid_pincode(pincode: str) -> bool:
    if not pincode:
        return True
    return bool(re.fullmatch(r"\d{6}", pincode.strip()))


def calculate_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# ------------------------------------------------------------------
# Waiting time / queue prediction
# ------------------------------------------------------------------

AVERAGE_CONSULT_MINUTES = 12


def estimate_wait_time(patients_ahead: int) -> int:
    """Very simple linear estimate; a real system would use historical
    consultation-duration data per doctor/department."""
    return max(0, patients_ahead) * AVERAGE_CONSULT_MINUTES


def ai_predict_wait_time(patients_ahead: int, department: str) -> int:
    """Demo 'AI' prediction: adjusts the base estimate slightly per
    department to simulate a smarter model without external dependencies."""
    dept_factor = {
        "Cardiology": 1.3, "Neurology": 1.25, "Orthopedics": 1.15,
        "General Medicine": 1.0, "Pediatrics": 0.9, "Dental": 0.85,
    }.get(department, 1.05)
    return int(estimate_wait_time(patients_ahead) * dept_factor)


# ------------------------------------------------------------------
# AI Symptom Checker (rule-based demo)
# ------------------------------------------------------------------

SYMPTOM_DEPARTMENT_MAP = {
    "chest pain": "Cardiology", "palpitations": "Cardiology", "high blood pressure": "Cardiology",
    "joint pain": "Orthopedics", "back pain": "Orthopedics", "fracture": "Orthopedics",
    "headache": "Neurology", "seizure": "Neurology", "dizziness": "Neurology",
    "ear pain": "ENT", "hearing loss": "ENT", "sore throat": "ENT",
    "skin rash": "Dermatology", "acne": "Dermatology", "itching": "Dermatology",
    "child fever": "Pediatrics", "child cough": "Pediatrics",
    "pregnancy": "Gynecology", "menstrual": "Gynecology",
    "anxiety": "Psychiatry", "depression": "Psychiatry", "insomnia": "Psychiatry",
    "blurred vision": "Ophthalmology", "eye pain": "Ophthalmology",
    "tooth pain": "Dental", "gum bleeding": "Dental",
    "fever": "General Medicine", "cough": "General Medicine", "cold": "General Medicine",
}


def ai_suggest_department(symptom_text: str) -> str:
    """Extremely simple keyword-matching 'AI' demo. Not a medical diagnostic
    tool — always recommend the user confirm with General Medicine if unsure."""
    text = symptom_text.lower()
    for keyword, dept in SYMPTOM_DEPARTMENT_MAP.items():
        if keyword in text:
            return dept
    return "General Medicine"


def ai_recommend_doctor(department: str, doctors: list) -> dict:
    """Pick the first available doctor in the department (demo logic)."""
    available = [d for d in doctors if d.get("available")]
    return available[0] if available else (doctors[0] if doctors else None)


# ------------------------------------------------------------------
# Notification simulation (Email + SMS)
# ------------------------------------------------------------------

def send_email_notification(to_email, subject, body, smtp_config=None):
    """Attempts a real SMTP send if smtp_config is supplied; otherwise just
    simulates by returning True. Safe to call without any mail server set up."""
    if not to_email:
        return False
    if not smtp_config:
        # Simulation mode — no SMTP server configured.
        return True
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = smtp_config["sender"]
        msg["To"] = to_email
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            server.starttls()
            server.login(smtp_config["user"], smtp_config["password"])
            server.sendmail(smtp_config["sender"], [to_email], msg.as_string())
        return True
    except Exception:
        return False


def send_sms_notification(phone_number, message):
    """SMS gateway integration placeholder. Wire this up to Twilio / MSG91 /
    any SMS gateway's REST API in production. Currently simulated."""
    # Example (Twilio-style) integration point:
    # client.messages.create(body=message, from_=GATEWAY_NUMBER, to=phone_number)
    return True


def notify_patient(patient_id, patient_email, patient_phone, message, db_module):
    """Fire simulated email + SMS notifications and log them to the DB."""
    send_email_notification(patient_email, "Hospital OP System Notification", message)
    send_sms_notification(patient_phone, message)
    db_module.insert_notification(patient_id, message, "Email")
    db_module.insert_notification(patient_id, message, "SMS")


# ------------------------------------------------------------------
# Time slots
# ------------------------------------------------------------------

def generate_time_slots():
    """Return a list of standard 30-minute OP slots for a working day."""
    slots = []
    for hour in list(range(9, 13)) + list(range(14, 18)):
        for minute in (0, 30):
            start = f"{hour:02d}:{minute:02d}"
            end_hour, end_minute = (hour, minute + 30) if minute == 0 else (hour + 1, 0)
            end = f"{end_hour:02d}:{end_minute:02d}"
            slots.append(f"{start} - {end}")
    return slots


def status_badge(status: str) -> str:
    """Return an emoji-prefixed label for consistent status display."""
    mapping = {
        "Scheduled": "🟡 Scheduled", "Completed": "🟢 Completed",
        "Cancelled": "🔴 Cancelled", "Waiting": "🟡 Waiting",
        "In Progress": "🔵 In Progress", "Paid": "🟢 Paid", "Pending": "🟡 Pending",
    }
    return mapping.get(status, status)
