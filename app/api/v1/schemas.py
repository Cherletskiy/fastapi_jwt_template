from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

    @field_validator("password")
    def password_strength(cls, v):
        if (
            len(v) < 8
            or not any(c.isupper() for c in v)
            or not any(c.isdigit() for c in v)
        ):
            raise ValueError(
                "Password must be at least 8 characters with uppercase and digit"
            )
        return v

    model_config = ConfigDict(extra="forbid")


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(extra="forbid")
