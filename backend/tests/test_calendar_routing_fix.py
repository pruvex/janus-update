"""Test calendar routing fix - shopping guardrail bypass for calendar intents."""

import pytest
from backend.services.orchestrator.intent_engine import (
    IntentEngine,
    calendar_user_text_overlap_snapshot,
)


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


# --- TASK-062: contextual intent boost vs. Kalender-Snapshot ----------------------------

ALD_SNAPSHOT = {
    "events": [
        {
            "title": "Einkauf Aldi Süd",
            "location": "",
            "start": "2026-05-03T18:30:00+02:00",
            "end": "2026-05-03T19:30:00+02:00",
        }
    ]
}


class TestCalendarSnapshotIntentBoost:
    def test_overlap_helper_detects_shared_token_with_title(self):
        assert calendar_user_text_overlap_snapshot(
            "Kannst du Aldi nächsten Samstag später legen?",
            ALD_SNAPSHOT,
        )

    def test_detect_all_intents_boosts_calendar_from_snapshot_without_calendar_lexemes(self):
        engine = IntentEngine()
        text = "Kannst du Aldi nächsten Samstag später legen?"
        assert calendar_user_text_overlap_snapshot(text, ALD_SNAPSHOT)
        base = engine.detect_all_intents(text, calendar_snapshot=None)
        boosted = engine.detect_all_intents(text, calendar_snapshot=ALD_SNAPSHOT)
        assert not base.is_calendar_intent
        assert boosted.is_calendar_intent
        assert boosted.primary_intent == "calendar"

    def test_snapshot_boost_suppressed_when_strong_price_shopping_signal(self):
        engine = IntentEngine()
        result = engine.detect_all_intents(
            "Was kostet Milch bei Aldi?",
            calendar_snapshot=ALD_SNAPSHOT,
        )
        assert result.is_shopping_intent
        assert not result.is_calendar_intent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
