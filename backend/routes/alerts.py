from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from core.database import get_db
from core.security import get_current_user, require_role
from models.alert import Alert
from models.zone import Zone
from schemas.alert import AlertCreate, AlertResponse

router = APIRouter()


async def get_zone_or_404(zone_id: int, db: AsyncSession) -> Zone:
    result = await db.execute(select(Zone).where(Zone.id == zone_id, Zone.is_active == True))
    zone   = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


# ── Get all active alerts ─────────────────────────────────────────────────────

@router.get("/", response_model=list[AlertResponse])
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    _=  Depends(get_current_user),
):
    """All active alerts — any logged-in user."""
    result = await db.execute(
        select(Alert)
        .where(Alert.is_active == True)
        .order_by(Alert.created_at.desc())
    )
    return result.scalars().all()


# ── Get alerts for a specific zone ───────────────────────────────────────────

@router.get("/zone/{zone_id}", response_model=list[AlertResponse])
async def get_zone_alerts(
    zone_id: int,
    db:      AsyncSession = Depends(get_db),
    _=       Depends(get_current_user),
):
    await get_zone_or_404(zone_id, db)
    result = await db.execute(
        select(Alert)
        .where(Alert.zone_id == zone_id, Alert.is_active == True)
        .order_by(Alert.created_at.desc())
    )
    return result.scalars().all()


# ── Create alert (ADMIN or auto-triggered by predictions) ────────────────────

@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(
    body: AlertCreate,
    db:   AsyncSession = Depends(get_db),
    _=    Depends(require_role("ADMIN", "RESCUE")),
):
    await get_zone_or_404(body.zone_id, db)

    alert = Alert(**body.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


# ── Resolve alert ─────────────────────────────────────────────────────────────

@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    db:       AsyncSession = Depends(get_db),
    current_user = Depends(require_role("ADMIN", "RESCUE")),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert  = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not alert.is_active:
        raise HTTPException(status_code=400, detail="Alert already resolved")

    alert.is_active   = False
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolved_by = current_user.id
    await db.commit()
    await db.refresh(alert)
    return alert


# ── Delete alert (ADMIN only) ─────────────────────────────────────────────────

@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    db:       AsyncSession = Depends(get_db),
    _=        Depends(require_role("ADMIN")),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert  = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()