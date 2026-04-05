from pydantic import BaseModel


class BudgetItemBase(BaseModel):
    name: str
    description: str | None
    type_id: int
    expected_amount: float
    user_id: int
    recurring: bool

    class Config:
        orm_mode = True


class BudgetItemCreate(BudgetItemBase):
    pass


class BudgetItemUpdate(BaseModel):
    name: str | None
    description: str | None
    type_id: int | None
    expected_amount: float | None
    recurring: bool | None
    id: int


class BudgetItemOut(BudgetItemBase):
    id: int
