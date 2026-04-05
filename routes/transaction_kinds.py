# routes/transaction_kinds.py
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common.db.config import get_db
from helpers.db_utils import active_query, get_active_or_404, soft_delete
from models.models import TransactionKind
from schemas.transaction_kinds import (
    TransactionKindCreate,
    TransactionKindRead,
    TransactionKindUpdate,
)

router = APIRouter(prefix="/transaction-kinds", tags=["transaction-kinds"])


@router.post("", response_model=TransactionKindRead, status_code=status.HTTP_201_CREATED)
def create_kind(payload: TransactionKindCreate, db: Annotated[Session, Depends(get_db)]):
    kind = TransactionKind(name=payload.name)
    db.add(kind)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create kind (maybe duplicate).") from exc
    db.refresh(kind)
    return kind


@router.get("", response_model=list[TransactionKindRead])
def list_kinds(db: Annotated[Session, Depends(get_db)]):
    return active_query(db, TransactionKind).order_by(TransactionKind.name.asc()).all()


@router.get("/{kind_id}", response_model=TransactionKindRead)
def get_kind(kind_id: UUID, db: Annotated[Session, Depends(get_db)]):
    return get_active_or_404(db, TransactionKind, kind_id, detail="Transaction kind not found")


@router.patch("/{kind_id}", response_model=TransactionKindRead)
def update_kind(
    kind_id: UUID,
    payload: TransactionKindUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    kind = get_active_or_404(db, TransactionKind, kind_id, detail="Transaction kind not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(kind, k, v)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not update kind (maybe duplicate).") from exc
    db.refresh(kind)
    return kind


@router.delete("/{kind_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_kind(kind_id: UUID, db: Annotated[Session, Depends(get_db)]):
    deleted = soft_delete(db, TransactionKind, kind_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction kind not found")
