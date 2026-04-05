# schemas/categories.py
from __future__ import annotations

import uuid

from pydantic import Field

from .common import APIModel, ReadBase


class CategoryCreate(APIModel):
    name: str = Field(min_length=1, max_length=120)


class CategoryUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None


class CategoryRead(ReadBase):
    user_id: uuid.UUID
    name: str
