# routes/views.py
from __future__ import annotations

import calendar as cal_lib
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from common.db.config import get_db
from helpers.db_utils import active_query
from models.models import Account, Budget, BudgetItem, Category
from routes.dashboard import get_dashboard

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=_TEMPLATES_DIR)


def _currency(value: object) -> str:
    return f"${float(value):,.2f}"  # type: ignore[arg-type]


def _date_fmt(value: object) -> str:
    return value.strftime("%b %d") if value else "—"  # type: ignore[union-attr]


def _month_name(value: object) -> str:
    return cal_lib.month_name[int(value)]  # type: ignore[arg-type]


def _kind_badge(kind: str) -> str:
    return {
        "income": "bg-emerald-100 text-emerald-700",
        "expense": "bg-rose-100 text-rose-700",
        "refund": "bg-blue-100 text-blue-700",
        "transfer": "bg-purple-100 text-purple-700",
    }.get(kind, "bg-slate-100 text-slate-600")


templates.env.filters["currency"] = _currency
templates.env.filters["date_fmt"] = _date_fmt
templates.env.filters["month_name"] = _month_name
templates.env.filters["kind_badge"] = _kind_badge

router = APIRouter(tags=["ui"])


@router.get("/ui/dashboard/{user_id}", response_class=HTMLResponse)
def ui_dashboard(
    request: Request,
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    data = get_dashboard(user_id, db)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, **data, "user_id": str(user_id)},
    )


@router.get("/ui/config/{user_id}", response_class=HTMLResponse)
def ui_config(
    request: Request,
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    accounts = (
        active_query(db, Account).filter(Account.user_id == user_id).order_by(Account.name).all()
    )
    categories = (
        active_query(db, Category).filter(Category.user_id == user_id).order_by(Category.name).all()
    )
    budgets = (
        active_query(db, Budget)
        .filter(Budget.user_id == user_id)
        .order_by(Budget.period_start.desc())
        .all()
    )
    # Attach active items to each budget
    budget_data = []
    for b in budgets:
        items = (
            active_query(db, BudgetItem)
            .filter(BudgetItem.budget_id == b.id)
            .join(Category, BudgetItem.category_id == Category.id)
            .filter(Category.is_active.is_(True))
            .with_entities(
                BudgetItem.id.label("id"),
                BudgetItem.limit_amount.label("limit_amount"),
                BudgetItem.category_id.label("category_id"),
                Category.name.label("category_name"),
            )
            .order_by(Category.name)
            .all()
        )
        budget_data.append({"budget": b, "items": items})

    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "user_id": str(user_id),
            "accounts": accounts,
            "categories": categories,
            "budgets": budget_data,
        },
    )
