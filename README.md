# 🏥 City Care Hospital — OP Pre-Registration System

A modern, professional Hospital Outpatient (OP) Pre-Registration and Management
System built with **Streamlit**, **SQLite**, and **Python**.

---

## ✨ Features

- **Patient Registration** with full validation, auto-generated Patient ID, and
  QR code + PDF confirmation
- **Patient Login** via Patient ID or Phone Number with simulated OTP
- **Patient Dashboard** — personal details, upcoming appointments, medical
  history, previous visits, prescription downloads, QR code
- **Appointment Booking** — department, doctor, branch, date, time slot,
  AI-based waiting time estimate, duplicate-booking prevention
- **AI Symptom Checker (demo)** — keyword-based department suggestion
- **AI Doctor Recommendation** — suggests the doctor with the shortest queue
- **Payment Module** — Cash / UPI / Credit Card / Insurance with PDF invoice
- **Token & Live Queue Management** — current token, patients ahead, estimated
  wait time
- **Admin Dashboard** — KPIs, Plotly pie/bar/line charts, search, and
  downloadable CSV/PDF reports (daily / weekly / monthly / department / doctor
  / patient)
- **Doctor Dashboard** — today's patients, upcoming patients, completed
  consultations, cancel appointment, patient search, prescription upload
- **Notifications (simulated)** — Email + SMS on registration, booking,
  payment, and prescription upload
- **Dark Mode**, **Language selection** (English / Hindi / Telugu)
- **Role-based authentication** with hashed passwords

---

## 🗂️ Project Structure

```
Hospital_OP_System/
│
├── app.py                     # Homepage / entry point
├── database.py                # SQLite schema + CRUD operations
├── auth.py                    # Password hashing, login, OTP simulation
├── utils.py                   # Validation, ID generation, AI demo helpers
├── qr_generator.py            # QR code generation
├── pdf_generator.py           # PDF invoices, receipts, reports
├── requirements.txt
├── README.md
│
├── database/
│   └── hospital.db            # Auto-created SQLite database (on first run)
│
├── pages/
│   ├── 1_Patient_Registration.py
│   ├── 2_Patient_Login.py
│   ├── 3_Book_Appointment.py
│   ├── 4_Payment.py
│   ├── 5_Token_Status.py
│   ├── 6_Admin_Dashboard.py
│   └── 7_Doctor_Dashboard.py
│
├── assets/
│   ├── logo.png
│   └── banner.jpg
│
└── styles/
    └── style.css               # Healthcare theme (primary #0066CC / secondary #00B894)
```

---

## ⚙️ Setup Instructions

### 1. Install Python
Requires **Python 3.9+**.

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.
The SQLite database (`database/hospital.db`) and its tables are created
automatically on first run, along with seed data (11 departments, an admin
account, and 11 demo doctors).

---

## 🔑 Demo Credentials

| Role    | Username / ID        | Password     |
|---------|-----------------------|--------------|
| Admin   | `admin`               | `admin123`   |
| Doctor  | any `DOC00xx` ID (e.g. `DOC0001`) | `doctor123` |
| Patient | Register via the **Patient Registration** page, then log in with your generated Patient ID / phone number (OTP is shown on-screen in demo mode) |

---

## 🧩 Tech Stack

| Layer            | Technology        |
|-------------------|--------------------|
| Frontend          | Streamlit          |
| Backend           | Python             |
| Database          | SQLite             |
| Data Handling     | Pandas             |
| Charts            | Plotly             |
| QR Codes          | qrcode             |
| PDF Generation    | ReportLab          |
| Email             | smtplib (SMTP)     |
| SMS               | Gateway-agnostic placeholder (see `utils.send_sms_notification`) |

---

## 🔌 Wiring Up Real Notifications

- **Email**: pass an `smtp_config` dict (`host`, `port`, `user`, `password`,
  `sender`) into `utils.send_email_notification()`. Without it, the app runs
  in simulation mode and just logs the notification.
- **SMS**: implement the marked integration point inside
  `utils.send_sms_notification()` with your SMS gateway of choice (Twilio,
  MSG91, etc.).

---

## ⚠️ Disclaimer

This is a **demo / educational** hospital management system. The AI Symptom
Checker and Waiting-Time Predictor use simple rule-based / heuristic logic for
demonstration purposes only and are **not** a substitute for professional
medical advice. Do not use this system for real patient data or real medical
decision-making without a full security, privacy, and compliance review
(e.g. HIPAA/DPDP compliance, encryption at rest, proper OTP/SMS gateway
integration, and production-grade authentication).

---

## 📄 License

Provided as-is for educational and demonstration purposes.

**🌐 [Live Demo](https://hospital-op-pre-registration-project-knb7tm9kiqx27vxk5577af.streamlit.app/)**
