"""Unit-Tests für VIDEO-FORCE Filesystem-Intent Veto (TASK-003: BACKLOG-004).

Testet dass VIDEO-FORCE nicht bei Filesystem-Intents angewendet wird.
"""
import pytest
from backend.services.orchestrator.intent_engine import IntentEngine, IntentDetectionResult


class TestVideoForceFilesystemVeto:
    """Testet die VIDEO-FORCE Filesystem-Intent Veto-Logik."""

    @pytest.fixture
    def intent_engine(self):
        """Intent-Engine Instanz für Tests."""
        return IntentEngine()

    # ─────────────────────────────────────────────────────────────────────────
    # Filesystem-Intent Detection in IntentDetectionResult
    # ─────────────────────────────────────────────────────────────────────────

    def test_filesystem_intent_detected_in_result(self, intent_engine):
        """Test: Filesystem-Intent wird in IntentDetectionResult erkannt."""
        text = "erstell auf dem desktop einen ordner 'Bilder'"
        result = intent_engine.detect_all_intents(text)
        assert result.is_filesystem_intent is True

    def test_filesystem_intent_not_detected_calendar_only(self, intent_engine):
        """Test: Calendar-Intent ohne Filesystem wird nicht als Filesystem erkannt."""
        text = "termin erstellen morgen um 14 uhr"
        result = intent_engine.detect_all_intents(text)
        assert result.is_filesystem_intent is False

    def test_filesystem_intent_reproduction_prompt(self, intent_engine):
        """Test: Reproduktions-Prompt aus BACKLOG-004 wird korrekt erkannt."""
        text = "hi, erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
        result = intent_engine.detect_all_intents(text)
        assert result.is_filesystem_intent is True

    # ─────────────────────────────────────────────────────────────────────────
    # Calendar-Intent Regression Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_calendar_intent_still_detected(self, intent_engine):
        """Regression: Calendar-Intents werden weiterhin erkannt."""
        text = "termin erstellen morgen um 14 uhr"
        result = intent_engine.detect_all_intents(text)
        assert result.is_calendar_intent is True
        assert result.is_filesystem_intent is False

    def test_calendar_mutation_still_detected(self, intent_engine):
        """Regression: Calendar-Mutation-Intents werden weiterhin erkannt."""
        text = "verschiebe termin morgen auf 15 uhr"
        result = intent_engine.detect_all_intents(text)
        assert result.is_calendar_intent is True
        assert result.is_calendar_mutation is True
        assert result.is_filesystem_intent is False

    def test_calendar_creation_still_detected(self, intent_engine):
        """Regression: Calendar-Creation-Intents werden weiterhin erkannt."""
        text = "erstell einen termin morgen um 14 uhr"
        result = intent_engine.detect_all_intents(text)
        assert result.is_calendar_intent is True
        assert result.is_calendar_creation is True
        assert result.is_filesystem_intent is False

    # ─────────────────────────────────────────────────────────────────────────
    # Gemischte Prompts Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_mixed_prompt_filesystem_wins(self, intent_engine):
        """Test: Bei gemischten Prompts gewinnt Filesystem-Intent."""
        text = "erstelle einen ordner für bilder und dokumente"
        result = intent_engine.detect_all_intents(text)
        assert result.is_filesystem_intent is True
        # Calendar sollte nicht erkannt werden (wegen Calendar-Objekt-Veto)
        assert result.is_calendar_intent is False

    def test_mixed_prompt_calendar_wins_without_filesystem_action(self, intent_engine):
        """Test: Ohne Filesystem-Action gewinnt Calendar-Intent."""
        text = "termin erstellen morgen um 14 uhr"
        result = intent_engine.detect_all_intents(text)
        assert result.is_filesystem_intent is False
        assert result.is_calendar_intent is True

    # ─────────────────────────────────────────────────────────────────────────
    # Edge Cases
    # ─────────────────────────────────────────────────────────────────────────

    def test_empty_text(self, intent_engine):
        """Test: Leerer Text gibt False zurück."""
        result = intent_engine.detect_all_intents("")
        assert result.is_filesystem_intent is False
        assert result.is_calendar_intent is False

    def test_none_text(self, intent_engine):
        """Test: None Text gibt False zurück."""
        result = intent_engine.detect_all_intents(None)
        assert result.is_filesystem_intent is False
        assert result.is_calendar_intent is False
