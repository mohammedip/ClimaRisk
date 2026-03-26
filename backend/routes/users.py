from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from core.database import get_db
from core.security import get_current_user, require_role
from models.user import User

router = APIRouter()



class UserResponse(BaseModel):
    id:         int
    username:   str
    email:      str
    role:       str
    team_name:  Optional[str] = None
    is_active:  bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserUpdateRole(BaseModel):
    role: str  # PUBLIC | RESCUE | ADMIN

    def validate_role(self):
        if self.role not in ("PUBLIC", "RESCUE", "ADMIN"):
            raise ValueError("role must be PUBLIC, RESCUE or ADMIN")
        return self


class UserUpdateTeam(BaseModel):
    team_name: Optional[str] = None



@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _=  Depends(require_role("ADMIN")),
):

    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):

    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db:      AsyncSession = Depends(get_db),
    _=       Depends(require_role("ADMIN")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_role(
    user_id: int,
    body:    UserUpdateRole,
    db:      AsyncSession = Depends(get_db),
    current_user=Depends(require_role("ADMIN")),
):

    if body.role not in ("PUBLIC", "RESCUE", "ADMIN"):
        raise HTTPException(status_code=400, detail="role must be PUBLIC, RESCUE or ADMIN")

    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    user.role = body.role
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    db:      AsyncSession = Depends(get_db),
    current_user=Depends(require_role("ADMIN")),
):

    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    db:      AsyncSession = Depends(get_db),
    _=       Depends(require_role("ADMIN")),
):

    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db:      AsyncSession = Depends(get_db),
    current_user=Depends(require_role("ADMIN")),
):

    result = await db.execute(select(User).where(User.id == user_id))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    await db.delete(user)
    await db.commit()