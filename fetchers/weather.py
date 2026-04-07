"""Fetch weather data from OpenWeatherMap API."""

import requests
from config import OPENWEATHER_API_KEY, WEATHER_CITY, WEATHER_LAT, WEATHER_LON


def format_weather_section():
    """Return formatted weather section for Round Rock, TX."""
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": WEATHER_LAT,
            "lon": WEATHER_LON,
            "appid": OPENWEATHER_API_KEY,
            "units": "imperial",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        high = data["main"]["temp_max"]
        low = data["main"]["temp_min"]
        humidity = data["main"]["humidity"]
        desc = data["weather"][0]["description"].capitalize()

        lines = [
            f"\u2600\ufe0f WEATHER - {WEATHER_CITY}",
            f"  {desc}, {temp:.0f}F (feels {feels:.0f}F)",
            f"  High {high:.0f}F / Low {low:.0f}F | Humidity {humidity}%",
        ]

        # Check for rain/snow alerts
        if "rain" in data:
            lines.append(f"  Rain: {data['rain'].get('1h', 0)}mm/hr")
        if "snow" in data:
            lines.append(f"  Snow: {data['snow'].get('1h', 0)}mm/hr")

        return "\n".join(lines)

    except Exception as e:
        return f"\u2600\ufe0f WEATHER - {WEATHER_CITY}\n  Unable to fetch: {e}"
