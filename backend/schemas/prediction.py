from pydantic import BaseModel, field_validator
from datetime import datetime



def probability_to_risk_level(p: float) -> str:

    if p >= 0.90: return "CRITICAL"
    if p >= 0.70: return "HIGH"
    if p >= 0.30: return "MEDIUM"
    return "LOW"



class FloodPredictionRequest(BaseModel):
    zone_id:           int
    rainfall_mm:       float | None = None
    river_level_m:     float | None = None
    soil_moisture_pct: float | None = None   
    elevation_m:       float | None = None  

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

class FloodSimulationRequest(BaseModel):
    precip_1d:      float = 25.0
    precip_3d:      float = 60.0
    elevation:      float = 50.0
    TWI:            float = 4.0
    slope:          float = 6.0
    upstream_area:  float = 1.0
    NDVI:           float = 0.5
    NDWI:           float = -0.2
    jrc_perm_water: float = 0.0
    landcover:      float = 40.0



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