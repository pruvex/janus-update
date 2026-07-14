import asyncio
import json
from pathlib import Path

import pytest
import pytest_asyncio

from backend.llm_providers.codex_app_server import (
    ALLOWED_PUBLIC_STATE_KEYS,
    CodexAppServerConfigurationError,
    CodexAppServerLifecycle,
    CodexAppServerSettings,
    CodexAppServerTimeoutError,
    CodexAppServerUnavailableError,
    create_codex_app_server_lifecycle,
)
from backend.utils.redaction import REDACTION_TEXT, redact_sensitive_text, redact_sensitive_value


class FakeStream:
    def __init__(self, process, *, outbound):
        self._process = process
        self._outbound = outbound
        self._closed = False
        self._read_queue: asyncio.Queue[bytes] = asyncio.Queue()

    def write(self, data: bytes):
        if not self._outbound:
            payload = data.decode("utf-8").strip()
            if payload:
                asyncio.get_running_loop().create_task(self._process.handle_request(payload))

    async def drain(self):
        return None

    async def readline(self):
        if self._closed and self._read_queue.empty():
            return b""
        return await self._read_queue.get()

    def close(self):
        if not self._closed:
            self._closed = True
            self._read_queue.put_nowait(b"")

    async def push_line(self, line: str):
        await self._read_queue.put((line + "\n").encode("utf-8"))


class FakeCodexProcess:
    def __init__(self, command, env, cwd, *, behavior=None):
        self.command = tuple(command)
        self.env = dict(env)
        self.cwd = cwd
        self.behavior = behavior or {}
        self.returncode = None
        self.requests = []
        self.stdin = FakeStream(self, outbound=False)
        self.stdout = FakeStream(self, outbound=True)
        self.stderr = FakeStream(self, outbound=True)

    async def handle_request(self, payload: str):
        message = json.loads(payload)
        self.requests.append(message)
        method = message.get("method")
        request_id = message.get("id")

        if method in self.behavior.get("drop_methods", set()):
            return
        if method in self.behavior.get("malformed_methods", set()):
            await self.stdout.push_line("not-json accessToken=must-not-leak")
            return
        if method in self.behavior.get("server_request_methods", set()):
            await self.stdout.push_line(
                json.dumps(
                    {
                        "id": 900,
                        "method": "account/chatgptAuthTokens/refresh",
                        "params": {"previousAccountId": "secret-account"},
                    }
                )
            )
            return

        if method == "initialize":
            await self.stdout.push_line(
                json.dumps(
                    {
                        "id": request_id,
                        "result": {
                            "userAgent": "codex-test",
                            "platformFamily": "windows",
                            "platformOs": "windows",
                        },
                    }
                )
            )
            return

        if method == "account/read":
            account_type = self.behavior.get("account_type", "chatgpt")
            await self.stdout.push_line(
                json.dumps(
                    {
                        "id": request_id,
                        "result": {
                            "account": {
                                "type": account_type,
                                "email": "user@example.com",
                                "planType": "plus",
                                "workspace": {"id": "ws-1", "name": "Default"},
                                "accessToken": "secret-token",
                            },
                            "requiresOpenaiAuth": True,
                        },
                    }
                )
            )
            return

        if method == "account/login/start":
            await self.stdout.push_line(
                json.dumps(
                    {
                        "id": request_id,
                        "result": {
                            "type": "chatgpt",
                            "loginId": "login-1",
                            "authUrl": "https://chatgpt.com/auth?code=abc123&state=xyz",
                        },
                    }
                )
            )
            return

        if method in {"account/login/cancel", "account/logout"}:
            await self.stdout.push_line(json.dumps({"id": request_id, "result": {}}))
            return

    def terminate(self):
        self.returncode = 0
        self.stdout.close()
        self.stderr.close()

    def kill(self):
        self.returncode = -9
        self.stdout.close()
        self.stderr.close()

    async def wait(self):
        return self.returncode


class FakeProcessFactory:
    def __init__(self, behavior=None):
        self.behavior = behavior or {}
        self.processes = []

    def __call__(self, command, env, cwd):
        process = FakeCodexProcess(command, env, cwd, behavior=self.behavior)
        self.processes.append(process)
        return process


@pytest.fixture
def codex_paths(tmp_path):
    runtime = (
        tmp_path
        / "node_modules"
        / "@openai"
        / "codex-win32-x64"
        / "vendor"
        / "x86_64-pc-windows-msvc"
        / "bin"
        / "codex.exe"
    )
    runtime.parent.mkdir(parents=True)
    runtime.write_text("stub", encoding="utf-8")
    codex_home = tmp_path / "Janus Projekt" / "codex-home"
    return runtime, codex_home


def make_lifecycle(codex_paths, *, behavior=None, timeout=2.0):
    runtime, codex_home = codex_paths
    settings = CodexAppServerSettings(
        runtime_path=runtime.resolve(),
        codex_home=codex_home.resolve(),
        credentials_store="keyring",
        request_timeout_seconds=timeout,
    )
    factory = FakeProcessFactory(behavior)
    return CodexAppServerLifecycle(settings, process_factory=factory), factory


@pytest_asyncio.fixture
async def lifecycle(codex_paths):
    instance, factory = make_lifecycle(codex_paths)
    try:
        yield instance, factory
    finally:
        await instance.close()


def _environment(runtime: Path, codex_home: Path, store="keyring"):
    return {
        "JANUS_CODEX_RUNTIME_PATH": str(runtime),
        "JANUS_CODEX_HOME": str(codex_home),
        "JANUS_CODEX_CREDENTIALS_STORE": store,
    }


def test_settings_fail_closed_without_explicit_runtime(codex_paths):
    _, codex_home = codex_paths
    env = _environment(Path(""), codex_home)
    env["JANUS_CODEX_RUNTIME_PATH"] = ""
    with pytest.raises(CodexAppServerConfigurationError, match="JANUS_CODEX_RUNTIME_PATH"):
        CodexAppServerSettings.from_environment(env)


def test_settings_reject_non_keyring_store(codex_paths):
    runtime, codex_home = codex_paths
    with pytest.raises(CodexAppServerConfigurationError, match='exactly "keyring"'):
        CodexAppServerSettings.from_environment(_environment(runtime, codex_home, "auto"))


@pytest.mark.asyncio
async def test_direct_settings_cannot_bypass_keyring_requirement(codex_paths):
    runtime, codex_home = codex_paths
    settings = CodexAppServerSettings(
        runtime_path=runtime.resolve(),
        codex_home=codex_home.resolve(),
        credentials_store="auto",
        request_timeout_seconds=2.0,
    )
    instance = CodexAppServerLifecycle(settings, process_factory=FakeProcessFactory())
    with pytest.raises(CodexAppServerConfigurationError, match='exactly "keyring"'):
        await instance.ensure_ready()


def test_settings_reject_shared_or_unpinned_paths(tmp_path, codex_paths):
    runtime, codex_home = codex_paths
    wrong_runtime = tmp_path / "codex.exe"
    wrong_runtime.write_text("stub", encoding="utf-8")
    with pytest.raises(CodexAppServerConfigurationError, match="pinned Windows x64"):
        CodexAppServerSettings.from_environment(_environment(wrong_runtime, codex_home))
    with pytest.raises(CodexAppServerConfigurationError, match="isolated"):
        CodexAppServerSettings.from_environment(_environment(runtime, tmp_path / ".codex"))


@pytest.mark.asyncio
async def test_unconfigured_lifecycle_exposes_fail_closed_state(monkeypatch):
    monkeypatch.delenv("JANUS_CODEX_RUNTIME_PATH", raising=False)
    monkeypatch.delenv("JANUS_CODEX_HOME", raising=False)
    monkeypatch.delenv("JANUS_CODEX_CREDENTIALS_STORE", raising=False)
    instance = create_codex_app_server_lifecycle()
    assert instance.configured is False
    assert instance.get_public_state()["connection_state"] == "unavailable"
    with pytest.raises(CodexAppServerUnavailableError):
        await instance.ensure_ready()


@pytest.mark.asyncio
async def test_lazy_start_reuses_single_process(lifecycle):
    instance, factory = lifecycle
    await instance.read_account()
    await instance.read_account()
    assert len(factory.processes) == 1
    assert instance._process is factory.processes[0]


@pytest.mark.asyncio
async def test_runtime_command_and_environment_are_fail_closed(lifecycle, monkeypatch, codex_paths):
    instance, _ = lifecycle
    runtime, codex_home = codex_paths
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-codex")
    monkeypatch.setenv("CODEX_API_KEY", "must-not-reach-codex")
    await instance.read_account()
    process = instance._process
    assert process.command == (
        str(runtime.resolve()),
        "-c",
        'cli_auth_credentials_store="keyring"',
        "-c",
        'forced_login_method="chatgpt"',
        "--strict-config",
        "app-server",
        "--stdio",
    )
    assert process.env["CODEX_HOME"] == str(codex_home.resolve())
    assert process.cwd == str(codex_home.resolve())
    assert "OPENAI_API_KEY" not in process.env
    assert "CODEX_API_KEY" not in process.env
    assert "PATH" in process.env
    assert all("jsonrpc" not in request for request in process.requests)


@pytest.mark.asyncio
async def test_account_read_exposes_allowlisted_non_secret_state(lifecycle):
    instance, _ = lifecycle
    state = await instance.read_account()
    assert set(state) <= ALLOWED_PUBLIC_STATE_KEYS
    assert state["connection_state"] == "connected"
    assert state["account_identifier"] == "user@example.com"
    assert state["workspace_id"] == "ws-1"
    assert state["workspace_display"] == "Default"
    assert state["auth_mode"] == "chatgpt"
    assert "secret-token" not in json.dumps(state)


@pytest.mark.asyncio
async def test_api_key_account_is_rejected_without_fallback(codex_paths):
    instance, _ = make_lifecycle(codex_paths, behavior={"account_type": "apiKey"})
    try:
        with pytest.raises(CodexAppServerUnavailableError, match="Unsupported"):
            await instance.read_account()
        assert instance.get_public_state()["connection_state"] == "unavailable"
    finally:
        await instance.close()


@pytest.mark.asyncio
async def test_login_url_is_transient_and_cancel_restores_prior_state(lifecycle):
    instance, _ = lifecycle
    before = await instance.read_account()
    login = await instance.start_login()
    assert login["login_id"] == "login-1"
    assert login["auth_url"].startswith("https://chatgpt.com/")
    assert "auth_url" not in login["state"]
    assert "abc123" not in json.dumps(instance.get_public_state())
    after_cancel = await instance.cancel_login()
    assert after_cancel["connection_state"] == before["connection_state"]
    assert after_cancel["account_identifier"] == before["account_identifier"]


@pytest.mark.asyncio
async def test_logout_clears_only_owned_public_state(lifecycle):
    instance, _ = lifecycle
    await instance.read_account()
    state = await instance.logout()
    assert state["connection_state"] == "disconnected"
    assert state["account_identifier"] is None
    assert state["auth_mode"] is None
    assert instance._process.returncode is None
    logout_request = next(
        request
        for request in instance._process.requests
        if request.get("method") == "account/logout"
    )
    assert "params" not in logout_request


@pytest.mark.asyncio
async def test_notification_handlers_receive_only_safe_state(lifecycle):
    instance, _ = lifecycle
    await instance.read_account()
    received = []
    instance.add_notification_handler(received.append)
    await instance._process.stdout.push_line(
        json.dumps(
            {
                "method": "account/updated",
                "params": {"authMode": "chatgpt", "planType": "plus", "accessToken": "secret"},
            }
        )
    )
    await asyncio.sleep(0.02)
    assert received
    assert received[-1]["method"] == "account/updated"
    assert "params" not in received[-1]
    assert "secret" not in json.dumps(received[-1])


@pytest.mark.asyncio
async def test_malformed_message_and_external_token_refresh_fail_closed(codex_paths):
    malformed, _ = make_lifecycle(
        codex_paths,
        behavior={"malformed_methods": {"account/read"}},
    )
    try:
        with pytest.raises(CodexAppServerUnavailableError):
            await malformed.read_account()
        assert malformed.get_public_state()["connection_state"] == "unavailable"
    finally:
        await malformed.close()

    refresh, _ = make_lifecycle(
        codex_paths,
        behavior={"server_request_methods": {"account/read"}},
    )
    try:
        with pytest.raises(CodexAppServerUnavailableError):
            await refresh.read_account()
        assert refresh.get_public_state()["connection_state"] == "unavailable"
    finally:
        await refresh.close()


@pytest.mark.asyncio
async def test_timeout_marks_boundary_unavailable(codex_paths):
    instance, _ = make_lifecycle(
        codex_paths,
        behavior={"drop_methods": {"account/read"}},
        timeout=0.02,
    )
    try:
        with pytest.raises(CodexAppServerTimeoutError):
            await instance.read_account()
        assert instance.get_public_state()["connection_state"] == "unavailable"
    finally:
        await instance.close()


@pytest.mark.asyncio
async def test_crash_retry_and_graceful_shutdown(codex_paths):
    instance, factory = make_lifecycle(codex_paths)
    await instance.read_account()
    first = instance._process
    first.stdout.close()
    await asyncio.sleep(0.02)
    with pytest.raises(CodexAppServerUnavailableError):
        await instance.read_account()
    await instance.retry_after_failure()
    await instance.read_account()
    assert instance._process is not first
    assert len(factory.processes) == 2
    second = instance._process
    await instance.close()
    assert instance._process is None
    assert second.returncode == 0


def test_oauth_url_redaction():
    raw = "https://chatgpt.com/auth?code=abc123&state=secret-state"
    redacted = redact_sensitive_text(raw)
    assert "abc123" not in redacted
    assert "secret-state" not in redacted
    assert REDACTION_TEXT in redacted


def test_structured_oauth_state_redaction_does_not_hide_generic_state():
    redacted = redact_sensitive_value({"state": "ready", "oauth_state": "secret-state"})
    assert redacted["state"] == "ready"
    assert redacted["oauth_state"] == REDACTION_TEXT
