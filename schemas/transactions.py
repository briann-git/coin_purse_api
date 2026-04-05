# schemas/transactions.py
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from .common import APIModel, ReadBase

# If you prefer: kind_id only. If you prefer convenience in the API: kind_name.
# Since you have lookup-table "transaction_kinds", both patterns are common.
KindName = Literal["income", "expense", "transfer", "refund"]


class TransactionCreate(APIModel):
    # Prefer kind_name for client UX; server resolves to kind_id
    kind: KindName

    account_id: uuid.UUID
    to_account_id: uuid.UUID | None = None  # required for transfers
    category_id: uuid.UUID | None = None  # usually null for transfer

    amount: Decimal = Field(ge=0)
    description: str | None = None
    posted_at: date

    refunded_transaction_id: uuid.UUID | None = None
    transfer_group_id: uuid.UUID | None = None  # server can generate if omitted

    @model_validator(mode="after")
    def validate_business_rules(self):
        if self.kind == "transfer":
            if self.to_account_id is None:
                raise ValueError("to_account_id is required for transfer transactions.")
            if self.category_id is not None:
                raise ValueError("category_id should be null for transfers.")
            if self.account_id == self.to_account_id:
                raise ValueError("account_id and to_account_id cannot be the same.")
        # non-transfer: destination account should generally be null
        # (keep it strict; relax if you want)
        elif self.to_account_id is not None:
            raise ValueError("to_account_id must be null for non-transfer transactions.")
        if self.kind == "refund" and self.refunded_transaction_id is None:
            # You can relax this if you want refunds without linkage
            raise ValueError("refunded_transaction_id is required for refund transactions.")
        return self


class TransactionUpdate(APIModel):
    # Typically you allow editing description/category/posted_at/amount etc.
    category_id: uuid.UUID | None = None
    description: str | None = None
    posted_at: date | None = None
    amount: Decimal | None = Field(default=None, ge=0)

    # For transfers you may allow editing to_account_id
    to_account_id: uuid.UUID | None = None

    is_active: bool | None = None


class TransactionRead(ReadBase):
    user_id: uuid.UUID

    kind_id: uuid.UUID
    kind: str  # populated via join in service layer if you like

    account_id: uuid.UUID
    to_account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None

    amount: Decimal
    description: str | None = None
    posted_at: date

    refunded_transaction_id: uuid.UUID | None = None
    transfer_group_id: uuid.UUID | None = None
