"""Tests for /users/{user_id}/budgets endpoints."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

BUDGET_PAYLOAD = {"name": "April 2026", "period_start": "2026-04-01", "period_end": "2026-04-30"}


# ---------------------------------------------------------------------------
# POST /users/{user_id}/budgets
# ---------------------------------------------------------------------------


def test_create_budget_returns_201(client: TestClient, user_id: str):
    res = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "April 2026"
    assert data["period_start"] == "2026-04-01"
    assert data["period_end"] == "2026-04-30"
    assert data["user_id"] == user_id
    assert data["is_active"] is True
    assert "id" in data


def test_create_budget_end_before_start_returns_422(client: TestClient, user_id: str):
    res = client.post(
        f"/users/{user_id}/budgets",
        json={"name": "Bad", "period_start": "2026-04-30", "period_end": "2026-04-01"},
    )
    assert res.status_code == 422


def test_create_budget_missing_fields_returns_422(client: TestClient, user_id: str):
    res = client.post(f"/users/{user_id}/budgets", json={"name": "No Dates"})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# GET /users/{user_id}/budgets
# ---------------------------------------------------------------------------


def test_list_budgets_empty(client: TestClient, user_id: str):
    res = client.get(f"/users/{user_id}/budgets")
    assert res.status_code == 200
    assert res.json() == []


def test_list_budgets_returns_own(client: TestClient, user_id: str):
    client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD)
    client.post(
        f"/users/{user_id}/budgets",
        json={"name": "May 2026", "period_start": "2026-05-01", "period_end": "2026-05-31"},
    )
    res = client.get(f"/users/{user_id}/budgets")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_list_budgets_excludes_other_users(client: TestClient, user_id: str):
    client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD)
    other = str(uuid.uuid4())
    client.post(
        f"/users/{other}/budgets",
        json={"name": "Other", "period_start": "2026-06-01", "period_end": "2026-06-30"},
    )
    res = client.get(f"/users/{user_id}/budgets")
    assert all(b["user_id"] == user_id for b in res.json())


# ---------------------------------------------------------------------------
# GET /users/{user_id}/budgets/{budget_id}
# ---------------------------------------------------------------------------


def test_get_budget(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    res = client.get(f"/users/{user_id}/budgets/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_get_budget_wrong_user_returns_404(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    res = client.get(f"/users/{uuid.uuid4()}/budgets/{created['id']}")
    assert res.status_code == 404


def test_get_budget_not_found_returns_404(client: TestClient, user_id: str):
    res = client.get(f"/users/{user_id}/budgets/{uuid.uuid4()}")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}/budgets/{budget_id}
# ---------------------------------------------------------------------------


def test_update_budget_name(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    res = client.patch(f"/users/{user_id}/budgets/{created['id']}", json={"name": "Renamed"})
    assert res.status_code == 200
    assert res.json()["name"] == "Renamed"


def test_update_budget_invalid_period_returns_422(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    res = client.patch(
        f"/users/{user_id}/budgets/{created['id']}",
        json={"period_start": "2026-04-30", "period_end": "2026-04-01"},
    )
    assert res.status_code == 422


def test_update_budget_wrong_user_returns_404(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    res = client.patch(f"/users/{uuid.uuid4()}/budgets/{created['id']}", json={"name": "Stolen"})
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}/budgets/{budget_id}
# ---------------------------------------------------------------------------


def test_delete_budget_returns_204(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    res = client.delete(f"/users/{user_id}/budgets/{created['id']}")
    assert res.status_code == 204


def test_deleted_budget_not_in_list(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    client.delete(f"/users/{user_id}/budgets/{created['id']}")
    ids = [b["id"] for b in client.get(f"/users/{user_id}/budgets").json()]
    assert created["id"] not in ids


def test_deleted_budget_not_retrievable(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    client.delete(f"/users/{user_id}/budgets/{created['id']}")
    res = client.get(f"/users/{user_id}/budgets/{created['id']}")
    assert res.status_code == 404


def test_delete_budget_wrong_user_returns_404(client: TestClient, user_id: str):
    created = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    res = client.delete(f"/users/{uuid.uuid4()}/budgets/{created['id']}")
    assert res.status_code == 404
