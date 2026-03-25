from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_current_user
from models.zone import Zone
from models.alert import Alert
from models.prediction import FloodPrediction, FirePrediction
from schemas.prediction import (
    FloodPredictionResponse,
    FirePredictionResponse,
    probability_to_risk_level,
)
from schemas.prediction import FloodSimulationRequest 
from services.predict import flood_probability, fire_probability
from services.weather import fetch_weather

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

async def get_zone_or_404(zone_id: int, db: AsyncSession) -> Zone:
    result = await db.execute(
        select(Zone).where(Zone.id == zone_id, Zone.is_active == True)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


async def auto_alert(db: AsyncSession, zone: Zone, hazard: str, risk_level: str, probability: float):
    if risk_level not in ("HIGH", "CRITICAL"):
        return
    db.add(Alert(
        zone_id     = zone.id,
        hazard_type = hazard,
        risk_level  = risk_level,
        title       = f"{risk_level} {hazard} Risk — {zone.name}",
        message     = (
            f"Automated alert: {hazard.lower()} probability reached "
            f"{round(probability * 100)}% in {zone.name} ({zone.code}). "
            f"Risk level: {risk_level}. Immediate attention required."
        ),
    ))


# ── Flood Prediction (AUTO WEATHER + ML) ──────────────────────────────────────



@router.post("/flood/{zone_id}/simulate", response_model=FloodPredictionResponse, status_code=201)
async def simulate_flood(
    zone_id: int,
    body: FloodSimulationRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    zone = await get_zone_or_404(zone_id, db)

    try:
        probability = flood_probability(
            precip_1d      = body.precip_1d,
            precip_3d      = body.precip_3d,
            ndvi           = body.NDVI,
            ndwi           = body.NDWI,
            jrc_perm_water = body.jrc_perm_water,
            landcover      = body.landcover,
            elevation      = body.elevation,
            slope          = body.slope,
            upstream_area  = body.upstream_area,
            twi            = body.TWI,
            lat            = zone.latitude,
            lon            = zone.longitude,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flood model error: {e}")

    risk_level = probability_to_risk_level(probability)

    # Simulation is always dry-run — never saved to DB
    return FloodPredictionResponse(
        id=None,
        zone_id=zone.id,
        probability=probability,
        risk_level=risk_level,
        model_version="xgboost-sim",
        created_at=None,
    )


@router.post("/flood/{zone_id}", response_model=FloodPredictionResponse, status_code=201)
async def predict_flood(
    zone_id: int,
    dry_run: bool = Query(False, description="Return prediction without saving to DB."),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    zone = await get_zone_or_404(zone_id, db)

    try:
        weather = await fetch_weather(zone.latitude, zone.longitude)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch failed: {e}")

    try:
        probability = flood_probability(
            precip_1d      = weather.get("precip_1d"),
            precip_3d      = weather.get("precip_3d"),
            ndvi           = weather.get("NDVI"),
            ndwi           = weather.get("NDWI"),
            jrc_perm_water = weather.get("jrc_perm_water"),
            landcover      = weather.get("landcover"),
            elevation      = weather.get("elevation"),
            slope          = weather.get("slope"),
            upstream_area  = weather.get("upstream_area"),
            twi            = weather.get("TWI"),
            lat            = weather.get("lat"),   
            lon            = weather.get("lon"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flood model error: {e}")

    risk_level = probability_to_risk_level(probability)

    if dry_run:
        return FloodPredictionResponse(
            id=None,
            zone_id=zone.id,
            probability=probability,
            risk_level=risk_level,
            model_version="xgboost-ml",
            created_at=None,
        )

    prediction = FloodPrediction(
        zone_id=zone.id,
        probability=probability,
        risk_level=risk_level,
        model_version="xgboost-ml",
    )

    db.add(prediction)
    await auto_alert(db, zone, "FLOOD", risk_level, probability)
    await db.commit()
    await db.refresh(prediction)

    return prediction


# ── Fire Prediction (AUTO WEATHER) ────────────────────────────────────────────

@router.post("/fire/{zone_id}", response_model=FirePredictionResponse, status_code=201)
async def predict_fire(
    zone_id: int,
    dry_run: bool = Query(False, description="Return prediction without saving to DB."),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    zone = await get_zone_or_404(zone_id, db)

    try:
        weather = await fetch_weather(zone.latitude, zone.longitude)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch failed: {e}")

    try:
        probability = fire_probability(
            temperature_c  = weather.get("temperature_c"),
            humidity_pct   = weather.get("humidity_pct"),
            wind_speed_kmh = weather.get("wind_speed_kmh"),
            rainfall_mm    = weather.get("rainfall_mm"),
            fwi            = weather.get("fwi"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fire model error: {e}")

    risk_level = probability_to_risk_level(probability)

    if dry_run:
        return FirePredictionResponse(
            id=None,
            zone_id=zone.id,
            probability=probability,
            risk_level=risk_level,
            model_version="fwi-ml",
            created_at=None,
        )

    prediction = FirePrediction(
        zone_id=zone.id,
        probability=probability,
        risk_level=risk_level,
        model_version="fwi-ml",
    )

    db.add(prediction)
    await auto_alert(db, zone, "FIRE", risk_level, probability)
    await db.commit()
    await db.refresh(prediction)

    return prediction


# ── Latest Predictions (for map) ──────────────────────────────────────────────

@router.get("/latest", response_model=list[dict])
async def get_latest_predictions(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from models.zone import Zone as ZoneModel

    zones_result = await db.execute(
        select(ZoneModel).where(ZoneModel.is_active == True)
    )
    zones = zones_result.scalars().all()

    risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    output = []

    for zone in zones:
        flood = (await db.execute(
            select(FloodPrediction)
            .where(FloodPrediction.zone_id == zone.id)
            .order_by(FloodPrediction.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()

        fire = (await db.execute(
            select(FirePrediction)
            .where(FirePrediction.zone_id == zone.id)
            .order_by(FirePrediction.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()

        flood_level = flood.risk_level if flood else "LOW"
        fire_level  = fire.risk_level  if fire  else "LOW"

        overall = flood_level if risk_order.get(flood_level, 0) >= risk_order.get(fire_level, 0) else fire_level

        output.append({
            "zone_id": zone.id,
            "zone_name": zone.name,
            "zone_code": zone.code,
            "latitude": zone.latitude,
            "longitude": zone.longitude,
            "flood_risk": flood_level,
            "flood_prob": round(flood.probability, 3) if flood else None,
            "fire_risk": fire_level,
            "fire_prob": round(fire.probability, 3) if fire else None,
            "overall_risk": overall,
            "last_updated": flood.created_at.isoformat() if flood else None,
        })

    return output