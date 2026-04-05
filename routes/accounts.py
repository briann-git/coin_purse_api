# routes/accounts.py
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common.db.config import get_db
from helpers.db_utils import active_query, require_owned_active, soft_delete
from models.models import Account
from schemas.accounts import AccountCreate, AccountRead, AccountUpdate

router = APIRouter(prefix="/users/{user_id}/accounts", tags=["accounts"])


@router.post(
    "",
    response_model=AccountRead,
    status_code=status.HTTP_201_CREATED,
)
def create_account(user_id: UUID, payload: AccountCreate, db: Annotated[Session, Depends(get_db)]):
    account = Account(
        user_id=user_id,
        name=payload.name,
        account_type=payload.account_type,
        opening_balance=payload.opening_balance,
    )
    db.add(account)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create account (maybe duplicate name).") from exc
    db.refresh(account)
    return account


@router.get("", response_model=list[AccountRead])
def list_accounts(user_id: UUID, db: Annotated[Session, Depends(get_db)]):
    return active_query(db, Account).filter(Account.user_id == user_id).all()


@router.get("/{account_id}", response_model=AccountRead)
def get_account(user_id: UUID, account_id: UUID, db: Annotated[Session, Depends(get_db)]):
    return require_owned_active(db, Account, account_id, user_id, detail="Account not found")


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    user_id: UUID,
    account_id: UUID,
    payload: AccountUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    acc = require_owned_active(db, Account, account_id, user_id, detail="Account not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(acc, k, v)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not update account (maybe duplicate name).") from exc
    db.refresh(acc)
    return acc


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_account(user_id: UUID, account_id: UUID, db: Annotated[Session, Depends(get_db)]):
    # enforce ownership before soft delete (soft_delete only checks active)
    _ = require_owned_active(db, Account, account_id, user_id, detail="Account not found")
    deleted = soft_delete(db, Account, account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
