from backend.services.orchestrator.intent_engine import intent_engine
from backend.utils import intent_classifier


def test_greeting_with_punctuation_gets_direct_smalltalk_response():
    assert intent_classifier.is_greeting("hey!!")
    assert intent_classifier.smalltalk_response("hey!!").startswith("Hey!")
    assert intent_classifier.is_greeting("na du")
    assert intent_classifier.smalltalk_response("na du").startswith("Na du!")


def test_how_are_you_is_smalltalk_not_help_how_to():
    assert intent_classifier.is_greeting("wie gehts dir?")
    assert intent_classifier.is_how_are_you("wie geht's dir?")
    assert intent_engine.detect_how_to("wie gehts dir?") is False

    result = intent_engine.detect_all_intents("wie gehts dir?")
    assert result.is_how_to is False


def test_greeting_prefix_does_not_hide_real_requests():
    assert intent_classifier.is_greeting("hey, was kannst du?") is False
    assert intent_classifier.is_greeting("hey, exportiere alles ueber mich") is False
