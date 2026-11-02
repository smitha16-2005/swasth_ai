from fastapi import APIRouter
from pydantic import BaseModel
from services.sms_service import send_followup_sms

router = APIRouter()

class SMSRequest(BaseModel):
    phone_number: str
    patient_name: str
    risk_level: str
    suspected_disease: str
    facility_message: str

@router.post("/sms/followup")
def send_sms(request: SMSRequest):
    result = send_followup_sms(
        phone_number=request.phone_number,
        patient_name=request.patient_name,
        risk_level=request.risk_level,
        suspected_disease=request.suspected_disease,
        facility_message=request.facility_message
    )
    return result