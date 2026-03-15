"""
APScheduler — runs every 30 minutes for every active zone:
  1. Fetch real weather from Open-Meteo
  2. Run flood prediction (XGBoost model)
  3. Run fire prediction (FWI formula)
  4. Auto-create alerts if HIGH / CRITICAL
"""
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import SessionLocal
from models.zone import Zone
from models.alert import Alert
from models.prediction import FloodPrediction, FirePrediction
from schemas.prediction import probability_to_risk_level
from services.weather import fetch_weather
from services.predict import flood_probability, fire_probability

logger    = logging.getLogger("climarisk.scheduler")
scheduler = AsyncIOScheduler()


async def get_active_zones():
    """Load all active zones and return as plain dicts to avoid session issues."""
    async with SessionLocal() as db:
        result = await db.execute(select(Zone).where(Zone.is_active == True))
        zones  = result.scalars().all()
        # Convert to dicts immediately so we don't need the session later
        return [
            {
                "id":        z.id,
                "name":      z.name,
                "code":      z.code,
                "latitude":  z.latitude,
                "longitude": z.longitude,
                "area_km2":  z.area_km2,
            }
            for z in zones
        ]


async def process_zone(zone: dict):
    """Fetch weather, run predictions, save to DB — one session per zone."""
    async with SessionLocal() as db:
        try:
            weather = await fetch_weather(zone["latitude"], zone["longitude"])

            # ── Flood ──────────────────────────────────────────────────────
            flood_prob  = flood_probability(
                rainfall_mm   = weather.get("rainfall_mm"),
                precip_3d     = weather.get("_daily_rainfall_mm"),
                elevation_m   = zone.get("area_km2"),
                ndvi          = weather.get("ndvi"),
                ndwi          = None,
                soil_moisture = weather.get("soil_moisture"),
                river_level_m = weather.get("river_level_m"),
                slope         = None,
            )
            flood_level = probability_to_risk_level(flood_prob)

            db.add(FloodPrediction(
                zone_id       = zone["id"],
                probability   = flood_prob,
                risk_level    = flood_level,
                rainfall_mm   = weather.get("rainfall_mm"),
                river_level_m = weather.get("river_level_m"),
                soil_moisture = weather.get("soil_moisture"),
                model_version = "xgboost-1.0.0-auto",
            ))

            if flood_level in ("HIGH", "CRITICAL"):
                db.add(Alert(
                    zone_id     = zone["id"],
                    hazard_type = "FLOOD",
                    risk_level  = flood_level,
                    title       = f"{flood_level} Flood Risk — {zone['name']}",
                    message     = (
                        f"Auto (30min): flood probability {round(flood_prob*100)}% "
                        f"in {zone['name']}. Rainfall: {weather.get('rainfall_mm')} mm, "
                        f"River: {weather.get('river_level_m')} m."
                    ),
                ))

            # ── Fire ───────────────────────────────────────────────────────
            fire_prob  = fire_probability(
                temperature_c  = weather.get("temperature_c"),
                humidity_pct   = weather.get("humidity_pct"),
                wind_speed_kmh = weather.get("wind_speed_kmh"),
                rainfall_mm    = weather.get("rainfall_mm"),
                fwi            = weather.get("fwi"),
            )
            fire_level = probability_to_risk_level(fire_prob)

            db.add(FirePrediction(
                zone_id        = zone["id"],
                probability    = fire_prob,
                risk_level     = fire_level,
                temperature_c  = weather.get("temperature_c"),
                humidity_pct   = weather.get("humidity_pct"),
                wind_speed_kmh = weather.get("wind_speed_kmh"),
                fwi            = weather.get("fwi"),
                model_version  = "fwi-1.0.0-auto",
            ))

            if fire_level in ("HIGH", "CRITICAL"):
                db.add(Alert(
                    zone_id     = zone["id"],
                    hazard_type = "FIRE",
                    risk_level  = fire_level,
                    title       = f"{fire_level} Fire Risk — {zone['name']}",
                    message     = (
                        f"Auto (30min): fire probability {round(fire_prob*100)}% "
                        f"in {zone['name']}. Temp: {weather.get('temperature_c')}°C, "
                        f"Humidity: {weather.get('humidity_pct')}%, "
                        f"FWI: {weather.get('fwi')}."
                    ),
                ))

            await db.commit()
            logger.info(f"  ✅ {zone['name']}: flood={flood_level} ({flood_prob:.2f}), fire={fire_level} ({fire_prob:.2f})")

        except Exception as e:
            logger.error(f"  ❌ {zone['name']}: {e}")
            await db.rollback()


async def run_predictions_for_all_zones():
    logger.info("⏱  Prediction job started")

    zones = await get_active_zones()
    logger.info(f"   Processing {len(zones)} zones...")

    for zone in zones:
        await process_zone(zone)

    logger.info("⏱  Prediction job complete")


def start_scheduler():
    job = scheduler.add_job(
        run_predictions_for_all_zones,
        trigger="interval",
        minutes=30,
        id="predictions_scheduler",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
    logger.info("✅ Scheduler started — predictions every 30 minutes")
    logger.info("⏰ First run: NOW (on startup)")
    logger.info(f"⏰ Next run: {job.next_run_time.strftime('%H:%M:%S UTC')}")