from backend.services.orchestrator.intent_engine import intent_engine


def test_detect_routine_save_confirm():
    assert intent_engine.detect_routine_save_confirm("Ja, speichere das") is True
    assert intent_engine.detect_routine_save_confirm("okay, mach das") is True
    assert intent_engine.detect_routine_save_confirm("nein danke") is False


def test_detect_routine_save_request():
    assert intent_engine.detect_routine_save_request("Speicher diesen Ablauf als Routine") is True
    assert intent_engine.detect_routine_save_request("Merke dir den Ablauf bitte als Routine") is True
    assert intent_engine.detect_routine_save_request("Wie wird das Wetter?") is False


def test_detect_routine_decline():
    assert intent_engine.detect_routine_decline("Nein danke") is True
    assert intent_engine.detect_routine_decline("Nicht mehr fragen") is True
    assert intent_engine.detect_routine_decline("Ja bitte") is False
