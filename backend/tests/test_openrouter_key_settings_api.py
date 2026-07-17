import json
import logging
from unittest.mock import patch

import httpx
import keyring
import pytest

from backend.api.routers import system


SERVICE = "Janus-Projekt"
RAW_ACCOUNT = "openrouter"
STATE_ACCOUNT = "openrouter-validation-state"
SENTINEL_A = "TEST_OPENROUTER_SECRET_ALPHA"
SENTINEL_B = "TEST_OPENROUTER_SECRET_BETA"


class MemoryKeyring:
    def __init__(self):
        self.values = {}
        self.get_calls = []
        self.set_calls = []
        self.delete_calls = []

    def get_password(self, service, account):
        self.get_calls.append((service, account))
        return self.values.get((service, account))

    def set_password(self, service, account, value):
        self.set_calls.append((service, account, value))
        self.values[(service, account)] = value

    def delete_password(self, service, account):
        self.delete_calls.append((service, account))
        try:
            del self.values[(service, account)]
        except KeyError as exc:
            raise keyring.errors.PasswordDeleteError("missing") from exc


class FakeResponse:
    def __init__(self, status_code=200, payload=None, json_error=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"data": {}}
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise self._json_error
        return self._payload


class HttpScenario:
    def __init__(self, response=None, error=None):
        self.response = response or FakeResponse()
        self.error = error
        self.client_kwargs = []
        self.requests = []

    def client_factory(self, **kwargs):
        scenario = self

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, traceback):
                return False

            async def get(self, url, **request_kwargs):
                scenario.requests.append((url, request_kwargs))
                if scenario.error:
                    raise scenario.error
                return scenario.response

        self.client_kwargs.append(kwargs)
        return Client()


@pytest.fixture
def memory_keyring():
    store = MemoryKeyring()
    with patch("backend.api.routers.system.keyring.get_password", side_effect=store.get_password), patch(
        "backend.api.routers.system.keyring.set_password", side_effect=store.set_password
    ), patch("backend.api.routers.system.keyring.delete_password", side_effect=store.delete_password):
        yield store


def install_http(monkeypatch, scenario):
    monkeypatch.setattr(system.httpx, "AsyncClient", scenario.client_factory)
    return scenario


def post_openrouter(test_client, api_key):
    return test_client.post("/api/keys", json={"provider": "openrouter", "api_key": api_key})


def public_openrouter_state(test_client):
    response = test_client.get("/api/keys")
    assert response.status_code == 200
    return response.json()["api_keys"]["openrouter"]


def test_first_save_uses_content_free_official_endpoint_and_returns_valid(
    test_client, memory_keyring, monkeypatch
):
    scenario = install_http(monkeypatch, HttpScenario(FakeResponse(200, {"data": {"label": "ignored"}})))

    response = post_openrouter(test_client, SENTINEL_A)

    assert response.status_code == 200
    assert response.json()["key"] == {"present": True, "masked": "********", "state": "VALID"}
    assert SENTINEL_A not in response.text
    assert memory_keyring.values[(SERVICE, RAW_ACCOUNT)] == SENTINEL_A
    assert SENTINEL_A not in memory_keyring.values[(SERVICE, STATE_ACCOUNT)]
    assert len(scenario.requests) == 1
    url, request_kwargs = scenario.requests[0]
    assert url == "https://openrouter.ai/api/v1/key"
    assert request_kwargs == {
        "headers": {"Authorization": f"Bearer {SENTINEL_A}", "Accept": "application/json"}
    }
    assert scenario.client_kwargs[0]["follow_redirects"] is False
    assert scenario.client_kwargs[0]["trust_env"] is False
    assert isinstance(scenario.client_kwargs[0]["timeout"], httpx.Timeout)


def test_explicit_401_sets_invalid_and_read_is_restart_safe(
    test_client, memory_keyring, monkeypatch
):
    install_http(monkeypatch, HttpScenario(FakeResponse(401, {"error": {}})))

    response = post_openrouter(test_client, SENTINEL_A)

    assert response.status_code == 200
    assert response.json()["key"]["state"] == "INVALID"
    assert public_openrouter_state(test_client) == {
        "present": True,
        "masked": "********",
        "state": "INVALID",
    }


@pytest.mark.parametrize(
    "response,error",
    [
        (FakeResponse(429, {}), None),
        (FakeResponse(500, {}), None),
        (FakeResponse(302, {}), None),
        (FakeResponse(200, {"unexpected": {}}), None),
        (FakeResponse(200, json_error=ValueError("malformed")), None),
        (None, httpx.TimeoutException("timeout")),
        pytest.param(None, httpx.ConnectError("dns resolution failed"), id="dns"),
        pytest.param(None, httpx.ConnectError("tls negotiation failed"), id="tls"),
        pytest.param(None, httpx.NetworkError("network unavailable"), id="network"),
    ],
)
def test_new_key_technical_or_incomplete_validation_is_unverified_without_retry(
    test_client, memory_keyring, monkeypatch, response, error
):
    scenario = install_http(monkeypatch, HttpScenario(response=response, error=error))

    result = post_openrouter(test_client, SENTINEL_A)

    assert result.status_code == 200
    assert result.json()["key"]["state"] == "UNVERIFIED"
    assert memory_keyring.values[(SERVICE, RAW_ACCOUNT)] == SENTINEL_A
    assert len(scenario.requests) == 1


def test_same_exact_previously_valid_key_survives_temporary_validation_failure(
    test_client, memory_keyring, monkeypatch
):
    install_http(monkeypatch, HttpScenario(FakeResponse(200, {"data": {}})))
    assert post_openrouter(test_client, SENTINEL_A).json()["key"]["state"] == "VALID"

    scenario = install_http(
        monkeypatch,
        HttpScenario(error=httpx.TimeoutException("temporary timeout")),
    )
    response = post_openrouter(test_client, SENTINEL_A)

    assert response.status_code == 200
    assert response.json()["key"]["state"] == "VALID"
    assert public_openrouter_state(test_client)["state"] == "VALID"
    assert len(scenario.requests) == 1


def test_same_exact_previously_valid_key_becomes_invalid_on_401(
    test_client, memory_keyring, monkeypatch
):
    install_http(monkeypatch, HttpScenario(FakeResponse(200, {"data": {}})))
    assert post_openrouter(test_client, SENTINEL_A).json()["key"]["state"] == "VALID"

    install_http(monkeypatch, HttpScenario(FakeResponse(401, {})))
    response = post_openrouter(test_client, SENTINEL_A)

    assert response.json()["key"]["state"] == "INVALID"
    assert public_openrouter_state(test_client)["state"] == "INVALID"


def test_replacement_never_inherits_prior_valid_state(test_client, memory_keyring, monkeypatch):
    install_http(monkeypatch, HttpScenario(FakeResponse(200, {"data": {}})))
    assert post_openrouter(test_client, SENTINEL_A).json()["key"]["state"] == "VALID"

    install_http(monkeypatch, HttpScenario(error=httpx.ConnectError("temporary network failure")))
    response = post_openrouter(test_client, SENTINEL_B)

    assert response.json()["key"]["state"] == "UNVERIFIED"
    assert memory_keyring.values[(SERVICE, RAW_ACCOUNT)] == SENTINEL_B
    metadata = json.loads(memory_keyring.values[(SERVICE, STATE_ACCOUNT)])
    assert metadata["state"] == "UNVERIFIED"
    assert SENTINEL_A not in json.dumps(metadata)
    assert SENTINEL_B not in json.dumps(metadata)


def test_missing_or_mismatched_validation_binding_fails_closed(
    test_client, memory_keyring
):
    memory_keyring.values[(SERVICE, RAW_ACCOUNT)] = SENTINEL_A
    assert public_openrouter_state(test_client)["state"] == "UNVERIFIED"

    memory_keyring.values[(SERVICE, STATE_ACCOUNT)] = json.dumps(
        {"version": 1, "key_fingerprint": "0" * 64, "state": "VALID"}
    )
    assert public_openrouter_state(test_client)["state"] == "UNVERIFIED"


def test_delete_removes_only_openrouter_entries(test_client, memory_keyring):
    memory_keyring.values.update(
        {
            (SERVICE, RAW_ACCOUNT): SENTINEL_A,
            (SERVICE, STATE_ACCOUNT): "metadata",
            (SERVICE, "openai"): "OPENAI_SENTINEL",
            (SERVICE, "gemini"): "GEMINI_SENTINEL",
        }
    )
    memory_keyring.get_calls.clear()

    response = test_client.delete("/api/keys/openrouter")

    assert response.status_code == 200
    assert response.json()["key"] == {"present": False, "masked": None, "state": "UNVERIFIED"}
    assert memory_keyring.delete_calls == [(SERVICE, RAW_ACCOUNT), (SERVICE, STATE_ACCOUNT)]
    assert memory_keyring.get_calls == []
    assert memory_keyring.values[(SERVICE, "openai")] == "OPENAI_SENTINEL"
    assert memory_keyring.values[(SERVICE, "gemini")] == "GEMINI_SENTINEL"


def test_openrouter_save_never_reads_or_mutates_other_provider_accounts(
    test_client, memory_keyring, monkeypatch
):
    memory_keyring.values[(SERVICE, "openai")] = "OPENAI_SENTINEL"
    install_http(monkeypatch, HttpScenario(FakeResponse(200, {"data": {}})))
    memory_keyring.get_calls.clear()
    memory_keyring.set_calls.clear()

    response = post_openrouter(test_client, SENTINEL_A)

    assert response.status_code == 200
    touched_accounts = {
        account for _, account in memory_keyring.get_calls
    } | {account for _, account, _ in memory_keyring.set_calls} | {
        account for _, account in memory_keyring.delete_calls
    }
    assert touched_accounts <= {RAW_ACCOUNT, STATE_ACCOUNT}
    assert memory_keyring.values[(SERVICE, "openai")] == "OPENAI_SENTINEL"


def test_failure_response_and_logs_do_not_expose_submitted_key(
    test_client, memory_keyring, monkeypatch, caplog
):
    def fail_set_password(service, account, value):
        raise RuntimeError("credential backend unavailable")

    monkeypatch.setattr(system.keyring, "set_password", fail_set_password)
    caplog.set_level(logging.WARNING, logger="janus_backend")

    response = post_openrouter(test_client, SENTINEL_A)

    assert response.status_code == 500
    assert SENTINEL_A not in response.text
    assert SENTINEL_A not in caplog.text


def test_existing_provider_save_contract_remains_unchanged(test_client, memory_keyring):
    response = test_client.post(
        "/api/keys",
        json={"provider": "openai", "api_key": "OPENAI_SENTINEL"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "API Key saved successfully"}
    assert memory_keyring.values[(SERVICE, "openai")] == "OPENAI_SENTINEL"
