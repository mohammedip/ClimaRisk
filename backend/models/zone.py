from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from core.database import Base


class Zone(Base):
    __tablename__ = "zones"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(255), nullable=False)
    code        = Column(String(50),  nullable=False, unique=True)
    region      = Column(String(200), nullable=True)
    country     = Column(String(100), default="France")
    latitude    = Column(Float, nullable=False)   
    longitude   = Column(Float, nullable=False)   
    area_km2    = Column(Float, nullable=True)
    population  = Column(Integer, nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())