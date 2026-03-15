from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_current_user
from models.zone import Zone
from models.alert import Alert
from models.prediction import FloodPrediction, FirePrediction
from schemas.prediction import (
    FloodPredictionRequest, FloodPredictionResponse,
    FirePredictionRequest,  FirePredictionResponse,
    probability_to_risk_level,
)
from services.predict import flood_probability, fire_probability

router = APIRouter()


async def get_zone_or_404(zone_id: int, db: AsyncSession) -> Zone:
    result = await db.execute(select(Zone).where(Zone.id == zone_id, Zone.is_active == True))
    zone   = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


async def auto_alert(db: AsyncSession, zone: Zone, hazard: str, risk_level: str, probability: float):
    if risk_level not in ("HIGH", "CRITICAL"):
        return
    alert = Alert(
        zone_id     = zone.id,
        hazard_type = hazard,
        risk_level  = risk_level,
        title       = f"{risk_level} {hazard} Risk — {zone.name}",
        message     = (
            f"Automated alert: {hazard.lower()} probability reached "
            f"{round(probability * 100)}% in {zone.name} ({zone.code}). "
            f"Risk level: {risk_level}. Immediate attention required."
        ),
    )
    db.add(alert)


# ── Flood ─────────────────────────────────────────────────────────────────────

@router.post("/flood", response_model=FloodPredictionResponse, status_code=201)
async def predict_flood(
    body: FloodPredictionRequest,
    db:   AsyncSession = Depends(get_db),
    _=    Depends(get_current_user),
):
    zone = await get_zone_or_404(body.zone_id, db)

    probability = flood_probability(
        rainfall_mm   = body.rainfall_mm,
        precip_3d     = None,
        elevation_m   = zone.area_km2,
        ndvi          = None,
        ndwi          = None,
        soil_moisture = body.soil_moisture,
        river_level_m = body.river_level_m,
        slope         = None,
    )
    risk_level = probability_to_risk_level(probability)

    prediction = FloodPrediction(
        zone_id        = body.zone_id,
        probability    = probability,
        risk_level     = risk_level,
        rainfall_mm    = body.rainfall_mm,
        river_level_m  = body.river_level_m,
        soil_moisture  = body.soil_moisture,
        drainage_score = body.drainage_score,
        elevation_m    = body.elevation_m,
        model_version  = "xgboost-1.0.0",
    )
    db.add(prediction)
    await auto_alert(db, zone, "FLOOD", risk_level, probability)
    await db.commit()
    await db.refresh(prediction)
    return prediction


@router.get("/flood/{zone_id}", response_model=list[FloodPredictionResponse])
async def get_flood_predictions(
    zone_id: int,
    db:      AsyncSession = Depends(get_db),
    _=       Depends(get_current_user),
):
    await get_zone_or_404(zone_id, db)
    result = await db.execute(
        select(FloodPrediction)
        .where(FloodPrediction.zone_id == zone_id)
        .order_by(FloodPrediction.created_at.desc())
        .limit(10)
    )
    return result.scalars().all()


# ── Fire ──────────────────────────────────────────────────────────────────────

@router.post("/fire", response_model=FirePredictionResponse, status_code=201)
async def predict_fire(
    body: FirePredictionRequest,
    db:   AsyncSession = Depends(get_db),
    _=    Depends(get_current_user),
):
    zone = await get_zone_or_404(body.zone_id, db)

    probability = fire_probability(
        temperature_c  = body.temperature_c,
        humidity_pct   = body.humidity_pct,
        wind_speed_kmh = body.wind_speed_kmh,
        rainfall_mm    = None,
        fwi            = body.fwi,
    )
    risk_level = probability_to_risk_level(probability)

    prediction = FirePrediction(
        zone_id        = body.zone_id,
        probability    = probability,
        risk_level     = risk_level,
        temperature_c  = body.temperature_c,
        humidity_pct   = body.humidity_pct,
        wind_speed_kmh = body.wind_speed_kmh,
        ndvi           = body.ndvi,
        fwi            = body.fwi,
        model_version  = "fwi-1.0.0",
    )
    db.add(prediction)
    await auto_alert(db, zone, "FIRE", risk_level, probability)
    await db.commit()
    await db.refresh(prediction)
    return prediction


@router.get("/fire/{zone_id}", response_model=list[FirePredictionResponse])
async def get_fire_predictions(
    zone_id: int,
    db:      AsyncSession = Depends(get_db),
    _=       Depends(get_current_user),
):
    await get_zone_or_404(zone_id, db)
    result = await db.execute(
        select(FirePrediction)
        .where(FirePrediction.zone_id == zone_id)
        .order_by(FirePrediction.created_at.desc())
        .limit(10)
    )
    return result.scalars().all()


# ── Latest predictions for all zones (for map coloring) ───────────────────────

@router.get("/latest", response_model=list[dict])
async def get_latest_predictions(
    db: AsyncSession = Depends(get_db),
    _=  Depends(get_current_user),
):
    """
    Returns the latest flood + fire prediction for every active zone.
    Used by the frontend to color map markers.
    """
    from models.zone import Zone as ZoneModel
    from sqlalchemy import func

    # Get all active zones
    zones_result = await db.execute(select(ZoneModel).where(ZoneModel.is_active == True))
    zones = zones_result.scalars().all()

    output = []
    for zone in zones:
        # Latest flood prediction
        flood_result = await db.execute(
            select(FloodPrediction)
            .where(FloodPrediction.zone_id == zone.id)
            .order_by(FloodPrediction.created_at.desc())
            .limit(1)
        )
        flood = flood_result.scalar_one_or_none()

        # Latest fire prediction
        fire_result = await db.execute(
            select(FirePrediction)
            .where(FirePrediction.zone_id == zone.id)
            .order_by(FirePrediction.created_at.desc())
            .limit(1)
        )
        fire = fire_result.scalar_one_or_none()

        # Determine overall risk (worst of flood/fire)
        risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        flood_level = flood.risk_level if flood else "LOW"
        fire_level  = fire.risk_level  if fire  else "LOW"
        overall     = flood_level if risk_order.get(flood_level, 0) >= risk_order.get(fire_level, 0) else fire_level

        output.append({
            "zone_id":        zone.id,
            "zone_name":      zone.name,
            "zone_code":      zone.code,
            "latitude":       zone.latitude,
            "longitude":      zone.longitude,
            "flood_risk":     flood_level,
            "flood_prob":     round(flood.probability, 3) if flood else None,
            "fire_risk":      fire_level,
            "fire_prob":      round(fire.probability, 3) if fire else None,
            "overall_risk":   overall,
            "last_updated":   flood.created_at.isoformat() if flood else None,
        })

    return output