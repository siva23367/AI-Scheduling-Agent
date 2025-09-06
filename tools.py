
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import smtplib
from email.message import EmailMessage
import pandas as pd
import uuid
from fpdf import FPDF
from langchain_core.tools import tool
from langchain_core.callbacks import CallbackManager
from langchain_core.callbacks.stdout import StdOutCallbackHandler

EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "nsiva390@gmail.com",
    "password": "XXXXXXXXXXXXXXXXX", #yours google 2f verify code
    "from_email": "nsiva390@gmail.com"
}
def generate_patient_id():
    """Generate a unique patient ID."""
    return f"PAT{str(uuid.uuid4())[:3].upper()}"


def send_email_with_attachment(to_email, subject, body, attachment_path=None):
    msg = EmailMessage()
    msg["From"] = EMAIL_CONFIG["from_email"]
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = f.name
        msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    # 👇 ikkadey pettali (inside function, last lo)
    try:
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["username"], EMAIL_CONFIG["password"])
            server.send_message(msg)
        print("✅ Email sent successfully to", to_email)
    except Exception as e:
        print("❌ Email error:", str(e))
        return False

def send_sms(to_number, body):
    """Send an SMS via Twilio."""
    try:
        # For demo purposes, we'll just print the SMS
        print(f"SMS to {to_number}: {body}")
        # Uncomment below when you have actual Twilio credentials
        # client = Client(TWILIO_CONFIG["account_sid"], TWILIO_CONFIG["auth_token"])
        # client.messages.create(body=body, from_=TWILIO_CONFIG["from_phone"], to=to_number)
        return True
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False

def normalize_phone(phone: str) -> str:
    """Normalize phone number to international format."""
    if not phone:
        return ""
    if phone.startswith("+"):
        return phone
    if phone.startswith("91") and len(phone) == 12:
        return f"+{phone}"
    if phone.startswith("9") and len(phone) == 10:
        return f"+91{phone}"
    return f"+91{phone}"

def send_intake_forms(patient_email, patient_name, doctor_name, appointment_date, appointment_time):
    """Send patient intake forms via email."""
    try:
        body = f"""
        <html>
        <body>
            <h2>Medical Intake Forms</h2>
            <p>Dear {patient_name},</p>
            <p>Thank you for booking your appointment with <strong>{doctor_name}</strong> on <strong>{appointment_date}</strong> at <strong>{appointment_time}</strong>.</p>
            <p>Please find attached the intake forms that need to be filled out before your visit.</p>
            <p>Please complete these forms at your earliest convenience and bring them to your appointment.</p>
            <br>
            <p>Best regards,<br>Medical Clinic Team</p>
        </body>
        </html>
        """
        
        # Create forms directory if it doesn't exist
        os.makedirs("forms", exist_ok=True)
        form_path = "forms/patient_intake_form.pdf"
        
        # Create a simple PDF form if it doesn't exist (for demo)
        if not os.path.exists(form_path):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Patient Intake Form", ln=1, align='C')
            pdf.cell(200, 10, txt=f"Patient Name: {patient_name}", ln=1)
            pdf.cell(200, 10, txt=f"Appointment Date: {appointment_date}", ln=1)
            pdf.cell(200, 10, txt=f"Appointment Time: {appointment_time}", ln=1)
            pdf.cell(200, 10, txt=f"Doctor: {doctor_name}", ln=1)
            pdf.output(form_path)
        
        return send_email_with_attachment.invoke({
            "to_email": patient_email,
            "subject": "Your Patient Intake Forms",
            "body": body,
            "attachment_path": form_path
        })
    except Exception as e:
        print(f"❌ Error sending intake forms: {e}")
        return False


def export_to_excel(booking_info, filename="data/admin_review.xlsx"):
    """Export booking information to Excel for admin review."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Convert booking info to DataFrame
        df = pd.DataFrame([booking_info])
        
        # Check if file exists and append or create new
        if os.path.exists(filename):
            existing_df = pd.read_excel(filename)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_excel(filename, index=False)
        return True
    except Exception as e:
        print(f"❌ Excel export error: {e}")
        return False
