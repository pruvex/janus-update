import pytest

from backend.services.chat_orchestrator import (
    _is_one_time_policy_choice,
    _is_policy_consent_choice,
    _is_policy_prompt_text,
)


def test_policy_prompt_detection_covers_core_prompt_text():
    text = (
        "Diese Aktion erfordert eine Freigabe. Möchtest du die Aktion 1. Einmalig erlauben, "
        "2. In Zukunft immer ohne Nachfragen erlauben, oder 3. Abbrechen?"
    )
    assert _is_policy_prompt_text(text) is True


def test_policy_prompt_detection_supports_ascii_variant():
    text = (
        "Diese Aktion erfordert eine Freigabe. Moechtest du die Aktion 1. Einmalig erlauben, "
        "2. In Zukunft immer ohne Nachfragen erlauben, oder 3. Abbrechen?"
    )
    assert _is_policy_prompt_text(text) is True


@pytest.mark.parametrize(
    "token,expected",
    [
        ("1", True),
        ("1.", True),
        ("einmalig", True),
        ("ja", True),
        ("erlauben", True),
        ("2", True),
        ("immer", True),
        ("3", True),
        ("abbrechen", True),
        ("nein", True),
        ("irgendwas", False),
    ],
)
def test_policy_consent_token_detection(token: str, expected: bool):
    assert _is_policy_consent_choice(token) is expected


@pytest.mark.parametrize(
    "token,expected",
    [
        ("1", True),
        ("1.", True),
        ("einmalig", True),
        ("ja", True),
        ("erlauben", True),
        ("2", False),
        ("3", False),
    ],
)
def test_one_time_policy_token_detection(token: str, expected: bool):
    assert _is_one_time_policy_choice(token) is expected
