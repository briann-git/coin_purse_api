
from typing import Union
from fastapi import FastAPI
import uvicorn

from common.db import Base
from common.db.config import engine

from routes.users import users_router
from routes.budget_item_types import budget_item_types_router
from routes.budget_items import budget_items_router
from routes.monthly_budget_items import monthly_budget_items_router

app = FastAPI()


metadata = Base.metadata

metadata.create_all(bind=engine)

app.include_router(users_router)
app.include_router(budget_item_types_router)
app.include_router(budget_items_router)
app.include_router(monthly_budget_items_router)

@app.get("") 
def main_route():     
  return {"message": "Hey, It is me Goku"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


if __name__ == "__main__":
    
    uvicorn.run(
       "main:app", 
       host="0.0.0.0", 
       port=8000,
        reload=True,
       )
