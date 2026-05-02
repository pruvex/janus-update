"""Test calendar routing fix - shopping guardrail bypass for calendar intents."""

import pytest
from backend.services.orchestrator.intent_engine import IntentEngine


class TestCalendarRoutingFix:
    """Test that calendar intents bypass shopping guardrail."""
    
    @pytest.fixture
    def intent_engine(self):
        return IntentEngine()
    
    def test_shopping_intent_vetoed_by_calendar_keywords(self, intent_engine):
        """Shopping intent should be vetoed when calendar keywords are present."""
        # Calendar + shopping context (should be vetoed)
        assert not intent_engine.detect_shopping_intent("um 14 uhr einkaufen beim netto")
        assert not intent_engine.detect_shopping_intent("termin: einkaufen morgen")
        assert not intent_engine.detect_shopping_intent("trage ein: einkaufen am montag um 15 uhr")
        
        # Price-focused queries should still work (override veto)
        assert intent_engine.detect_shopping_intent("was kostet einkaufen beim netto")
        assert intent_engine.detect_shopping_intent("wie viel kostet der einkauf")
    
    def test_calendar_intent_detection(self, intent_engine):
        """Calendar intent should be detected correctly."""
        assert intent_engine.detect_calendar_intent("um 14 uhr einkaufen beim netto")
        assert intent_engine.detect_calendar_intent("termin morgen um 15 uhr")
        assert intent_engine.detect_calendar_intent("trage ein: meeting am dienstag")
        assert intent_engine.detect_calendar_intent("termin erstellen für nächste woche")
        
        # Non-calendar queries
        assert not intent_engine.detect_calendar_intent("was kostet das")
        assert not intent_engine.detect_calendar_intent("kaufen bei amazon")
    
    def test_shopping_intent_without_calendar_keywords(self, intent_engine):
        """Shopping intent should work normally without calendar keywords."""
        assert intent_engine.detect_shopping_intent("kaufen bei amazon")
        assert intent_engine.detect_shopping_intent("was kostet das bei otto")
        assert intent_engine.detect_shopping_intent("günstige offers bei zalando")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
