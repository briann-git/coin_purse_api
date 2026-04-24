from __future__ import annotations

from pydantic import EmailStr, Field

from .common import APIModel, ReadBase


class UserCreate(APIModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)


class UserUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    # email update typically requires verification; omit unless you want it


class UserRead(ReadBase):
    name: str
    email: EmailStr
    phone: str | None = None
    # never expose password_hash
