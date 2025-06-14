

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.db.config import get_db
from models.models import BudgetItem
from schemas.budget_items import BudgetItemCreate, BudgetItemUpdate, BudgetItemOut  # Assuming you have these schemas defined

budget_items_router = APIRouter(
    prefix="/budget_items",
    tags=["budget_items"],
    responses={404: {"description": "Not found"}},
)


# Generate crud endpoints for budget_item model
@budget_items_router.get("", response_model=List[BudgetItemOut])
def get_budget_items(db: Session = Depends(get_db)):  # Assuming you have a session dependency

    budget_items = db.query(BudgetItem).all()
    if not budget_items:
        return {"message": "No budget_items found"}
    return {"success": True, "budget_items": budget_items}

@budget_items_router.get("/{budget_item_id}", response_model=BudgetItemOut)
def get_budget_item(budget_item_id: int, db: Session = Depends(get_db)):
    budget_item = db.query(BudgetItem).filter(BudgetItem.id == budget_item_id).first()
    if not budget_item:
        return {"message": "budget_item not found"}
    return budget_item

@budget_items_router.post("", response_model=BudgetItemOut)
def create_budget_item(budget_item: BudgetItemCreate, db: Session = Depends(get_db)):
    db.add(BudgetItem(**budget_item.dict()))
    db.commit()
    db.refresh(budget_item)
    budget_item = db.query(BudgetItem).filter(BudgetItem.email == budget_item.email).first()
    if not budget_item:
        return {"message": "budget_item creation failed"}
    return budget_item


@budget_items_router.put("/{budget_item_id}", response_model=BudgetItemOut)
def update_budget_item(budget_item_id: int, budget_item: BudgetItemUpdate, db: Session = Depends(get_db)):
    existing_budget_item = db.query(BudgetItem).filter(BudgetItem.id == budget_item_id).first()
    if not existing_budget_item:
        return {"message": "budget_item not found"}
    for key, value in budget_item.items():
        setattr(existing_budget_item, key, value)
    db.commit()
    db.refresh(existing_budget_item)
    budget_item = db.query(BudgetItem).filter(BudgetItem.id == budget_item_id).first()
    if not budget_item:
        return {"message": "budget_item update failed"}
    return budget_item


@budget_items_router.delete("/{budget_item_id}", response_model=dict)
def delete_budget_item(budget_item_id: int, db: Session = Depends(get_db)):
    budget_item = db.query(BudgetItem).filter(BudgetItem.id == budget_item_id).first()
    if not budget_item:
        return {"message": "budget_item not found"}
    db.delete(budget_item)
    db.commit()
    return {"message": f"budget_item with ID {budget_item_id} deleted"}


