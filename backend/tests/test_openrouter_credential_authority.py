import json

import keyring
import pytest

from backend.data.schemas import OpenRouterKeyValidationState
from backend.services import openrouter_credential_authority as authority_module
from backend.services.openrouter_credential_authority import (
    KEYRING_SERVICE,
    RAW_KEY_ACCOUNT,
    VALIDATION_STATE_ACCOUNT,
    OpenRouterCredentialAuthority,
    OpenRouterRuntimeEligibilityReader,
    OpenRouterRuntimeInvalidator,
    OpenRouterSettingsCapability,
)


SENTINEL_A = "TEST_OPENROUTER_AUTHORITY_ALPHA"
SENTINEL_B = "TEST_OPENROUTER_AUTHORITY_BETA"


class MemoryKeyring:
    def __init__(self):
        self.values = {}
        self.set_calls = []
        self.delete_calls = []

    def get_password(self, service, account):
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


@pytest.fixture
def capabilities(monkeypatch):
    store = MemoryKeyring()
    monkeypatch.setattr(authority_module.keyring, "get_password", store.get_password)
    monkeypatch.setattr(authority_module.keyring, "set_password", store.set_password)
    monkeypatch.setattr(authority_module.keyring, "delete_password", store.delete_password)
    authority = OpenRouterCredentialAuthority()
    return (
        store,
        OpenRouterSettingsCapability(authority),
        OpenRouterRuntimeEligibilityReader(authority),
        OpenRouterRuntimeInvalidator(authority),
    )


def validate(settings, api_key=SENTINEL_A):
    lease = settings.begin_save(api_key)
    return settings.complete_validation(lease, OpenRouterKeyValidationState.VALID)


def test_only_exact_valid_binding_is_runtime_eligible(capabilities):
    store, settings, reader, _invalidator = capabilities
    assert reader.get_eligible_credential() is None

    store.values[(KEYRING_SERVICE, RAW_KEY_ACCOUNT)] = SENTINEL_A
    assert reader.get_eligible_credential() is None

    store.values[(KEYRING_SERVICE, VALIDATION_STATE_ACCOUNT)] = "malformed"
    assert reader.get_eligible_credential() is None

    store.values[(KEYRING_SERVICE, VALIDATION_STATE_ACCOUNT)] = json.dumps(
        {"version": 999, "key_fingerprint": "0" * 64, "state": "VALID"}
    )
    assert reader.get_eligible_credential() is None

    validate(settings)
    credential = reader.get_eligible_credential()
    assert credential is not None
    assert credential.api_key == SENTINEL_A
    assert SENTINEL_A not in repr(credential)
    assert "redacted" in repr(credential)

    metadata = json.loads(store.values[(KEYRING_SERVICE, VALIDATION_STATE_ACCOUNT)])
    metadata["state"] = "UNVERIFIED"
    store.values[(KEYRING_SERVICE, VALIDATION_STATE_ACCOUNT)] = json.dumps(metadata)
    assert reader.get_eligible_credential() is None


def test_runtime_capabilities_are_minimal_and_cannot_grant_valid(capabilities):
    _store, settings, reader, invalidator = capabilities
    reader_names = set(dir(reader))
    invalidator_names = set(dir(invalidator))

    assert not {"begin_save", "complete_validation", "delete", "invalidate_authenticated_rejection"} & reader_names
    assert not {"begin_save", "complete_validation", "delete", "get_eligible_credential"} & invalidator_names
    assert {"begin_save", "complete_validation", "delete"} <= set(dir(settings))


def test_invalidate_only_changes_same_exact_valid_key(capabilities):
    store, settings, reader, invalidator = capabilities
    validate(settings)
    credential = reader.get_eligible_credential()
    assert credential is not None

    assert invalidator.invalidate_authenticated_rejection(credential.binding) is True
    assert settings.public_state().state == OpenRouterKeyValidationState.INVALID
    assert invalidator.invalidate_authenticated_rejection(credential.binding) is True

    touched_accounts = {
        account for _service, account, _value in store.set_calls
    } | {account for _service, account in store.delete_calls}
    assert touched_accounts <= {RAW_KEY_ACCOUNT, VALIDATION_STATE_ACCOUNT}
    assert store.values[(KEYRING_SERVICE, RAW_KEY_ACCOUNT)] == SENTINEL_A


def test_replacement_between_authorization_and_rejection_is_not_invalidated(capabilities):
    store, settings, reader, invalidator = capabilities
    validate(settings, SENTINEL_A)
    old_credential = reader.get_eligible_credential()
    assert old_credential is not None

    replacement_lease = settings.begin_save(SENTINEL_B)
    assert invalidator.invalidate_authenticated_rejection(old_credential.binding) is False
    assert store.values[(KEYRING_SERVICE, RAW_KEY_ACCOUNT)] == SENTINEL_B
    assert settings.public_state().state == OpenRouterKeyValidationState.UNVERIFIED

    settings.complete_validation(replacement_lease, OpenRouterKeyValidationState.VALID)
    assert settings.public_state().state == OpenRouterKeyValidationState.VALID


def test_settings_technical_result_cannot_restore_runtime_invalidated_key(capabilities):
    _store, settings, reader, invalidator = capabilities
    validate(settings)
    lease = settings.begin_save(SENTINEL_A)
    credential = reader.get_eligible_credential()
    assert credential is not None
    assert invalidator.invalidate_authenticated_rejection(credential.binding) is True

    result = settings.complete_validation(lease, OpenRouterKeyValidationState.UNVERIFIED)
    assert result.state == OpenRouterKeyValidationState.UNVERIFIED
    assert reader.get_eligible_credential() is None


def test_delete_is_settings_only_and_provider_isolated(capabilities):
    store, settings, _reader, _invalidator = capabilities
    validate(settings)
    store.values[(KEYRING_SERVICE, "openai")] = "OPENAI_SENTINEL"

    settings.delete()

    assert (KEYRING_SERVICE, RAW_KEY_ACCOUNT) not in store.values
    assert (KEYRING_SERVICE, VALIDATION_STATE_ACCOUNT) not in store.values
    assert store.values[(KEYRING_SERVICE, "openai")] == "OPENAI_SENTINEL"
