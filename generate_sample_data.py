#!/usr/bin/env python3
"""
Sample Data Generator for Ai_Scheduler Project
Generates patients.csv, doctors_availability.xlsx, and sample intake form
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# Initialize Faker
fake = Faker()

def generate_patients_data(num_patients=50):
    """Generate synthetic patient data"""
    print("Generating patient data...")
    
    patients_list = []
    for i in range(1, num_patients + 1):
        first_name = fake.first_name()
        last_name = fake.last_name()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        
        patients_list.append({
            'patient_id': f'PAT{i:03d}',
            'first_name': first_name,
            'last_name': last_name,
            'dob': dob.strftime('%Y-%m-%d'),
            'email': fake.email(),
            'phone': f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}",
            'address': fake.address().replace('\n', ', '),
            'emergency_contact': f"{fake.first_name()} {fake.last_name()}",
            'emergency_phone': f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}",
            'primary_care_physician': random.choice(['Dr. Smith', 'Dr. Johnson', 'Dr. Lee', 'Dr. Garcia', 'Dr. Wilson']),
            'insurance_provider': random.choice(['UnitedHealth', 'Anthem', 'Aetna', 'Cigna', 'Blue Cross']),
            'insurance_id': f"INS{random.randint(10000, 99999)}",
            'last_visit': fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d'),
            'is_active': random.choices([True, False], weights=[0.8, 0.2])[0]
        })
    
    patients_df = pd.DataFrame(patients_list)
    patients_df.to_csv('data/patients.csv', index=False)
    print(f"Generated {num_patients} patients in data/patients.csv")
    return patients_df

def generate_doctors_availability():
    """Generate doctor availability schedule"""
    print("Generating doctor availability...")
    
    doctors = [
        'Dr. Smith (Cardiology)',
        'Dr. Johnson (Neurology)', 
        'Dr. Lee (Pediatrics)',
        'Dr. Garcia (Dermatology)',
        'Dr. Wilson (Orthopedics)'
    ]
    
    slots_list = []
    start_date = datetime.now().date()
    
    for doctor in doctors:
        for day in range(14):  # Generate for next 14 days
            current_date = start_date + timedelta(days=day)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
                
            # Create slots from 9 AM to 4 PM with 30-minute intervals
            for hour in [9, 10, 11, 13, 14, 15]:  # Skip 12 PM (lunch)
                start_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour)
                
                # Add 30-min slot (for returning patients)
                end_time_30min = start_time + timedelta(minutes=30)
                slots_list.append({
                    'doctor_name': doctor,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'day_of_week': current_date.strftime('%A'),
                    'start_time': start_time.strftime('%H:%M'),
                    'end_time': end_time_30min.strftime('%H:%M'),
                    'duration_minutes': 30,
                    'is_available': True,
                    'appointment_type': 'Follow-up'
                })
                
                # Add 60-min slot (for new patients)
                end_time_60min = start_time + timedelta(minutes=60)
                slots_list.append({
                    'doctor_name': doctor,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'day_of_week': current_date.strftime('%A'),
                    'start_time': end_time_30min.strftime('%H:%M'),
                    'end_time': end_time_60min.strftime('%H:%M'),
                    'duration_minutes': 60,
                    'is_available': True,
                    'appointment_type': 'New Patient'
                })
    
    availability_df = pd.DataFrame(slots_list)
    
    # Randomly book some slots to make it realistic
    mask = np.random.random(len(availability_df)) < 0.3  # 30% of slots are booked
    availability_df.loc[mask, 'is_available'] = False
    availability_df.loc[mask, 'patient_id'] = random.choices(
        [f'PAT{i:03d}' for i in range(1, 51)], 
        k=mask.sum()
    )
    
    with pd.ExcelWriter('data/doctors_availability.xlsx', engine='openpyxl') as writer:
        availability_df.to_excel(writer, sheet_name='Availability', index=False)
        
        # Add a summary sheet
        summary_df = availability_df.groupby(['doctor_name', 'date', 'is_available']).size().unstack(fill_value=0)
        summary_df.to_excel(writer, sheet_name='Summary')
    
    print("Generated doctor availability in data/doctors_availability.xlsx")
    return availability_df

def create_booked_appointments_file():
    """Create empty booked appointments file with proper columns"""
    print("Creating booked appointments template...")
    
    columns = [
        'appointment_id', 'patient_id', 'patient_name', 'doctor_name',
        'appointment_date', 'appointment_time', 'duration_minutes',
        'appointment_type', 'reason', 'insurance_provider',
        'insurance_id', 'status', 'booked_date', 'reminders_sent'
    ]
    
    booked_df = pd.DataFrame(columns=columns)
    booked_df.to_excel('data/booked_appointments.xlsx', index=False)
    print("Created booked appointments template in data/booked_appointments.xlsx")

def create_sample_intake_form():
    """Create a sample intake form text file (simulating PDF)"""
    print("Creating sample intake form...")
    
    form_content = """RAGAAI MEDICAL CENTER - PATIENT INTAKE FORM

Please complete this form to help us provide you with the best possible care.

PERSONAL INFORMATION:
Full Name: _________________________
Date of Birth: _____________________
Phone Number: ______________________
Email: _____________________________
Address: ___________________________

EMERGENCY CONTACT:
Name: ______________________________
Relationship: ______________________
Phone: _____________________________

INSURANCE INFORMATION:
Provider: ___________________________
Member ID: _________________________
Group Number: ______________________

MEDICAL HISTORY:
Please list any current medications: 
____________________________________
____________________________________

Allergies: 
____________________________________
____________________________________

Previous surgeries or medical conditions:
____________________________________
____________________________________

REASON FOR TODAY'S VISIT:
____________________________________
____________________________________

SIGNATURE: _________________________
DATE: ______________________________

Thank you for completing this form. Your information is kept confidential.
"""
    
    with open('data/intake_form.pdf', 'w') as f:
        f.write(form_content)
    print("Created sample intake form in data/intake_form.pdf")

def main():
    """Main function to generate all sample data"""
    print("=" * 50)
    print("GENERATING SAMPLE DATA FOR AI SCHEDULER")
    print("=" * 50)
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    try:
        # Generate all data files
        generate_patients_data(50)
        generate_doctors_availability()
        create_booked_appointments_file()
        create_sample_intake_form()
        
        print("=" * 50)
        print("SAMPLE DATA GENERATION COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("Files created:")
        print("- data/patients.csv (50 synthetic patients)")
        print("- data/doctors_availability.xlsx (2-week schedule)")
        print("- data/booked_appointments.xlsx (empty template)")
        print("- data/intake_form.pdf (sample form)")
        
    except Exception as e:
        print(f"Error generating sample data: {e}")
        raise

if __name__ == "__main__":
    main()