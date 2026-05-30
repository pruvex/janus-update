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

    def test_general_world_how_to_does_not_trigger_help_fast_path(self, engine):
        """Generic advice must go to the LLM instead of deterministic Janus help."""
        prompt = (
            "schau mal ich habe gestern abend ein fertigback steinofenbagutt gemacht, "
            "das wuerde ich gerne wieder aufbacken, wie mache ich das am bestne?"
        )

        result = engine.detect_all_intents(prompt)

        assert result.is_how_to is False
        assert result.is_navigation_query is False

    def test_janus_scoped_how_to_still_triggers_help_fast_path(self, engine):
        """Janus/app capability questions should still use deterministic help."""
        assert engine.detect_how_to("Wie kann ich Dateien hochladen?") is True
        assert engine.detect_how_to("Wie funktioniert lokales LLM in Janus?") is True

    def test_general_world_navigation_does_not_trigger_help_fast_path(self, engine):
        """General location questions must not be swallowed by Janus navigation help."""
        assert engine.detect_navigation("Wo ist Berlin?") is False
        assert engine.detect_navigation("Wo finde ich frische Baguettes?") is False
        assert engine.detect_navigation("Wo finde ich meine Dateien?") is True
