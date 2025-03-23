from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    name: str


class UserCreate(UserBase):
    """User creation model."""

    password: str


class UserLogin(BaseModel):
    """User login model."""

    email: EmailStr
    password: str


class UserInDB(UserBase):
    """User model stored in DB."""

    id: int
    hashed_password: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class User(UserBase):
    """User model returned to client."""

    id: int
    created_at: Optional[datetime] = None


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload model."""

    sub: Optional[str] = None
    exp: Optional[datetime] = None
