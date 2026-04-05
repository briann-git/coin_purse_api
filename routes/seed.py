# routes/seed.py
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.db.config import get_db
from helpers.db_utils import active_query
from models.models import Account, Category

router = APIRouter(prefix="/users/{user_id}", tags=["seed"])


DEFAULT_ACCOUNTS = [
    {"name": "Cash Wallet", "account_type": "cash"},
    {"name": "Bank Account", "account_type": "bank"},
    {"name": "Mobile Money", "account_type": "mobile_money"},
]

DEFAULT_CATEGORIES = [
    "Groceries",
    "Transport",
    "Eating Out",
    "Utilities",
    "Entertainment",
    "Subscriptions",
    "Savings",
    "CSR",
]


@router.get("/seed")
def seed_defaults(user_id: UUID, db: Annotated[Session, Depends(get_db)]):
    created_accounts = []
    created_categories = []

    # -------- Accounts --------
    existing_accounts = {acc.name for acc in active_query(db, Account).filter(Account.user_id == user_id).all()}

    for acc in DEFAULT_ACCOUNTS:
        if acc["name"] not in existing_accounts:
            new_acc = Account(
                user_id=user_id,
                name=acc["name"],
                account_type=acc["account_type"],
                opening_balance=0,
            )
            db.add(new_acc)
            created_accounts.append(acc["name"])

    # -------- Categories --------
    existing_categories = {cat.name for cat in active_query(db, Category).filter(Category.user_id == user_id).all()}

    for name in DEFAULT_CATEGORIES:
        if name not in existing_categories:
            cat = Category(
                user_id=user_id,
                name=name,
            )
            db.add(cat)
            created_categories.append(name)

    db.commit()

    return {
        "message": "Seed completed",
        "accounts_created": created_accounts,
        "categories_created": created_categories,
    }
