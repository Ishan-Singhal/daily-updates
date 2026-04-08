import os
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
PUTER_TOKEN = os.getenv("PUTER_TOKEN")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Weather location
WEATHER_CITY = "Round Rock"
WEATHER_STATE = "TX"
WEATHER_COUNTRY = "US"
WEATHER_LAT = 30.5083
WEATHER_LON = -97.6789

# Market tickers to track
MARKET_TICKERS = ["^GSPC", "^DJI", "^IXIC", "^VIX"]  # S&P500, Dow, Nasdaq, VIX
TICKER_NAMES = {"^GSPC": "S&P 500", "^DJI": "Dow", "^IXIC": "Nasdaq", "^VIX": "VIX"}
