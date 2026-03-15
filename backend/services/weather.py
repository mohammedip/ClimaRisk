"""
Fetches real-time weather data from Open-Meteo (free, no API key).
Returns a dict of all variables needed for flood + fire predictions.
"""
import math
import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_VARS = [
    "precipitation",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm",
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
]

DAILY_VARS = [
    "precipitation_sum",
    "river_discharge",
]


async def fetch_weather(lat: float, lon: float) -> dict:
    """
    Fetches current weather for a lat/lon.
    Returns a flat dict ready to pass into prediction functions.
    """
    # Try with river_discharge first, fall back without it
    for daily in [DAILY_VARS, ["precipitation_sum"]]:
        try:
            params = {
                "latitude":      lat,
                "longitude":     lon,
                "hourly":        ",".join(HOURLY_VARS),
                "daily":         ",".join(daily),
                "timezone":      "auto",
                "forecast_days": 1,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(OPEN_METEO_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                break  # success

        except httpx.HTTPStatusError:
            if daily == ["precipitation_sum"]:
                raise  # both attempts failed
            continue  # try without river_discharge

    hourly = data.get("hourly", {})
    daily_data = data.get("daily", {})

    def latest(series: list):
        vals = [v for v in (series or []) if v is not None]
        return vals[-1] if vals else None

    rainfall_mm    = latest(hourly.get("precipitation", []))
    soil_moisture  = latest(hourly.get("soil_moisture_0_to_1cm", []))
    temperature_c  = latest(hourly.get("temperature_2m", []))
    humidity_pct   = latest(hourly.get("relative_humidity_2m", []))
    wind_speed_kmh = latest(hourly.get("wind_speed_10m", []))
    daily_rain     = (daily_data.get("precipitation_sum") or [None])[0]
    river_discharge = (daily_data.get("river_discharge") or [None])[0]

    # Derive river level from discharge
    river_level_m = None
    if river_discharge is not None:
        river_level_m = round(min(math.log10(max(river_discharge, 0.1) + 1) * 2.5, 10.0), 2)

    return {
        "rainfall_mm":    rainfall_mm or daily_rain,
        "river_level_m":  river_level_m,
        "soil_moisture":  soil_moisture,
        "drainage_score": None,
        "elevation_m":    None,
        "temperature_c":  temperature_c,
        "humidity_pct":   humidity_pct,
        "wind_speed_kmh": wind_speed_kmh,
        "ndvi":           None,
        "fwi":            None,
        "_river_discharge_m3s": river_discharge,
        "_daily_rainfall_mm":   daily_rain,
    }