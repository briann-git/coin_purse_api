from typing import Optional
from pydantic import BaseModel


class MonthlyBudgetItemBase(BaseModel):
    budget_item_id: int
    actual_amount: float
    notes: Optional[str]
    month: int
    year: int

    class Config:
        orm_mode = True

class MonthlyBudgetItemCreate(MonthlyBudgetItemBase):
    pass

class MonthlyBudgetItemUpdate(BaseModel):
    actual_amount: Optional[float]
    notes: Optional[str]
    month: Optional[int]
    year: Optional[int]

class MonthlyBudgetItemOut(MonthlyBudgetItemBase):
    id: int
