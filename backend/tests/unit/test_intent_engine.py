"""Unit tests for IntentEngine normalization and detection (TASK-069.14).

Verifies that _normalize_intent_text robustly strips multiple trailing
punctuation marks, spaces, and uses casefold for reliable matching.
"""

import pytest
from backend.services.orchestrator.intent_engine import IntentEngine


class TestIntentEngineNormalization:
    """Test suite for _normalize_intent_text hardening."""

    @pytest.fixture
    def engine(self):
        return IntentEngine()

    def test_single_question_mark(self, engine):
        assert engine._normalize_intent_text("Was kannst du?") == "was kannst du"

    def test_multiple_question_marks(self, engine):
        assert engine._normalize_intent_text("WAS KANNST DU ???") == "was kannst du"

    def test_mixed_punctuation(self, engine):
        assert engine._normalize_intent_text("was kannst du?!?") == "was kannst du"

    def test_trailing_space(self, engine):
        assert engine._normalize_intent_text("Welche Fähigkeiten hast du? ") == "welche fähigkeiten hast du"

    def test_trailing_period(self, engine):
        assert engine._normalize_intent_text("Was kannst du.") == "was kannst du"

    def test_trailing_exclamation(self, engine):
        assert engine._normalize_intent_text("Was kannst du!") == "was kannst du"

    def test_multiple_spaces_collapsed(self, engine):
        assert engine._normalize_intent_text("Was   kannst    du?") == "was kannst du"

    def test_empty_string(self, engine):
        assert engine._normalize_intent_text("") == ""

    def test_only_punctuation(self, engine):
        assert engine._normalize_intent_text("?!?") == ""

    def test_capability_overview_detected_with_multiple_marks(self, engine):
        """Multiple trailing punctuation must not prevent trigger match."""
        assert engine.detect_capability_overview("was kannst du???") is True
        assert engine.detect_capability_overview("was kannst du?!?") is True
        assert engine.detect_capability_overview("was kannst du? ") is True
        assert engine.detect_capability_overview("WAS KANNST DU !!!") is True
