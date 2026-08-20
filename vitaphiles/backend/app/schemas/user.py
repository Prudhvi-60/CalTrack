from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

USERNAME_PATTERN = r"^[a-z][a-z0-9_]{2,23}$"


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    display_name: str
    bio: str | None = None
    avatar_url: str | None = None
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=24, pattern=USERNAME_PATTERN)
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("username")
    @classmethod
    def lowercase_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("display_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Display name is required")
        return cleaned


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    bio: str | None = Field(default=None, max_length=500)

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Display name is required")
        return cleaned
