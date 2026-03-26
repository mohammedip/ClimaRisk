from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_current_user
from models.zone import Zone
from services.weather import fetch_weather

router = APIRouter()


@router.get("/{zone_id}")
async def get_zone_weather(
    zone_id: int,
    db:      AsyncSession = Depends(get_db),
    _=       Depends(get_current_user),
):

    result = await db.execute(select(Zone).where(Zone.id == zone_id, Zone.is_active == True))
    zone   = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    weather = await fetch_weather(zone.latitude, zone.longitude)
    return {
        "zone_id":   zone.id,
        "zone_name": zone.name,
        "latitude":  zone.latitude,
        "longitude": zone.longitude,
        "weather":   weather,
    }