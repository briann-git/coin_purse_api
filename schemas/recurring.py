# schemas/recurring.py
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from .common import APIModel, ReadBase

KindName = Literal["income", "expense", "transfer", "refund"]
Cadence = Literal["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly"]


class RecurringTransactionCreate(APIModel):
    kind: KindName

    account_id: uuid.UUID
    to_account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None

    amount: Decimal = Field(ge=0)
    description: str | None = None

    cadence: Cadence
    next_run_date: date
    end_date: date | None = None

    refunded_transaction_id: uuid.UUID | None = None  # only if you want recurring refunds (rare)

    @model_validator(mode="after")
    def validate_rules(self):
        if self.end_date and self.end_date < self.next_run_date:
            raise ValueError("end_date must be >= next_run_date")

        if self.kind == "transfer":
            if self.to_account_id is None:
                raise ValueError("to_account_id is required for transfer recurrence.")
            if self.category_id is not None:
                raise ValueError("category_id should be null for transfer recurrence.")
            if self.account_id == self.to_account_id:
                raise ValueError("account_id and to_account_id cannot be the same.")
        elif self.to_account_id is not None:
            raise ValueError("to_account_id must be null for non-transfer recurrence.")

        if self.kind == "refund" and self.refunded_transaction_id is None:
            raise ValueError("refunded_transaction_id is required for refund recurrence.")
        return self


class RecurringTransactionUpdate(APIModel):
    account_id: uuid.UUID | None = None
    to_account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None

    amount: Decimal | None = Field(default=None, ge=0)
    description: str | None = None

    cadence: Cadence | None = None
    next_run_date: date | None = None
    end_date: date | None = None

    is_active: bool | None = None


class RecurringTransactionRead(ReadBase):
    user_id: uuid.UUID

    kind_id: uuid.UUID
    kind: str

    account_id: uuid.UUID
    account_name: str
    to_account_id: uuid.UUID | None = None
    to_account_name: str | None = None
    category_id: uuid.UUID | None = None
    category_name: str | None = None

    amount: Decimal
    description: str | None = None

    cadence: str
    next_run_date: date
    end_date: date | None = None

    @model_validator(mode="before")
    @classmethod
    def _resolve_names(cls, data):
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
            "is_active": data.is_active,
            "user_id": data.user_id,
            "kind_id": data.kind_id,
            "kind": data.kind.name if data.kind else "",
            "account_id": data.account_id,
            "account_name": data.account.name if data.account else "",
            "to_account_id": data.to_account_id,
            "to_account_name": data.to_account.name if data.to_account else None,
            "category_id": data.category_id,
            "category_name": data.category.name if data.category else None,
            "amount": data.amount,
            "description": data.description,
            "cadence": data.cadence,
            "next_run_date": data.next_run_date,
            "end_date": data.end_date,
        }
