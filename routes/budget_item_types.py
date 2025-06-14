

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.db.config import get_db
from models.models import BudgetItemType
from schemas.budget_item_types import BudgetItemTypeCreate, BudgetItemTypeUpdate, BudgetItemTypeOut  # Assuming you have these schemas defined

budget_item_types_router = APIRouter(
    prefix="/budget_item_types",
    tags=["budget_item_types"],
    responses={404: {"description": "Not found"}},
)


# Generate crud endpoints for budget_item_type model
@budget_item_types_router.get("", response_model=List[BudgetItemTypeOut])
def get_budget_item_types(db: Session = Depends(get_db)):  # Assuming you have a session dependency

    budget_item_types = db.query(BudgetItemType).all()
    if not budget_item_types:
        return {"message": "No budget_item_types found"}
    return budget_item_types

@budget_item_types_router.get("/{budget_item_type_id}", response_model=BudgetItemTypeOut)
def get_budget_item_type(budget_item_type_id: int, db: Session = Depends(get_db)):
    budget_item_type = db.query(BudgetItemType).filter(BudgetItemType.id == budget_item_type_id).first()
    if not budget_item_type:
        return {"message": "budget_item_type not found"}
    return budget_item_type

@budget_item_types_router.post("", response_model=BudgetItemTypeOut)
def create_budget_item_type(budget_item_type: BudgetItemTypeCreate, db: Session = Depends(get_db)):
    db.add(BudgetItemType(**budget_item_type.dict()))
    db.commit()
    db.refresh(budget_item_type)
    budget_item_type = db.query(BudgetItemType).filter(BudgetItemType.email == budget_item_type.email).first()
    if not budget_item_type:
        return {"message": "budget_item_type creation failed"}
    return {"message": "budget_item_type created", "budget_item_type": budget_item_type}


@budget_item_types_router.put("/{budget_item_type_id}", response_model=BudgetItemTypeOut)
def update_budget_item_type(budget_item_type_id: int, budget_item_type: BudgetItemTypeUpdate, db: Session = Depends(get_db)):
    existing_budget_item_type = db.query(BudgetItemType).filter(BudgetItemType.id == budget_item_type_id).first()
    if not existing_budget_item_type:
        return {"message": "budget_item_type not found"}
    for key, value in budget_item_type.dict().items():
        setattr(existing_budget_item_type, key, value)
    db.commit()
    db.refresh(existing_budget_item_type)
    return existing_budget_item_type


@budget_item_types_router.delete("/{budget_item_type_id}", response_model=dict)
def delete_budget_item_type(budget_item_type_id: int, db: Session = Depends(get_db)):
    budget_item_type = db.query(BudgetItemType).filter(BudgetItemType.id == budget_item_type_id).first()
    if not budget_item_type:
        return {"message": "budget_item_type not found"}
    db.delete(budget_item_type)
    db.commit()
    return {"message": f"budget_item_type with ID {budget_item_type_id} deleted"}
# Include the budget_item_types router in the main application

