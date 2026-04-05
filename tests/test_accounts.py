"""Tests for /users/{user_id}/accounts endpoints."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# POST /users/{user_id}/accounts
# ---------------------------------------------------------------------------


def test_create_account_returns_201(client: TestClient, user_id: str):
    res = client.post(f"/users/{user_id}/accounts", json={"name": "Checking", "account_type": "bank"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Checking"
    assert data["account_type"] == "bank"
    assert data["user_id"] == user_id
    assert data["is_active"] is True
    assert "id" in data


def test_create_account_default_opening_balance(client: TestClient, user_id: str):
    res = client.post(f"/users/{user_id}/accounts", json={"name": "Wallet", "account_type": "cash"})
    assert res.status_code == 201
    assert res.json()["opening_balance"] == "0.00"


def test_create_account_with_opening_balance(client: TestClient, user_id: str):
    res = client.post(
        f"/users/{user_id}/accounts",
        json={"name": "Savings", "account_type": "bank", "opening_balance": "1500.00"},
    )
    assert res.status_code == 201
    assert res.json()["opening_balance"] == "1500.00"


def test_create_account_unknown_user_still_creates(client: TestClient):
    """Accounts are not yet ownership-verified on create — user_id from path is trusted."""

    fake_user = str(uuid.uuid4())
    res = client.post(f"/users/{fake_user}/accounts", json={"name": "Ghost", "account_type": "other"})
    # Route trusts the user_id path param; 201 is expected behaviour until auth is added.
    assert res.status_code == 201


# ---------------------------------------------------------------------------
# GET /users/{user_id}/accounts
# ---------------------------------------------------------------------------


def test_list_accounts_empty(client: TestClient, user_id: str):
    res = client.get(f"/users/{user_id}/accounts")
    assert res.status_code == 200
    assert res.json() == []


def test_list_accounts_returns_own_accounts(client: TestClient, user_id: str):
    client.post(f"/users/{user_id}/accounts", json={"name": "A", "account_type": "cash"})
    client.post(f"/users/{user_id}/accounts", json={"name": "B", "account_type": "bank"})
    res = client.get(f"/users/{user_id}/accounts")
    assert res.status_code == 200
    names = {a["name"] for a in res.json()}
    assert names == {"A", "B"}


def test_list_accounts_excludes_other_users(client: TestClient, user_id: str):

    other = str(uuid.uuid4())
    client.post(f"/users/{other}/accounts", json={"name": "Other", "account_type": "cash"})
    res = client.get(f"/users/{user_id}/accounts")
    assert all(a["user_id"] == user_id for a in res.json())


# ---------------------------------------------------------------------------
# GET /users/{user_id}/accounts/{account_id}
# ---------------------------------------------------------------------------


def test_get_account(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/accounts", json={"name": "Card", "account_type": "card"}).json()
    res = client.get(f"/users/{user_id}/accounts/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_get_account_wrong_user_returns_404(client: TestClient, user_id: str):

    created = client.post(f"/users/{user_id}/accounts", json={"name": "Card", "account_type": "card"}).json()
    wrong_user = str(uuid.uuid4())
    res = client.get(f"/users/{wrong_user}/accounts/{created['id']}")
    assert res.status_code == 404


def test_get_account_not_found_returns_404(client: TestClient, user_id: str):

    res = client.get(f"/users/{user_id}/accounts/{uuid.uuid4()}")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}/accounts/{account_id}
# ---------------------------------------------------------------------------


def test_update_account_name(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/accounts", json={"name": "Old", "account_type": "cash"}).json()
    res = client.patch(f"/users/{user_id}/accounts/{created['id']}", json={"name": "New"})
    assert res.status_code == 200
    assert res.json()["name"] == "New"


def test_update_account_wrong_user_returns_404(client: TestClient, user_id: str):

    created = client.post(f"/users/{user_id}/accounts", json={"name": "Mine", "account_type": "cash"}).json()
    res = client.patch(f"/users/{uuid.uuid4()}/accounts/{created['id']}", json={"name": "Stolen"})
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}/accounts/{account_id}
# ---------------------------------------------------------------------------


def test_delete_account_returns_204(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/accounts", json={"name": "ToDelete", "account_type": "cash"}).json()
    res = client.delete(f"/users/{user_id}/accounts/{created['id']}")
    assert res.status_code == 204


def test_deleted_account_not_in_list(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/accounts", json={"name": "Gone", "account_type": "cash"}).json()
    client.delete(f"/users/{user_id}/accounts/{created['id']}")
    ids = [a["id"] for a in client.get(f"/users/{user_id}/accounts").json()]
    assert created["id"] not in ids


def test_deleted_account_not_retrievable(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/accounts", json={"name": "Gone", "account_type": "cash"}).json()
    client.delete(f"/users/{user_id}/accounts/{created['id']}")
    res = client.get(f"/users/{user_id}/accounts/{created['id']}")
    assert res.status_code == 404


def test_delete_wrong_user_returns_404(client: TestClient, user_id: str):

    created = client.post(f"/users/{user_id}/accounts", json={"name": "Mine", "account_type": "cash"}).json()
    res = client.delete(f"/users/{uuid.uuid4()}/accounts/{created['id']}")
    assert res.status_code == 404
