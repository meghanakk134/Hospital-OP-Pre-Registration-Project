"""
pdf_generator.py
-----------------
Generates PDF documents using ReportLab:
  - Payment receipt / invoice
  - Patient registration summary
  - Admin analytical reports (daily/weekly/monthly/department/doctor/patient)

All functions return raw PDF bytes so they can be piped straight into
Streamlit's st.download_button.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
)

PRIMARY_COLOR = colors.HexColor("#0066CC")
SECONDARY_COLOR = colors.HexColor("#00B894")


def _base_doc(buffer):
    return SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
    )


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="HospitalTitle", fontSize=18, leading=22,
        textColor=PRIMARY_COLOR, spaceAfter=6, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader", fontSize=12, leading=16,
        textColor=PRIMARY_COLOR, spaceBefore=10, spaceAfter=6, fontName="Helvetica-Bold",
    ))
    return styles


def generate_invoice_pdf(payment: dict, patient: dict, appointment: dict) -> bytes:
    """Generate a payment receipt / invoice PDF."""
    buffer = io.BytesIO()
    doc = _base_doc(buffer)
    styles = _styles()
    elements = []

    elements.append(Paragraph("City Care Hospital", styles["HospitalTitle"]))
    elements.append(Paragraph("Outpatient Payment Receipt", styles["Normal"]))
    elements.append(Spacer(1, 10))

    info_table = Table([
        ["Receipt No.", payment.get("payment_id", "-"), "Date", payment.get("transaction_date", "-")[:19]],
        ["Patient ID", patient.get("patient_id", "-"), "Patient Name", patient.get("full_name", "-")],
        ["Appointment ID", appointment.get("appointment_id", "-"), "Department", appointment.get("department", "-")],
    ], colWidths=[80, 140, 90, 140])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Payment Details", styles["SectionHeader"]))
    pay_table = Table([
        ["Description", "Amount (INR)"],
        [f"OP Consultation - {appointment.get('department', '-')}", f"{payment.get('amount', 0):,.2f}"],
        ["Payment Mode", payment.get("payment_type", "-")],
        ["Status", payment.get("status", "-")],
        ["Total Paid", f"Rs. {payment.get('amount', 0):,.2f}"],
    ], colWidths=[320, 130])
    pay_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(pay_table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "This is a system-generated receipt and does not require a physical signature.",
        styles["Italic"],
    ))

    doc.build(elements)
    return buffer.getvalue()


def generate_registration_pdf(patient: dict, qr_bytes: bytes = None) -> bytes:
    """Generate a printable registration summary for a newly registered patient."""
    buffer = io.BytesIO()
    doc = _base_doc(buffer)
    styles = _styles()
    elements = []

    elements.append(Paragraph("City Care Hospital", styles["HospitalTitle"]))
    elements.append(Paragraph("Patient Registration Confirmation", styles["Normal"]))
    elements.append(Spacer(1, 10))

    rows = [
        ["Patient ID", patient.get("patient_id", "-")],
        ["Full Name", patient.get("full_name", "-")],
        ["Gender", patient.get("gender", "-")],
        ["Date of Birth", patient.get("dob", "-")],
        ["Age", str(patient.get("age", "-"))],
        ["Blood Group", patient.get("blood_group", "-")],
        ["Phone", patient.get("phone", "-")],
        ["Email", patient.get("email", "-")],
        ["Address", patient.get("address", "-")],
        ["City / State / PIN",
         f"{patient.get('city', '-')} / {patient.get('state', '-')} / {patient.get('pincode', '-')}"],
        ["Emergency Contact", patient.get("emergency_contact", "-")],
        ["Insurance Provider", patient.get("insurance_provider", "-") or "N/A"],
    ]
    table = Table(rows, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    if qr_bytes:
        elements.append(Spacer(1, 16))
        elements.append(Paragraph("Your Patient QR Code", styles["SectionHeader"]))
        qr_img = RLImage(io.BytesIO(qr_bytes), width=100, height=100)
        elements.append(qr_img)

    doc.build(elements)
    return buffer.getvalue()


def generate_report_pdf(title: str, headers: list, rows: list, summary_lines=None) -> bytes:
    """Generic tabular report generator used by the Admin Dashboard for
    daily/weekly/monthly/department/doctor/patient reports."""
    buffer = io.BytesIO()
    doc = _base_doc(buffer)
    styles = _styles()
    elements = []

    elements.append(Paragraph("City Care Hospital", styles["HospitalTitle"]))
    elements.append(Paragraph(title, styles["SectionHeader"]))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    if summary_lines:
        for line in summary_lines:
            elements.append(Paragraph(line, styles["Normal"]))
        elements.append(Spacer(1, 10))

    data = [headers] + rows if rows else [headers, ["No data available"] + [""] * (len(headers) - 1)]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()


def generate_prescription_pdf(patient, doctor, diagnosis, prescription, visit_date) -> bytes:
    """Generate a simple downloadable prescription PDF."""
    buffer = io.BytesIO()
    doc = _base_doc(buffer)
    styles = _styles()
    elements = []

    elements.append(Paragraph("City Care Hospital", styles["HospitalTitle"]))
    elements.append(Paragraph("Prescription", styles["Normal"]))
    elements.append(Spacer(1, 10))

    header = Table([
        ["Patient", patient.get("full_name", "-"), "Date", str(visit_date)],
        ["Doctor", doctor.get("full_name", "-"), "Department", doctor.get("department", "-")],
    ], colWidths=[70, 170, 70, 130])
    header.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Diagnosis", styles["SectionHeader"]))
    elements.append(Paragraph(diagnosis or "-", styles["Normal"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Rx (Prescription)", styles["SectionHeader"]))
    for line in (prescription or "-").split("\n"):
        elements.append(Paragraph(f"• {line}", styles["Normal"]))

    doc.build(elements)
    return buffer.getvalue()
