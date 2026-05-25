from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def local_test_client():
    with TestClient(app, client=("127.0.0.1", 50000)) as client:
        yield client


def test_mcp_debug_auth_preflight_allows_local_personality_reads(local_test_client, monkeypatch):
    monkeypatch.setenv("NODE_ENV", "development")

    preflight = local_test_client.post(
        "/api/debug/mcp/auth-preflight",
        headers={"Origin": "http://localhost:5173"},
    )

    assert preflight.status_code == 200
    body = preflight.json()
    assert body["token_type"] == "janus_mcp_debug_session"
    assert body["access_token"]
    assert body["debug_session"]
    assert "no-internal-api-key-export" in body["security_boundaries"]
    assert "api_key" not in body

    without_session = local_test_client.get("/api/personalities")
    assert without_session.status_code == 401

    with_session = local_test_client.get(
        "/api/personalities",
        headers={"X-Janus-MCP-Debug-Session": body["debug_session"]},
    )
    assert with_session.status_code == 200

    active = local_test_client.get(
        "/api/personalities/active",
        headers={"X-Janus-MCP-Debug-Session": body["debug_session"]},
    )
    assert active.status_code == 200
    assert "active_personality_id" in active.json()


def test_mcp_debug_auth_preflight_rejects_external_origins(local_test_client, monkeypatch):
    monkeypatch.setenv("NODE_ENV", "development")

    response = local_test_client.post(
        "/api/debug/mcp/auth-preflight",
        headers={"Origin": "https://example.com"},
    )

    assert response.status_code == 403


def test_mcp_debug_session_is_disabled_outside_debug_mode(local_test_client, monkeypatch):
    monkeypatch.delenv("NODE_ENV", raising=False)
    monkeypatch.delenv("JANUS_DEV_MODE", raising=False)
    monkeypatch.delenv("JANUS_ENABLE_DEBUG_ENDPOINTS", raising=False)

    response = local_test_client.post(
        "/api/debug/mcp/auth-preflight",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 403
