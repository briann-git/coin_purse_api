# schemas/transaction_kinds.py
from __future__ import annotations

from pydantic import Field

from .common import APIModel, ReadBase


class TransactionKindCreate(APIModel):
    # You probably won't expose this in public API; seeded by migration
    name: str = Field(min_length=2, max_length=50)


class TransactionKindUpdate(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    is_active: bool | None = None


class TransactionKindRead(ReadBase):
    name: str
