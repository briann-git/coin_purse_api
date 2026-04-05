from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

T = TypeVar("T")


def active_query(db: Session, model: type[T]):
    return db.query(model).filter(model.is_active.is_(True))
    # eg accounts = active_query(db, Account).all() instead of db.query(Account).all()


def get_active_or_404(db: Session, model: type[T], obj_id, *, detail: str = "Not found"):
    obj = active_query(db, model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=detail)
    return obj


def require_owned_active(db: Session, model, obj_id: UUID, user_id: UUID, *, detail: str):
    """
    For models that have model.user_id columns
    (Account, Category, Budget, Transaction, RecurringTransaction),
    enforce: active + belongs to user.
    """
    obj = active_query(db, model).filter(model.id == obj_id, model.user_id == user_id).first()
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
