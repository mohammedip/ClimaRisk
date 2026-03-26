from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime



class RegisterRequest(BaseModel):
    username:  str
    email:     EmailStr
    password:  str
    role:      str = "PUBLIC"
    team_name: str = ""

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v):
        if v not in ("PUBLIC", "RESCUE", "ADMIN"):
            raise ValueError("Role must be PUBLIC, RESCUE or ADMIN")
        return v

    @field_validator("username")
    @classmethod
    def username_no_spaces(cls, v):
        if " " in v:
            raise ValueError("Username cannot contain spaces")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str



class UserResponse(BaseModel):
    id:         int
    username:   str
    email:      str
    role:       str
    team_name:  str | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type:   str
    user_id:      int
    username:     str
    role:         str
    team_name:    str | None