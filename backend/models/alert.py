from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id          = Column(Integer, primary_key=True, index=True)
    zone_id     = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    hazard_type = Column(String(10), nullable=False)   # FLOOD / FIRE
    risk_level  = Column(String(10), nullable=False)   # MEDIUM / HIGH / CRITICAL
    title       = Column(String(255), nullable=False)
    message     = Column(Text, nullable=False)
    is_active   = Column(Boolean, default=True, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)