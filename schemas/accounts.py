# schemas/accounts.py
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal

from pydantic import Field

from .common import APIModel, ReadBase

# You can swap this for a lookup table later if you want it fully dynamic.
AccountType = Literal["cash", "bank", "card", "mobile_money", "other"]


class AccountCreate(APIModel):
    name: str = Field(min_length=1, max_length=200)
    account_type: AccountType
    opening_balance: Decimal = Field(default=Decimal("0.00"), ge=0)


class AccountUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    account_type: AccountType | None = None
    opening_balance: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class AccountRead(ReadBase):
    user_id: uuid.UUID
    name: str
    account_type: str
    opening_balance: Decimal
