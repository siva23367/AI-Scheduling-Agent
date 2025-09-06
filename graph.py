import pandas as pd
from datetime import datetime, timedelta
from langchain_core.tools import tool
from tools import send_email_with_attachment, send_sms, send_intake_forms, export_to_excel, generate_patient_id, normalize_phone
import os
from langchain_core.callbacks import CallbackManager
from langchain_core.callbacks.stdout import StdOutCallbackHandler

# Create a callback manager for LangChain tools
callback_manager = CallbackManager([StdOutCallbackHandler()])

# -------------------------------
# Patient Lookup
# -------------------------------
@tool("patient_lookup_tool", description="Lookup patient by name and date of birth.")
def patient_lookup(name: str, dob: str) -> dict:
    """
    Lookup patient in patients.csv.
    Returns patient info or marks as new patient if not found.
    """
    try:
        df = pd.read_csv("data/patients.csv")
        # Handle potential empty values
        df = df[df['name'].notna()]
        
        # Try to find patient by name and DOB
        patient_row = df[(df['name'].str.lower() == name.lower()) & (df['dob'] == dob)]
        
        if patient_row.empty:
            return {"is_new_patient": True, "name": name, "dob": dob}
        else:
            patient_data = patient_row.iloc[0].to_dict()
            patient_data["is_new_patient"] = False
            return patient_data
    except FileNotFoundError:
        return {"is_new_patient": True, "name": name, "dob": dob}

# -------------------------------
# Add New Patient
# -------------------------------
@tool("add_new_patient_tool", description="Add a new patient to patients.csv.")
def add_new_patient(patient: dict) -> str:
    """
    Adds a new patient to patients.csv file.
    """
    try:
        # Generate patient ID if not provided
        if 'patient_id' not in patient or not patient['patient_id']:
            patient_id_result = generate_patient_id.invoke({}, config={"callbacks": callback_manager})
            patient['patient_id'] = patient_id_result
        
        # Set created_at timestamp
        patient['created_at'] = datetime.now().isoformat()
        
        df = pd.DataFrame([patient])
        
        # Read existing data or create new dataframe
        try:
            existing = pd.read_csv("data/patients.csv")
            df = pd.concat([existing, df], ignore_index=True)
        except FileNotFoundError:
            pass
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/patients.csv", index=False)
        return "New patient added successfully."
    except Exception as e:
        return f"Error adding patient: {e}"

# -------------------------------
# Get Available Slots - FIXED VERSION
# -------------------------------
@tool("get_available_slots_tool", description="Get available slots for a doctor on a given date.")
def get_available_slots(doctor: str, date: str) -> pd.DataFrame:
    """
    Returns a dataframe of available slots for the selected doctor on the specified date.
    """
    try:
        df = pd.read_csv("data/doctors_availability.csv")
        
        # Debug: Print the raw data
        print(f"Raw data for {doctor} on {date}:")
        print(df[(df['doctor'] == doctor) & (df['date'] == date)])
        
        # Convert date strings to datetime objects for comparison
        df['date'] = pd.to_datetime(df['date']).dt.date
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        print(f"Looking for doctor: {doctor}, date: {selected_date}")
        print(f"Available doctors: {df['doctor'].unique()}")
        print(f"Available dates: {df['date'].unique()}")
        
        # Filter by doctor, date, and available slots
        available_slots = df[(df['doctor'] == doctor) & 
                            (df['date'] == selected_date) & 
                            (df['is_booked'] == False)]
        
        print(f"Found {len(available_slots)} available slots")
        
        return available_slots
    except Exception as e:
        print(f"Error getting available slots: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

# -------------------------------
# Book Slot
# -------------------------------
@tool("book_slot_tool", description="Book an appointment slot for a patient.")
def book_slot(booking_info: dict) -> str:
    """
    Records the appointment booking in bookings.csv and updates availability.
    """
    try:
        # Update doctors availability
        df_availability = pd.read_csv("data/doctors_availability.csv")
        
        # Find the slot to mark as booked
        mask = ((df_availability['doctor'] == booking_info['doctor']) &
                (df_availability['date'] == booking_info['date']) &
                (df_availability['start_time'] == booking_info['start_time']))
        
        if mask.any():
            df_availability.loc[mask, 'is_booked'] = True
            df_availability.loc[mask, 'patient_id'] = booking_info.get('patient_id', '')
            df_availability.to_csv("data/doctors_availability.csv", index=False)
        
        # Add to bookings
        booking_df = pd.DataFrame([booking_info])
        try:
            existing_bookings = pd.read_csv("data/bookings.csv")
            booking_df = pd.concat([existing_bookings, booking_df], ignore_index=True)
        except FileNotFoundError:
            pass
        
        booking_df.to_csv("data/bookings.csv", index=False)
        return "Appointment booked successfully."
    except Exception as e:
        return f"Error booking slot: {e}"

# -------------------------------
# Confirm & Notify
# -------------------------------
@tool("confirm_and_notify_tool", description="Send confirmation message to patient.")
def confirm_and_notify(booking_info: dict) -> str:
    """
    Send email/SMS confirmation to patient.
    """
    try:
        # Email confirmation
        email_body = f"""
        <html>
        <body>
            <h2>Appointment Confirmation</h2>
            <p>Dear {booking_info['patient_name']},</p>
            
            <p>Your appointment has been confirmed:</p>
            <ul>
                <li><strong>Doctor:</strong> {booking_info['doctor']}</li>
                <li><strong>Date:</strong> {booking_info.get('date', 'Not specified')}</li>
                <li><strong>Time:</strong> {booking_info['start_time']} - {booking_info['end_time']}</li>
                <li><strong>Duration:</strong> {booking_info.get('duration_minutes', 30)} minutes</li>
                <li><strong>Reason:</strong> {booking_info['reason']}</li>
            </ul>
            
            <p>Please arrive 15 minutes early for your appointment.</p>
            
            <p>Best regards,<br>Medical Clinic Team</p>
        </body>
        </html>
        """
        
        send_email_with_attachment.invoke({
            "to_email": booking_info['patient_email'],
            "subject": "Appointment Confirmation",
            "body": email_body
        }, config={"callbacks": callback_manager})
        
        # SMS confirmation
        sms_body = f"Appt confirmed with {booking_info['doctor']} on {booking_info.get('date', '')} at {booking_info['start_time']}. Reply CANCEL to cancel."
        send_sms.invoke({
            "to_number": normalize_phone(booking_info['patient_phone']),
            "body": sms_body
        }, config={"callbacks": callback_manager})
        
        return "Confirmation sent successfully."
    except Exception as e:
        return f"Error sending confirmation: {e}"

# -------------------------------
# Schedule Reminders
# -------------------------------
@tool("schedule_reminders_tool", description="Schedule reminders for upcoming appointment.")
def schedule_reminders_for_appointment(booking_info: dict) -> str:
    """
    Schedule reminders for appointments with form tracking.
    """
    try:
        # Store reminder schedule in a CSV
        reminder_data = {
            'patient_name': booking_info['patient_name'],
            'patient_email': booking_info['patient_email'],
            'patient_phone': booking_info['patient_phone'],
            'appointment_date': booking_info.get('date', ''),
            'appointment_time': booking_info['start_time'],
            'doctor': booking_info['doctor'],
            'forms_sent': True,  # We're sending them now
            'forms_completed': False,
            'visit_confirmed': True,
            'cancellation_reason': '',
            'reminder1_sent': False,
            'reminder2_sent': False,
            'reminder3_sent': False,
            'created_at': datetime.now().isoformat()
        }
        
        df = pd.DataFrame([reminder_data])
        try:
            existing = pd.read_csv("data/reminders.csv")
            df = pd.concat([existing, df], ignore_index=True)
        except FileNotFoundError:
            pass
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/reminders.csv", index=False)
        
        # Send intake forms
        send_intake_forms.invoke({
            "patient_email": booking_info['patient_email'],
            "patient_name": booking_info['patient_name'],
            "doctor_name": booking_info['doctor'],
            "appointment_date": booking_info.get('date', ''),
            "appointment_time": booking_info['start_time']
        }, config={"callbacks": callback_manager})
        
        return "Reminder scheduled successfully and intake forms sent."
    except Exception as e:
        return f"Error scheduling reminders: {e}"

# -------------------------------
# Check Form Status
# -------------------------------
@tool("check_form_status_tool", description="Check if patient has completed intake forms.")
def check_form_status(patient_email: str) -> dict:
    """
    Check if patient has completed intake forms.
    """
    try:
        df = pd.read_csv("data/reminders.csv")
        patient_data = df[df['patient_email'] == patient_email]
        
        if patient_data.empty:
            return {"forms_completed": False, "error": "Patient not found"}
        
        return {
            "forms_completed": bool(patient_data.iloc[0]['forms_completed']),
            "forms_sent": bool(patient_data.iloc[0]['forms_sent'])
        }
    except FileNotFoundError:
        return {"forms_completed": False, "error": "No reminders data found"}

# -------------------------------
# Update Visit Status
# -------------------------------
@tool("update_visit_status_tool", description="Update patient visit confirmation status.")
def update_visit_status(patient_email: str, confirmed: bool, reason: str = "") -> str:
    """
    Update patient visit confirmation status.
    """
    try:
        df = pd.read_csv("data/reminders.csv")
        if patient_email in df['patient_email'].values:
            df.loc[df['patient_email'] == patient_email, 'visit_confirmed'] = confirmed
            df.loc[df['patient_email'] == patient_email, 'cancellation_reason'] = reason
            df.to_csv("data/reminders.csv", index=False)
            return "Visit status updated successfully."
        return "Patient not found in reminders."
    except FileNotFoundError:
        return "No reminders data found."

