"""Tests for /ui/transactions/{user_id} and /ui/transactions/{user_id}/stats."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

TODAY = "2026-04-24"


@pytest.fixture
def account(client: TestClient, user_id: str) -> dict:
    res = client.post(
        f"/users/{user_id}/accounts", json={"name": "Main", "account_type": "bank"}
    )
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def second_account(client: TestClient, user_id: str) -> dict:
    res = client.post(
        f"/users/{user_id}/accounts", json={"name": "Savings", "account_type": "bank"}
    )
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def category(client: TestClient, user_id: str) -> dict:
    res = client.post(f"/users/{user_id}/categories", json={"name": "Food"})
    assert res.status_code == 201
    return res.json()


# ---------------------------------------------------------------------------
# GET /ui/transactions/{user_id}
# ---------------------------------------------------------------------------


def test_transactions_page_returns_200(client: TestClient, user_id: str):
    res = client.get(f"/ui/transactions/{user_id}")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_transactions_page_contains_form(client: TestClient, user_id: str):
    res = client.get(f"/ui/transactions/{user_id}")
    assert "txn-form" in res.text
    assert "Save Transaction" in res.text


def test_transactions_page_lists_accounts_in_form(
    client: TestClient, user_id: str, account: dict
):
    res = client.get(f"/ui/transactions/{user_id}")
    assert account["name"] in res.text


def test_transactions_page_shows_transaction_log(
    client: TestClient, user_id: str, account: dict
):
    client.post(
        f"/users/{user_id}/transactions",
        json={
            "kind": "expense",
            "account_id": account["id"],
            "amount": "42.00",
            "posted_at": TODAY,
        },
    )
    res = client.get(f"/ui/transactions/{user_id}")
    assert "42" in res.text


def test_transactions_page_renders_with_no_transactions(
    client: TestClient, user_id: str
):
    """Page should render and show empty state message when there are no transactions."""
    res = client.get(f"/ui/transactions/{user_id}")
    assert res.status_code == 200
    assert "No transactions yet" in res.text


# ---------------------------------------------------------------------------
# GET /ui/transactions/{user_id}/stats
# ---------------------------------------------------------------------------


def test_stats_returns_200(client: TestClient, user_id: str):
    res = client.get(f"/ui/transactions/{user_id}/stats")
    assert res.status_code == 200


def test_stats_structure(client: TestClient, user_id: str):
    res = client.get(f"/ui/transactions/{user_id}/stats")
    data = res.json()
    assert "kind_counts" in data
    assert "daily_labels" in data
    assert "daily_data" in data
    assert len(data["daily_labels"]) == 7
    assert len(data["daily_data"]) == 7


def test_stats_kind_counts_reflect_transactions(
    client: TestClient, user_id: str, account: dict, second_account: dict
):
    client.post(
        f"/users/{user_id}/transactions",
        json={
            "kind": "income",
            "account_id": account["id"],
            "amount": "100.00",
            "posted_at": TODAY,
        },
    )
    client.post(
        f"/users/{user_id}/transactions",
        json={
            "kind": "income",
            "account_id": account["id"],
            "amount": "200.00",
            "posted_at": TODAY,
        },
    )
    client.post(
        f"/users/{user_id}/transactions",
        json={
            "kind": "expense",
            "account_id": account["id"],
            "amount": "50.00",
            "posted_at": TODAY,
        },
    )
    client.post(
        f"/users/{user_id}/transactions",
        json={
            "kind": "transfer",
            "account_id": account["id"],
            "to_account_id": second_account["id"],
            "amount": "75.00",
            "posted_at": TODAY,
        },
    )
    data = client.get(f"/ui/transactions/{user_id}/stats").json()
    assert data["kind_counts"].get("income") == 2
    assert data["kind_counts"].get("expense") == 1
    assert data["kind_counts"].get("transfer") == 1
    assert data["kind_counts"].get("refund", 0) == 0


def test_stats_daily_data_counts_todays_transactions(
    client: TestClient, user_id: str, account: dict
):
    for _ in range(3):
        client.post(
            f"/users/{user_id}/transactions",
            json={
                "kind": "expense",
                "account_id": account["id"],
                "amount": "10.00",
                "posted_at": TODAY,
            },
        )
    data = client.get(f"/ui/transactions/{user_id}/stats").json()
    assert sum(data["daily_data"]) >= 3


def test_stats_isolated_per_user(client: TestClient, user_id: str, account: dict):
    """Stats for one user should not include another user's transactions."""
    other_uid = client.post(
        "/users",
        json={
            "name": "Other",
            "email": f"{uuid.uuid4()}@test.com",
        },
    ).json()["id"]

    client.post(
        f"/users/{user_id}/transactions",
        json={
            "kind": "income",
            "account_id": account["id"],
            "amount": "500.00",
            "posted_at": TODAY,
        },
    )

    data = client.get(f"/ui/transactions/{other_uid}/stats").json()
    assert data["kind_counts"].get("income", 0) == 0
