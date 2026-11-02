from pydantic import BaseModel
from enum import Enum
from typing import Optional

class Language(str, Enum):
    hindi   = "hi"
    tamil   = "ta"
    telugu  = "te"
    kannada = "kn"
    bengali = "bn"
    english = "en"

# First message from user
class TriageRequest(BaseModel):
    text: str
    language: Language

# Follow-up answer from user
class FollowUpRequest(BaseModel):
    session_id: str
    answer: str
    latitude: float = 12.9716   # default Bangalore
    longitude: float = 77.5946  # default Bangalore           # user's answer to the follow-up question

# What server sends back every round
class TriageResponse(BaseModel):
    session_id: str
    received_text: str
    language: str
    timestamp: str
    status: str
    follow_up_question: Optional[str] = None   # next question to ask user
    risk_level: Optional[str] = None           # only set when decision is made