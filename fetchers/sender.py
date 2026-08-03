"""Send the daily brief via iMessage (primary) or Gmail email.

Delivery is split by machine, using IMESSAGE_RECIPIENT as the signal for
which one this is:

- This Mac (IMESSAGE_RECIPIENT set): iMessage to yourself is primary; email
  to yourself only fires if iMessage genuinely fails (both retried, since a
  scheduled-wake run can race Messages.app/network coming up after sleep).
- Anywhere else, e.g. the GitHub Actions cloud run (IMESSAGE_RECIPIENT
  unset): iMessage isn't possible there at all, so that path is dedicated
  to emailing EXTRA_EMAIL_RECIPIENTS (family without iMessage) every day —
  it never emails your own address, since you already get iMessage from
  the Mac and don't want a daily duplicate.
"""

import subprocess
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, IMESSAGE_RECIPIENT, EXTRA_EMAIL_RECIPIENTS

RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 20  # long enough to survive a post-wake network/Messages race


def _retry(fn, step):
    """Run fn() up to RETRY_ATTEMPTS times, returning its result dict as soon
    as one attempt succeeds. Used for delivery calls that can hit a transient
    cold-start race right after the Mac wakes from sleep."""
    result = {"success": False, "error": "never attempted"}
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        result = fn()
        if result["success"]:
            return result
        print(f"  [{step}] attempt {attempt}/{RETRY_ATTEMPTS} failed: {result.get('error')}")
        if attempt < RETRY_ATTEMPTS:
            time.sleep(RETRY_BACKOFF_SECONDS)
    return result


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

    def _attempt():
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

    return _retry(_attempt, "send_imessage")


def _escape_applescript(text):
    """Escape a string for safe embedding inside an AppleScript double-quoted literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def send_email(message, recipients):
    """Send the daily brief as an email via Gmail SMTP to an explicit recipient list."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("Email not configured: GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing")
        return {"success": False, "error": "Not configured"}
    if not recipients:
        print("Email not sent: no recipients")
        return {"success": False, "error": "No recipients"}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = message.split("\n")[0][:80]  # First line as subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(message, "plain", "utf-8"))

    def _attempt():
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                server.sendmail(GMAIL_ADDRESS, recipients, msg.as_string())
            print(f"Email sent successfully to {', '.join(recipients)}!")
            return {"success": True}
        except Exception as e:
            print(f"Email failed: {e}")
            return {"success": False, "error": str(e)}

    return _retry(_attempt, "send_email")


def send_daily_brief(imessage_text, email_text=None):
    """Send the daily brief via the appropriate channel(s) for this machine.

    imessage_text: condensed text to send via Messages.
    email_text: full report to email; defaults to imessage_text.
    """
    email_text = email_text if email_text is not None else imessage_text

    if IMESSAGE_RECIPIENT:
        # This is the Mac: iMessage primary (already retried internally),
        # email-to-self only as a true fallback if it still fails.
        result = send_imessage(imessage_text)
        if result["success"]:
            return result
        print(f"iMessage failed after retries ({result.get('error')}), falling back to email...")
        return send_email(email_text, recipients=[GMAIL_ADDRESS] if GMAIL_ADDRESS else [])

    # No iMessage possible here (e.g. the cloud run) — dedicated to
    # email-only family recipients, never your own address.
    if not EXTRA_EMAIL_RECIPIENTS:
        print("No IMESSAGE_RECIPIENT and no EXTRA_EMAIL_RECIPIENTS configured; nothing to send.")
        return {"success": False, "error": "No delivery channel configured"}
    return send_email(email_text, recipients=EXTRA_EMAIL_RECIPIENTS)


def send_sms(message):
    """Deprecated alias kept for backward compatibility. Use send_daily_brief instead."""
    return send_daily_brief(message)
