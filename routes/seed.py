# routes/seed.py
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from common.db.config import get_db
from helpers.seed_data import create_full_dev_seed, seed_transaction_kinds, seed_user_defaults

router = APIRouter(tags=["seed"])


@router.post("/dev/seed", status_code=201, summary="Create a full dev test user with sample data")
def dev_seed(db: Annotated[Session, Depends(get_db)]):
    """
    Creates a complete test user (test@coinpurse.dev / TestPass123!) with:
    - 3 accounts, 8 categories
    - ~30 transactions across the last 60 days
    - A current-month budget with 6 category limits
    - 2 recurring transactions

    Also ensures transaction kinds are seeded.
    Fails if the test user already exists.
    """
    seed_transaction_kinds(db)
    try:
        return create_full_dev_seed(db)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/seed/kinds", summary="Seed transaction kinds lookup table")
def seed_kinds(db: Annotated[Session, Depends(get_db)]):
    """Idempotent — ensures income, expense, transfer, refund rows exist."""
    created = seed_transaction_kinds(db)
    return {"message": "Transaction kinds seeded", "created": created}


@router.get("/users/{user_id}/seed", summary="Seed default accounts and categories for a user")
def seed_user(user_id: UUID, db: Annotated[Session, Depends(get_db)]):
    """Idempotent — skips anything that already exists."""
    result = seed_user_defaults(db, user_id)
    return {"message": "User defaults seeded", **result}
