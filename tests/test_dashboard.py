"""Tests for GET /users/{user_id}/dashboard."""

from __future__ import annotations

import calendar
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

TODAY = datetime.now(UTC).date()
YEAR = TODAY.year
MONTH = TODAY.month
MONTH_START = TODAY.replace(day=1)
MONTH_END = TODAY.replace(day=calendar.monthrange(YEAR, MONTH)[1])


@pytest.fixture
def account(client: TestClient, user_id: str) -> dict:
    res = client.post(
        f"/users/{user_id}/accounts",
        json={"name": "Main", "account_type": "bank", "opening_balance": "1000.00"},
    )
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def category(client: TestClient, user_id: str) -> dict:
    res = client.post(f"/users/{user_id}/categories", json={"name": "Groceries"})
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def budget(client: TestClient, user_id: str) -> dict:
    res = client.post(
        f"/users/{user_id}/budgets",
        json={"name": "This Month", "period_start": str(MONTH_START), "period_end": str(MONTH_END)},
    )
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def budget_item(client: TestClient, user_id: str, budget: dict, category: dict) -> dict:
    res = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/items",
        json={"category_id": category["id"], "limit_amount": "400.00"},
    )
    assert res.status_code == 201
    return res.json()


# ---------------------------------------------------------------------------
# GET /users/{user_id}/dashboard
# ---------------------------------------------------------------------------


def test_dashboard_empty_user(client: TestClient, user_id: str):
    """Dashboard returns valid structure even when user has nothing set up."""
    res = client.get(f"/users/{user_id}/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "as_of" in data
    assert "net_worth" in data
    assert data["accounts"] == []
    assert data["active_budget"] is None
    assert data["recent_transactions"] == []
    assert data["upcoming_recurring"] == []
    assert "current_month" in data


def test_dashboard_net_worth(client: TestClient, user_id: str, account: dict):  # noqa: ARG001
    """Net worth equals opening_balance when there are no transactions."""
    res = client.get(f"/users/{user_id}/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert len(data["accounts"]) == 1
    assert float(data["accounts"][0]["current_balance"]) == pytest.approx(1000.00)
    assert float(data["net_worth"]) == pytest.approx(1000.00)


def test_dashboard_net_worth_after_income(client: TestClient, user_id: str, account: dict):
    client.post(
        f"/users/{user_id}/transactions",
        json={"kind": "income", "account_id": account["id"], "amount": "500.00", "posted_at": str(TODAY)},
    )
    res = client.get(f"/users/{user_id}/dashboard")
    data = res.json()
    assert float(data["accounts"][0]["current_balance"]) == pytest.approx(1500.00)
    assert float(data["net_worth"]) == pytest.approx(1500.00)


def test_dashboard_net_worth_after_expense(client: TestClient, user_id: str, account: dict):
    client.post(
        f"/users/{user_id}/transactions",
        json={"kind": "expense", "account_id": account["id"], "amount": "200.00", "posted_at": str(TODAY)},
    )
    res = client.get(f"/users/{user_id}/dashboard")
    data = res.json()
    assert float(data["accounts"][0]["current_balance"]) == pytest.approx(800.00)


def test_dashboard_current_month_totals(client: TestClient, user_id: str, account: dict):
    client.post(
        f"/users/{user_id}/transactions",
        json={"kind": "income", "account_id": account["id"], "amount": "3000.00", "posted_at": str(TODAY)},
    )
    client.post(
        f"/users/{user_id}/transactions",
        json={"kind": "expense", "account_id": account["id"], "amount": "750.00", "posted_at": str(TODAY)},
    )
    res = client.get(f"/users/{user_id}/dashboard")
    m = res.json()["current_month"]
    assert float(m["income"]) == pytest.approx(3000.00)
    assert float(m["expense"]) == pytest.approx(750.00)
    assert float(m["net"]) == pytest.approx(2250.00)


def test_dashboard_active_budget_none_when_no_budget(client: TestClient, user_id: str):
    res = client.get(f"/users/{user_id}/dashboard")
    assert res.json()["active_budget"] is None


def test_dashboard_active_budget_returned(client: TestClient, user_id: str, budget_item: dict, budget: dict):  # noqa: ARG001
    res = client.get(f"/users/{user_id}/dashboard")
    assert res.status_code == 200
    ab = res.json()["active_budget"]
    assert ab is not None
    assert ab["budget_id"] == budget["id"]
    assert ab["budget_name"] == budget["name"]
    assert len(ab["items"]) == 1
    assert float(ab["items"][0]["limit"]) == pytest.approx(400.00)
    assert float(ab["items"][0]["spent"]) == pytest.approx(0.00)
    assert float(ab["items"][0]["remaining"]) == pytest.approx(400.00)


def test_dashboard_budget_item_spent_reflects_transactions(
    client: TestClient, user_id: str, account: dict, category: dict, budget_item: dict  # noqa: ARG001
):
    client.post(
        f"/users/{user_id}/transactions",
        json={
            "kind": "expense",
            "account_id": account["id"],
            "category_id": category["id"],
            "amount": "150.00",
            "posted_at": str(TODAY),
        },
    )
    res = client.get(f"/users/{user_id}/dashboard")
    item = res.json()["active_budget"]["items"][0]
    assert float(item["spent"]) == pytest.approx(150.00)
    assert float(item["remaining"]) == pytest.approx(250.00)
    assert float(item["percent_used"]) == pytest.approx(37.5)
    assert item["over_budget"] is False


def test_dashboard_budget_item_over_budget_flag(
    client: TestClient, user_id: str, account: dict, category: dict, budget_item: dict  # noqa: ARG001
):
    client.post(
        f"/users/{user_id}/transactions",
        json={
            "kind": "expense",
            "account_id": account["id"],
            "category_id": category["id"],
            "amount": "500.00",
            "posted_at": str(TODAY),
        },
    )
    res = client.get(f"/users/{user_id}/dashboard")
    item = res.json()["active_budget"]["items"][0]
    assert item["over_budget"] is True
    assert float(item["remaining"]) == pytest.approx(-100.00)


def test_dashboard_recent_transactions(client: TestClient, user_id: str, account: dict):
    for i in range(3):
        client.post(
            f"/users/{user_id}/transactions",
            json={"kind": "income", "account_id": account["id"], "amount": f"{100 + i}.00", "posted_at": str(TODAY)},
        )
    res = client.get(f"/users/{user_id}/dashboard")
    txns = res.json()["recent_transactions"]
    assert len(txns) == 3
    assert all(t["account_name"] == account["name"] for t in txns)


def test_dashboard_recent_transactions_capped_at_10(client: TestClient, user_id: str, account: dict):
    for _i in range(15):
        client.post(
            f"/users/{user_id}/transactions",
            json={"kind": "income", "account_id": account["id"], "amount": "10.00", "posted_at": str(TODAY)},
        )
    res = client.get(f"/users/{user_id}/dashboard")
    assert len(res.json()["recent_transactions"]) == 10


def test_dashboard_upcoming_recurring(client: TestClient, user_id: str, account: dict):
    next_week = TODAY + timedelta(days=7)
    client.post(
        f"/users/{user_id}/recurring",
        json={
            "kind": "expense",
            "account_id": account["id"],
            "amount": "50.00",
            "cadence": "monthly",
            "next_run_date": str(next_week),
            "description": "Subscription",
        },
    )
    res = client.get(f"/users/{user_id}/dashboard")
    upcoming = res.json()["upcoming_recurring"]
    assert len(upcoming) == 1
    assert upcoming[0]["account_name"] == account["name"]
    assert upcoming[0]["description"] == "Subscription"


def test_dashboard_upcoming_recurring_excludes_distant(client: TestClient, user_id: str, account: dict):
    far_future = TODAY + timedelta(days=60)
    client.post(
        f"/users/{user_id}/recurring",
        json={
            "kind": "expense",
            "account_id": account["id"],
            "amount": "50.00",
            "cadence": "monthly",
            "next_run_date": str(far_future),
        },
    )
    res = client.get(f"/users/{user_id}/dashboard")
    assert res.json()["upcoming_recurring"] == []
