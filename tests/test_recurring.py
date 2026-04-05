"""Tests for /users/{user_id}/recurring endpoints."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def account(client: TestClient, user_id: str) -> dict:
    res = client.post(f"/users/{user_id}/accounts", json={"name": "Main", "account_type": "bank"})
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def second_account(client: TestClient, user_id: str) -> dict:
    res = client.post(f"/users/{user_id}/accounts", json={"name": "Savings", "account_type": "bank"})
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def category(client: TestClient, user_id: str) -> dict:
    res = client.post(f"/users/{user_id}/categories", json={"name": "Bills"})
    assert res.status_code == 201
    return res.json()


def _expense_payload(account_id: str, **kwargs) -> dict:
    return {
        "kind": "expense",
        "account_id": account_id,
        "amount": "50.00",
        "cadence": "monthly",
        "next_run_date": "2026-05-01",
        **kwargs,
    }


def _transfer_payload(account_id: str, to_account_id: str, **kwargs) -> dict:
    return {
        "kind": "transfer",
        "account_id": account_id,
        "to_account_id": to_account_id,
        "amount": "200.00",
        "cadence": "monthly",
        "next_run_date": "2026-05-01",
        **kwargs,
    }


# ---------------------------------------------------------------------------
# POST /users/{user_id}/recurring
# ---------------------------------------------------------------------------


def test_create_recurring_expense_returns_201(client: TestClient, user_id: str, account: dict, category: dict):
    res = client.post(
        f"/users/{user_id}/recurring",
        json=_expense_payload(account["id"], category_id=category["id"]),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["kind"] == "expense"
    assert data["account_id"] == account["id"]
    assert data["account_name"] == account["name"]
    assert data["category_id"] == category["id"]
    assert data["category_name"] == category["name"]
    assert data["cadence"] == "monthly"
    assert "id" in data


def test_create_recurring_transfer_returns_201(
    client: TestClient, user_id: str, account: dict, second_account: dict
):
    res = client.post(
        f"/users/{user_id}/recurring",
        json=_transfer_payload(account["id"], second_account["id"]),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["kind"] == "transfer"
    assert data["to_account_id"] == second_account["id"]
    assert data["to_account_name"] == second_account["name"]


def test_create_recurring_transfer_missing_to_account_returns_422(client: TestClient, user_id: str, account: dict):
    res = client.post(
        f"/users/{user_id}/recurring",
        json={
            "kind": "transfer",
            "account_id": account["id"],
            "amount": "10.00",
            "cadence": "monthly",
            "next_run_date": "2026-05-01",
        },
    )
    assert res.status_code == 422


def test_create_recurring_transfer_same_account_returns_422(client: TestClient, user_id: str, account: dict):
    res = client.post(
        f"/users/{user_id}/recurring",
        json=_transfer_payload(account["id"], account["id"]),
    )
    assert res.status_code == 422


def test_create_recurring_end_before_next_run_returns_422(client: TestClient, user_id: str, account: dict):
    res = client.post(
        f"/users/{user_id}/recurring",
        json=_expense_payload(account["id"], next_run_date="2026-05-01", end_date="2026-04-01"),
    )
    assert res.status_code == 422


def test_create_recurring_unknown_account_returns_404(client: TestClient, user_id: str):
    res = client.post(
        f"/users/{user_id}/recurring",
        json=_expense_payload(str(uuid.uuid4())),
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# GET /users/{user_id}/recurring
# ---------------------------------------------------------------------------


def test_list_recurring_empty(client: TestClient, user_id: str):
    res = client.get(f"/users/{user_id}/recurring")
    assert res.status_code == 200
    assert res.json() == []


def test_list_recurring_returns_own(client: TestClient, user_id: str, account: dict):
    client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"]))
    client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"], description="Second"))
    res = client.get(f"/users/{user_id}/recurring")
    assert len(res.json()) == 2


def test_list_recurring_excludes_other_users(client: TestClient, user_id: str, account: dict):
    client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"]))
    other = str(uuid.uuid4())
    other_account = client.post(f"/users/{other}/accounts", json={"name": "Acc", "account_type": "bank"}).json()
    client.post(f"/users/{other}/recurring", json=_expense_payload(other_account["id"]))
    res = client.get(f"/users/{user_id}/recurring")
    assert all(r["user_id"] == user_id for r in res.json())


# ---------------------------------------------------------------------------
# GET /users/{user_id}/recurring/{recurring_id}
# ---------------------------------------------------------------------------


def test_get_recurring(client: TestClient, user_id: str, account: dict):
    created = client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"])).json()
    res = client.get(f"/users/{user_id}/recurring/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_get_recurring_wrong_user_returns_404(client: TestClient, user_id: str, account: dict):
    created = client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"])).json()
    res = client.get(f"/users/{uuid.uuid4()}/recurring/{created['id']}")
    assert res.status_code == 404


def test_get_recurring_not_found_returns_404(client: TestClient, user_id: str):
    res = client.get(f"/users/{user_id}/recurring/{uuid.uuid4()}")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}/recurring/{recurring_id}
# ---------------------------------------------------------------------------


def test_update_recurring_amount(client: TestClient, user_id: str, account: dict):
    created = client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"])).json()
    res = client.patch(f"/users/{user_id}/recurring/{created['id']}", json={"amount": "75.00"})
    assert res.status_code == 200
    assert res.json()["amount"] == "75.00"


def test_update_recurring_cadence(client: TestClient, user_id: str, account: dict):
    created = client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"])).json()
    res = client.patch(f"/users/{user_id}/recurring/{created['id']}", json={"cadence": "weekly"})
    assert res.status_code == 200
    assert res.json()["cadence"] == "weekly"


def test_update_recurring_wrong_user_returns_404(client: TestClient, user_id: str, account: dict):
    created = client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"])).json()
    res = client.patch(f"/users/{uuid.uuid4()}/recurring/{created['id']}", json={"amount": "1.00"})
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}/recurring/{recurring_id}
# ---------------------------------------------------------------------------


def test_delete_recurring_returns_204(client: TestClient, user_id: str, account: dict):
    created = client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"])).json()
    assert client.delete(f"/users/{user_id}/recurring/{created['id']}").status_code == 204


def test_deleted_recurring_not_in_list(client: TestClient, user_id: str, account: dict):
    created = client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"])).json()
    client.delete(f"/users/{user_id}/recurring/{created['id']}")
    ids = [r["id"] for r in client.get(f"/users/{user_id}/recurring").json()]
    assert created["id"] not in ids


def test_delete_recurring_wrong_user_returns_404(client: TestClient, user_id: str, account: dict):
    created = client.post(f"/users/{user_id}/recurring", json=_expense_payload(account["id"])).json()
    res = client.delete(f"/users/{uuid.uuid4()}/recurring/{created['id']}")
    assert res.status_code == 404
