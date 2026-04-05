"""Tests for /users/{user_id}/categories endpoints."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# POST /users/{user_id}/categories
# ---------------------------------------------------------------------------


def test_create_category_returns_201(client: TestClient, user_id: str):
    res = client.post(f"/users/{user_id}/categories", json={"name": "Groceries"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Groceries"
    assert data["user_id"] == user_id
    assert data["is_active"] is True
    assert "id" in data


def test_create_category_name_too_short_returns_422(client: TestClient, user_id: str):
    res = client.post(f"/users/{user_id}/categories", json={"name": ""})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# GET /users/{user_id}/categories
# ---------------------------------------------------------------------------


def test_list_categories_empty(client: TestClient, user_id: str):
    res = client.get(f"/users/{user_id}/categories")
    assert res.status_code == 200
    assert res.json() == []


def test_list_categories_returns_own(client: TestClient, user_id: str):
    client.post(f"/users/{user_id}/categories", json={"name": "Food"})
    client.post(f"/users/{user_id}/categories", json={"name": "Transport"})
    res = client.get(f"/users/{user_id}/categories")
    names = {c["name"] for c in res.json()}
    assert names == {"Food", "Transport"}


def test_list_categories_excludes_other_users(client: TestClient, user_id: str):
    other = str(uuid.uuid4())
    client.post(f"/users/{other}/categories", json={"name": "Other"})
    res = client.get(f"/users/{user_id}/categories")
    assert all(c["user_id"] == user_id for c in res.json())


# ---------------------------------------------------------------------------
# GET /users/{user_id}/categories/{category_id}
# ---------------------------------------------------------------------------


def test_get_category(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/categories", json={"name": "Bills"}).json()
    res = client.get(f"/users/{user_id}/categories/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_get_category_wrong_user_returns_404(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/categories", json={"name": "Bills"}).json()
    res = client.get(f"/users/{uuid.uuid4()}/categories/{created['id']}")
    assert res.status_code == 404


def test_get_category_not_found_returns_404(client: TestClient, user_id: str):
    res = client.get(f"/users/{user_id}/categories/{uuid.uuid4()}")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}/categories/{category_id}
# ---------------------------------------------------------------------------


def test_update_category_name(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/categories", json={"name": "Old"}).json()
    res = client.patch(f"/users/{user_id}/categories/{created['id']}", json={"name": "New"})
    assert res.status_code == 200
    assert res.json()["name"] == "New"


def test_update_category_wrong_user_returns_404(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/categories", json={"name": "Mine"}).json()
    res = client.patch(f"/users/{uuid.uuid4()}/categories/{created['id']}", json={"name": "Stolen"})
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}/categories/{category_id}
# ---------------------------------------------------------------------------


def test_delete_category_returns_204(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/categories", json={"name": "ToDelete"}).json()
    res = client.delete(f"/users/{user_id}/categories/{created['id']}")
    assert res.status_code == 204


def test_deleted_category_not_in_list(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/categories", json={"name": "Gone"}).json()
    client.delete(f"/users/{user_id}/categories/{created['id']}")
    ids = [c["id"] for c in client.get(f"/users/{user_id}/categories").json()]
    assert created["id"] not in ids


def test_deleted_category_not_retrievable(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/categories", json={"name": "Gone"}).json()
    client.delete(f"/users/{user_id}/categories/{created['id']}")
    res = client.get(f"/users/{user_id}/categories/{created['id']}")
    assert res.status_code == 404


def test_delete_wrong_user_returns_404(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/categories", json={"name": "Mine"}).json()
    res = client.delete(f"/users/{uuid.uuid4()}/categories/{created['id']}")
    assert res.status_code == 404
