"""Single authority for OpenRouter credential state and exact-key eligibility."""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
from dataclasses import dataclass
from typing import Optional

import keyring

from backend.data.schemas import OpenRouterKeyPublicState, OpenRouterKeyValidationState


KEYRING_SERVICE = "Janus-Projekt"
RAW_KEY_ACCOUNT = "openrouter"
VALIDATION_STATE_ACCOUNT = "openrouter-validation-state"
VALIDATION_STATE_VERSION = 1


def _fingerprint(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OpenRouterCredentialBinding:
    """Opaque exact-key handle. Its key-derived value must never be logged."""

    _key_fingerprint: str

    def __init__(self, key_fingerprint: str) -> None:
        object.__setattr__(self, "_key_fingerprint", key_fingerprint)

    def __repr__(self) -> str:
        return "OpenRouterCredentialBinding(<redacted>)"


@dataclass(frozen=True)
class OpenRouterRuntimeCredential:
    api_key: str
    binding: OpenRouterCredentialBinding

    def __repr__(self) -> str:
        return "OpenRouterRuntimeCredential(api_key=<redacted>, binding=<redacted>)"


@dataclass(frozen=True)
class OpenRouterSaveLease:
    """Exact-key lease spanning the content-free Settings validation request."""

    _key_fingerprint: str

    def __repr__(self) -> str:
        return "OpenRouterSaveLease(<redacted>)"


class OpenRouterCredentialAuthority:
    """Owns metadata interpretation and every allowed OpenRouter state transition."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    @staticmethod
    def _read_raw_key() -> Optional[str]:
        return keyring.get_password(KEYRING_SERVICE, RAW_KEY_ACCOUNT)

    @staticmethod
    def _read_metadata_raw() -> Optional[str]:
        return keyring.get_password(KEYRING_SERVICE, VALIDATION_STATE_ACCOUNT)

    @staticmethod
    def _delete_account(account: str) -> None:
        try:
            keyring.delete_password(KEYRING_SERVICE, account)
        except keyring.errors.PasswordDeleteError:
            return

    @staticmethod
    def _parse_state_for_key(api_key: str, raw_metadata: Optional[str]) -> OpenRouterKeyValidationState:
        if not raw_metadata:
            return OpenRouterKeyValidationState.UNVERIFIED
        try:
            metadata = json.loads(raw_metadata)
            if not isinstance(metadata, dict):
                return OpenRouterKeyValidationState.UNVERIFIED
            if metadata.get("version") != VALIDATION_STATE_VERSION:
                return OpenRouterKeyValidationState.UNVERIFIED
            metadata_fingerprint = str(metadata.get("key_fingerprint") or "")
            if not hmac.compare_digest(metadata_fingerprint, _fingerprint(api_key)):
                return OpenRouterKeyValidationState.UNVERIFIED
            return OpenRouterKeyValidationState(str(metadata.get("state") or ""))
        except (TypeError, ValueError, json.JSONDecodeError):
            return OpenRouterKeyValidationState.UNVERIFIED

    @staticmethod
    def _write_state(api_key: str, state: OpenRouterKeyValidationState) -> None:
        metadata = {
            "version": VALIDATION_STATE_VERSION,
            "key_fingerprint": _fingerprint(api_key),
            "state": state.value,
        }
        keyring.set_password(
            KEYRING_SERVICE,
            VALIDATION_STATE_ACCOUNT,
            json.dumps(metadata, separators=(",", ":"), sort_keys=True),
        )

    def public_state(self) -> OpenRouterKeyPublicState:
        with self._lock:
            api_key = self._read_raw_key()
            if not api_key:
                return OpenRouterKeyPublicState(present=False)
            state = self._parse_state_for_key(api_key, self._read_metadata_raw())
            return OpenRouterKeyPublicState(present=True, masked="********", state=state)

    def begin_settings_save(self, api_key: str) -> OpenRouterSaveLease:
        if not api_key or not api_key.strip():
            raise ValueError("OpenRouter API key is required.")
        with self._lock:
            current_key = self._read_raw_key()
            same_key = bool(current_key) and hmac.compare_digest(str(current_key), api_key)
            if not same_key:
                self._delete_account(VALIDATION_STATE_ACCOUNT)
                keyring.set_password(KEYRING_SERVICE, RAW_KEY_ACCOUNT, api_key)
                self._write_state(api_key, OpenRouterKeyValidationState.UNVERIFIED)
            return OpenRouterSaveLease(_fingerprint(api_key))

    def complete_settings_validation(
        self,
        lease: OpenRouterSaveLease,
        state: OpenRouterKeyValidationState,
    ) -> OpenRouterKeyPublicState:
        if not isinstance(lease, OpenRouterSaveLease):
            raise TypeError("Invalid OpenRouter save lease.")
        if not isinstance(state, OpenRouterKeyValidationState):
            raise TypeError("Invalid OpenRouter validation state.")
        with self._lock:
            current_key = self._read_raw_key()
            if not current_key:
                return OpenRouterKeyPublicState(present=False)
            current_fingerprint = _fingerprint(current_key)
            if not hmac.compare_digest(current_fingerprint, lease._key_fingerprint):
                return self.public_state()

            current_state = self._parse_state_for_key(current_key, self._read_metadata_raw())
            final_state = state
            if (
                state == OpenRouterKeyValidationState.UNVERIFIED
                and current_state == OpenRouterKeyValidationState.VALID
            ):
                final_state = OpenRouterKeyValidationState.VALID
            self._write_state(current_key, final_state)
            return OpenRouterKeyPublicState(
                present=True,
                masked="********",
                state=final_state,
            )

    def delete_from_settings(self) -> None:
        with self._lock:
            self._delete_account(RAW_KEY_ACCOUNT)
            self._delete_account(VALIDATION_STATE_ACCOUNT)

    def read_runtime_credential(self) -> Optional[OpenRouterRuntimeCredential]:
        with self._lock:
            api_key = self._read_raw_key()
            if not api_key:
                return None
            fingerprint = _fingerprint(api_key)
            state = self._parse_state_for_key(api_key, self._read_metadata_raw())
            if state != OpenRouterKeyValidationState.VALID:
                return None
            return OpenRouterRuntimeCredential(
                api_key=api_key,
                binding=OpenRouterCredentialBinding(fingerprint),
            )

    def invalidate_authenticated_rejection(
        self,
        binding: OpenRouterCredentialBinding,
    ) -> bool:
        if not isinstance(binding, OpenRouterCredentialBinding):
            return False
        with self._lock:
            current_key = self._read_raw_key()
            if not current_key:
                return False
            current_fingerprint = _fingerprint(current_key)
            if not hmac.compare_digest(current_fingerprint, binding._key_fingerprint):
                return False
            current_state = self._parse_state_for_key(current_key, self._read_metadata_raw())
            if current_state == OpenRouterKeyValidationState.INVALID:
                return True
            if current_state != OpenRouterKeyValidationState.VALID:
                return False
            self._write_state(current_key, OpenRouterKeyValidationState.INVALID)
            return True


class OpenRouterSettingsCapability:
    def __init__(self, authority: OpenRouterCredentialAuthority) -> None:
        self._authority = authority

    def public_state(self) -> OpenRouterKeyPublicState:
        return self._authority.public_state()

    def begin_save(self, api_key: str) -> OpenRouterSaveLease:
        return self._authority.begin_settings_save(api_key)

    def complete_validation(
        self,
        lease: OpenRouterSaveLease,
        state: OpenRouterKeyValidationState,
    ) -> OpenRouterKeyPublicState:
        return self._authority.complete_settings_validation(lease, state)

    def delete(self) -> None:
        self._authority.delete_from_settings()


class OpenRouterRuntimeEligibilityReader:
    def __init__(self, authority: OpenRouterCredentialAuthority) -> None:
        self._authority = authority

    def get_eligible_credential(self) -> Optional[OpenRouterRuntimeCredential]:
        return self._authority.read_runtime_credential()


class OpenRouterRuntimeInvalidator:
    def __init__(self, authority: OpenRouterCredentialAuthority) -> None:
        self._authority = authority

    def invalidate_authenticated_rejection(
        self,
        binding: OpenRouterCredentialBinding,
    ) -> bool:
        return self._authority.invalidate_authenticated_rejection(binding)


_AUTHORITY = OpenRouterCredentialAuthority()
_SETTINGS_CAPABILITY = OpenRouterSettingsCapability(_AUTHORITY)
_RUNTIME_READER = OpenRouterRuntimeEligibilityReader(_AUTHORITY)
_RUNTIME_INVALIDATOR = OpenRouterRuntimeInvalidator(_AUTHORITY)


def get_openrouter_settings_capability() -> OpenRouterSettingsCapability:
    return _SETTINGS_CAPABILITY


def get_openrouter_runtime_reader() -> OpenRouterRuntimeEligibilityReader:
    return _RUNTIME_READER


def get_openrouter_runtime_invalidator() -> OpenRouterRuntimeInvalidator:
    return _RUNTIME_INVALIDATOR
