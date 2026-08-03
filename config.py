import os
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Additional email recipients for the daily brief (e.g. family members without
# iMessage), comma-separated. Always sent alongside GMAIL_ADDRESS.
EXTRA_EMAIL_RECIPIENTS = [
    addr.strip() for addr in os.getenv("EXTRA_EMAIL_RECIPIENTS", "").split(",") if addr.strip()
]

# Phone number (e.g. +15551234567) or Apple ID email to iMessage the daily brief to.
# Leave blank to send to yourself at the Mac's own Apple ID (Messages will prompt
# for a chat with no recipient set, so this should normally be your own number).
IMESSAGE_RECIPIENT = os.getenv("IMESSAGE_RECIPIENT")

# Weather location
WEATHER_CITY = "Round Rock"
WEATHER_STATE = "TX"
WEATHER_COUNTRY = "US"
WEATHER_LAT = 30.5083
WEATHER_LON = -97.6789

# Market tickers to track
MARKET_TICKERS = ["^GSPC", "^DJI", "^IXIC", "^VIX"]  # S&P500, Dow, Nasdaq, VIX
TICKER_NAMES = {"^GSPC": "S&P 500", "^DJI": "Dow", "^IXIC": "Nasdaq", "^VIX": "VIX"}
