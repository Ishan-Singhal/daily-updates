"""Send SMS via TextBelt API."""

import requests
from config import PHONE_NUMBER, TEXTBELT_KEY


def send_sms(message):
    """Send an SMS using TextBelt. Free tier = 1 text/day with key 'textbelt'."""
    resp = requests.post(
        "https://textbelt.com/text",
        data={
            "phone": PHONE_NUMBER,
            "message": message,
            "key": TEXTBELT_KEY,
        },
        timeout=15,
    )
    result = resp.json()
    if result.get("success"):
        print(f"SMS sent successfully! Quota remaining: {result.get('quotaRemaining')}")
    else:
        print(f"SMS failed: {result.get('error', 'Unknown error')}")
    return result
