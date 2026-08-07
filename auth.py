"""
auth.py
-------
Authentication helpers: password hashing, patient/doctor/admin login,
OTP simulation, and simple session-timeout support for Streamlit's
session_state.
"""

import hashlib
import os
import random
import time

SESSION_TIMEOUT_SECONDS = 30 * 60  # 30 minutes


def hash_password(password: str) -> str:
    """Salted SHA-256 hash. (For a production system, prefer bcrypt/argon2;
    SHA-256 + per-app salt is used here to avoid an extra native dependency
    and keep the demo fully self-contained.)"""
    salt = "hospital_op_salt_v1"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def generate_otp() -> str:
    """Simulate an OTP. In production this would be sent via SMS gateway."""
    return str(random.randint(100000, 999999))


def authenticate_admin(username, password):
    import database as db
    admin = db.run_query("SELECT * FROM Admins WHERE username = ?", (username,), fetchone=True)
    if admin and verify_password(password, admin["password_hash"]):
        return admin
    return None


def authenticate_doctor(doctor_id, password):
    import database as db
    doctor = db.get_doctor_by_id(doctor_id)
    if doctor and verify_password(password, doctor["password_hash"]):
        return doctor
    return None


def authenticate_patient_by_id(patient_id):
    import database as db
    return db.get_patient_by_id(patient_id)


def authenticate_patient_by_phone(phone):
    import database as db
    return db.get_patient_by_phone(phone)


def touch_session(session_state):
    """Update last-activity timestamp."""
    session_state["last_active"] = time.time()


def is_session_expired(session_state):
    """Return True if the session has exceeded the timeout window."""
    last_active = session_state.get("last_active")
    if last_active is None:
        return False
    return (time.time() - last_active) > SESSION_TIMEOUT_SECONDS
