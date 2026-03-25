from pydantic import BaseModel, field_validator
from datetime import datetime


# ── Shared ────────────────────────────────────────────────────────────────────

def probability_to_risk_level(p: float) -> str:

    if p >= 0.90: return "CRITICAL"
    if p >= 0.70: return "HIGH"
    if p >= 0.30: return "MEDIUM"
    return "LOW"


# ── Flood ─────────────────────────────────────────────────────────────────────

class FloodPredictionRequest(BaseModel):
    zone_id:           int
    rainfall_mm:       float | None = None
    river_level_m:     float | None = None
    soil_moisture_pct: float | None = None   # percentage 0-100
    elevation_m:       float | None = None   # auto-fetched from zone if None

    @field_validator("zone_id")
    @classmethod
    def zone_id_positive(cls, v):
        if v <= 0:
            raise ValueError("zone_id must be a positive integer")
        return v


class FloodPredictionResponse(BaseModel):
    id:                int | None      = None
    zone_id:           int
    probability:       float
    risk_level:        str
    rainfall_mm:       float | None    = None
    river_level_m:     float | None    = None
    soil_moisture_pct: float | None    = None
    elevation_m:       float | None    = None
    model_version:     str
    created_at:        datetime | None = None

    model_config = {"from_attributes": True}


# ── Fire ──────────────────────────────────────────────────────────────────────

class FirePredictionRequest(BaseModel):
    zone_id:        int
    temperature_c:  float | None = None
    humidity_pct:   float | None = None
    wind_speed_kmh: float | None = None
    fwi:            float | None = None

    @field_validator("zone_id")
    @classmethod
    def zone_id_positive(cls, v):
        if v <= 0:
            raise ValueError("zone_id must be a positive integer")
        return v


class FirePredictionResponse(BaseModel):
    id:             int | None      = None
    zone_id:        int
    probability:    float
    risk_level:     str
    temperature_c:  float | None    = None
    humidity_pct:   float | None    = None
    wind_speed_kmh: float | None    = None
    fwi:            float | None    = None
    model_version:  str
    created_at:     datetime | None = None

    model_config = {"from_attributes": True}