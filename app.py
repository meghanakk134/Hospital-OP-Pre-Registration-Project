"""
app.py
------
Homepage / entry point for the Hospital OP Pre-Registration System.
Run with:  streamlit run app.py
"""

import os
import base64
import streamlit as st

import database as db

# ------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="City Care Hospital | OP Pre-Registration",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Initialize database on first load
# ------------------------------------------------------------------
db.init_db()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_css():
    css_path = os.path.join(BASE_DIR, "styles", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def img_to_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


load_css()

# ------------------------------------------------------------------
# Dark mode toggle (simple CSS-variable override)
# ------------------------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "language" not in st.session_state:
    st.session_state.language = "English"

if st.session_state.dark_mode:
    st.markdown("""
        <style>
        .stApp { background-color: #0F172A; color: #E2E8F0; }
        h1, h2, h3, p, span, label { color: #E2E8F0 !important; }
        .hospital-card, .kpi-card { background: #1E293B !important; }
        </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------
# Sidebar navigation
# ------------------------------------------------------------------
logo_path = os.path.join(BASE_DIR, "assets", "logo.png")
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, width=90)
    st.markdown("### 🏥 City Care Hospital")
    st.caption("Outpatient Pre-Registration System")
    st.divider()

    st.session_state.language = st.selectbox(
        "🌐 Language / भाषा / భాష", ["English", "Hindi", "Telugu"],
        index=["English", "Hindi", "Telugu"].index(st.session_state.language),
    )
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)

    st.divider()
    st.markdown("**Quick Navigation**")
    st.page_link("app.py", label="🏠 Home")
    st.page_link("pages/1_Patient_Registration.py", label="📝 Patient Registration")
    st.page_link("pages/2_Patient_Login.py", label="🔐 Patient Login")
    st.page_link("pages/3_Book_Appointment.py", label="📅 Book Appointment")
    st.page_link("pages/4_Payment.py", label="💳 Payment")
    st.page_link("pages/5_Token_Status.py", label="🎫 Token Status")
    st.page_link("pages/6_Admin_Dashboard.py", label="📊 Admin Dashboard")
    st.page_link("pages/7_Doctor_Dashboard.py", label="🩺 Doctor Dashboard")

    st.divider()
    st.markdown("**🚨 Emergency Contact**")
    st.error("Ambulance: 108\nHospital: +91-40-4000-1234")

# ------------------------------------------------------------------
# Top navigation bar
# ------------------------------------------------------------------
# ------------------ Header ------------------

st.markdown("<h1 style='text-align:center;'>🏥 City Care Hospital</h1>",
            unsafe_allow_html=True)

st.write("")

# ---------------- Navigation ----------------

col1,col2,col3,col4,col5,col6,col7 = st.columns([0.5,1.2,1.2,2.3,1.2,1.2,0.5])
with col2:
    if st.button("Register", use_container_width=True):
        st.switch_page("pages/1_Patient_Registration.py")

with col3:
    if st.button("Login", use_container_width=True):
        st.switch_page("pages/2_Patient_Login.py")

with col4:
    if st.button("Book Appointment", use_container_width=True):
        st.switch_page("pages/3_Book_Appointment.py")

with col5:
    if st.button("Admin", use_container_width=True):
        st.switch_page("pages/6_Admin_Dashboard.py")

with col6:
    if st.button("Doctor", use_container_width=True):
        st.switch_page("pages/7_Doctor_Dashboard.py")

# ------------------------------------------------------------------
# Hero banner
# ------------------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <h1>Your Health, Our Priority</h1>
    <p>Book OP appointments online, skip the queue, and manage your visits digitally —
    fast, secure, and paperless.</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Quick action cards
# ------------------------------------------------------------------
st.markdown("## Quick Actions")

c1, c2, c3, c4, c5 = st.columns(5, gap="large")

actions = [
    (c1, "📝", "Patient Registration", "New here? Create your profile.", "pages/1_Patient_Registration.py"),
    (c2, "🔐", "Patient Login", "Access your dashboard & records.", "pages/2_Patient_Login.py"),
    (c3, "🗓️", "Book Appointment", "Choose a doctor & time slot.", "pages/3_Book_Appointment.py"),
    (c4, "🛡️", "Admin Login", "Hospital administration panel.", "pages/6_Admin_Dashboard.py"),
    (c5, "🩺", "Doctor Login", "Doctor consultation dashboard.", "pages/7_Doctor_Dashboard.py"),
]

for col, icon, title, desc, page in actions:
    with col:
        st.markdown(
            f"""
            <div class="hospital-card">
                <div class="icon">{icon}</div>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("Go →", key=title, use_container_width=True):
            st.switch_page(page)
st.divider()

# ------------------------------------------------------------------
# Hospital information
# ------------------------------------------------------------------
left, right = st.columns([1.3, 1])
with left:
    st.markdown("### 🏥 Hospital Information")
    st.markdown("""
    <div class="hospital-card">
    <b>City Care Hospital</b> is a multi-speciality outpatient care center offering
    11 departments including Cardiology, Neurology, Orthopedics, Pediatrics and more.<br>
    <b>OP Timings:</b> Mon–Sat, 9:00 AM – 6:00 PM (Lunch break 1:00 PM – 2:00 PM)<br>
    <b>Emergency:</b> 24x7<br>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Departments Available")
    depts = db.get_all_departments()
    dept_names = [d["name"] for d in depts] if depts else []
    dept_cols = st.columns(3)
    for i, name in enumerate(dept_names):
        with dept_cols[i % 3]:
            st.markdown(f"<div class='badge badge-info' style='margin-bottom:6px;display:block;text-align:center;padding:8px;'>{name}</div>", unsafe_allow_html=True)

with right:
    st.markdown("### 📢 Announcements")
    st.info("🩺 Free health checkup camp this Saturday — Cardiology & General Medicine.")
    st.warning("⏳ OP registration counters close 30 minutes before closing time.")
    st.success("💉 Flu vaccination now available at the Pediatrics department.")

    st.markdown("### 💡 Health Tip of the Day")
    st.markdown("""
    <div class="hospital-card">
    Stay hydrated! Drinking 8–10 glasses of water daily supports digestion,
    circulation, and overall energy levels.
    </div>
    """, unsafe_allow_html=True)


st.divider()

# ------------------------------------------------------------------
# Footer
# ------------------------------------------------------------------
st.markdown("""
<div class="footer">
    © 2026 City Care Hospital · Outpatient Pre-Registration System <br>
    Built with Streamlit · For emergencies dial <b>108</b> · This is a demo system, not for real medical use.
</div>
""", unsafe_allow_html=True)
