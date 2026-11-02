import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from database import get_db
from models import TriageSession
from schemas import TriageRequest, FollowUpRequest, TriageResponse
from services.nlp import translate_to_english, translate_from_english
from services.extractor import extract_symptoms
from services.questioner import (
    check_red_flags,
    get_next_question,
    get_suspected_disease,
    GENERIC_PHASE_COUNT,
    DISEASE_PHASE_COUNT
)
from services.risk_scorer import assign_risk_level
from services.facility_locator import find_nearby_facilities, format_facility_message
from services.sms_service import send_followup_sms

router = APIRouter()

RED_ALERT_EN = "Emergency. Go to the nearest hospital immediately. Call 108."


def readable_answers(questions_asked: list, question_texts: list, answers: dict) -> dict:
    """{"disease_confirm_1": "yes"} -> {"Do you have pain behind your eyes?": "yes"}"""
    readable = {}
    for category, text in zip(questions_asked, question_texts):
        if category in answers:
            readable[text] = answers[category]
    return readable


async def red_alert_text(language: str) -> str:
    message = await translate_from_english(RED_ALERT_EN, language)
    return f"🔴 RED — {message}"


@router.post("/triage", response_model=TriageResponse)
async def triage(request: TriageRequest, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    language = request.language.value

    # Patient's language -> English
    translated_text = await translate_to_english(
        text=request.text,
        source_language=language
    )

    extracted = await extract_symptoms(translated_text)
    symptoms = extracted.get("symptoms", [])

    if check_red_flags(symptoms, {}):
        record = TriageSession(
            session_id          = session_id,
            input_text          = request.text,
            language            = language,
            translated          = translated_text,
            extracted_symptoms  = symptoms,
            answers_collected   = {},
            questions_asked     = [],
            question_texts      = [],
            clarification_round = 0,
            confidence          = 100,
            suspected_disease   = None,
            risk_level          = "RED",
            status              = "red_flag_detected"
        )
        db.add(record)
        db.commit()

        return TriageResponse(
            session_id         = session_id,
            received_text      = request.text,
            language           = language,
            timestamp          = datetime.utcnow().isoformat(),
            status             = "red_flag_detected",
            follow_up_question = None,
            risk_level         = await red_alert_text(language)
        )

    category, question_en = await get_next_question(
        symptoms                = symptoms,
        questions_asked         = [],
        answers_collected       = {},
        phase                   = "generic",
        suspected_disease       = None,
        disease_questions_asked = 0
    )

    record = TriageSession(
        session_id          = session_id,
        input_text          = request.text,
        language            = language,
        translated          = translated_text,
        extracted_symptoms  = symptoms,
        answers_collected   = {},
        questions_asked     = [category],
        question_texts      = [question_en],      # English is stored for the AI
        clarification_round = 1,
        confidence          = 0,
        suspected_disease   = None,
        risk_level          = None,
        status              = "phase1_generic"
    )
    db.add(record)
    db.commit()

    # English -> patient's language for display
    question_local = await translate_from_english(question_en, language)

    return TriageResponse(
        session_id         = session_id,
        received_text      = request.text,
        language           = language,
        timestamp          = datetime.utcnow().isoformat(),
        status             = "phase1_generic — question 1 of 5",
        follow_up_question = question_local,
        risk_level         = None
    )


@router.post("/triage/followup", response_model=TriageResponse)
async def followup(request: FollowUpRequest, db: Session = Depends(get_db)):

    session = db.query(TriageSession).filter(
        TriageSession.session_id == request.session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    language = session.language

    answers         = dict(session.answers_collected or {})
    questions_asked = list(session.questions_asked or [])
    question_texts  = list(session.question_texts or [])

    # Patient's answer -> English BEFORE any checks
    english_answer = await translate_to_english(request.answer, language)

    last_category = questions_asked[-1]
    answers[last_category] = english_answer

    if check_red_flags(session.extracted_symptoms or [], answers):
        session.answers_collected = answers
        session.risk_level        = "RED"
        session.confidence        = 100
        session.status            = "red_flag_detected"
        db.commit()

        return TriageResponse(
            session_id         = request.session_id,
            received_text      = request.answer,
            language           = language,
            timestamp          = datetime.utcnow().isoformat(),
            status             = "red_flag_detected",
            follow_up_question = None,
            risk_level         = await red_alert_text(language)
        )

    qa = readable_answers(questions_asked, question_texts, answers)

    round_number      = session.clarification_round
    suspected_disease = session.suspected_disease

    disease_questions_asked = sum(
        1 for q in questions_asked if q.startswith("disease_confirm_")
    )

    # ── PHASE 1: Generic questions ────────────────────────────────
    if round_number < GENERIC_PHASE_COUNT:
        next_category, next_question = await get_next_question(
            symptoms                = session.extracted_symptoms or [],
            questions_asked         = questions_asked,
            answers_collected       = qa,
            phase                   = "generic",
            suspected_disease       = None,
            disease_questions_asked = 0
        )

        questions_asked.append(next_category)
        question_texts.append(next_question)

        session.answers_collected   = answers
        session.questions_asked     = questions_asked
        session.question_texts      = question_texts
        session.clarification_round = round_number + 1
        session.status              = "phase1_generic"
        db.commit()

        return TriageResponse(
            session_id         = request.session_id,
            received_text      = request.answer,
            language           = language,
            timestamp          = datetime.utcnow().isoformat(),
            status             = f"phase1_generic — question {round_number + 1} of {GENERIC_PHASE_COUNT}",
            follow_up_question = await translate_from_english(next_question, language),
            risk_level         = None
        )

    # ── TRANSITION: suspect disease once ──────────────────────────
    if round_number == GENERIC_PHASE_COUNT and not suspected_disease:
        disease_data = await get_suspected_disease(
            symptoms = session.extracted_symptoms or [],
            answers  = qa
        )
        suspected_disease         = disease_data.get("suspected_disease")
        session.suspected_disease = suspected_disease
        session.confidence        = disease_data.get("confidence", 0)

    # ── PHASE 2: Disease-specific questions ───────────────────────
    if disease_questions_asked < DISEASE_PHASE_COUNT:
        next_category, next_question = await get_next_question(
            symptoms                = session.extracted_symptoms or [],
            questions_asked         = questions_asked,
            answers_collected       = qa,
            phase                   = "disease_specific",
            suspected_disease       = suspected_disease,
            disease_questions_asked = disease_questions_asked
        )

        questions_asked.append(next_category)
        question_texts.append(next_question)

        session.answers_collected   = answers
        session.questions_asked     = questions_asked
        session.question_texts      = question_texts
        session.clarification_round = round_number + 1
        session.status              = "phase2_disease_specific"
        db.commit()

        return TriageResponse(
            session_id         = request.session_id,
            received_text      = request.answer,
            language           = language,
            timestamp          = datetime.utcnow().isoformat(),
            status             = f"phase2_disease_specific — question {disease_questions_asked + 1} of {DISEASE_PHASE_COUNT} — suspected: {suspected_disease}",
            follow_up_question = await translate_from_english(next_question, language),
            risk_level         = None
        )

    # ── FINAL: Assign risk level ──────────────────────────────────
    result = await assign_risk_level(
        symptoms          = session.extracted_symptoms or [],
        answers           = qa,
        suspected_disease = suspected_disease
    )

    emoji_map = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}
    risk    = result.get("risk_level", "YELLOW")
    emoji   = emoji_map.get(risk, "🟡")
    disease = result.get("suspected_disease", suspected_disease or "unknown")
    action  = result.get("recommended_action", "")

    facilities       = find_nearby_facilities(
        latitude   = request.latitude,
        longitude  = request.longitude,
        risk_level = risk
    )
    facility_message_en = format_facility_message(facilities, risk)

    # Translate summary and facility info together to save time
    summary_local, facility_local = await asyncio.gather(
        translate_from_english(f"Possible {disease}. {action}", language),
        translate_from_english(facility_message_en, language),
    )

    send_followup_sms(
        phone_number      = "+919999999999",
        patient_name      = "Patient",
        risk_level        = risk,
        suspected_disease = disease,
        facility_message  = facility_local
    )

    session.answers_collected = answers
    session.confidence        = result.get("confidence", 0)
    session.risk_level        = risk
    session.status            = "completed"
    db.commit()

    # "RED"/"YELLOW"/"GREEN" stays in English so the frontend colours still work
    return TriageResponse(
        session_id         = request.session_id,
        received_text      = request.answer,
        language           = language,
        timestamp          = datetime.utcnow().isoformat(),
        status             = "completed",
        follow_up_question = None,
        risk_level         = f"{emoji} {risk} — {summary_local}\n\n{facility_local}"
    )


@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(TriageSession).all()
    return [
        {
            "session_id":        s.session_id,
            "language":          s.language,
            "input_text":        s.input_text,
            "translated":        s.translated,
            "symptoms":          s.extracted_symptoms,
            "suspected_disease": s.suspected_disease,
            "risk_level":        s.risk_level,
            "confidence":        s.confidence,
            "rounds":            s.clarification_round,
            "status":            s.status,
            "created_at":        s.created_at.isoformat()
        }
        for s in sessions
    ]