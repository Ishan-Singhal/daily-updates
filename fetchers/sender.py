"""Send the daily brief via iMessage (primary), falling back to Gmail email."""

import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, IMESSAGE_RECIPIENT, EXTRA_EMAIL_RECIPIENTS


def send_imessage(message, recipient=None):
    """Send a message via the Messages app on this Mac using AppleScript.

    Only works when run locally on macOS with Messages.app signed in.
    """
    recipient = recipient or IMESSAGE_RECIPIENT
    if not recipient:
        return {"success": False, "error": "IMESSAGE_RECIPIENT not configured"}

    script = f'''
    tell application "Messages"
        set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy "{recipient}" of targetService
        send "{_escape_applescript(message)}" to targetBuddy
    end tell
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip() or "osascript failed"}
        print("iMessage sent successfully!")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _escape_applescript(text):
    """Escape a string for safe embedding inside an AppleScript double-quoted literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def send_email(message):
    """Send the daily brief as an email via Gmail SMTP."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("Email not configured: GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing")
        return {"success": False, "error": "Not configured"}

    recipients = [GMAIL_ADDRESS] + EXTRA_EMAIL_RECIPIENTS

    msg = MIMEMultipart("alternative")
    msg["Subject"] = message.split("\n")[0][:80]  # First line as subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = ", ".join(recipients)

    # Plain text version
    msg.attach(MIMEText(message, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, recipients, msg.as_string())
        print(f"Email sent successfully to {', '.join(recipients)}!")
        return {"success": True}
    except Exception as e:
        print(f"Email failed: {e}")
        return {"success": False, "error": str(e)}


def send_daily_brief(imessage_text, email_text=None):
    """Send the daily brief via iMessage; fall back to email if that fails.

    imessage_text: condensed text to send via Messages (primary channel).
    email_text: full report to email if iMessage isn't available; defaults to imessage_text.
    """
    result = send_imessage(imessage_text)
    if result["success"]:
        return result

    print(f"iMessage failed ({result.get('error')}), falling back to email...")
    return send_email(email_text if email_text is not None else imessage_text)


def send_sms(message):
    """Deprecated alias kept for backward compatibility. Use send_daily_brief instead."""
    return send_daily_brief(message)
