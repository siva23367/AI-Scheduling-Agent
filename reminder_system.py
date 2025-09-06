import pandas as pd
from datetime import datetime, timedelta
from tools import send_email_with_attachment, send_sms, normalize_phone

def check_and_send_reminders():
    """Check and send reminders for upcoming appointments."""
    try:
        df = pd.read_csv("data/reminders.csv")
        today = datetime.now().date()
        
        for idx, row in df.iterrows():
            appt_date = datetime.strptime(row['appointment_date'], "%Y-%m-%d").date()
            days_until = (appt_date - today).days
            
            # Send reminders at specific intervals
            if days_until == 7 and not row['reminder1_sent']:
                send_reminder(row, 1)
                df.at[idx, 'reminder1_sent'] = True
                
            elif days_until == 3 and not row['reminder2_sent']:
                # Check form status for second reminder
                form_status = "not completed" if not row['forms_completed'] else "completed"
                send_reminder(row, 2, form_status)
                df.at[idx, 'reminder2_sent'] = True
                
            elif days_until == 1 and not row['reminder3_sent']:
                # Check confirmation status for final reminder
                confirmation_status = "confirmed" if row['visit_confirmed'] else f"cancelled: {row['cancellation_reason']}"
                send_reminder(row, 3, confirmation_status)
                df.at[idx, 'reminder3_sent'] = True
        
        # Save updated reminders
        df.to_csv("data/reminders.csv", index=False)
        print("Reminder check completed successfully.")
        
    except FileNotFoundError:
        print("No reminders data found.")
    except Exception as e:
        print(f"Error in reminder system: {e}")

def send_reminder(patient_data, reminder_num, status=""):
    """Send a reminder to a patient."""
    try:
        if reminder_num == 1:
            # First reminder - general reminder
            email_body = f"""
            <html>
            <body>
                <h2>Appointment Reminder</h2>
                <p>Dear {patient_data['patient_name']},</p>
                
                <p>This is a friendly reminder about your upcoming appointment:</p>
                <ul>
                    <li><strong>Doctor:</strong> {patient_data['doctor']}</li>
                    <li><strong>Date:</strong> {patient_data['appointment_date']}</li>
                    <li><strong>Time:</strong> {patient_data['appointment_time']}</li>
                </ul>
                
                <p>Please remember to complete your intake forms before the appointment.</p>
                
                <p>Best regards,<br>Medical Clinic Team</p>
            </body>
            </html>
            """
            
            send_email_with_attachment(
                patient_data['patient_email'],
                "Appointment Reminder",
                email_body
            )
            
            sms_body = f"Reminder: Appt with {patient_data['doctor']} on {patient_data['appointment_date']} at {patient_data['appointment_time']}."
            send_sms(normalize_phone(patient_data['patient_phone']), sms_body)
            
        elif reminder_num == 2:
            # Second reminder - check form status
            email_body = f"""
            <html>
            <body>
                <h2>Appointment Reminder - Form Status</h2>
                <p>Dear {patient_data['patient_name']},</p>
                
                <p>Your appointment is coming up soon:</p>
                <ul>
                    <li><strong>Doctor:</strong> {patient_data['doctor']}</li>
                    <li><strong>Date:</strong> {patient_data['appointment_date']}</li>
                    <li><strong>Time:</strong> {patient_data['appointment_time']}</li>
                </ul>
                
                <p><strong>Form Status:</strong> {status}</p>
                
                <p>Please complete your intake forms if you haven't already.</p>
                
                <p>Best regards,<br>Medical Clinic Team</p>
            </body>
            </html>
            """
            
            send_email_with_attachment(
                patient_data['patient_email'],
                "Appointment Reminder - Form Check",
                email_body
            )
            
            sms_body = f"Reminder: Appt in 3 days. Forms: {status}. Please complete if needed."
            send_sms(normalize_phone(patient_data['patient_phone']), sms_body)
            
        elif reminder_num == 3:
            # Third reminder - final confirmation
            email_body = f"""
            <html>
            <body>
                <h2>Final Appointment Reminder</h2>
                <p>Dear {patient_data['patient_name']},</p>
                
                <p>Your appointment is tomorrow:</p>
                <ul>
                    <li><strong>Doctor:</strong> {patient_data['doctor']}</li>
                    <li><strong>Date:</strong> {patient_data['appointment_date']}</li>
                    <li><strong>Time:</strong> {patient_data['appointment_time']}</li>
                </ul>
                
                <p><strong>Visit Status:</strong> {status}</p>
                
                <p>Please arrive 15 minutes early for your appointment.</p>
                
                <p>Best regards,<br>Medical Clinic Team</p>
            </body>
            </html>
            """
            
            send_email_with_attachment(
                patient_data['patient_email'],
                "Final Appointment Reminder",
                email_body
            )
            
            sms_body = f"Final reminder: Appt tomorrow at {patient_data['appointment_time']}. Status: {status}."
            send_sms(normalize_phone(patient_data['patient_phone']), sms_body)
            
    except Exception as e:
        print(f"Error sending reminder: {e}")

if __name__ == "__main__":
    check_and_send_reminders()