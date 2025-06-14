from typing import Optional
from pydantic import BaseModel


class BudgetItemBase(BaseModel):
    name: str
    description: Optional[str]
    type_id: int
    expected_amount: float
    user_id: int
    recurring: bool

    class Config:
        orm_mode = True

class BudgetItemCreate(BudgetItemBase):
    pass

class BudgetItemUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    type_id: Optional[int]
    expected_amount: Optional[float]
    recurring: Optional[bool]
    id: int

class BudgetItemOut(BudgetItemBase):
    id: int
