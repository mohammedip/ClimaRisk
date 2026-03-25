import httpx
import math
import time
import asyncio

OPEN_METEO_URL  = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ELEV = "https://api.open-meteo.com/v1/elevation"

HOURLY_VARS = [
    "precipitation",
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
]

DAILY_VARS = [
    "precipitation_sum",
    "et0_fao_evapotranspiration",
]

# ── Cache: stores results for 30 min, rounds coords to ~1km grid ─────────────
_CACHE_TTL = 1800
_cache:    dict = {}
_inflight: dict = {}


def _key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)},{round(lon, 2)}"


def _latest(series):
    vals = [v for v in (series or []) if v is not None]
    return vals[-1] if vals else None


def _sum_nonnull(series):
    vals = [v for v in (series or []) if v is not None]
    return round(sum(vals), 4) if vals else 0.0


async def _fetch_open_meteo(lat: float, lon: float, client: httpx.AsyncClient) -> dict:
    for attempt_daily in [DAILY_VARS, ["precipitation_sum"]]:
        try:
            params = {
                "latitude":      lat,
                "longitude":     lon,
                "hourly":        ",".join(HOURLY_VARS),
                "daily":         ",".join(attempt_daily),
                "timezone":      "auto",
                "forecast_days": 3,
            }
            resp = await client.get(OPEN_METEO_URL, params=params, timeout=10.0)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError:
            if attempt_daily == ["precipitation_sum"]:
                raise
            continue


async def _fetch_terrain(lat: float, lon: float, client: httpx.AsyncClient) -> dict:
    elevation = None
    try:
        resp = await client.get(
            OPEN_METEO_ELEV,
            params={"latitude": lat, "longitude": lon},
            timeout=8.0,
        )
        resp.raise_for_status()
        elev_data  = resp.json()
        elevations = elev_data.get("elevation", [])
        elevation  = elevations[0] if elevations else None
    except Exception:
        elevation = None

    elev = float(elevation or 50.0)
    elev = max(0.0, min(elev, 8000.0))

    if elev < 10:     slope = 1.0
    elif elev < 50:   slope = 2.5
    elif elev < 200:  slope = 6.0
    elif elev < 500:  slope = 14.0
    elif elev < 1500: slope = 25.0
    else:             slope = 35.0

    slope_rad     = math.radians(max(slope, 0.5))
    upstream_area = max(0.5, 200.0 / (elev + 1))
    twi_raw       = math.log(upstream_area / math.tan(slope_rad))
    twi           = round(max(0.0, min(twi_raw, 15.0)), 4)

    return {
        "elevation":      round(elev, 2),
        "slope":          round(slope, 4),
        "TWI":            twi,
        "upstream_area":  round(upstream_area, 4),
        "jrc_perm_water": 0.0,
        "landcover":      40.0,
    }


def _derive_ndvi_ndwi(
    temperature_c: float | None,
    humidity_pct:  float | None,
    precip_3d:     float,
    et0:           float | None,
) -> tuple[float, float]:
    temp = temperature_c or 25.0
    rh   = humidity_pct  or 60.0

    ndvi_raw = (
        0.25 * min(precip_3d / 30.0, 1.0)       +
        0.20 * min(rh        / 80.0, 1.0)        +
        0.25 * max(0.0, 1.0 - temp / 45.0)       +
        0.10 * min((et0 or 3.0) / 6.0, 1.0)      +
        0.30
    )
    ndvi = round(max(-0.1, min(ndvi_raw, 0.85)), 4)

    ndwi_raw = (
        0.6 * min(precip_3d / 80.0, 1.0)        -
        0.3 * min((et0 or 3.0) / 6.0, 1.0)      +
        0.1 * min(rh / 100.0, 1.0)
    ) - 0.45
    ndwi = round(max(-0.5, min(ndwi_raw, 0.6)), 4)

    return ndvi, ndwi


async def _do_fetch(lat: float, lon: float) -> dict:
    """Raw fetch + process. Only called on a true cache miss."""
    async with httpx.AsyncClient() as client:
        meteo_data, terrain = await asyncio.gather(
            _fetch_open_meteo(lat, lon, client),
            _fetch_terrain(lat, lon, client),
        )

    hourly     = meteo_data.get("hourly", {})
    daily_data = meteo_data.get("daily",  {})

    hourly_precip = hourly.get("precipitation", [])
    precip_1d     = _sum_nonnull(hourly_precip[-24:])
    precip_3d     = _sum_nonnull(hourly_precip)

    daily_precip_list = daily_data.get("precipitation_sum") or []
    daily_rain        = sum(v for v in daily_precip_list if v is not None)

    if precip_1d == 0.0 and daily_rain > 0:
        precip_1d = daily_rain
    if precip_3d == 0.0 and daily_rain > 0:
        precip_3d = daily_rain

    temperature_c  = _latest(hourly.get("temperature_2m", []))
    humidity_pct   = _latest(hourly.get("relative_humidity_2m", []))
    wind_speed_kmh = _latest(hourly.get("wind_speed_10m", []))

    et0_list = daily_data.get("et0_fao_evapotranspiration") or []
    et0      = et0_list[0] if et0_list else None

    ndvi, ndwi = _derive_ndvi_ndwi(temperature_c, humidity_pct, precip_3d, et0)

    return {
        "precip_1d":      round(precip_1d, 4),
        "precip_3d":      round(precip_3d, 4),
        "NDVI":           ndvi,
        "NDWI":           ndwi,
        "jrc_perm_water": terrain["jrc_perm_water"],
        "landcover":      terrain["landcover"],
        "elevation":      terrain["elevation"],
        "slope":          terrain["slope"],
        "upstream_area":  terrain["upstream_area"],
        "TWI":            terrain["TWI"],
        "lat":            lat,
        "lon":            lon,
        "temperature_c":  temperature_c,
        "humidity_pct":   humidity_pct,
        "wind_speed_kmh": wind_speed_kmh,
        "rainfall_mm":    round(precip_1d, 4),
        "fwi":            None,
        "_daily_rain_mm": round(daily_rain, 4),
        "_et0":           et0,
    }


async def fetch_weather(lat: float, lon: float) -> dict:
    key = _key(lat, lon)

    # 1. Cache hit — return immediately, zero API calls
    entry = _cache.get(key)
    if entry and entry["expires_at"] > time.monotonic():
        return entry["data"]

    # 2. Already fetching — wait for that result instead of making a new request
    if key in _inflight:
        return await _inflight[key]

    # 3. First caller — fetch and let everyone else wait on the same Future
    future = asyncio.get_event_loop().create_future()
    _inflight[key] = future
    try:
        result = await _do_fetch(lat, lon)
        _cache[key] = {"data": result, "expires_at": time.monotonic() + _CACHE_TTL}
        future.set_result(result)
        return result
    except Exception as exc:
        future.set_exception(exc)
        raise
    finally:
        _inflight.pop(key, None)