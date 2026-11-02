from groq import AsyncGroq
from core.config import settings
import json

client = AsyncGroq(api_key=settings.groq_api_key)

async def extract_symptoms(translated_text: str) -> dict:
    prompt = f"""
    You are a medical data extraction assistant.
    Extract symptoms from this patient statement and return ONLY a JSON object.
    No explanation, no markdown, just raw JSON.

    Patient says: "{translated_text}"

    Return this exact format:
    {{
        "symptoms": ["list", "of", "symptoms"],
        "duration": "how long (e.g. 3 days) or null if not mentioned",
        "severity": "mild/moderate/severe or null if not mentioned",
        "red_flags": ["any dangerous symptoms like chest pain, difficulty breathing"]
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
