from groq import AsyncGroq
from deep_translator import GoogleTranslator
from core.config import settings

client = AsyncGroq(api_key=settings.groq_api_key)

LANGUAGE_NAMES = {
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "bn": "Bengali",
    "en": "English",
}


async def translate_to_english(text: str, source_language: str) -> str:
    """Patient's language -> English (for AI reasoning and red-flag checks)."""
    if source_language == "en" or not text:
        return text

    language = LANGUAGE_NAMES.get(source_language, source_language)

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a medical translator. Translate the patient's "
                        f"{language} text into simple, accurate English. "
                        "Keep every symptom, body part, duration and number. "
                        "Short answers like yes/no must stay short. "
                        "Return ONLY the English translation, nothing else."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Groq translation failed, falling back to Google: {e}")
        return GoogleTranslator(
            source=source_language, target="en"
        ).translate(text)


async def translate_from_english(text: str, target_language: str) -> str:
    """English -> patient's language (for questions and results shown to them)."""
    if target_language == "en" or not text:
        return text

    language = LANGUAGE_NAMES.get(target_language, target_language)

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a medical translator for rural {language} speakers. "
                        f"Translate the text into simple, everyday spoken {language}, "
                        "the way a village health worker would say it. "
                        "Avoid difficult medical jargon. "
                        "Keep numbers, phone numbers, URLs, emojis, line breaks "
                        "and place names exactly unchanged. "
                        "Return ONLY the translation, nothing else."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        # Show English rather than crash the whole triage
        print(f"Translation to {language} failed, showing English: {e}")
        return text