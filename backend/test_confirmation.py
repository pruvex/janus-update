
import pytest
from backend.main import is_confirmation

@pytest.mark.parametrize("phrase, expected", [
    ("ja", True),
    ("stimmt", True),
    ("genau", True),
    ("richtig", True),
    ("korrekt", True),
    ("das stimmt", True),
    ("ja genau", True),
    ("ja das stimmt", True),
    ("das ist richtig", True),
    ("ist korrekt", True),
    ("Ja, das stimmt.", True),
    ("Stimmt!", True),
    ("Nein", False),
    ("Falsch", False),
    ("Ich glaube nicht", False),
    ("das ist falsch", False),
    ("vielleicht", False),
])
def test_is_confirmation(phrase, expected):
    assert is_confirmation(phrase) == expected
