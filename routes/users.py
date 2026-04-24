# routes/users.py
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common.db.config import get_db
from helpers.db_utils import active_query, get_active_or_404, soft_delete
from models.models import User
from schemas.users import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Annotated[Session, Depends(get_db)]):
    user = User(
        name=payload.name,
        email=str(payload.email),
        phone=payload.phone,
    )

    print("user:", user)
    db.add(user)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Could not create user (maybe duplicate email/phone).",
        ) from exc
    db.refresh(user)
    print("created user:", user)
    return user


@router.get("", response_model=list[UserRead])
def list_users(db: Annotated[Session, Depends(get_db)]):
    return active_query(db, User).order_by(User.created_at.desc()).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, db: Annotated[Session, Depends(get_db)]):
    return get_active_or_404(db, User, user_id, detail="User not found")


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, payload: UserUpdate, db: Annotated[Session, Depends(get_db)]):
    user = get_active_or_404(db, User, user_id, detail="User not found")

    data = payload.model_dump(exclude_unset=True)

    # For now, we allow name/phone updates only (per schema)
    for k, v in data.items():
        setattr(user, k, v)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not update user (maybe duplicate phone).") from exc
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: UUID, db: Annotated[Session, Depends(get_db)]):
    deleted = soft_delete(db, User, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
