import json
from unittest.mock import patch

import pytest

from backend.llm_providers.codex_app_server import (
    ALLOWED_PUBLIC_STATE_KEYS,
    CodexAppServerError,
    CodexAppServerUnavailableError,
)
from backend.main import app


class FakeCodexLifecycle:
    def __init__(
        self,
        *,
        configured=True,
        public_state=None,
        login_verification_url=None,
        login_user_code="ABCD-EFGH",
        login_error=None,
    ):
        self.configured = configured
        self._public_state = public_state or {
            "connection_state": "disconnected",
            "account_identifier": None,
            "workspace_id": None,
            "workspace_display": None,
            "auth_mode": None,
            "plan_type": None,
            "retry_reason": None,
            "login_pending": False,
            "login_id": None,
            "capabilities": {
                "managed_chatgpt_login": True,
                "keyring_only": True,
                "janus_isolated": True,
            },
        }
        self.login_verification_url = (
            login_verification_url or "https://auth.openai.com/codex/device"
        )
        self.login_user_code = login_user_code
        self.login_error = login_error
        self.read_account_calls = []
        self.cancel_login_calls = []
        self._login_restore_snapshot = None

    def get_public_state(self):
        return dict(self._public_state)

    async def read_account(self, *, refresh_token=False):
        self.read_account_calls.append(refresh_token)
        if self._public_state.get("connection_state") == "raise_on_read":
            raise CodexAppServerUnavailableError("runtime unavailable")
        return self.get_public_state()

    async def start_login(self):
        self._login_restore_snapshot = self.get_public_state()
        if self.login_error is not None:
            raise self.login_error
        self._public_state = {
            **self._public_state,
            "connection_state": "connecting",
            "login_pending": True,
            "login_id": "login-test-1",
        }
        return {
            "login_id": "login-test-1",
            "verification_url": self.login_verification_url,
            "user_code": self.login_user_code,
            "state": self.get_public_state(),
        }

    async def cancel_login(self, login_id=None):
        self.cancel_login_calls.append(login_id)
        self._public_state = self._login_restore_snapshot or {
            **self._public_state,
            "connection_state": "disconnected",
            "login_pending": False,
            "login_id": None,
        }
        self._login_restore_snapshot = None
        return self.get_public_state()

    async def logout(self):
        self._public_state = {
            **self._public_state,
            "connection_state": "disconnected",
            "account_identifier": None,
            "workspace_id": None,
            "workspace_display": None,
            "login_pending": False,
            "login_id": None,
        }
        return self.get_public_state()

    async def retry_after_failure(self):
        self._public_state = {
            **self._public_state,
            "connection_state": "disconnected",
            "retry_reason": None,
        }


@pytest.fixture
def fake_lifecycle():
    lifecycle = FakeCodexLifecycle()
    app.state.codex_app_server = lifecycle
    yield lifecycle
    app.state.codex_app_server = None


def _assert_no_secret_shapes(payload):
    serialized = json.dumps(payload)
    forbidden = (
        "accessToken",
        "refresh_token",
        "api_key",
        "secret-token",
        "Bearer ",
    )
    lowered = serialized.lower()
    for marker in forbidden:
        assert marker.lower() not in lowered
    for key in payload.keys():
        assert key != "authorization"
        assert not key.endswith("_token")


def test_get_codex_connection_refreshes_without_token(fake_lifecycle, test_client):
    fake_lifecycle._public_state["connection_state"] = "connected"
    fake_lifecycle._public_state["account_identifier"] = "user@example.com"

    response = test_client.get("/api/codex-connection")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["codex_connection"]["connection_state"] == "connected"
    assert fake_lifecycle.read_account_calls == [False]
    _assert_no_secret_shapes(body)


def test_get_codex_connection_unconfigured_returns_stable_unavailable(test_client):
    app.state.codex_app_server = None

    response = test_client.get("/api/codex-connection")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["codex_connection"]["connection_state"] == "unavailable"
    assert body["codex_connection"]["retry_reason"] == "codex_connection_unavailable"


def test_get_codex_connection_read_failure_returns_public_state_only(fake_lifecycle, test_client):
    fake_lifecycle._public_state = {
        **fake_lifecycle.get_public_state(),
        "connection_state": "raise_on_read",
        "retry_reason": "runtime_unavailable",
    }

    response = test_client.get("/api/codex-connection")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["status"] == "unavailable"
    assert body["codex_connection"]["retry_reason"] == "runtime_unavailable"
    assert "runtime unavailable" not in json.dumps(body)


def test_start_login_returns_transient_device_code_response_only(fake_lifecycle, test_client):
    response = test_client.post("/api/codex-connection/login")

    assert response.status_code == 200
    body = response.json()
    assert body["verification_url"] == "https://auth.openai.com/codex/device"
    assert body["user_code"] == "ABCD-EFGH"
    assert body["login_id"] == "login-test-1"
    assert body["codex_connection"]["login_pending"] is True
    assert "authorization_url" not in body
    assert "verification_url" not in body["codex_connection"]
    assert "user_code" not in body["codex_connection"]
    _assert_no_secret_shapes(body)


def test_replacement_login_cancel_preserves_prior_janus_connection(fake_lifecycle, test_client):
    fake_lifecycle._public_state = {
        **fake_lifecycle.get_public_state(),
        "connection_state": "connected",
        "account_identifier": "first@example.com",
        "workspace_id": "ws-first",
        "workspace_display": "First workspace",
        "auth_mode": "chatgpt",
    }
    prior_state = fake_lifecycle.get_public_state()

    start = test_client.post("/api/codex-connection/login")
    assert start.status_code == 200
    assert start.json()["codex_connection"]["account_identifier"] == "first@example.com"

    cancel = test_client.post(
        "/api/codex-connection/login/cancel", json={"login_id": "login-test-1"}
    )
    assert cancel.status_code == 200
    assert cancel.json()["codex_connection"] == prior_state


def test_replacement_login_failure_preserves_prior_janus_connection(test_client):
    lifecycle = FakeCodexLifecycle(
        public_state={
            **FakeCodexLifecycle().get_public_state(),
            "connection_state": "connected",
            "account_identifier": "first@example.com",
            "auth_mode": "chatgpt",
        },
        login_error=CodexAppServerUnavailableError("private failure details"),
    )
    app.state.codex_app_server = lifecycle

    response = test_client.post("/api/codex-connection/login")

    assert response.status_code == 503
    assert lifecycle.get_public_state()["account_identifier"] == "first@example.com"
    assert lifecycle.get_public_state()["connection_state"] == "connected"
    assert "private failure details" not in json.dumps(response.json())


def test_cancel_logout_and_retry_routes_dispatch(fake_lifecycle, test_client):
    fake_lifecycle._public_state["login_pending"] = True
    fake_lifecycle._public_state["login_id"] = "login-test-1"

    cancel = test_client.post(
        "/api/codex-connection/login/cancel",
        json={"login_id": "login-test-1"},
    )
    assert cancel.status_code == 200
    assert fake_lifecycle.cancel_login_calls == ["login-test-1"]

    fake_lifecycle._public_state["connection_state"] = "connected"
    logout = test_client.post("/api/codex-connection/logout")
    assert logout.status_code == 200
    assert logout.json()["codex_connection"]["connection_state"] == "disconnected"

    retry = test_client.post("/api/codex-connection/retry")
    assert retry.status_code == 200
    assert retry.json()["codex_connection"]["connection_state"] == "disconnected"


def test_unconfigured_actions_fail_closed(test_client):
    app.state.codex_app_server = FakeCodexLifecycle(configured=False)

    response = test_client.post("/api/codex-connection/login")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["code"] == "codex_connection_unavailable"
    assert detail["codex_connection"]["connection_state"] == "unavailable"


def test_isolation_evidence_pending_blocks_login_with_public_state_only(test_client):
    pending_state = {
        "connection_state": "unavailable",
        "account_identifier": None,
        "workspace_id": None,
        "workspace_display": None,
        "auth_mode": None,
        "plan_type": None,
        "retry_reason": "isolation_evidence_pending",
        "login_pending": False,
        "login_id": None,
        "capabilities": {
            "managed_chatgpt_login": False,
            "keyring_only": True,
            "janus_isolated": False,
        },
    }
    app.state.codex_app_server = FakeCodexLifecycle(
        public_state=pending_state,
        login_error=CodexAppServerUnavailableError("private failure details"),
    )

    response = test_client.post("/api/codex-connection/login")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["code"] == "codex_connection_unavailable"
    assert detail["codex_connection"] == pending_state
    assert "private failure details" not in json.dumps(detail)
    _assert_no_secret_shapes(detail)


def test_secret_shaped_public_values_never_escape_responses(fake_lifecycle, test_client):
    fake_lifecycle._public_state = {
        "connection_state": "connected",
        "account_identifier": "user@example.com",
        "workspace_id": "ws-1",
        "workspace_display": "Default",
        "auth_mode": "chatgpt",
        "plan_type": "plus",
        "retry_reason": None,
        "login_pending": False,
        "login_id": None,
        "capabilities": {"managed_chatgpt_login": True},
        "accessToken": "must-not-leak",
        "refresh_token": "must-not-leak",
        "api_key": "must-not-leak",
    }

    response = test_client.get("/api/codex-connection")
    body = response.json()

    assert set(body["codex_connection"].keys()).issubset(ALLOWED_PUBLIC_STATE_KEYS)
    _assert_no_secret_shapes(body)


def test_codex_routes_do_not_touch_api_key_store(fake_lifecycle, test_client):
    with patch("backend.api.routers.system.keyring.get_password", return_value="masked") as get_password:
        with patch("backend.api.routers.system.keyring.set_password") as set_password:
            keys = test_client.get("/api/keys")
            login = test_client.post("/api/codex-connection/login")

    assert keys.status_code == 200
    assert keys.json()["api_keys"]
    assert login.status_code == 200
    get_password.assert_called()
    set_password.assert_not_called()
