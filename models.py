from sqlalchemy import Column, String, DateTime, Integer, JSON
from datetime import datetime
from database import Base

class TriageSession(Base):
    __tablename__ = "triage_sessions"

    session_id          = Column(String, primary_key=True)
    input_text          = Column(String)
    language            = Column(String)
    translated          = Column(String, nullable=True)
    extracted_symptoms  = Column(JSON, nullable=True)
    answers_collected   = Column(JSON, nullable=True)
    questions_asked     = Column(JSON, nullable=True)
    question_texts      = Column(JSON, nullable=True)   # NEW: actual question wording
    clarification_round = Column(Integer, default=0)
    confidence          = Column(Integer, default=0)
    suspected_disease   = Column(String, nullable=True)
    risk_level          = Column(String, nullable=True)
    status              = Column(String)
    created_at          = Column(DateTime, default=datetime.utcnow)