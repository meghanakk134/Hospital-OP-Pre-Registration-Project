"""
database.py
------------
Central database module for the Hospital OP Pre-Registration System.
Handles connection management, schema creation, and all CRUD operations.
Uses SQLite for lightweight, file-based, zero-config storage.
"""

import sqlite3
import os
from datetime import datetime, date
from contextlib import contextmanager

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "hospital.db")


def ensure_db_dir():
    """Make sure the database directory exists before connecting."""
    os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_connection():
    """Context manager that yields a SQLite connection with row access by column name."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create all tables required by the system if they do not already exist."""
    with get_connection() as conn:
        cur = conn.cursor()

        # ---------------- Patients ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Patients (
            patient_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            gender TEXT,
            dob TEXT,
            age INTEGER,
            blood_group TEXT,
            phone TEXT NOT NULL,
            email TEXT,
            aadhaar TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            emergency_contact TEXT,
            medical_history TEXT,
            insurance_provider TEXT,
            insurance_id TEXT,
            photo_path TEXT,
            password_hash TEXT,
            created_at TEXT
        )""")

        # ---------------- Departments ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )""")

        # ---------------- Hospitals ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Hospitals (
            hospital_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT,
            address TEXT,
            phone TEXT,
            specialties TEXT,
            rating REAL DEFAULT 4.5,
            icon TEXT,
            created_at TEXT
        )""")

        # ---------------- Doctors ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Doctors (
            doctor_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            department TEXT,
            branch TEXT,
            hospital_id TEXT,
            phone TEXT,
            email TEXT,
            password_hash TEXT,
            available INTEGER DEFAULT 1,
            consultation_fee REAL DEFAULT 300,
            created_at TEXT,
            FOREIGN KEY (hospital_id) REFERENCES Hospitals (hospital_id)
        )""")

        # ---------------- Admins ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Admins (
            admin_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TEXT
        )""")

        # ---------------- Appointments ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Appointments (
            appointment_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT,
            department TEXT,
            branch TEXT,
            hospital_id TEXT,
            hospital_name TEXT,
            appointment_date TEXT,
            time_slot TEXT,
            reason TEXT,
            preferred_language TEXT,
            payment_type TEXT,
            status TEXT DEFAULT 'Scheduled',
            token_number INTEGER,
            created_at TEXT,
            FOREIGN KEY (patient_id) REFERENCES Patients (patient_id)
        )""")

        # ---------------- Payments ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Payments (
            payment_id TEXT PRIMARY KEY,
            appointment_id TEXT,
            patient_id TEXT,
            amount REAL,
            payment_type TEXT,
            status TEXT DEFAULT 'Paid',
            transaction_date TEXT,
            FOREIGN KEY (appointment_id) REFERENCES Appointments (appointment_id)
        )""")

        # ---------------- Tokens ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Tokens (
            token_id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT,
            token_number INTEGER,
            department TEXT,
            token_date TEXT,
            status TEXT DEFAULT 'Waiting',
            FOREIGN KEY (appointment_id) REFERENCES Appointments (appointment_id)
        )""")

        # ---------------- Notifications ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            message TEXT,
            channel TEXT,
            status TEXT DEFAULT 'Sent',
            created_at TEXT
        )""")

        # ---------------- Medical Records ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS MedicalRecords (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            appointment_id TEXT,
            doctor_id TEXT,
            diagnosis TEXT,
            prescription TEXT,
            prescription_file TEXT,
            visit_date TEXT,
            FOREIGN KEY (patient_id) REFERENCES Patients (patient_id)
        )""")

        conn.commit()
        migrate_schema(conn)
        seed_defaults(conn)


def _column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def migrate_schema(conn):
    """Add newly-introduced columns to existing databases created by an
    older version of the app, so upgrades don't require deleting data."""
    cur = conn.cursor()
    if not _column_exists(cur, "Doctors", "hospital_id"):
        cur.execute("ALTER TABLE Doctors ADD COLUMN hospital_id TEXT")
    if not _column_exists(cur, "Appointments", "hospital_id"):
        cur.execute("ALTER TABLE Appointments ADD COLUMN hospital_id TEXT")
    if not _column_exists(cur, "Appointments", "hospital_name"):
        cur.execute("ALTER TABLE Appointments ADD COLUMN hospital_name TEXT")
    conn.commit()


# Name pools used to generate varied demo doctor names per hospital.
_FIRST_NAMES = [
    "Anil", "Priya", "Ramesh", "Sunitha", "Farah", "Vikram", "Anjali", "Meera",
    "Karthik", "Divya", "Sameer", "Neha", "Rajesh", "Kavya", "Arjun", "Pooja",
    "Suresh", "Lakshmi", "Imran", "Swathi",
]
_LAST_NAMES = [
    "Sharma", "Nair", "Kumar", "Reddy", "Khan", "Singh", "Rao", "Iyer",
    "Menon", "Pillai", "Ali", "Gupta", "Verma", "Chowdary", "Naidu",
]

# 15 fictional multi-speciality hospitals shown on the hospital-selection screen.
_HOSPITALS = [
    ("HOS01", "City Care Multi-Speciality Hospital", "Kukatpally, Hyderabad", "1-2-3, KPHB Colony, Kukatpally", "040-4000-1001", 4.6, "🏥"),
    ("HOS02", "Sunrise Multi-Speciality Hospital", "Kondapur, Hyderabad", "Plot 45, Kondapur Main Road", "040-4000-1002", 4.4, "🌅"),
    ("HOS03", "LifeLine Super-Speciality Hospital", "Madhapur, Hyderabad", "Road No. 2, Madhapur", "040-4000-1003", 4.7, "❤️"),
    ("HOS04", "Green Valley Multi-Speciality Hospital", "Miyapur, Hyderabad", "Beside Metro Station, Miyapur", "040-4000-1004", 4.3, "🌿"),
    ("HOS05", "Care Plus Hospital", "Gachibowli, Hyderabad", "Financial District, Gachibowli", "040-4000-1005", 4.5, "➕"),
    ("HOS06", "Unity Multi-Speciality Hospital", "Ameerpet, Hyderabad", "SR Nagar Road, Ameerpet", "040-4000-1006", 4.2, "🤝"),
    ("HOS07", "Wellness Care Hospital", "Secunderabad, Hyderabad", "SP Road, Secunderabad", "040-4000-1007", 4.4, "💚"),
    ("HOS08", "Rainbow Multi-Speciality Hospital", "Banjara Hills, Hyderabad", "Road No. 12, Banjara Hills", "040-4000-1008", 4.8, "🌈"),
    ("HOS09", "Trinity Health City", "Hitech City, Hyderabad", "Cyber Towers Road, Hitech City", "040-4000-1009", 4.6, "🏙️"),
    ("HOS10", "Metro Care Hospital", "Kukatpally Housing Board, Hyderabad", "KPHB Phase 3, Kukatpally", "040-4000-1010", 4.1, "🏨"),
    ("HOS11", "Horizon Multi-Speciality Hospital", "LB Nagar, Hyderabad", "Main Road, LB Nagar", "040-4000-1011", 4.3, "🌇"),
    ("HOS12", "Prime Care Hospital", "Uppal, Hyderabad", "Ring Road, Uppal", "040-4000-1012", 4.2, "⭐"),
    ("HOS13", "Zenith Multi-Speciality Hospital", "Dilsukhnagar, Hyderabad", "Chaitanyapuri X Roads, Dilsukhnagar", "040-4000-1013", 4.5, "🏢"),
    ("HOS14", "Harmony Health Hospital", "Kompally, Hyderabad", "NH44, Kompally", "040-4000-1014", 4.4, "🕊️"),
    ("HOS15", "NovaCare Multi-Speciality Hospital", "Miyapur X Roads, Hyderabad", "JNTU-Miyapur Road", "040-4000-1015", 4.6, "🩺"),
]


def seed_defaults(conn):
    """Seed departments, hospitals, a default admin, and demo doctors if
    tables are empty."""
    cur = conn.cursor()

    departments = [
        "General Medicine", "Cardiology", "Orthopedics", "Neurology", "ENT",
        "Dermatology", "Pediatrics", "Gynecology", "Psychiatry",
        "Ophthalmology", "Dental",
    ]
    cur.execute("SELECT COUNT(*) FROM Departments")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO Departments (name, description) VALUES (?, ?)",
            [(d, f"{d} department") for d in departments],
        )

    cur.execute("SELECT COUNT(*) FROM Admins")
    if cur.fetchone()[0] == 0:
        from auth import hash_password
        cur.execute(
            "INSERT INTO Admins (admin_id, username, password_hash, full_name, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("ADM0001", "admin", hash_password("admin123"), "Hospital Administrator",
             datetime.now().isoformat()),
        )

    # ---------------- Hospitals (10-15 multi-speciality hospitals) ----------------
    cur.execute("SELECT COUNT(*) FROM Hospitals")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO Hospitals (hospital_id, name, city, address, phone, specialties, "
            "rating, icon, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (hid, name, city, address, phone, "Multi-Speciality · 11 Departments",
                 rating, icon, datetime.now().isoformat())
                for hid, name, city, address, phone, rating, icon in _HOSPITALS
            ],
        )

    # ---------------- Doctors (each hospital gets one doctor per department) ----------------
    cur.execute("SELECT COUNT(*) FROM Doctors WHERE hospital_id IS NOT NULL AND hospital_id != ''")
    if cur.fetchone()[0] == 0:
        from auth import hash_password
        # Doctors table exists from an older version of the app (or is empty) and
        # has no hospital-linked records yet — clear any stale, unlinked demo
        # doctors and (re)seed a full hospital-linked roster so booking works.
        cur.execute("DELETE FROM Doctors")
        doc_counter = 1
        for h_idx, (hid, hname, *_rest) in enumerate(_HOSPITALS):
            for d_idx, dept in enumerate(departments):
                doc_id = f"DOC{doc_counter:04d}"
                first = _FIRST_NAMES[(h_idx * 11 + d_idx) % len(_FIRST_NAMES)]
                last = _LAST_NAMES[(h_idx * 7 + d_idx) % len(_LAST_NAMES)]
                full_name = f"Dr. {first} {last}"
                fee = 300 + ((h_idx * 37 + d_idx * 19) % 5) * 100
                phone = f"90{doc_counter:08d}"
                cur.execute(
                    "INSERT INTO Doctors (doctor_id, full_name, department, branch, hospital_id, "
                    "phone, email, password_hash, available, consultation_fee, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                    (doc_id, full_name, dept, hname, hid, phone,
                     f"{doc_id.lower()}@hospital.com", hash_password("doctor123"), fee,
                     datetime.now().isoformat()),
                )
                doc_counter += 1
    conn.commit()


# ------------------------------------------------------------------
# Generic helpers
# ------------------------------------------------------------------

def run_query(query, params=(), fetch=False, fetchone=False):
    """Run a parametrized query. Returns rows (list of dict) if fetch requested."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        if fetchone:
            row = cur.fetchone()
            return dict(row) if row else None
        if fetch:
            return [dict(r) for r in cur.fetchall()]
        return cur.lastrowid


# ------------------------------------------------------------------
# Patients
# ------------------------------------------------------------------

def insert_patient(patient: dict):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Patients (patient_id, full_name, gender, dob, age, blood_group, phone,
                email, aadhaar, address, city, state, pincode, emergency_contact,
                medical_history, insurance_provider, insurance_id, photo_path,
                password_hash, created_at)
            VALUES (:patient_id, :full_name, :gender, :dob, :age, :blood_group, :phone,
                :email, :aadhaar, :address, :city, :state, :pincode, :emergency_contact,
                :medical_history, :insurance_provider, :insurance_id, :photo_path,
                :password_hash, :created_at)
        """, patient)


def get_patient_by_id(patient_id):
    return run_query("SELECT * FROM Patients WHERE patient_id = ?", (patient_id,), fetchone=True)


def get_patient_by_phone(phone):
    return run_query("SELECT * FROM Patients WHERE phone = ?", (phone,), fetchone=True)


def get_all_patients():
    return run_query("SELECT * FROM Patients ORDER BY created_at DESC", fetch=True)


def search_patients(term):
    like = f"%{term}%"
    return run_query(
        "SELECT * FROM Patients WHERE patient_id LIKE ? OR phone LIKE ? OR full_name LIKE ?",
        (like, like, like), fetch=True,
    )


# ------------------------------------------------------------------
# Doctors
# ------------------------------------------------------------------

def get_all_doctors():
    return run_query("SELECT * FROM Doctors ORDER BY full_name", fetch=True)


def get_doctors_by_department(department):
    return run_query(
        "SELECT * FROM Doctors WHERE department = ? AND available = 1", (department,), fetch=True
    )


def get_doctors_by_hospital_department(hospital_id, department):
    return run_query(
        "SELECT * FROM Doctors WHERE hospital_id = ? AND department = ? AND available = 1",
        (hospital_id, department), fetch=True,
    )


def get_doctors_by_hospital(hospital_id):
    return run_query(
        "SELECT * FROM Doctors WHERE hospital_id = ? ORDER BY department",
        (hospital_id,), fetch=True,
    )


def get_doctor_by_id(doctor_id):
    return run_query("SELECT * FROM Doctors WHERE doctor_id = ?", (doctor_id,), fetchone=True)


# ------------------------------------------------------------------
# Hospitals
# ------------------------------------------------------------------

def get_all_hospitals():
    return run_query("SELECT * FROM Hospitals ORDER BY name", fetch=True)


def get_hospital_by_id(hospital_id):
    return run_query("SELECT * FROM Hospitals WHERE hospital_id = ?", (hospital_id,), fetchone=True)


# ------------------------------------------------------------------
# Departments
# ------------------------------------------------------------------

def get_all_departments():
    return run_query("SELECT * FROM Departments ORDER BY name", fetch=True)


# ------------------------------------------------------------------
# Appointments
# ------------------------------------------------------------------

def insert_appointment(appt: dict):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Appointments (appointment_id, patient_id, doctor_id, department, branch,
                hospital_id, hospital_name, appointment_date, time_slot, reason,
                preferred_language, payment_type, status, token_number, created_at)
            VALUES (:appointment_id, :patient_id, :doctor_id, :department, :branch,
                :hospital_id, :hospital_name, :appointment_date, :time_slot, :reason,
                :preferred_language, :payment_type, :status, :token_number, :created_at)
        """, appt)


def get_appointments_by_patient(patient_id):
    return run_query(
        "SELECT * FROM Appointments WHERE patient_id = ? ORDER BY appointment_date DESC",
        (patient_id,), fetch=True,
    )


def get_appointments_by_doctor_date(doctor_id, appt_date):
    return run_query(
        "SELECT * FROM Appointments WHERE doctor_id = ? AND appointment_date = ? "
        "ORDER BY token_number", (doctor_id, appt_date), fetch=True,
    )


def get_all_appointments():
    return run_query("SELECT * FROM Appointments ORDER BY appointment_date DESC", fetch=True)


def check_duplicate_booking(patient_id, doctor_id, appt_date):
    row = run_query(
        "SELECT COUNT(*) as c FROM Appointments WHERE patient_id = ? AND doctor_id = ? "
        "AND appointment_date = ? AND status != 'Cancelled'",
        (patient_id, doctor_id, appt_date), fetchone=True,
    )
    return row["c"] > 0 if row else False


def get_next_token_number(doctor_id, appt_date):
    row = run_query(
        "SELECT COALESCE(MAX(token_number), 0) as m FROM Appointments "
        "WHERE doctor_id = ? AND appointment_date = ?",
        (doctor_id, appt_date), fetchone=True,
    )
    return (row["m"] if row else 0) + 1


def update_appointment_status(appointment_id, status):
    run_query("UPDATE Appointments SET status = ? WHERE appointment_id = ?", (status, appointment_id))


# ------------------------------------------------------------------
# Payments
# ------------------------------------------------------------------

def insert_payment(payment: dict):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Payments (payment_id, appointment_id, patient_id, amount, payment_type,
                status, transaction_date)
            VALUES (:payment_id, :appointment_id, :patient_id, :amount, :payment_type,
                :status, :transaction_date)
        """, payment)


def get_all_payments():
    return run_query("SELECT * FROM Payments ORDER BY transaction_date DESC", fetch=True)


def get_payment_by_appointment(appointment_id):
    return run_query(
        "SELECT * FROM Payments WHERE appointment_id = ?", (appointment_id,), fetchone=True
    )


# ------------------------------------------------------------------
# Tokens
# ------------------------------------------------------------------

def insert_token(appointment_id, token_number, department, token_date):
    run_query(
        "INSERT INTO Tokens (appointment_id, token_number, department, token_date, status) "
        "VALUES (?, ?, ?, ?, 'Waiting')",
        (appointment_id, token_number, department, token_date),
    )


def get_tokens_for_doctor_date(doctor_id, appt_date):
    return get_appointments_by_doctor_date(doctor_id, appt_date)


# ------------------------------------------------------------------
# Notifications
# ------------------------------------------------------------------

def insert_notification(patient_id, message, channel):
    run_query(
        "INSERT INTO Notifications (patient_id, message, channel, status, created_at) "
        "VALUES (?, ?, ?, 'Sent', ?)",
        (patient_id, message, channel, datetime.now().isoformat()),
    )


def get_notifications_for_patient(patient_id):
    return run_query(
        "SELECT * FROM Notifications WHERE patient_id = ? ORDER BY created_at DESC",
        (patient_id,), fetch=True,
    )


# ------------------------------------------------------------------
# Medical Records
# ------------------------------------------------------------------

def insert_medical_record(record: dict):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO MedicalRecords (patient_id, appointment_id, doctor_id, diagnosis,
                prescription, prescription_file, visit_date)
            VALUES (:patient_id, :appointment_id, :doctor_id, :diagnosis,
                :prescription, :prescription_file, :visit_date)
        """, record)


def get_medical_records_for_patient(patient_id):
    return run_query(
        "SELECT * FROM MedicalRecords WHERE patient_id = ? ORDER BY visit_date DESC",
        (patient_id,), fetch=True,
    )
