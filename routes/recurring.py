# routes/recurring.py
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common.db.config import get_db
from helpers.db_utils import active_query, require_owned_active, soft_delete
from helpers.kinds import resolve_kind_id_or_400
from models.models import Account, Category, RecurringTransaction
from schemas.recurring import (
    RecurringTransactionCreate,
    RecurringTransactionRead,
    RecurringTransactionUpdate,
)

router = APIRouter(prefix="/users/{user_id}/recurring", tags=["recurring"])


def _require_account(db: Session, user_id: UUID, account_id: UUID):
    return require_owned_active(db, Account, account_id, user_id, detail="Account not found")


def _require_category(db: Session, user_id: UUID, category_id: UUID):
    return require_owned_active(db, Category, category_id, user_id, detail="Category not found")


@router.post("", response_model=RecurringTransactionRead, status_code=status.HTTP_201_CREATED)
def create_recurring(
    user_id: UUID,
    payload: RecurringTransactionCreate,
    db: Annotated[Session, Depends(get_db)],
):
    kind_id = resolve_kind_id_or_400(db, payload.kind)

    _require_account(db, user_id, payload.account_id)

    if payload.kind == "transfer":
        if not payload.to_account_id:
            raise HTTPException(status_code=400, detail="to_account_id required for transfer recurrence")
        _require_account(db, user_id, payload.to_account_id)
        if payload.category_id is not None:
            raise HTTPException(
                status_code=400,
                detail="category_id must be null for transfer recurrence",
            )
    else:
        if payload.to_account_id is not None:
            raise HTTPException(
                status_code=400,
                detail="to_account_id must be null for non-transfer recurrence",
            )
        if payload.category_id is not None:
            _require_category(db, user_id, payload.category_id)

    rec = RecurringTransaction(
        user_id=user_id,
        kind_id=kind_id,
        account_id=payload.account_id,
        to_account_id=payload.to_account_id,
        category_id=payload.category_id,
        amount=payload.amount,
        description=payload.description,
        cadence=payload.cadence,
        next_run_date=payload.next_run_date,
        end_date=payload.end_date,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    out = RecurringTransactionRead.model_validate(rec, from_attributes=True)
    out.kind = payload.kind
    return out


@router.get("", response_model=list[RecurringTransactionRead])
def list_recurring(user_id: UUID, db: Annotated[Session, Depends(get_db)]):
    recs = active_query(db, RecurringTransaction).filter(RecurringTransaction.user_id == user_id).all()
    return [RecurringTransactionRead.model_validate(r, from_attributes=True) for r in recs]


@router.get("/{recurring_id}", response_model=RecurringTransactionRead)
def get_recurring(user_id: UUID, recurring_id: UUID, db: Annotated[Session, Depends(get_db)]):
    rec = require_owned_active(db, RecurringTransaction, recurring_id, user_id, detail="Recurring not found")
    return RecurringTransactionRead.model_validate(rec, from_attributes=True)


@router.patch("/{recurring_id}", response_model=RecurringTransactionRead)
def update_recurring(
    user_id: UUID,
    recurring_id: UUID,
    payload: RecurringTransactionUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    rec = require_owned_active(db, RecurringTransaction, recurring_id, user_id, detail="Recurring not found")
    data = payload.model_dump(exclude_unset=True)

    if "account_id" in data and data["account_id"] is not None:
        _require_account(db, user_id, data["account_id"])
    if "to_account_id" in data and data["to_account_id"] is not None:
        _require_account(db, user_id, data["to_account_id"])
    if "category_id" in data and data["category_id"] is not None:
        _require_category(db, user_id, data["category_id"])

    for k, v in data.items():
        setattr(rec, k, v)

    db.commit()
    db.refresh(rec)
    return RecurringTransactionRead.model_validate(rec, from_attributes=True)


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_recurring(user_id: UUID, recurring_id: UUID, db: Annotated[Session, Depends(get_db)]):
    _ = require_owned_active(db, RecurringTransaction, recurring_id, user_id, detail="Recurring not found")
    deleted = soft_delete(db, RecurringTransaction, recurring_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recurring not found")
