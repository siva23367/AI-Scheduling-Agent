from dataclasses import dataclass

@dataclass
class PatientInfo:
    name: str
    dob: str
    email: str
    phone: str
    doctor: str = ""
    insurance_carrier: str = ""
    insurance_member_id: str = ""
    insurance_group_number: str = ""
    is_new_patient: bool = True

@dataclass
class AppointmentInfo:
    patient_name: str
    patient_email: str
    patient_phone: str
    doctor: str
    start_time: str
    end_time: str
    reason: str
    insurance_carrier: str
    insurance_member_id: str
    insurance_group_number: str
    confirmed: bool = False
