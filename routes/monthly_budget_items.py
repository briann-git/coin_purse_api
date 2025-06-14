

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.db.config import get_db
from models.models import MonthlyBudgetItem

monthly_budget_items_router = APIRouter(
    prefix="/monthly_budget_items",
    tags=["monthly_budget_items"],
    responses={404: {"description": "Not found"}},
)


# Generate crud endpoints for monthly_budget_item model
@monthly_budget_items_router.get("")
def get_monthly_budget_items(db: Session = Depends(get_db)):  # Assuming you have a session dependency

    monthly_budget_items = db.query(MonthlyBudgetItem).all()
    if not monthly_budget_items:
        return {"message": "No monthly_budget_items found"}
    return {"success": True, "monthly_budget_items": monthly_budget_items}

@monthly_budget_items_router.get("/{monthly_budget_item_id}")
def get_monthly_budget_item(monthly_budget_item_id: int, db: Session = Depends(get_db)):
    monthly_budget_item = db.query(MonthlyBudgetItem).filter(MonthlyBudgetItem.id == monthly_budget_item_id).first()
    if not monthly_budget_item:
        return {"message": "monthly_budget_item not found"}
    return {"success": True, "monthly_budget_item": monthly_budget_item}

@monthly_budget_items_router.post("")
def create_monthly_budget_item(monthly_budget_item: dict, db: Session = Depends(get_db)):
    db.add(MonthlyBudgetItem(**monthly_budget_item))
    db.commit()
    db.refresh(monthly_budget_item)
    monthly_budget_item = db.query(MonthlyBudgetItem).filter(MonthlyBudgetItem.email == monthly_budget_item['email']).first()
    if not monthly_budget_item:
        return {"message": "monthly_budget_item creation failed"}
    return {"message": "monthly_budget_item created", "monthly_budget_item": monthly_budget_item}


@monthly_budget_items_router.put("/{monthly_budget_item_id}")
def update_monthly_budget_item(monthly_budget_item_id: int, monthly_budget_item: dict, db: Session = Depends(get_db)):
    existing_monthly_budget_item = db.query(MonthlyBudgetItem).filter(MonthlyBudgetItem.id == monthly_budget_item_id).first()
    if not existing_monthly_budget_item:
        return {"message": "monthly_budget_item not found"}
    for key, value in monthly_budget_item.items():
        setattr(existing_monthly_budget_item, key, value)
    db.commit()
    db.refresh(existing_monthly_budget_item)
    monthly_budget_item = db.query(MonthlyBudgetItem).filter(MonthlyBudgetItem.id == monthly_budget_item_id).first()
    if not monthly_budget_item:
        return {"message": "monthly_budget_item update failed"}
    return {"message": f"monthly_budget_item with ID {monthly_budget_item_id} updated", "monthly_budget_item": monthly_budget_item}


@monthly_budget_items_router.delete("/{monthly_budget_item_id}")
def delete_monthly_budget_item(monthly_budget_item_id: int, db: Session = Depends(get_db)):
    monthly_budget_item = db.query(MonthlyBudgetItem).filter(MonthlyBudgetItem.id == monthly_budget_item_id).first()
    if not monthly_budget_item:
        return {"message": "monthly_budget_item not found"}
    db.delete(monthly_budget_item)
    db.commit()
    return {"message": f"monthly_budget_item with ID {monthly_budget_item_id} deleted"}
# Include the monthly_budget_items router in the main application

