from backend.services.memory_extractor import _contains_email_pii


def test_contains_email_pii_detects_email_strings():
    assert _contains_email_pii("user@example.com") is True
    assert _contains_email_pii("Der Nutzer verwendet rolfadam74@gmail.com") is True


def test_contains_email_pii_ignores_non_email_text():
    assert _contains_email_pii("Der Nutzer mag Kaffee") is False
    assert _contains_email_pii("", None, "kein pii") is False

