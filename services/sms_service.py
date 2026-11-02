# services/sms_service.py
# Twilio SMS integration
# Production: requires Twilio account + DLT registration for India
# Demo: logs SMS content to console and database

from datetime import datetime

def send_followup_sms(
    phone_number: str,
    patient_name: str,
    risk_level: str,
    suspected_disease: str,
    facility_message: str
) -> dict:
    """
    Sends follow-up SMS to patient after triage.
    Currently in demo mode — logs instead of sending.
    Production ready: swap send_demo_sms with send_twilio_sms
    """

    message = build_sms_message(
        patient_name=patient_name,
        risk_level=risk_level,
        suspected_disease=suspected_disease,
        facility_message=facility_message
    )

    # Demo mode — print to console
    result = send_demo_sms(phone_number, message)

    return result


def build_sms_message(
    patient_name: str,
    risk_level: str,
    suspected_disease: str,
    facility_message: str
) -> str:
    """Builds the SMS text in simple English."""

    emoji_map = {
        "RED": "🔴 EMERGENCY",
        "YELLOW": "🟡 ATTENTION",
        "GREEN": "🟢 OKAY"
    }

    urgency = emoji_map.get(risk_level, "🟡 ATTENTION")

    message = f"""SwasthAI Health Alert
---
{urgency}
Patient: {patient_name}
Assessment: Possible {suspected_disease}
Time: {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC

{facility_message}

---
Reply STOP to unsubscribe.
SwasthAI — Bridging healthcare gaps in India.
National Helpline: 104
"""
    return message


def send_demo_sms(phone_number: str, message: str) -> dict:
    """
    Demo mode — logs SMS instead of sending.
    Replace with send_twilio_sms() for production.
    """
    print("\n" + "="*50)
    print(f"SMS TO: {phone_number}")
    print("="*50)
    print(message)
    print("="*50 + "\n")

    return {
        "status": "demo_sent",
        "to": phone_number,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }


def send_twilio_sms(phone_number: str, message: str) -> dict:
    """
    Production Twilio SMS sender.
    Uncomment when Twilio credentials are configured.
    """
    # from twilio.rest import Client
    # from core.config import settings
    #
    # client = Client(
    #     settings.twilio_account_sid,
    #     settings.twilio_auth_token
    # )
    # message = client.messages.create(
    #     body=message,
    #     from_=settings.twilio_phone_number,
    #     to=phone_number
    # )
    # return {"status": "sent", "sid": message.sid}
    pass
