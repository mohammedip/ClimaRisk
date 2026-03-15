from pydantic import BaseModel, field_validator
from datetime import datetime


class AlertCreate(BaseModel):
    zone_id:     int
    hazard_type: str
    risk_level:  str
    title:       str
    message:     str

    @field_validator("hazard_type")
    @classmethod
    def validate_hazard(cls, v):
        if v not in ("FLOOD", "FIRE"):
            raise ValueError("hazard_type must be FLOOD or FIRE")
        return v

    @field_validator("risk_level")
    @classmethod
    def validate_risk(cls, v):
        if v not in ("MEDIUM", "HIGH", "CRITICAL"):
            raise ValueError("risk_level must be MEDIUM, HIGH, or CRITICAL")
        return v


class AlertResponse(BaseModel):
    id:          int
    zone_id:     int
    hazard_type: str
    risk_level:  str
    title:       str
    message:     str
    is_active:   bool
    resolved_at: datetime | None
    resolved_by: int      | None
    created_at:  datetime

    model_config = {"from_attributes": True}