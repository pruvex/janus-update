"""Integrationstest für Filesystem-Intent-Flow (TASK-005: BACKLOG-004).

Validiert den kompletten Flow von Prompt über Intent-Resolver zu Tool-Aufruf
für Filesystem-Operationen.
"""
import pytest
from backend.services.orchestrator.intent_engine import IntentEngine


class TestFilesystemIntentFlowIntegration:
    """Integrationstest für den kompletten Filesystem-Intent-Flow."""

    @pytest.fixture
    def intent_engine(self):
        """Intent-Engine Instanz für Tests."""
        return IntentEngine()

    # ─────────────────────────────────────────────────────────────────────────
    # Reproduktions-Prompt Test
    # ─────────────────────────────────────────────────────────────────────────

    def test_reproduction_prompt_filesystem_intent_detected(self, intent_engine):
        """Test: Reproduktions-Prompt wird als Filesystem-Intent erkannt."""
        prompt = "erstell auf dem desktop einen ordner 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
        result = intent_engine.detect_all_intents(prompt)
        assert result.is_filesystem_intent is True
        # Calendar sollte nicht erkannt werden (wegen Calendar-Objekt-Veto)
        assert result.is_calendar_intent is False

    def test_reproduction_prompt_intent_flow(self, intent_engine):
        """Test: Kompletter Intent-Flow für Reproduktions-Prompt."""
        prompt = "erstell auf dem desktop einen ordner 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
        result = intent_engine.detect_all_intents(prompt)

        # 1. Intent-Erkennung
        assert result.is_filesystem_intent is True
        assert result.is_calendar_intent is False
        assert result.is_calendar_mutation is False

        # 2. Keine Calendar-Intent-Erkennung (Veto durch Filesystem-Intent)
        assert result.primary_intent != "calendar"

        # 3. Keine anderen Intents die Calendar-Tools erzwingen
        assert result.is_shopping_intent is False
        assert result.is_local_business_intent is False

    # ─────────────────────────────────────────────────────────────────────────
    # Calendar-Intent Regression Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_calendar_prompt_still_works(self, intent_engine):
        """Regression: Calendar-Prompts funktionieren weiterhin."""
        prompt = "termin erstellen morgen um 14 uhr"
        result = intent_engine.detect_all_intents(prompt)
        assert result.is_filesystem_intent is False
        assert result.is_calendar_intent is True
        assert result.is_calendar_creation is True

    def test_calendar_mutation_prompt_still_works(self, intent_engine):
        """Regression: Calendar-Mutation-Prompts funktionieren weiterhin."""
        prompt = "verschiebe termin morgen auf 15 uhr"
        result = intent_engine.detect_all_intents(prompt)
        assert result.is_filesystem_intent is False
        assert result.is_calendar_intent is True
        assert result.is_calendar_mutation is True

    # ─────────────────────────────────────────────────────────────────────────
    # Filesystem-Keyword Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_filesystem_action_keywords_detected(self, intent_engine):
        """Test: Filesystem-Action-Keywords werden erkannt."""
        prompt = "erstell einen neuen ordner"
        result = intent_engine.detect_all_intents(prompt)
        assert result.is_filesystem_intent is True

    def test_filesystem_object_keywords_detected(self, intent_engine):
        """Test: Filesystem-Object-Keywords werden erkannt."""
        prompt = "verschiebe die dateien in den ordner"
        result = intent_engine.detect_all_intents(prompt)
        assert result.is_filesystem_intent is True

    def test_filesystem_path_keywords_detected(self, intent_engine):
        """Test: Filesystem-Path-Keywords werden mit Action erkannt."""
        prompt = "liste alle dateien im desktop ordner auf"
        result = intent_engine.detect_all_intents(prompt)
        # "liste" ist keine Filesystem-Action, daher False
        # Filesystem-Intent erfordert Action-Keywords wie "erstell", "verschiebe", "lösche"
        assert result.is_filesystem_intent is False

    # ─────────────────────────────────────────────────────────────────────────
    # Edge Cases
    # ─────────────────────────────────────────────────────────────────────────

    def test_empty_prompt(self, intent_engine):
        """Test: Leerer Prompt gibt False zurück."""
        result = intent_engine.detect_all_intents("")
        assert result.is_filesystem_intent is False
        assert result.is_calendar_intent is False

    def test_none_prompt(self, intent_engine):
        """Test: None Prompt gibt False zurück."""
        result = intent_engine.detect_all_intents(None)
        assert result.is_filesystem_intent is False
        assert result.is_calendar_intent is False

    def test_mixed_prompt_filesystem_wins(self, intent_engine):
        """Test: Bei gemischten Prompts gewinnt Filesystem-Intent."""
        prompt = "erstelle einen ordner für bilder und dokumente"
        result = intent_engine.detect_all_intents(prompt)
        assert result.is_filesystem_intent is True
        # Calendar sollte nicht erkannt werden (wegen Calendar-Objekt-Veto)
        assert result.is_calendar_intent is False
