# routes/categories.py
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common.db.config import get_db
from helpers.db_utils import active_query, require_owned_active, soft_delete
from models.models import Category
from schemas.categories import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/users/{user_id}/categories", tags=["categories"])


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(user_id: UUID, payload: CategoryCreate, db: Annotated[Session, Depends(get_db)]):
    cat = Category(user_id=user_id, name=payload.name)
    db.add(cat)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create category (maybe duplicate name).") from exc
    db.refresh(cat)
    return cat


@router.get("", response_model=list[CategoryRead])
def list_categories(user_id: UUID, db: Annotated[Session, Depends(get_db)]):
    return active_query(db, Category).filter(Category.user_id == user_id).all()


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(user_id: UUID, category_id: UUID, db: Annotated[Session, Depends(get_db)]):
    return require_owned_active(db, Category, category_id, user_id, detail="Category not found")


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    user_id: UUID,
    category_id: UUID,
    payload: CategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    cat = require_owned_active(db, Category, category_id, user_id, detail="Category not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not update category (maybe duplicate name).") from exc
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_category(user_id: UUID, category_id: UUID, db: Annotated[Session, Depends(get_db)]):
    _ = require_owned_active(db, Category, category_id, user_id, detail="Category not found")
    deleted = soft_delete(db, Category, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
