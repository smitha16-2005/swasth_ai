from groq import AsyncGroq
from core.config import settings
import json

client = AsyncGroq(api_key=settings.groq_api_key)

GENERIC_QUESTIONS = [
    "duration",
    "severity",
    "location",
    "associated_symptoms",
    "context"
]

GENERIC_PHASE_COUNT = 5
DISEASE_PHASE_COUNT = 4

RED_FLAG_KEYWORDS = [
    "chest pain", "chest tightness",
    "difficulty breathing", "can't breathe", "cannot breathe",
    "loss of consciousness", "unconscious", "fainted",
    "blood in urine", "blood in stool", "vomiting blood",
    "severe headache sudden", "worst headache",
    "stiff neck", "sensitivity to light",
    "paralysis", "can't move", "cannot move",
    "seizure", "convulsion",
    "high fever infant", "fever in baby"
]


def check_red_flags(symptoms: list, answers: dict) -> bool:
    all_text = " ".join(symptoms).lower()
    for answer in answers.values():
        all_text += " " + answer.lower()
    return any(flag in all_text for flag in RED_FLAG_KEYWORDS)


async def get_suspected_disease(symptoms: list, answers: dict) -> dict:
    from services.vector_db import query_guidelines
    rag_context = query_guidelines(symptoms)
    prompt = f"""
    You are a clinical triage AI trained on Indian disease patterns.
    Patient symptoms: {', '.join(symptoms)}
    Patient answers so far: {json.dumps(answers, indent=2)}
    Relevant ICMR clinical guidelines:
    {rag_context}
    Based on this complete picture:
    1. What is the single most likely disease or condition?
    2. How confident are you (0-100)?
    Common Indian diseases to consider:
    Malaria, Dengue, Typhoid, Tuberculosis, Chikungunya,
    Viral fever, COVID-19, Pneumonia, Gastroenteritis,
    Urinary tract infection, Anaemia, Hypertension crisis,
    Appendicitis, Jaundice, Leptospirosis
    Return ONLY this JSON, no explanation:
    {{
        "suspected_disease": "disease name",
        "confidence": number between 0-100,
        "reasoning": "one sentence why you suspect this"
    }}
    """
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

async def get_generic_question(category: str, symptoms: list) -> str:
    from services.cache import get_cached_question, set_cached_question

    # Check cache first — skips Groq call entirely if seen before
    cached = get_cached_question(symptoms, category)
    if cached:
        return cached

    prompt = f"""
    You are a medical triage assistant working in rural India.
    Patient symptoms: {', '.join(symptoms)}
    Generate ONE short follow-up question about: {category}
    Rules:
    - Maximum 15 words
    - Simple everyday language, zero medical jargon
    - Warm and caring tone
    - For severity, always use 1-10 scale
    - Return ONLY the question, nothing else
    Category meanings:
    - duration: how long they have had the symptoms
    - severity: how bad it feels on a 1 to 10 scale
    - location: exactly where on the body the problem is
    - associated_symptoms: any other symptoms they have alongside
    - context: recent travel, injury, or contact with sick people
    """
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    question = response.choices[0].message.content.strip()

    # Save to cache for next time
    set_cached_question(symptoms, category, question)
    return question


async def get_disease_specific_question(
    disease: str,
    symptoms: list,
    questions_already_asked: list,
    answers_collected: dict,
    disease_questions_asked: int
) -> tuple[str, str]:
    from services.vector_db import query_guidelines
    rag_context = query_guidelines(symptoms, suspected_disease=disease)
    prompt = f"""
    You are a clinical triage assistant.
    You suspect the patient has: {disease}
    Their symptoms: {', '.join(symptoms)}
    This is question number {disease_questions_asked + 1} of 4 about this disease.
    Relevant ICMR guidelines for {disease}:
    {rag_context}
    Everything already asked and answered by the patient:
    {json.dumps(answers_collected, indent=2)}
    Generate ONE targeted question based on the ICMR guidelines
    that would CONFIRM or RULE OUT {disease}.
    STRICT RULES:
    - Do NOT ask about anything already covered in the answers above
    - Do NOT repeat any topic even if the patient said no
    - Base your question on the ICMR guidelines provided
    - Maximum 20 words
    - Simple language, no jargon
    - Return ONLY the question, nothing else
    """
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    question = response.choices[0].message.content.strip()
    category = f"disease_confirm_{disease_questions_asked + 1}"
    return category, question


async def get_next_question(
    symptoms: list,
    questions_asked: list,
    answers_collected: dict,
    phase: str,
    suspected_disease: str = None,
    disease_questions_asked: int = 0
) -> tuple[str, str]:
    if phase == "generic":
        for category in GENERIC_QUESTIONS:
            if category not in questions_asked:
                question = await get_generic_question(category, symptoms)
                return category, question
    elif phase == "disease_specific" and suspected_disease:
        return await get_disease_specific_question(
            disease=suspected_disease,
            symptoms=symptoms,
            questions_already_asked=questions_asked,
            answers_collected=answers_collected,
            disease_questions_asked=disease_questions_asked
        )
    return None, None
