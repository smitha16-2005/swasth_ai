from fastapi import APIRouter
from pydantic import BaseModel
from services.facility_locator import find_nearby_facilities, format_facility_message

router = APIRouter()

class FacilityRequest(BaseModel):
    latitude: float
    longitude: float
    risk_level: str
    session_id: str

class FacilityResponse(BaseModel):
    facilities: list
    message: str
    emergency_number: str = "104"

@router.post("/facilities/nearby", response_model=FacilityResponse)
def get_nearby_facilities(request: FacilityRequest):
    facilities = find_nearby_facilities(
        latitude=request.latitude,
        longitude=request.longitude,
        risk_level=request.risk_level
    )
    message = format_facility_message(facilities, request.risk_level)
    return FacilityResponse(
        facilities=facilities,
        message=message,
        emergency_number="104"
    )