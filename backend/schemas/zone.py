from pydantic import BaseModel, field_validator
from datetime import datetime

class ZoneCreate(BaseModel):
    name:       str
    code:       str
    region:     str = ""
    country:    str = "France"
    latitude:   float
    longitude:  float
    area_km2:   float | None = None
    population: int   | None = None

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @field_validator("code")
    @classmethod
    def code_no_spaces(cls, v):
        if " " in v:
            raise ValueError("Code cannot contain spaces")
        return v.upper()



class ZoneResponse(BaseModel):
    id:         int
    name:       str
    code:       str
    region:     str | None
    country:    str
    latitude:   float
    longitude:  float
    area_km2:   float   | None
    population: int     | None
    is_active:  bool
    created_at: datetime | None

    model_config = {"from_attributes": True}