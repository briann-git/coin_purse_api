"""Tests for /users endpoints."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# POST /users
# ---------------------------------------------------------------------------


def test_create_user_returns_201(client: TestClient):
    res = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "password_hash" not in data


def test_create_user_with_phone(client: TestClient):
    res = client.post(
        "/users",
        json={"name": "Bob", "email": "bob@example.com", "phone": "+1234567890"},
    )
    assert res.status_code == 201
    assert res.json()["phone"] == "+1234567890"


def test_create_user_duplicate_email_returns_400(client: TestClient):
    payload = {"name": "Alice", "email": "dup@example.com"}
    assert client.post("/users", json=payload).status_code == 201
    assert client.post("/users", json=payload).status_code == 400


def test_create_user_invalid_email_returns_422(client: TestClient):
    res = client.post("/users", json={"name": "A", "email": "not-an-email"})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------


def test_list_users_includes_created(client: TestClient, user: dict):
    res = client.get("/users")
    assert res.status_code == 200
    ids = [u["id"] for u in res.json()]
    assert user["id"] in ids


# ---------------------------------------------------------------------------
# GET /users/{user_id}
# ---------------------------------------------------------------------------


def test_get_user(client: TestClient, user: dict):
    res = client.get(f"/users/{user['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == user["id"]


def test_get_user_not_found_returns_404(client: TestClient):
    res = client.get(f"/users/{uuid.uuid4()}")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}
# ---------------------------------------------------------------------------


def test_update_user_name(client: TestClient, user: dict):
    res = client.patch(f"/users/{user['id']}", json={"name": "Updated Name"})
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Name"


def test_update_user_not_found_returns_404(client: TestClient):
    res = client.patch(f"/users/{uuid.uuid4()}", json={"name": "Ghost"})
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}
# ---------------------------------------------------------------------------


def test_delete_user_returns_204(client: TestClient, user: dict):
    res = client.delete(f"/users/{user['id']}")
    assert res.status_code == 204


def test_deleted_user_not_retrievable(client: TestClient, user: dict):
    client.delete(f"/users/{user['id']}")
    res = client.get(f"/users/{user['id']}")
    assert res.status_code == 404
