"""Tests for /users/{user_id}/budgets endpoints."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

BUDGET_PAYLOAD = {"period_start": "2026-04-01", "period_end": "2026-04-30"}


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


def test_create_budget_name_defaults_to_month_year(client: TestClient, user_id: str):
    res = client.post(f"/users/{user_id}/budgets", json={"period_start": "2026-06-01", "period_end": "2026-06-30"})
    assert res.status_code == 201
    assert res.json()["name"] == "June 2026"


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
        json={
            "name": "May 2026",
            "period_start": "2026-05-01",
            "period_end": "2026-05-31",
        },
    )
    res = client.get(f"/users/{user_id}/budgets")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_list_budgets_excludes_other_users(client: TestClient, user_id: str):
    client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD)
    other = str(uuid.uuid4())
    client.post(
        f"/users/{other}/budgets",
        json={
            "name": "Other",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
        },
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
    res = client.patch(
        f"/users/{user_id}/budgets/{created['id']}", json={"name": "Renamed"}
    )
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
    res = client.patch(
        f"/users/{uuid.uuid4()}/budgets/{created['id']}", json={"name": "Stolen"}
    )
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


# ---------------------------------------------------------------------------
# POST /users/{user_id}/budgets/{budget_id}/clone
# ---------------------------------------------------------------------------

CLONE_PERIOD = {"period_start": "2026-05-01", "period_end": "2026-05-31"}


def _budget_with_items(client: TestClient, user_id: str) -> tuple[dict, list[dict]]:
    """Create a budget with two items and return (budget, [item, item])."""
    budget = client.post(f"/users/{user_id}/budgets", json=BUDGET_PAYLOAD).json()
    cat1 = client.post(
        f"/users/{user_id}/categories", json={"name": "Groceries"}
    ).json()
    cat2 = client.post(
        f"/users/{user_id}/categories", json={"name": "Transport"}
    ).json()
    item1 = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/items",
        json={"category_id": cat1["id"], "limit_amount": "300.00"},
    ).json()
    item2 = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/items",
        json={"category_id": cat2["id"], "limit_amount": "100.00"},
    ).json()
    return budget, [item1, item2]


def test_clone_budget_returns_201(client: TestClient, user_id: str):
    budget, _ = _budget_with_items(client, user_id)
    res = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/clone", json=CLONE_PERIOD
    )
    assert res.status_code == 201


def test_clone_budget_copies_items(client: TestClient, user_id: str):
    budget, items = _budget_with_items(client, user_id)
    clone = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/clone", json=CLONE_PERIOD
    ).json()
    cloned_items = client.get(f"/users/{user_id}/budgets/{clone['id']}/items").json()
    assert len(cloned_items) == 2
    original_limits = {i["limit_amount"] for i in items}
    cloned_limits = {i["limit_amount"] for i in cloned_items}
    assert original_limits == cloned_limits


def test_clone_budget_sets_source_budget_id(client: TestClient, user_id: str):
    budget, _ = _budget_with_items(client, user_id)
    clone = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/clone", json=CLONE_PERIOD
    ).json()
    assert clone["source_budget_id"] == budget["id"]


def test_clone_budget_inherits_name_when_not_provided(client: TestClient, user_id: str):
    budget, _ = _budget_with_items(client, user_id)
    clone = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/clone", json=CLONE_PERIOD
    ).json()
    assert clone["name"] == "May 2026"


def test_clone_budget_uses_provided_name(client: TestClient, user_id: str):
    budget, _ = _budget_with_items(client, user_id)
    payload = {**CLONE_PERIOD, "name": "May Budget Custom"}
    clone = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/clone", json=payload
    ).json()
    assert clone["name"] == "May Budget Custom"


def test_clone_budget_new_period(client: TestClient, user_id: str):
    budget, _ = _budget_with_items(client, user_id)
    clone = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/clone", json=CLONE_PERIOD
    ).json()
    assert clone["period_start"] == "2026-05-01"
    assert clone["period_end"] == "2026-05-31"


def test_clone_budget_conflict_returns_409(client: TestClient, user_id: str):
    budget, _ = _budget_with_items(client, user_id)
    client.post(f"/users/{user_id}/budgets/{budget['id']}/clone", json=CLONE_PERIOD)
    res = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/clone", json=CLONE_PERIOD
    )
    assert res.status_code == 409


def test_clone_nonexistent_budget_returns_404(client: TestClient, user_id: str):
    res = client.post(
        f"/users/{user_id}/budgets/{uuid.uuid4()}/clone", json=CLONE_PERIOD
    )
    assert res.status_code == 404


def test_clone_budget_wrong_user_returns_404(client: TestClient, user_id: str):
    budget, _ = _budget_with_items(client, user_id)
    res = client.post(
        f"/users/{uuid.uuid4()}/budgets/{budget['id']}/clone", json=CLONE_PERIOD
    )
    assert res.status_code == 404


def test_clone_budget_invalid_period_returns_422(client: TestClient, user_id: str):
    budget, _ = _budget_with_items(client, user_id)
    res = client.post(
        f"/users/{user_id}/budgets/{budget['id']}/clone",
        json={"period_start": "2026-05-31", "period_end": "2026-05-01"},
    )
    assert res.status_code == 422
