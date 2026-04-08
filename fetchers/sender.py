"""Send daily brief via Gmail SMTP."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


def send_sms(message):
    """Send the daily brief via Gmail. Named send_sms for backward compatibility."""
    return send_email(message)


def send_email(message):
    """Send the daily brief as an email via Gmail SMTP."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("Email not configured: GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing")
        return {"success": False, "error": "Not configured"}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = message.split("\n")[0][:80]  # First line as subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS

    # Plain text version
    msg.attach(MIMEText(message, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print("Email sent successfully!")
        return {"success": True}
    except Exception as e:
        print(f"Email failed: {e}")
        return {"success": False, "error": str(e)}
