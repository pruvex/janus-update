"""Janus-owned lifecycle boundary for the official Codex App Server."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import re
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from backend.utils.redaction import REDACTION_TEXT, redact_sensitive_text

logger = logging.getLogger(__name__)

CLIENT_NAME = "janus_backend"
CLIENT_TITLE = "Janus Backend"
CLIENT_VERSION = "1.0.0"
EXPECTED_RUNTIME_TAIL = ("vendor", "x86_64-pc-windows-msvc", "bin", "codex.exe")
EXPECTED_HOME_TAIL = ("janus projekt", "codex-home")
PROCESS_LINE_LIMIT = 1024 * 1024
CREATE_NO_WINDOW = 0x08000000
MANAGED_AUTH_MODE = "chatgpt"
MANAGED_LOGIN_TYPE = "chatgptDeviceCode"
OFFICIAL_DEVICE_VERIFICATION_URL = "https://auth.openai.com/codex/device"
DEVICE_USER_CODE_PATTERN = re.compile(r"[A-Za-z0-9-]{3,128}")
PINNED_CODEX_AUTH_NAMESPACE_VERSION = "0.144.4"
REQUIRED_ISOLATION_EVIDENCE_REVISION = (
    "TASK-CHATGPT-DEVICE-CODE-PROVIDER.5/codex-0.144.4-device-code-keyring-v1"
)
# This remains unset until the controlled two-account evidence has actually passed.
# It is deliberately source-bound: environment variables, API payloads and Settings
# cannot turn the production isolation claim on.
PRODUCTION_ISOLATION_EVIDENCE_REVISION: str | None = None
ISOLATION_EVIDENCE_PENDING_REASON = "isolation_evidence_pending"

_REMOVED_AUTH_ENV_KEYS = (
    "OPENAI_API_KEY",
    "CODEX_API_KEY",
    "OPENAI_BASE_URL",
    "AZURE_OPENAI_API_KEY",
)

ALLOWED_PUBLIC_STATE_KEYS = frozenset(
    {
        "connection_state",
        "account_identifier",
        "workspace_id",
        "workspace_display",
        "auth_mode",
        "plan_type",
        "retry_reason",
        "login_pending",
        "login_id",
        "capabilities",
    }
)

ACCOUNT_NOTIFICATION_METHODS = frozenset(
    {
        "account/updated",
        "account/login/completed",
        "account/rateLimits/updated",
    }
)


class CodexAppServerError(Exception):
    """Base error for the Codex App Server boundary."""


class CodexAppServerConfigurationError(CodexAppServerError):
    """Raised when required runtime configuration is missing or unsafe."""


class CodexAppServerUnavailableError(CodexAppServerError):
    """Raised when the boundary is unavailable and must fail closed."""


class CodexAppServerProtocolError(CodexAppServerError):
    """Raised when JSON-RPC protocol handling fails."""


class CodexAppServerTimeoutError(CodexAppServerError):
    """Raised when a request exceeds the configured timeout."""


def _normalized_tail(path: Path, size: int) -> tuple[str, ...]:
    return tuple(part.lower() for part in path.parts[-size:])


def _validate_settings_paths(runtime_path: Path, codex_home: Path) -> tuple[Path, Path]:
    if not runtime_path.is_absolute():
        raise CodexAppServerConfigurationError("The bundled Codex runtime path must be absolute.")
    if not codex_home.is_absolute():
        raise CodexAppServerConfigurationError("The Janus Codex home path must be absolute.")

    try:
        resolved_runtime = runtime_path.resolve(strict=True)
    except OSError as exc:
        raise CodexAppServerConfigurationError("The bundled Codex runtime is unavailable.") from exc
    if not resolved_runtime.is_file():
        raise CodexAppServerConfigurationError("The bundled Codex runtime is not a file.")
    if _normalized_tail(resolved_runtime, len(EXPECTED_RUNTIME_TAIL)) != EXPECTED_RUNTIME_TAIL:
        raise CodexAppServerConfigurationError(
            "The Codex runtime must use the pinned Windows x64 vendor path."
        )

    resolved_home = codex_home.resolve()
    if _normalized_tail(resolved_home, len(EXPECTED_HOME_TAIL)) != EXPECTED_HOME_TAIL:
        raise CodexAppServerConfigurationError(
            "JANUS_CODEX_HOME must end with the isolated 'Janus Projekt/codex-home' namespace."
        )
    default_codex_home = (Path.home() / ".codex").resolve()
    if resolved_home == default_codex_home:
        raise CodexAppServerConfigurationError("The shared default Codex home is forbidden.")
    return resolved_runtime, resolved_home


@dataclass(frozen=True)
class CodexAppServerSettings:
    runtime_path: Path
    codex_home: Path
    credentials_store: str
    request_timeout_seconds: float = 30.0

    @classmethod
    def from_environment(
        cls,
        environ: dict[str, str] | os._Environ[str] | None = None,
    ) -> CodexAppServerSettings:
        source = os.environ if environ is None else environ
        runtime_raw = str(source.get("JANUS_CODEX_RUNTIME_PATH", "")).strip()
        codex_home_raw = str(source.get("JANUS_CODEX_HOME", "")).strip()
        credentials_store = str(source.get("JANUS_CODEX_CREDENTIALS_STORE", "")).strip().lower()

        if not runtime_raw:
            raise CodexAppServerConfigurationError(
                "JANUS_CODEX_RUNTIME_PATH is required for the bundled Codex runtime."
            )
        if not codex_home_raw:
            raise CodexAppServerConfigurationError(
                "JANUS_CODEX_HOME is required for Janus-only account isolation."
            )
        if credentials_store != "keyring":
            raise CodexAppServerConfigurationError(
                'JANUS_CODEX_CREDENTIALS_STORE must be exactly "keyring".'
            )

        runtime_path, codex_home = _validate_settings_paths(
            Path(runtime_raw),
            Path(codex_home_raw),
        )
        return cls(
            runtime_path=runtime_path,
            codex_home=codex_home,
            credentials_store=credentials_store,
        )


@dataclass
class CodexAccountPublicState:
    connection_state: str = "unavailable"
    account_identifier: str | None = None
    workspace_id: str | None = None
    workspace_display: str | None = None
    auth_mode: str | None = None
    plan_type: str | None = None
    retry_reason: str | None = None
    login_pending: bool = False
    login_id: str | None = None
    capabilities: dict[str, bool] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        payload = {
            "connection_state": self.connection_state,
            "account_identifier": self.account_identifier,
            "workspace_id": self.workspace_id,
            "workspace_display": self.workspace_display,
            "auth_mode": self.auth_mode,
            "plan_type": self.plan_type,
            "retry_reason": self.retry_reason,
            "login_pending": self.login_pending,
            "login_id": self.login_id,
            "capabilities": dict(self.capabilities),
        }
        return {key: value for key, value in payload.items() if key in ALLOWED_PUBLIC_STATE_KEYS}


def _configured_capabilities(*, isolation_verified: bool) -> dict[str, bool]:
    return {
        "managed_chatgpt_login": isolation_verified,
        "keyring_only": True,
        "janus_isolated": isolation_verified,
    }


def _unavailable_capabilities() -> dict[str, bool]:
    return {
        "managed_chatgpt_login": False,
        "keyring_only": False,
        "janus_isolated": False,
    }


def _production_isolation_evidence_verified() -> bool:
    """Bind production enablement to the reviewed pin and evidence revision."""

    return (
        PINNED_CODEX_AUTH_NAMESPACE_VERSION == "0.144.4"
        and PRODUCTION_ISOLATION_EVIDENCE_REVISION == REQUIRED_ISOLATION_EVIDENCE_REVISION
    )


def _is_official_device_verification_url(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname == "auth.openai.com"
        and port in {None, 443}
        and parsed.username is None
        and parsed.password is None
        and parsed.path == "/codex/device"
        and not parsed.query
        and not parsed.fragment
    )


def _is_valid_device_user_code(value: Any) -> bool:
    return isinstance(value, str) and DEVICE_USER_CODE_PATTERN.fullmatch(value) is not None


def _sanitize_public_account(
    account: dict[str, Any] | None,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    if not account:
        return None, None, None, None, None

    account_type = account.get("type")
    auth_mode = account_type if isinstance(account_type, str) else None
    plan_type = account.get("planType") if isinstance(account.get("planType"), str) else None

    identifier = None
    email = account.get("email")
    account_id = account.get("accountId") or account.get("id")
    if isinstance(email, str) and email:
        identifier = email
    elif isinstance(account_id, str) and account_id:
        identifier = account_id

    workspace = account.get("workspace") if isinstance(account.get("workspace"), dict) else {}
    workspace_id = workspace.get("id") if isinstance(workspace.get("id"), str) else None
    workspace_display = workspace.get("name") if isinstance(workspace.get("name"), str) else None
    if workspace_display is None and isinstance(workspace.get("displayName"), str):
        workspace_display = workspace.get("displayName")

    return identifier, workspace_id, workspace_display, auth_mode, plan_type


class CodexAppServerLifecycle:
    """Own one lazy App Server process and expose only managed-account state."""

    def __init__(
        self,
        settings: CodexAppServerSettings | None,
        *,
        configuration_error: str | None = None,
        process_factory: Callable[..., Any] | None = None,
        _isolation_evidence_verified: bool = False,
    ) -> None:
        self.settings = settings
        self._isolation_evidence_verified = bool(_isolation_evidence_verified)
        self._configuration_error = redact_sensitive_text(configuration_error or "") or None
        self._process_factory = process_factory
        self._process: asyncio.subprocess.Process | Any | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._next_request_id = 1
        self._pending: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._lifecycle_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._initialized = False
        self._crashed = False
        self._closing = False
        self._notification_handlers: list[Callable[[dict[str, Any]], None]] = []
        self._login_restore_snapshot: dict[str, Any] | None = None
        self._transient_login_secrets: tuple[str, ...] = ()
        if settings is None:
            self._public_state = CodexAccountPublicState(
                connection_state="unavailable",
                retry_reason=self._configuration_error or "Codex App Server is not configured.",
                capabilities=_unavailable_capabilities(),
            )
        elif self._isolation_evidence_verified:
            self._public_state = CodexAccountPublicState(
                connection_state="disconnected",
                capabilities=_configured_capabilities(isolation_verified=True),
            )
        else:
            self._public_state = CodexAccountPublicState(
                connection_state="unavailable",
                retry_reason=ISOLATION_EVIDENCE_PENDING_REASON,
                capabilities=_configured_capabilities(isolation_verified=False),
            )

    @property
    def configured(self) -> bool:
        return self.settings is not None

    @property
    def public_state(self) -> CodexAccountPublicState:
        return self._public_state

    def get_public_state(self) -> dict[str, Any]:
        return self._public_state.to_public_dict()

    def _restore_public_state(self, snapshot: dict[str, Any]) -> None:
        self._public_state = CodexAccountPublicState(
            connection_state=snapshot.get("connection_state", "disconnected"),
            account_identifier=snapshot.get("account_identifier"),
            workspace_id=snapshot.get("workspace_id"),
            workspace_display=snapshot.get("workspace_display"),
            auth_mode=snapshot.get("auth_mode"),
            plan_type=snapshot.get("plan_type"),
            retry_reason=snapshot.get("retry_reason"),
            login_pending=bool(snapshot.get("login_pending")),
            login_id=snapshot.get("login_id"),
            capabilities=dict(
                snapshot.get("capabilities")
                or _configured_capabilities(
                    isolation_verified=self._isolation_evidence_verified,
                )
            ),
        )

    def add_notification_handler(self, handler: Callable[[dict[str, Any]], None]) -> None:
        self._notification_handlers.append(handler)

    async def ensure_ready(self) -> None:
        if self.settings is None:
            raise CodexAppServerUnavailableError(
                self._configuration_error or "Codex App Server is not configured."
            )
        if not self._isolation_evidence_verified:
            raise CodexAppServerUnavailableError(ISOLATION_EVIDENCE_PENDING_REASON)
        async with self._lifecycle_lock:
            if self._crashed:
                raise CodexAppServerUnavailableError(
                    self._public_state.retry_reason or "Codex App Server is unavailable after a failure."
                )
            if self._process is None or self._process.returncode is not None:
                await self._start_locked()
            if not self._initialized:
                await self._initialize_locked()

    async def read_account(self, *, refresh_token: bool = False) -> dict[str, Any]:
        await self.ensure_ready()
        result = await self._request("account/read", {"refreshToken": bool(refresh_token)})
        self._apply_account_result(result)
        return self.get_public_state()

    async def list_models(self) -> list[dict[str, str]]:
        """Return only current, public model metadata for this Janus-owned session."""

        await self.read_account(refresh_token=False)
        if (
            self._public_state.connection_state != "connected"
            or self._public_state.auth_mode != MANAGED_AUTH_MODE
        ):
            return []

        result = await self._request("model/list", {"includeHidden": False})
        models = result.get("models")
        if not isinstance(models, list):
            raise CodexAppServerProtocolError("Codex App Server model list is unsupported.")

        public_models: list[dict[str, str]] = []
        for model in models:
            if not isinstance(model, dict) or model.get("hidden") is True:
                continue
            model_id = model.get("id")
            if not isinstance(model_id, str) or not model_id.strip():
                continue
            display_name = model.get("displayName")
            public_models.append(
                {
                    "id": model_id.strip(),
                    "name": display_name.strip()
                    if isinstance(display_name, str) and display_name.strip()
                    else model_id.strip(),
                    "provider": "chatgpt",
                    "type": "text",
                }
            )
        return public_models

    async def start_login(self) -> dict[str, Any]:
        await self.ensure_ready()
        self._login_restore_snapshot = self.get_public_state()
        try:
            result = await self._request("account/login/start", {"type": MANAGED_LOGIN_TYPE})
            login_id = result.get("loginId")
            verification_url = result.get("verificationUrl")
            user_code = result.get("userCode")
            if result.get("type") != MANAGED_LOGIN_TYPE:
                raise CodexAppServerProtocolError(
                    "Managed ChatGPT device-code login returned an unexpected type."
                )
            if not isinstance(login_id, str) or not login_id:
                raise CodexAppServerProtocolError(
                    "Managed ChatGPT device-code login did not return a login id."
                )
            if not _is_official_device_verification_url(verification_url):
                raise CodexAppServerProtocolError(
                    "Managed ChatGPT device-code login returned an unsupported verification URL."
                )
            if not _is_valid_device_user_code(user_code):
                raise CodexAppServerProtocolError(
                    "Managed ChatGPT device-code login returned an invalid user code."
                )
        except (CodexAppServerError, asyncio.CancelledError):
            self._transient_login_secrets = ()
            if self._login_restore_snapshot is not None:
                self._restore_public_state(self._login_restore_snapshot)
                self._login_restore_snapshot = None
            raise

        self._transient_login_secrets = (user_code, verification_url)
        self._public_state.login_id = login_id
        self._public_state.login_pending = True
        self._public_state.connection_state = "connecting"
        self._public_state.retry_reason = None
        logger.info(
            "Codex managed ChatGPT device-code login started; one-time values omitted from logs."
        )
        return {
            "login_id": login_id,
            "verification_url": verification_url,
            "user_code": user_code,
            "state": self.get_public_state(),
        }

    async def cancel_login(self, login_id: str | None = None) -> dict[str, Any]:
        await self.ensure_ready()
        target_login_id = login_id or self._public_state.login_id
        if not target_login_id:
            raise CodexAppServerProtocolError("No pending managed login to cancel.")

        await self._request("account/login/cancel", {"loginId": target_login_id})
        self._transient_login_secrets = ()
        if self._login_restore_snapshot is not None:
            self._restore_public_state(self._login_restore_snapshot)
            self._login_restore_snapshot = None
        else:
            self._public_state.login_pending = False
            self._public_state.login_id = None
        return self.get_public_state()

    async def logout(self) -> dict[str, Any]:
        await self.ensure_ready()
        await self._request("account/logout", None)
        self._transient_login_secrets = ()
        self._public_state = CodexAccountPublicState(
            connection_state="disconnected",
            capabilities=_configured_capabilities(
                isolation_verified=self._isolation_evidence_verified,
            ),
        )
        self._login_restore_snapshot = None
        return self.get_public_state()

    async def retry_after_failure(self) -> None:
        if self.settings is None:
            raise CodexAppServerUnavailableError(
                self._configuration_error or "Codex App Server is not configured."
            )
        if not self._isolation_evidence_verified:
            raise CodexAppServerUnavailableError(ISOLATION_EVIDENCE_PENDING_REASON)
        async with self._lifecycle_lock:
            await self._shutdown_locked()
            self._crashed = False
            self._transient_login_secrets = ()
            self._public_state = CodexAccountPublicState(
                connection_state="disconnected",
                capabilities=_configured_capabilities(
                    isolation_verified=self._isolation_evidence_verified,
                ),
            )

    async def close(self) -> None:
        async with self._lifecycle_lock:
            await self._shutdown_locked()

    def _build_command(self) -> tuple[str, ...]:
        assert self.settings is not None
        return (
            str(self.settings.runtime_path),
            "-c",
            'cli_auth_credentials_store="keyring"',
            "-c",
            'forced_login_method="chatgpt"',
            "--strict-config",
            "app-server",
            "--stdio",
        )

    def _build_subprocess_environment(self) -> dict[str, str]:
        assert self.settings is not None
        env = os.environ.copy()
        env["CODEX_HOME"] = str(self.settings.codex_home)
        for key in _REMOVED_AUTH_ENV_KEYS:
            env.pop(key, None)
        return env

    async def _start_locked(self) -> None:
        assert self.settings is not None
        if self.settings.credentials_store != "keyring":
            raise CodexAppServerConfigurationError(
                'Codex credentials_store must be exactly "keyring".'
            )
        runtime_path, codex_home = _validate_settings_paths(
            self.settings.runtime_path,
            self.settings.codex_home,
        )
        codex_home.mkdir(parents=True, exist_ok=True)
        command = self._build_command()
        env = self._build_subprocess_environment()
        logger.info("Starting the explicit Janus-managed Codex App Server runtime.")

        if self._process_factory is not None:
            created = self._process_factory(command=command, env=env, cwd=str(codex_home))
            self._process = await created if inspect.isawaitable(created) else created
        else:
            kwargs: dict[str, Any] = {
                "stdin": asyncio.subprocess.PIPE,
                "stdout": asyncio.subprocess.PIPE,
                "stderr": asyncio.subprocess.PIPE,
                "env": env,
                "cwd": str(codex_home),
                "limit": PROCESS_LINE_LIMIT,
            }
            if os.name == "nt":
                kwargs["creationflags"] = CREATE_NO_WINDOW
            try:
                self._process = await asyncio.create_subprocess_exec(
                    str(runtime_path),
                    *command[1:],
                    **kwargs,
                )
            except (NotImplementedError, OSError) as exc:
                await self._mark_process_crashed(
                    "Codex App Server subprocess support is unavailable in this runtime."
                )
                raise CodexAppServerUnavailableError(
                    "Codex App Server subprocess could not be started."
                ) from exc

        if self._process is None or self._process.stdin is None or self._process.stdout is None:
            raise CodexAppServerUnavailableError("Codex App Server did not provide stdio pipes.")
        self._closing = False
        self._reader_task = asyncio.create_task(self._read_stdout_loop())
        self._stderr_task = asyncio.create_task(self._read_stderr_loop())
        self._public_state.connection_state = "disconnected"
        self._public_state.retry_reason = None

    async def _initialize_locked(self) -> None:
        result = await self._request(
            "initialize",
            {
                "clientInfo": {
                    "name": CLIENT_NAME,
                    "title": CLIENT_TITLE,
                    "version": CLIENT_VERSION,
                }
            },
            require_ready=False,
        )
        if not isinstance(result.get("userAgent"), str):
            await self._mark_process_crashed("Codex App Server initialize response is unsupported.")
            raise CodexAppServerProtocolError("Unsupported Codex App Server initialize response.")
        await self._send_notification("initialized", None)
        self._initialized = True

    async def _request(
        self,
        method: str,
        params: dict[str, Any] | None,
        *,
        require_ready: bool = True,
    ) -> dict[str, Any]:
        if require_ready and (self._process is None or self._process.stdin is None):
            raise CodexAppServerUnavailableError("Codex App Server process is not running.")

        request_id = self._next_request_id
        self._next_request_id += 1
        payload: dict[str, Any] = {"method": method, "id": request_id}
        if params is not None:
            payload["params"] = params
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        try:
            await self._send_payload(payload)
            return await asyncio.wait_for(
                asyncio.shield(future),
                timeout=self.settings.request_timeout_seconds if self.settings else 30.0,
            )
        except asyncio.TimeoutError as exc:
            if not future.done():
                future.cancel()
            await self._mark_process_crashed(f"Codex App Server request timed out: {method}.")
            raise CodexAppServerTimeoutError(f"Timed out waiting for {method}.") from exc
        finally:
            self._pending.pop(request_id, None)

    async def _send_notification(
        self,
        method: str,
        params: dict[str, Any] | None,
    ) -> None:
        payload: dict[str, Any] = {"method": method}
        if params is not None:
            payload["params"] = params
        await self._send_payload(payload)

    async def _send_payload(self, payload: dict[str, Any]) -> None:
        if self._process is None or self._process.stdin is None:
            raise CodexAppServerUnavailableError("Codex App Server stdin is unavailable.")
        line = json.dumps(payload, separators=(",", ":")) + "\n"
        async with self._write_lock:
            try:
                self._process.stdin.write(line.encode("utf-8"))
                await self._process.stdin.drain()
            except (BrokenPipeError, ConnectionError, OSError) as exc:
                await self._mark_process_crashed("Codex App Server stdin closed unexpectedly.")
                raise CodexAppServerUnavailableError("Codex App Server write failed.") from exc

    async def _read_stdout_loop(self) -> None:
        assert self._process is not None
        assert self._process.stdout is not None
        while True:
            try:
                line = await self._process.stdout.readline()
            except (ValueError, OSError) as exc:
                await self._mark_process_crashed("Codex App Server emitted an oversized or invalid frame.")
                logger.warning("Codex App Server protocol frame rejected: %s", type(exc).__name__)
                return
            if not line:
                break
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            try:
                message = json.loads(text)
            except json.JSONDecodeError:
                await self._mark_process_crashed("Codex App Server emitted malformed JSON.")
                logger.warning("Codex App Server malformed JSON rejected; payload omitted.")
                return
            if not isinstance(message, dict):
                await self._mark_process_crashed("Codex App Server emitted a non-object frame.")
                return
            await self._dispatch_message(message)
            if self._crashed:
                return

        if not self._closing:
            await self._mark_process_crashed("Codex App Server stdout closed unexpectedly.")

    async def _read_stderr_loop(self) -> None:
        assert self._process is not None
        if self._process.stderr is None:
            return
        while True:
            line = await self._process.stderr.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").strip()
            if text:
                logger.warning("Codex App Server diagnostic: %s", self._redact_runtime_text(text))

    def _redact_runtime_text(self, value: Any) -> str:
        text = str(value)
        for secret in sorted(self._transient_login_secrets, key=len, reverse=True):
            if secret:
                text = text.replace(secret, REDACTION_TEXT)
        return redact_sensitive_text(text)

    async def _dispatch_message(self, message: dict[str, Any]) -> None:
        if "method" in message and "id" in message:
            await self._mark_process_crashed("Unsupported server-initiated Codex App Server request.")
            return

        if "id" in message:
            request_id = message.get("id")
            future = self._pending.get(request_id)
            if future is None or future.done():
                return
            if "error" in message:
                error = message.get("error") if isinstance(message.get("error"), dict) else {}
                code = error.get("code")
                code_text = str(code) if isinstance(code, (int, str)) else "unknown"
                future.set_exception(
                    CodexAppServerProtocolError(
                        f"Codex App Server returned a protocol error (code={code_text})."
                    )
                )
                return
            result = message.get("result")
            future.set_result(result if isinstance(result, dict) else {})
            return

        method = message.get("method")
        if method not in ACCOUNT_NOTIFICATION_METHODS:
            return
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        self._apply_notification(str(method), params)
        safe_event = {"method": method, "state": self.get_public_state()}
        for handler in tuple(self._notification_handlers):
            try:
                handler(safe_event)
            except Exception:
                logger.warning("Codex App Server notification handler failed; payload omitted.")

    def _apply_notification(self, method: str, params: dict[str, Any]) -> None:
        if method == "account/updated":
            auth_mode = params.get("authMode")
            plan_type = params.get("planType")
            if auth_mode not in {None, MANAGED_AUTH_MODE}:
                self._crashed = True
                self._public_state.connection_state = "unavailable"
                self._public_state.retry_reason = "Unsupported Codex authentication mode rejected."
                return
            self._public_state.auth_mode = auth_mode
            self._public_state.plan_type = plan_type if isinstance(plan_type, str) else None
            self._public_state.login_pending = False
            self._public_state.login_id = None
            self._public_state.connection_state = "connected" if auth_mode else "disconnected"
            if auth_mode is None:
                self._public_state.account_identifier = None
                self._public_state.workspace_id = None
                self._public_state.workspace_display = None
        elif method == "account/login/completed":
            success = bool(params.get("success"))
            if success:
                self._public_state.login_pending = False
                self._public_state.connection_state = "connecting"
                self._login_restore_snapshot = None
                self._public_state.retry_reason = None
            else:
                if self._login_restore_snapshot is not None:
                    self._restore_public_state(self._login_restore_snapshot)
                    self._login_restore_snapshot = None
                else:
                    self._public_state.login_pending = False
                    self._public_state.login_id = None
                    self._public_state.connection_state = (
                        "connected" if self._public_state.auth_mode == MANAGED_AUTH_MODE else "disconnected"
                    )
                error = params.get("error")
                if error:
                    self._public_state.retry_reason = self._redact_runtime_text(error)
            self._transient_login_secrets = ()

    def _apply_account_result(self, result: dict[str, Any]) -> None:
        account = result.get("account") if isinstance(result.get("account"), dict) else None
        identifier, workspace_id, workspace_display, auth_mode, plan_type = _sanitize_public_account(account)
        if auth_mode not in {None, MANAGED_AUTH_MODE}:
            self._crashed = True
            self._public_state.connection_state = "unavailable"
            self._public_state.retry_reason = "Unsupported Codex authentication mode rejected."
            raise CodexAppServerUnavailableError(self._public_state.retry_reason)

        self._public_state.account_identifier = identifier
        self._public_state.workspace_id = workspace_id
        self._public_state.workspace_display = workspace_display
        self._public_state.auth_mode = auth_mode
        self._public_state.plan_type = plan_type
        self._public_state.connection_state = "connected" if auth_mode else "disconnected"
        self._public_state.retry_reason = None

    async def _mark_process_crashed(self, reason: str) -> None:
        self._crashed = True
        self._initialized = False
        self._public_state.connection_state = "unavailable"
        self._public_state.retry_reason = redact_sensitive_text(reason)
        for future in list(self._pending.values()):
            if not future.done():
                future.set_exception(CodexAppServerUnavailableError(self._public_state.retry_reason))
        self._pending.clear()

    async def _cancel_task(self, task: asyncio.Task[None] | None) -> None:
        if task is None:
            return
        task.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await task

    async def _shutdown_locked(self) -> None:
        self._closing = True
        for future in list(self._pending.values()):
            if not future.done():
                future.cancel()
        self._pending.clear()

        await self._cancel_task(self._reader_task)
        await self._cancel_task(self._stderr_task)
        self._reader_task = None
        self._stderr_task = None

        if self._process is not None and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()
        self._process = None
        self._initialized = False
        self._transient_login_secrets = ()
        self._closing = False


def create_codex_app_server_lifecycle(
    *,
    process_factory: Callable[..., Any] | None = None,
) -> CodexAppServerLifecycle:
    try:
        settings = CodexAppServerSettings.from_environment()
    except CodexAppServerConfigurationError as exc:
        reason = redact_sensitive_text(str(exc))
        logger.warning("Codex App Server boundary unavailable: %s", reason)
        return CodexAppServerLifecycle(
            None,
            configuration_error=reason,
            process_factory=process_factory,
        )
    return CodexAppServerLifecycle(
        settings,
        process_factory=process_factory,
        _isolation_evidence_verified=_production_isolation_evidence_verified(),
    )


async def shutdown_codex_app_server(lifecycle: CodexAppServerLifecycle | None) -> None:
    if lifecycle is not None:
        await lifecycle.close()
