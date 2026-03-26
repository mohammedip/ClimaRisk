from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class FloodPrediction(Base):
    __tablename__ = "flood_predictions"

    id          = Column(Integer, primary_key=True, index=True)
    zone_id     = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    probability = Column(Float,   nullable=False)          
    risk_level  = Column(String(10), nullable=False)       


    rainfall_mm      = Column(Float, nullable=True)
    river_level_m    = Column(Float, nullable=True)
    soil_moisture    = Column(Float, nullable=True)
    drainage_score   = Column(Float, nullable=True)
    elevation_m      = Column(Float, nullable=True)

    model_version = Column(String(50), default="1.0.0")
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class FirePrediction(Base):
    __tablename__ = "fire_predictions"

    id          = Column(Integer, primary_key=True, index=True)
    zone_id     = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    probability = Column(Float,   nullable=False)
    risk_level  = Column(String(10), nullable=False)


    temperature_c  = Column(Float, nullable=True)
    humidity_pct   = Column(Float, nullable=True)
    wind_speed_kmh = Column(Float, nullable=True)
    ndvi           = Column(Float, nullable=True) 
    fwi            = Column(Float, nullable=True)   

    model_version = Column(String(50), default="1.0.0")
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), index=True)