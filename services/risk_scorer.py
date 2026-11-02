from groq import AsyncGroq
from core.config import settings
from services.vector_db import query_guidelines
import json

client = AsyncGroq(api_key=settings.groq_api_key)


async def assign_risk_level(
    symptoms: list,
    answers: dict,
    suspected_disease: str = None
) -> dict:
    rag_context = query_guidelines(symptoms, suspected_disease)
    disease_context = ""
    if suspected_disease:
        disease_context = f"The AI suspects this may be {suspected_disease}."

    prompt = f"""
    You are a clinical triage assistant trained on Indian disease patterns.
    Patient symptoms: {', '.join(symptoms)}
    Patient answers: {json.dumps(answers, indent=2)}
    Relevant ICMR clinical guidelines:
    {rag_context}
    {disease_context}
    Assign a final risk level based on ALL the data above.
    Risk levels:
    - RED: Life threatening. Go to emergency immediately.
    - YELLOW: Needs medical attention within 24 hours.
    - GREEN: Can safely monitor at home for 24-48 hours.
    Return ONLY this JSON, no explanation:
    {{
        "risk_level": "RED" or "YELLOW" or "GREEN",
        "confidence": number between 0-100,
        "suspected_disease": "most likely condition name",
        "reasoning": "one sentence clinical reasoning",
        "recommended_action": "specific action for patient to take"
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
