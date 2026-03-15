from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_current_user, require_role
from models.zone import Zone
from schemas.zone import ZoneCreate, ZoneResponse

router = APIRouter()


@router.get("/", response_model=list[ZoneResponse])
async def get_zones(db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Zone).where(Zone.is_active == True))
    return result.scalars().all()


@router.get("/{zone_id}", response_model=ZoneResponse)
async def get_zone(zone_id: int, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone   = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.post("/", response_model=ZoneResponse, status_code=201)
async def create_zone(
    body: ZoneCreate,
    db:   AsyncSession = Depends(get_db),
    _=    Depends(require_role("ADMIN")),   
):

    result = await db.execute(select(Zone).where(Zone.code == body.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Zone code '{body.code}' already exists")

    zone = Zone(**body.model_dump())
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


@router.delete("/{zone_id}", status_code=204)
async def delete_zone(
    zone_id: int,
    db:      AsyncSession = Depends(get_db),
    _=       Depends(require_role("ADMIN")),
):
    """Soft delete a zone — ADMIN only."""
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone   = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    zone.is_active = False
    await db.commit()