from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    last_name: str = Field(..., min_length=2, max_length=100)
    first_name: str = Field(..., min_length=2, max_length=100)
    middle_name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

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

    @field_validator("confirm_password")
    def password_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    model_config = ConfigDict(extra="forbid")


class UserUpdate(UserBase):
    username: str | None = None
    email: EmailStr | None = None
    last_name: str | None = None
    first_name: str | None = None
    middle_name: str | None = None

    @model_validator(mode='after')
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError('At least one field must be provided for update')
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    last_name: str
    first_name: str
    middle_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(extra="forbid")
