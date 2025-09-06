import streamlit as st
from datetime import datetime
import pandas as pd
import time
import os

DATA_DIR = "data"  # All CSV files are in this folder

# -------------------------------
# Initialize session state variables
# -------------------------------
if 'patient_info' not in st.session_state:
    st.session_state.patient_info = None
if 'doctor_availability' not in st.session_state:
    st.session_state.doctor_availability = None
if 'slots_data' not in st.session_state:
    st.session_state.slots_data = None
if 'booking_complete' not in st.session_state:
    st.session_state.booking_complete = False
if 'email_sent' not in st.session_state:
    st.session_state.email_sent = False

# -------------------------------
# Email Simulation Function
# -------------------------------
def simulate_send_email(recipient_email, patient_name, doctor, appointment_date, appointment_time):
    st.info(f"📧 Preparing email to {recipient_email}...")
    time.sleep(1)  # Simulate processing time

    html_content = f"""
    <html>
    <body>
        <h2>Appointment Confirmation</h2>
        <p>Dear {patient_name},</p>
        <p>Your appointment has been confirmed:</p>
        <ul>
            <li><b>Doctor:</b> {doctor}</li>
            <li><b>Date:</b> {appointment_date}</li>
            <li><b>Time:</b> {appointment_time}</li>
        </ul>
        <p>Please complete your intake forms: 
            <a href="https://forms.example.com/patient-intake">Patient Intake Forms</a>
        </p>
    </body>
    </html>
    """
    st.success(f"✅ Email sent to {recipient_email}!")
    with st.expander("View Email Content"):
        st.markdown(html_content, unsafe_allow_html=True)
        st.write("Intake Forms Link: https://forms.example.com/patient-intake")
    return True

# -------------------------------
# Load CSV Data from data folder
# -------------------------------
def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"{filename} not found in '{DATA_DIR}' folder.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return pd.DataFrame()

# -------------------------------
# Save CSV Data to data folder
# -------------------------------
def save_csv(df, filename):
    path = os.path.join(DATA_DIR, filename)
    df.to_csv(path, index=False)

# -------------------------------
# Get Available Slots
# -------------------------------
def get_available_slots(doctor, date):
    df = st.session_state.doctor_availability
    doctor_date_slots = df[(df['doctor'] == doctor) & (df['date'] == date)]
    available_slots = doctor_date_slots[doctor_date_slots['is_booked'] == False]
    return available_slots

# -------------------------------
# Main App
# -------------------------------
st.title("Medical Appointment Scheduler")

# Load doctor availability
if st.session_state.doctor_availability is None:
    st.session_state.doctor_availability = load_csv("doctors_availability.csv")

if st.session_state.doctor_availability.empty:
    st.error("Unable to load doctor availability data. Please check the 'data' folder.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name*", value="Siva Kumar Yerramsetti")
    dob = st.date_input("Date of Birth*", min_value=datetime(1900,1,1).date(), max_value=datetime.today().date(), value=datetime(2002,3,12).date())
    email = st.text_input("Email*", value="nsiva390@gmail.com")
    phone = st.text_input("Phone*", value="9391241551")
with col2:
    insurance_carrier = st.text_input("Insurance Carrier*", value="Optum")
    member_id = st.text_input("Member ID*", value="Meme004")
    group_number = st.text_input("Group Number*", value="Grp0303")
    reason = st.text_area("Reason for Visit*", value="Regular Checkup")

# Check mandatory fields
mandatory_fields = [name,dob,email,phone,insurance_carrier,member_id,group_number,reason]
all_fields_filled = all([field is not None and str(field).strip() != "" for field in mandatory_fields])

if not all_fields_filled:
    st.warning("⚠️ Please fill in all mandatory fields.")
else:
    st.success("✅ All mandatory fields filled.")

    # Patient Lookup (placeholder)
    if st.session_state.patient_info is None:
        st.session_state.patient_info = {"is_new_patient": True, "name": name, "dob": str(dob)}
    
    patient_info = st.session_state.patient_info
    is_new_patient = patient_info.get("is_new_patient", True)
    patient_type = "New Patient" if is_new_patient else "Returning Patient"
    duration = 60 if is_new_patient else 30
    st.info(f"**Patient Type:** {patient_type} ({duration} mins)")

    # Doctor Selection
    available_doctors = st.session_state.doctor_availability["doctor"].unique().tolist()
    doctor = st.selectbox("Choose Doctor*", available_doctors)
    
    # Available dates
    doctor_dates = st.session_state.doctor_availability[st.session_state.doctor_availability['doctor']==doctor]
    available_dates = doctor_dates['date'].unique()
    selected_date = st.date_input("Select Appointment Date*", min_value=datetime.strptime(sorted(available_dates)[0], "%Y-%m-%d").date(), max_value=datetime.strptime(sorted(available_dates)[-1], "%Y-%m-%d").date())
    
    if str(selected_date) in available_dates:
        available_slots = get_available_slots(doctor, str(selected_date))
        slot_options = [f"{row['start_time']} → {row['end_time']} ({row['duration_mins']} mins)" for idx,row in available_slots.iterrows()]
        slot = st.selectbox("Available Slots*", slot_options)
        
        if st.button("Book Appointment") and not st.session_state.booking_complete:
            start_time, end_time = slot.split("→")[0].strip(), slot.split("→")[1].split("(")[0].strip()
            
            # Save appointment to CSV
            appointments_df = load_csv("appointments.csv")
            new_booking = {
                "patient_name": name,
                "email": email,
                "doctor": doctor,
                "date": str(selected_date),
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "reason": reason,
                "booked_at": datetime.now().isoformat()
            }
            appointments_df = pd.concat([appointments_df, pd.DataFrame([new_booking])], ignore_index=True)
            save_csv(appointments_df, "appointments.csv")
            
            # Mark slot as booked
            slot_idx = st.session_state.doctor_availability[(st.session_state.doctor_availability['doctor']==doctor)&(st.session_state.doctor_availability['date']==str(selected_date))&(st.session_state.doctor_availability['start_time']==start_time)].index[0]
            st.session_state.doctor_availability.at[slot_idx,'is_booked'] = True
            save_csv(st.session_state.doctor_availability, "doctors_availability.csv")
            
            # Send email
            st.session_state.email_sent = simulate_send_email(email, name, doctor, str(selected_date), f"{start_time} - {end_time}")
            
            st.success(f"✅ Appointment booked with {doctor} on {selected_date} at {start_time}")
            st.session_state.booking_complete = True

# Reset button
if st.session_state.booking_complete:
    if st.button("Book Another Appointment"):
        st.session_state.booking_complete = False
        st.session_state.patient_info = None
        st.session_state.email_sent = False
        st.rerun()
