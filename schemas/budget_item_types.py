from typing import Optional
from pydantic import BaseModel


class BudgetItemTypeBase(BaseModel):
    name: str

    class Config:
        orm_mode = True
        # allow_population_by_field_name = True
        # use_enum_values = True
        # arbitrary_types_allowed = True
        # json_encoders = {
        #     int: lambda v: str(v)  # Example of custom encoder for int
        # }

class BudgetItemTypeCreate(BudgetItemTypeBase):
    pass

class BudgetItemTypeUpdate(BaseModel):
    name: Optional[str]

class BudgetItemTypeOut(BudgetItemTypeBase):
    id: int
    