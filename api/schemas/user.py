import base64
import zlib
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from ..core.images import decompress_avatar


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    avatar: str | None = None
    avatar_content_type: str | None = None

    @field_validator("avatar", mode="before")
    @classmethod
    def avatar_to_base64(cls, value):
        if value is None:
            return None
        if isinstance(value, bytes):
            try:
                return base64.b64encode(decompress_avatar(value)).decode("ascii")
            except (zlib.error, ValueError):
                raise ValueError("Stored avatar is corrupt")
        return value


class AvatarUpload(BaseModel):
    content_type: str | None = None
    data: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenResponse):
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str