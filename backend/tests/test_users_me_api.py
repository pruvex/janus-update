"""Integration tests for GET/PATCH /api/users/me (suggestion_mode)."""

from __future__ import annotations

import pytest

from backend.dependencies import api_key_auth, create_access_token
from backend.main import app
from backend.data.models import User


@pytest.fixture(autouse=True)
def bypass_api_key_auth():
    app.dependency_overrides[api_key_auth] = lambda: None
    yield
    app.dependency_overrides.pop(api_key_auth, None)


def _auth_headers():
    token = create_access_token(
        data={"sub": "local_user", "scopes": ["me", "settings:write"]},
    )
    return {"Authorization": f"Bearer {token}"}


def test_users_me_get_returns_default_suggestion_mode_without_user_row(test_client):
    """No User row: crud defaults to 1."""
    r = test_client.get("/api/users/me", headers=_auth_headers())
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "authenticated"
    assert body["user"] == "local_user"
    assert body["suggestion_mode"] == 1


def test_users_me_patch_cycles_suggestion_mode_0_1_2_persisted_in_db(test_client, db_session):
    """PATCH 0→1→2 updates JSON and SQLite row."""
    headers = {**_auth_headers(), "Content-Type": "application/json"}

    r0 = test_client.patch("/api/users/me", headers=headers, json={"suggestion_mode": 0})
    assert r0.status_code == 200
    assert r0.json()["suggestion_mode"] == 0

    row = db_session.query(User).order_by(User.id.asc()).first()
    assert row is not None
    assert int(row.suggestion_mode) == 0

    r1 = test_client.patch("/api/users/me", headers=headers, json={"suggestion_mode": 1})
    assert r1.status_code == 200
    assert r1.json()["suggestion_mode"] == 1
    db_session.refresh(row)
    assert int(row.suggestion_mode) == 1

    r2 = test_client.patch("/api/users/me", headers=headers, json={"suggestion_mode": 2})
    assert r2.status_code == 200
    assert r2.json()["suggestion_mode"] == 2
    db_session.refresh(row)
    assert int(row.suggestion_mode) == 2

    r_get = test_client.get("/api/users/me", headers=_auth_headers())
    assert r_get.status_code == 200
    assert r_get.json()["suggestion_mode"] == 2


def test_users_me_patch_rejects_invalid_suggestion_mode(test_client):
    headers = {**_auth_headers(), "Content-Type": "application/json"}
    r = test_client.patch("/api/users/me", headers=headers, json={"suggestion_mode": 3})
    assert r.status_code == 422
