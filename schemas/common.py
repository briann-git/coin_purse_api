from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

# ---------- Base building blocks (DRY) ----------


class APIModel(BaseModel):
    # Pydantic v2
    model_config = ConfigDict(from_attributes=True)


class UUIDMixin(APIModel):
    id: uuid.UUID


class ActiveMixin(APIModel):
    is_active: bool = True


class TimestampsMixin(APIModel):
    created_at: datetime
    updated_at: datetime


class ReadBase(UUIDMixin, ActiveMixin, TimestampsMixin):
    """Use for most *Read* schemas"""


class DeactivateSchema(BaseModel):
    is_active: bool = False


# Fixed-precision money field helper
Money = Decimal  # typed alias; constraints applied in fields


# Optional: generic list response if you like consistent outputs
T = TypeVar("T")


class ListResponse(APIModel, Generic[T]):
    items: list[T]
    total: int
