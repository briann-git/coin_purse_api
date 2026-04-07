# routes/budgets.py
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common.db.config import get_db
from helpers.db_utils import active_query, get_or_reactivate, require_owned_active, soft_delete
from models.models import Budget
from schemas.budgets import BudgetCreate, BudgetRead, BudgetUpdate

router = APIRouter(prefix="/users/{user_id}/budgets", tags=["budgets"])


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(user_id: UUID, payload: BudgetCreate, db: Annotated[Session, Depends(get_db)]):
    return get_or_reactivate(
        db, Budget,
        [
            Budget.user_id == user_id,
            Budget.period_start == payload.period_start,
            Budget.period_end == payload.period_end,
        ],
        create=lambda: Budget(
            user_id=user_id,
            name=payload.name,
            period_start=payload.period_start,
            period_end=payload.period_end,
        ),
        updates={"name": payload.name},
        conflict_detail="A budget for that period already exists.",
    )


@router.get("", response_model=list[BudgetRead])
def list_budgets(user_id: UUID, db: Annotated[Session, Depends(get_db)]):
    return active_query(db, Budget).filter(Budget.user_id == user_id).order_by(Budget.period_start.desc()).all()


@router.get("/{budget_id}", response_model=BudgetRead)
def get_budget(user_id: UUID, budget_id: UUID, db: Annotated[Session, Depends(get_db)]):
    return require_owned_active(db, Budget, budget_id, user_id, detail="Budget not found")


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(
    user_id: UUID,
    budget_id: UUID,
    payload: BudgetUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    budget = require_owned_active(db, Budget, budget_id, user_id, detail="Budget not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(budget, k, v)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not update budget (maybe duplicate period).") from exc
    db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_budget(user_id: UUID, budget_id: UUID, db: Annotated[Session, Depends(get_db)]):
    _ = require_owned_active(db, Budget, budget_id, user_id, detail="Budget not found")
    deleted = soft_delete(db, Budget, budget_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Budget not found")
