from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

T = TypeVar("T")


def active_query(db: Session, model: type[T]):
    return db.query(model).filter(model.is_active.is_(True))
    # eg accounts = active_query(db, Account).all() instead of db.query(Account).all()


def get_active_or_404(
    db: Session, model: type[T], obj_id, *, detail: str = "Not found"
):
    obj = active_query(db, model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=detail)
    return obj


def require_owned_active(
    db: Session, model, obj_id: UUID, user_id: UUID, *, detail: str
):
    """
    For models that have model.user_id columns
    (Account, Category, Budget, Transaction, RecurringTransaction),
    enforce: active + belongs to user.
    """
    obj = (
        active_query(db, model)
        .filter(model.id == obj_id, model.user_id == user_id)
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail=detail)
    return obj


def soft_delete(db: Session, model: type[T], obj_id: UUID):
    obj = db.query(model).filter(model.id == obj_id, model.is_active).first()

    if not obj:
        return None

    obj.is_active = False
    db.commit()
    db.refresh(obj)

    return obj


def get_or_reactivate(
    db: Session,
    model: type[T],
    filters: list,
    *,
    create: Callable[[], T],
    updates: dict | None = None,
    conflict_detail: str,
) -> T:
    """Find a row matching `filters` (regardless of is_active).

    - If found and active  → raise 409.
    - If found and inactive → set is_active=True, apply `updates`, commit & return.
    - If not found         → call `create()`, add, commit & return.
    """
    existing = db.query(model).filter(*filters).first()
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=409, detail=conflict_detail)
        existing.is_active = True
        for k, v in (updates or {}).items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing
    obj = create()
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
