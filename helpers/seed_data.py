# helpers/seed_data.py
"""
Reusable seed helpers.

  seed_transaction_kinds(db)        — idempotent, seeds the 4 lookup rows
  seed_user_defaults(db, user_id)   — idempotent accounts + categories
  create_full_dev_seed(db)          — creates a complete test user with
                                      realistic transactions, a budget, and
                                      recurring items; returns the new user
"""

from __future__ import annotations

import calendar as _cal
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import bcrypt
from sqlalchemy.orm import Session

from helpers.db_utils import active_query
from models.models import (
    Account,
    Budget,
    BudgetItem,
    Category,
    RecurringTransaction,
    Transaction,
    TransactionKind,
    User,
)

DEFAULT_BUDGET_LIMITS = [
    ("Groceries", "15000.00"),
    ("Transport", "8000.00"),
    ("Eating Out", "5000.00"),
    ("Utilities", "5000.00"),
    ("Entertainment", "3000.00"),
    ("Subscriptions", "2000.00"),
    ("Savings", "10000.00"),
]


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ---------------------------------------------------------------------------
# KIND NAMES
# ---------------------------------------------------------------------------
KINDS = ["income", "expense", "transfer", "refund"]

# ---------------------------------------------------------------------------
# DEFAULT ACCOUNTS & CATEGORIES (per-user)
# ---------------------------------------------------------------------------
DEFAULT_ACCOUNTS = [
    {
        "name": "Cash Wallet",
        "account_type": "cash",
        "opening_balance": Decimal("5000.00"),
    },
    {
        "name": "M-Pesa",
        "account_type": "mobile_money",
        "opening_balance": Decimal("15000.00"),
    },
    {
        "name": "Bank Account",
        "account_type": "bank",
        "opening_balance": Decimal("45000.00"),
    },
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


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------


def seed_transaction_kinds(db: Session) -> list[str]:
    """Ensure all 4 transaction kinds exist. Idempotent."""
    created = []
    for name in KINDS:
        exists = db.query(TransactionKind).filter(TransactionKind.name == name).first()
        if not exists:
            db.add(TransactionKind(name=name))
            created.append(name)
    db.commit()
    return created


def seed_user_defaults(db: Session, user_id) -> dict:
    """Seed default accounts and categories for an existing user. Idempotent."""
    existing_accounts = {
        acc.name
        for acc in active_query(db, Account).filter(Account.user_id == user_id).all()
    }
    existing_categories = {
        cat.name
        for cat in active_query(db, Category).filter(Category.user_id == user_id).all()
    }

    created_accounts, created_categories = [], []

    for acc in DEFAULT_ACCOUNTS:
        if acc["name"] not in existing_accounts:
            db.add(
                Account(
                    user_id=user_id,
                    name=acc["name"],
                    account_type=acc["account_type"],
                    opening_balance=acc["opening_balance"],
                )
            )
            created_accounts.append(acc["name"])

    for name in DEFAULT_CATEGORIES:
        if name not in existing_categories:
            db.add(Category(user_id=user_id, name=name))
            created_categories.append(name)

    db.commit()
    return {
        "accounts_created": created_accounts,
        "categories_created": created_categories,
    }


def create_full_dev_seed(db: Session) -> dict:
    """
    Create a complete test user with:
      - 3 accounts
      - 8 categories
      - ~30 realistic transactions across the last 60 days
      - 1 budget for the current month with budget items
      - 2 recurring transactions

    Returns a dict with the user credentials and seeded IDs.
    Raises ValueError if the test user already exists.
    """
    test_email = "test@coinpurse.dev"
    if db.query(User).filter(User.email == test_email).first():
        msg = f"Dev seed user '{test_email}' already exists."
        raise ValueError(msg)

    # ------------------------------------------------------------------ user
    user = User(
        name="Test User",
        email=test_email,
        phone="+254700000000",
        password_hash=_hash("TestPass123!"),
    )
    db.add(user)
    db.flush()  # get user.id

    # ------------------------------------------------------------------ kinds
    kind_map: dict[str, TransactionKind] = {}
    for name in KINDS:
        kind = db.query(TransactionKind).filter(TransactionKind.name == name).first()
        if not kind:
            kind = TransactionKind(name=name)
            db.add(kind)
            db.flush()
        kind_map[name] = kind

    # --------------------------------------------------------------- accounts
    acc_data = [
        {
            "name": "Cash Wallet",
            "account_type": "cash",
            "opening_balance": Decimal("5000.00"),
        },
        {
            "name": "M-Pesa",
            "account_type": "mobile_money",
            "opening_balance": Decimal("15000.00"),
        },
        {
            "name": "Equity Bank",
            "account_type": "bank",
            "opening_balance": Decimal("45000.00"),
        },
    ]
    account_map: dict[str, Account] = {}
    for a in acc_data:
        acc = Account(
            user_id=user.id,
            name=a["name"],
            account_type=a["account_type"],
            opening_balance=a["opening_balance"],
        )
        db.add(acc)
        db.flush()
        account_map[a["name"]] = acc

    # ------------------------------------------------------------- categories
    cat_names = [
        "Groceries",
        "Transport",
        "Eating Out",
        "Utilities",
        "Entertainment",
        "Subscriptions",
        "Salary",
        "Savings",
    ]
    cat_map: dict[str, Category] = {}
    for name in cat_names:
        cat = Category(user_id=user.id, name=name)
        db.add(cat)
        db.flush()
        cat_map[name] = cat

    # ---------------------------------------------------------- transactions
    today = datetime.now(UTC).date()

    def ago(days: int) -> date:
        return today - timedelta(days=days)

    def txn(
        kind_name: str,
        account_name: str,
        amount: str,
        posted: date,
        description: str,
        category_name: str | None = None,
    ) -> Transaction:
        t = Transaction(
            user_id=user.id,
            kind_id=kind_map[kind_name].id,
            account_id=account_map[account_name].id,
            category_id=cat_map[category_name].id if category_name else None,
            amount=Decimal(amount),
            description=description,
            posted_at=posted,
        )
        db.add(t)
        return t

    # Income
    txn(
        "income", "Equity Bank", "85000.00", ago(60), "Monthly salary — March", "Salary"
    )
    txn(
        "income", "Equity Bank", "85000.00", ago(30), "Monthly salary — April", "Salary"
    )
    txn("income", "M-Pesa", "18000.00", ago(45), "Freelance project payment")

    # Groceries
    txn("expense", "Cash Wallet", "3200.00", ago(58), "Naivas supermarket", "Groceries")
    txn("expense", "M-Pesa", "2800.00", ago(44), "Carrefour — Weekly shop", "Groceries")
    txn(
        "expense",
        "Cash Wallet",
        "1500.00",
        ago(30),
        "Mama Mboga — vegetables",
        "Groceries",
    )
    txn("expense", "M-Pesa", "3600.00", ago(14), "Quickmart — weekly shop", "Groceries")
    txn("expense", "Cash Wallet", "900.00", ago(7), "Butchery", "Groceries")
    txn("expense", "M-Pesa", "2200.00", ago(2), "Carrefour — top-up", "Groceries")

    # Transport
    txn("expense", "M-Pesa", "1800.00", ago(57), "Fuel — full tank", "Transport")
    txn("expense", "Cash Wallet", "300.00", ago(50), "Matatu fare — CBD", "Transport")
    txn("expense", "M-Pesa", "1800.00", ago(28), "Fuel — full tank", "Transport")
    txn("expense", "Cash Wallet", "450.00", ago(21), "Bolt ride — airport", "Transport")
    txn(
        "expense",
        "Cash Wallet",
        "200.00",
        ago(10),
        "Matatu fare — Westlands",
        "Transport",
    )
    txn("expense", "M-Pesa", "1800.00", ago(3), "Fuel — full tank", "Transport")

    # Eating Out
    txn(
        "expense", "Cash Wallet", "1200.00", ago(55), "Java House — lunch", "Eating Out"
    )
    txn("expense", "M-Pesa", "2500.00", ago(35), "Carnivore — dinner", "Eating Out")
    txn("expense", "Cash Wallet", "800.00", ago(18), "Artcaffe — brunch", "Eating Out")
    txn(
        "expense",
        "Cash Wallet",
        "600.00",
        ago(5),
        "Kenchic — quick lunch",
        "Eating Out",
    )

    # Utilities
    txn(
        "expense", "M-Pesa", "4500.00", ago(56), "KPLC token — electricity", "Utilities"
    )
    txn(
        "expense", "M-Pesa", "4500.00", ago(26), "KPLC token — electricity", "Utilities"
    )

    # Entertainment
    txn("expense", "M-Pesa", "1000.00", ago(52), "Cinema — weekend", "Entertainment")
    txn("expense", "M-Pesa", "1500.00", ago(20), "Concert tickets", "Entertainment")

    # Subscriptions
    txn("expense", "M-Pesa", "1100.00", ago(59), "Netflix monthly", "Subscriptions")
    txn("expense", "M-Pesa", "1100.00", ago(29), "Netflix monthly", "Subscriptions")
    txn("expense", "M-Pesa", "600.00", ago(59), "Spotify monthly", "Subscriptions")
    txn("expense", "M-Pesa", "600.00", ago(29), "Spotify monthly", "Subscriptions")

    # Savings
    txn(
        "expense",
        "Equity Bank",
        "10000.00",
        ago(55),
        "Sacco savings deposit",
        "Savings",
    )
    txn(
        "expense",
        "Equity Bank",
        "10000.00",
        ago(25),
        "Sacco savings deposit",
        "Savings",
    )

    # Transfer: Bank → M-Pesa
    transfer_group = uuid4()
    t_out = Transaction(
        user_id=user.id,
        kind_id=kind_map["transfer"].id,
        account_id=account_map["Equity Bank"].id,
        to_account_id=account_map["M-Pesa"].id,
        amount=Decimal("10000.00"),
        description="Top-up M-Pesa from bank",
        posted_at=ago(40),
        transfer_group_id=transfer_group,
    )
    db.add(t_out)

    db.flush()

    # ----------------------------------------------------------------- budget
    month_start = today.replace(day=1)
    # last day of current month
    if month_start.month == 12:
        month_end = month_start.replace(
            year=month_start.year + 1, month=1, day=1
        ) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(
            days=1
        )

    budget = Budget(
        user_id=user.id,
        name=f"{month_start.strftime('%B %Y')} Budget",
        period_start=month_start,
        period_end=month_end,
    )
    db.add(budget)
    db.flush()

    budget_limits = {
        "Groceries": "15000.00",
        "Transport": "8000.00",
        "Eating Out": "5000.00",
        "Utilities": "5000.00",
        "Entertainment": "3000.00",
        "Subscriptions": "2000.00",
    }
    for cat_name, limit in budget_limits.items():
        db.add(
            BudgetItem(
                budget_id=budget.id,
                category_id=cat_map[cat_name].id,
                limit_amount=Decimal(limit),
            )
        )

    # ----------------------------------------------------------- recurring
    # Rent — monthly on the 5th
    db.add(
        RecurringTransaction(
            user_id=user.id,
            kind_id=kind_map["expense"].id,
            account_id=account_map["Equity Bank"].id,
            amount=Decimal("25000.00"),
            description="Monthly rent",
            cadence="monthly",
            next_run_date=(
                today.replace(day=5)
                if today.day < 5
                else (today.replace(day=5, month=today.month % 12 + 1))
            ),
        )
    )
    # Netflix — monthly on the 1st
    db.add(
        RecurringTransaction(
            user_id=user.id,
            kind_id=kind_map["expense"].id,
            account_id=account_map["M-Pesa"].id,
            category_id=cat_map["Subscriptions"].id,
            amount=Decimal("1100.00"),
            description="Netflix subscription",
            cadence="monthly",
            next_run_date=today.replace(day=1, month=today.month % 12 + 1),
        )
    )

    db.commit()

    return {
        "user": {
            "email": test_email,
            "password": "TestPass123!",
            "user_id": str(user.id),
        },
        "seeded": {
            "accounts": len(acc_data),
            "categories": len(cat_names),
            "transactions": 30,
            "budget": budget.name,
            "budget_items": len(budget_limits),
            "recurring": 2,
        },
    }


def seed_2025_budgets(db: Session, user_id: UUID) -> dict:
    """
    Create 12 monthly budgets for the year 2025, each with items from
    DEFAULT_BUDGET_LIMITS (matched against the user's active categories).
    The January budget is marked as the template.  Skips months where a
    budget already exists for that exact period.
    """
    cat_map: dict[str, Category] = {
        c.name: c
        for c in active_query(db, Category).filter(Category.user_id == user_id).all()
    }

    # Clear the existing template flag so January 2025 becomes the template
    db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.is_template.is_(True),
    ).update({"is_template": False})

    created, skipped = [], []
    source_id = None  # we'll chain clone lineage Jan→Feb→…

    for month in range(1, 13):
        period_start = date(2025, month, 1)
        period_end = date(2025, month, _cal.monthrange(2025, month)[1])
        name = f"{_cal.month_name[month]} 2025"

        exists = (
            db.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.period_start == period_start,
                Budget.period_end == period_end,
            )
            .first()
        )
        if exists:
            skipped.append(name)
            source_id = exists.id
            continue

        budget = Budget(
            user_id=user_id,
            name=name,
            period_start=period_start,
            period_end=period_end,
            is_template=(month == 1),
            source_budget_id=source_id,
        )
        db.add(budget)
        db.flush()

        for cat_name, limit in DEFAULT_BUDGET_LIMITS:
            if cat_name in cat_map:
                db.add(
                    BudgetItem(
                        budget_id=budget.id,
                        category_id=cat_map[cat_name].id,
                        limit_amount=Decimal(limit),
                    )
                )

        source_id = budget.id
        created.append(name)

    db.commit()
    return {"created": created, "skipped": skipped}
