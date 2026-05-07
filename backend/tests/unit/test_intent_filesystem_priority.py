"""Unit-Tests für Filesystem-Intent-Priorisierung (TASK-001: BACKLOG-004).

Testet dass Filesystem-Keywords höher priorisiert werden als Calendar-Keywords
um Fehlklassifikationen zu vermeiden.
"""
import pytest
from backend.services.orchestrator.intent_engine import IntentEngine


class TestFilesystemIntentPriority:
    """Testet die Filesystem-Intent-Erkennung und Priorisierung über Calendar-Intent."""

    @pytest.fixture
    def intent_engine(self):
        """Intent-Engine Instanz für Tests."""
        return IntentEngine()

    # ─────────────────────────────────────────────────────────────────────────
    # Filesystem-Intent Detection Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_filesystem_intent_detected_with_folder_creation(self, intent_engine):
        """Test: 'Ordner erstellen' wird als Filesystem-Intent erkannt."""
        text = "erstell auf dem desktop einen ordner 'Bilder'"
        assert intent_engine.detect_filesystem_intent(text) is True

    def test_filesystem_intent_detected_with_file_move(self, intent_engine):
        """Test: 'Dateien verschieben' wird als Filesystem-Intent erkannt."""
        text = "verschiebe alle jpg und png dateien vom desktop in diesen ordner"
        assert intent_engine.detect_filesystem_intent(text) is True

    def test_filesystem_intent_detected_with_path_marker(self, intent_engine):
        """Test: 'auf dem desktop' mit Action wird als Filesystem-Intent erkannt."""
        text = "erstelle einen ordner auf dem desktop"
        assert intent_engine.detect_filesystem_intent(text) is True

    def test_filesystem_intent_detected_with_object_marker(self, intent_engine):
        """Test: 'Ordner' mit Action wird als Filesystem-Intent erkannt."""
        text = "erstelle einen neuen ordner"
        assert intent_engine.detect_filesystem_intent(text) is True

    def test_filesystem_intent_not_detected_without_action(self, intent_engine):
        """Test: Nur 'Ordner' ohne Action wird nicht als Filesystem-Intent erkannt."""
        text = "was ist mit dem ordner"
        assert intent_engine.detect_filesystem_intent(text) is False

    def test_filesystem_intent_not_detected_calendar_only(self, intent_engine):
        """Test: Reine Calendar-Keywords ohne Filesystem-Action werden nicht erkannt."""
        text = "termin morgen um 14 uhr"
        assert intent_engine.detect_filesystem_intent(text) is False

    def test_filesystem_intent_empty_text(self, intent_engine):
        """Test: Leerer Text gibt False zurück."""
        assert intent_engine.detect_filesystem_intent("") is False
        assert intent_engine.detect_filesystem_intent(None) is False

    # ─────────────────────────────────────────────────────────────────────────
    # Calendar-Intent Veto Tests (Filesystem hat Vorrang)
    # ─────────────────────────────────────────────────────────────────────────

    def test_calendar_intent_suppressed_by_filesystem(self, intent_engine):
        """Test: Calendar-Intent wird unterdrückt wenn Filesystem-Intent vorhanden."""
        text = "erstell auf dem desktop einen ordner 'Bilder'"
        # Filesystem-Intent sollte erkannt werden
        assert intent_engine.detect_filesystem_intent(text) is True
        # Calendar-Intent sollte unterdrückt werden
        assert intent_engine.detect_calendar_intent(text) is False

    def test_calendar_intent_not_suppressed_without_filesystem(self, intent_engine):
        """Test: Calendar-Intent wird NICHT unterdrückt ohne Filesystem-Intent."""
        text = "termin erstellen morgen um 14 uhr"
        # Filesystem-Intent sollte nicht erkannt werden
        assert intent_engine.detect_filesystem_intent(text) is False
        # Calendar-Intent sollte erkannt werden
        assert intent_engine.detect_calendar_intent(text) is True

    def test_calendar_intent_reproduction_prompt(self, intent_engine):
        """Test: Reproduktions-Prompt aus BACKLOG-004 wird korrekt erkannt."""
        text = "hi, erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
        # Filesystem-Intent sollte erkannt werden
        assert intent_engine.detect_filesystem_intent(text) is True
        # Calendar-Intent sollte unterdrückt werden
        assert intent_engine.detect_calendar_intent(text) is False

    # ─────────────────────────────────────────────────────────────────────────
    # Regression Tests (Calendar-Intents sollten weiterhin funktionieren)
    # ─────────────────────────────────────────────────────────────────────────

    def test_calendar_intent_still_works_pure_calendar(self, intent_engine):
        """Regression: Reine Calendar-Intents funktionieren weiterhin."""
        text = "termin erstellen morgen um 15 uhr"
        assert intent_engine.detect_calendar_intent(text) is True
        assert intent_engine.detect_filesystem_intent(text) is False

    def test_calendar_intent_still_works_with_meeting(self, intent_engine):
        """Regression: Meeting-Termin-Erstellung funktioniert weiterhin."""
        text = "plane mir ein meeting morgen"
        assert intent_engine.detect_calendar_intent(text) is True
        assert intent_engine.detect_filesystem_intent(text) is False

    def test_calendar_intent_still_works_with_reminder(self, intent_engine):
        """Regression: Erinnerungen funktionieren weiterhin."""
        text = "erinnere mich an den termin morgen"
        assert intent_engine.detect_calendar_intent(text) is True
        assert intent_engine.detect_filesystem_intent(text) is False

    def test_calendar_intent_still_works_with_date(self, intent_engine):
        """Regression: Calendar mit Datum funktioniert weiterhin."""
        text = "was habe ich am montag"
        assert intent_engine.detect_calendar_intent(text) is True
        assert intent_engine.detect_filesystem_intent(text) is False

    # ─────────────────────────────────────────────────────────────────────────
    # Gemischte Prompts Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_mixed_prompt_filesystem_wins(self, intent_engine):
        """Test: Bei gemischten Prompts gewinnt Filesystem-Intent."""
        text = "erstelle einen ordner für bilder und dokumente"
        # Filesystem-Intent sollte erkannt werden (Action + Object)
        assert intent_engine.detect_filesystem_intent(text) is True
        # Calendar-Intent sollte unterdrückt werden
        assert intent_engine.detect_calendar_intent(text) is False

    def test_mixed_prompt_calendar_wins_without_filesystem_action(self, intent_engine):
        """Test: Ohne Filesystem-Action gewinnt Calendar-Intent."""
        text = "termin erstellen morgen um 14 uhr"
        # Kein Filesystem-Action (nur "Ordner" ohne erstellen/verschiebe/etc)
        assert intent_engine.detect_filesystem_intent(text) is False
        # Calendar-Intent sollte erkannt werden (hat "termin erstellen")
        assert intent_engine.detect_calendar_intent(text) is True

    def test_mixed_prompt_with_calendar_keyword_but_filesystem_action(self, intent_engine):
        """Test: Filesystem-Action überschreibt Calendar-Keyword."""
        text = "verschiebe ordner bilder auf desktop"
        # Filesystem-Intent sollte erkannt werden
        assert intent_engine.detect_filesystem_intent(text) is True
        # Calendar-Intent sollte unterdrückt werden
        assert intent_engine.detect_calendar_intent(text) is False
