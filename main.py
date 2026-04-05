import uvicorn
from fastapi import FastAPI

from common.db import Base
from common.db.config import engine
from common.errors.errors import register_error_handlers
from routes.budget_items import router as budget_items_router
from routes.budgets import router as budgets_router
from routes.recurring import router as recurring_router
from routes.seed import router as seed_router
from routes.transaction_kinds import router as transaction_kinds_router
from routes.transactions import router as transactions_router
from routes.users import router as user_router

app = FastAPI(title="Coin Purse")
register_error_handlers(app)


metadata = Base.metadata

metadata.create_all(bind=engine)

app.include_router(budgets_router)
app.include_router(budget_items_router)
app.include_router(recurring_router)
app.include_router(seed_router)
app.include_router(transaction_kinds_router)
app.include_router(transactions_router)
app.include_router(user_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
