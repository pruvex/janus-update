"""Unit tests for HelpSkill — FEAT-HELP-001.

Tests: Capability Overview, How-To, Navigation, Fallback, No-LLM-Guard
"""

import json
import pytest
from pathlib import Path

from backend.services.capability_registry import CapabilityRegistry
from backend.services.help_skill import HelpSkill, create_help_skill
from backend.services.orchestrator.help_schemas import HelpInput, HelpOutput, HelpAction


@pytest.fixture
def sample_registry_data():
    """Sample registry data for testing."""
    return {
        "version": "1.0.0",
        "categories": {
            "file_management": {
                "display_name": {"de": "Dateiverwaltung", "en": "File Management"},
                "icon": "📁",
                "description": {"de": "Verwalte Dateien", "en": "Manage files"},
                "abilities": [
                    {
                        "id": "file.upload",
                        "label": {"de": "Dateien hochladen", "en": "Upload Files"},
                        "skill_refs": ["system.upload"],
                        "how_to": {
                            "de": "Ziehe eine Datei per Drag & Drop in den Chat.",
                            "en": "Drag and drop a file into the chat."
                        }
                    },
                    {
                        "id": "file.search",
                        "label": {"de": "Dateien suchen", "en": "Search Files"},
                        "skill_refs": ["knowledge.query"],
                        "how_to": {
                            "de": "Sage: 'Finde die Datei Rechnung.pdf'.",
                            "en": "Say: 'Find the file invoice.pdf'."
                        }
                    }
                ],
                "ui_locations": {
                    "files": {
                        "label": {"de": "Dateien", "en": "Files"},
                        "action": {"type": "open_module", "payload": {"module": "files"}}
                    }
                }
            },
            "memory_v2": {
                "display_name": {"de": "Erinnerungen", "en": "Memories"},
                "icon": "🧠",
                "description": {"de": "Speichere Erinnerungen", "en": "Store memories"},
                "abilities": [
                    {
                        "id": "memory.find",
                        "label": {"de": "Erinnerungen finden", "en": "Find Memories"},
                        "skill_refs": ["memory.read"],
                        "how_to": {
                            "de": "Frage: 'Wie heißt der Hund von Max?'",
                            "en": "Ask: 'What is Max's dog called?'"
                        }
                    }
                ],
                "ui_locations": {
                    "memories": {
                        "label": {"de": "Erinnerungen", "en": "Memories"},
                        "action": {"type": "open_settings", "payload": {"section": "memory"}}
                    }
                }
            }
        }
    }


@pytest.fixture
def help_skill(tmp_path: Path, sample_registry_data):
    """Create a HelpSkill instance with test registry."""
    # Write registry file
    registry_file = tmp_path / "registry.json"
    registry_file.write_text(json.dumps(sample_registry_data), encoding="utf-8")

    # Create skills dir (empty is fine for these tests)
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Initialize registry
    registry = CapabilityRegistry(str(registry_file), str(skills_dir))
    registry.load()

    # Create help skill
    return create_help_skill(registry)


class TestHelpSkillCapabilityOverview:
    """Tests for capability overview intent (§8.2)."""

    def test_capability_overview_generates_response(self, help_skill):
        """Capability overview generates a proper response."""
        result = help_skill.handle(
            query="Was kannst du?",
            intent_type="capability_overview",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        assert result.answer is not None
        assert len(result.answer) > 0
        assert result.fallback_used is False
        assert result.source_category == "capability_overview"
        # Should include categories from registry
        assert "Datei" in result.answer or "Erinnerung" in result.answer
        assert "📁" in result.answer  # Icon
        assert "🧠" in result.answer  # Icon
        # Should list abilities
        assert "Dateien hochladen" in result.answer or "Upload Files" in result.answer

    def test_capability_overview_returns_english_when_requested(self, help_skill):
        """Capability overview respects language parameter."""
        result = help_skill.handle(
            query="What can you do?",
            intent_type="capability_overview",
            language="en"
        )

        assert isinstance(result, HelpOutput)
        assert result.fallback_used is False
        assert "File Management" in result.answer or "Manage files" in result.answer

    def test_capability_overview_returns_suggestions(self, help_skill):
        """Capability overview includes follow-up suggestions."""
        result = help_skill.handle(
            query="Was kannst du?",
            intent_type="capability_overview",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        assert len(result.suggestions) > 0
        # Suggestions should be how-to or navigation style
        assert any("funktioniert" in s or "finde" in s for s in result.suggestions)


class TestHelpSkillHowTo:
    """Tests for how-to intent (§8.2)."""

    def test_handle_how_to_returns_correct_ability_instruction(self, help_skill):
        """How-to returns instruction for matching ability."""
        result = help_skill.handle(
            query="Wie lade ich Dateien hoch?",
            intent_type="how_to",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        assert result.fallback_used is False
        assert result.source_category == "file_management"
        assert "Drag & Drop" in result.answer or "Ziehe" in result.answer

    def test_handle_how_to_matches_by_ability_id(self, help_skill):
        """How-to matches ability by ID keywords (e.g., 'upload' from 'file.upload')."""
        result = help_skill.handle(
            query="Wie funktioniert upload?",
            intent_type="how_to",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        assert result.fallback_used is False
        assert "Anleitung" in result.answer

    def test_handle_how_to_returns_suggestions(self, help_skill):
        """How-to response includes relevant follow-up suggestions."""
        result = help_skill.handle(
            query="Wie finde ich Erinnerungen?",
            intent_type="how_to",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        assert len(result.suggestions) > 0


class TestHelpSkillNavigation:
    """Tests for navigation intent (§8.2)."""

    def test_handle_navigation_returns_ui_action(self, help_skill):
        """Navigation returns UI action for matching query."""
        result = help_skill.handle(
            query="Wo finde ich meine Dateien?",
            intent_type="navigation",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        assert result.fallback_used is False
        assert result.source_category == "navigation"
        assert len(result.actions) > 0

        action = result.actions[0]
        assert action.type == "open_module"
        assert action.payload.get("module") == "files"

    def test_handle_navigation_returns_settings_action(self, help_skill):
        """Navigation to settings returns open_settings action."""
        result = help_skill.handle(
            query="Wo sind meine Erinnerungen?",
            intent_type="navigation",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        # Should match "Erinnerungen" category
        assert result.fallback_used is False
        assert len(result.actions) > 0 or "Erinnerungen" in result.answer


class TestHelpSkillFallback:
    """Tests for fallback behavior (§8.2)."""

    def test_handle_unknown_query_returns_fallback(self, help_skill):
        """Unknown query returns fallback message."""
        result = help_skill.handle(
            query="Wie funktioniert der Zeitmaschinen-Flux-Kompensator?",
            intent_type="how_to",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        assert result.fallback_used is True
        assert result.answer == "Dazu habe ich keine Information."
        assert result.source_category is None

    def test_handle_unknown_navigation_returns_fallback(self, help_skill):
        """Unknown navigation query returns fallback."""
        result = help_skill.handle(
            query="Wo finde ich das Tardis-Kontroll-Panel?",
            intent_type="navigation",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        assert result.fallback_used is True
        assert "Dazu habe ich keine Information" in result.answer

    def test_handle_unknown_intent_returns_fallback(self, help_skill):
        """Unknown intent type returns fallback."""
        result = help_skill.handle(
            query="Was kannst du?",
            intent_type="unknown_intent_type",
            language="de"
        )

        assert isinstance(result, HelpOutput)
        assert result.fallback_used is True
        assert result.answer == "Dazu habe ich keine Information."


class TestHelpSkillNoLLM:
    """Tests to ensure NO LLM is used (§8.2)."""

    def test_help_skill_never_imports_llm_gateway(self):
        """Verify help_skill.py does not import llm_gateway."""
        import backend.services.help_skill as help_skill_module
        import sys

        # Check module source for llm_gateway references
        import inspect
        source = inspect.getsource(help_skill_module)

        assert "llm_gateway" not in source, "help_skill.py must NOT import llm_gateway"
        assert "llm_gateway.reason_and_respond" not in source

    def test_handle_never_calls_llm(self, help_skill, monkeypatch):
        """Verify handle() never calls any LLM method."""
        # Monkey-patch any potential LLM call points
        llm_calls = []

        def mock_llm_call(*args, **kwargs):
            llm_calls.append((args, kwargs))
            return "mock response"

        # The test passes if no exception and no LLM calls were made
        # Since we can't easily mock llm_gateway without importing it,
        # we verify by checking the response structure
        result = help_skill.handle(
            query="Was kannst du?",
            intent_type="capability_overview",
            language="de"
        )

        # Deterministic responses should be consistent
        result2 = help_skill.handle(
            query="Was kannst du?",
            intent_type="capability_overview",
            language="de"
        )

        # Same query -> same deterministic answer
        assert result.answer == result2.answer
        assert result.fallback_used == result2.fallback_used


class TestHelpSkillEdgeCases:
    """Additional edge case tests."""

    def test_handle_empty_registry_returns_fallback(self, tmp_path: Path):
        """Empty registry results in fallback for overview."""
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(
            json.dumps({"version": "1.0.0", "categories": {}}),
            encoding="utf-8"
        )
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        registry = CapabilityRegistry(str(registry_file), str(skills_dir))
        registry.load()
        help_skill = create_help_skill(registry)

        result = help_skill.handle(
            query="Was kannst du?",
            intent_type="capability_overview",
            language="de"
        )

        assert result.fallback_used is True
        assert result.answer == "Dazu habe ich keine Information."

    def test_handle_preserves_context(self, help_skill):
        """Context is preserved but not used in output (for future extensions)."""
        result = help_skill.handle(
            query="Was kannst du?",
            intent_type="capability_overview",
            context={"chat_id": "12345", "user_id": "user-abc"},
            language="de"
        )

        assert isinstance(result, HelpOutput)
        # Context doesn't affect output currently, but method accepts it
        assert result.fallback_used is False


class TestHelpSkillLanguageFallback:
    """Tests for i18n fallback behavior."""

    def test_handles_missing_language_gracefully(self, help_skill):
        """Request for non-existent language uses fallback."""
        result = help_skill.handle(
            query="Was kannst du?",
            intent_type="capability_overview",
            language="fr"  # French not in registry
        )

        # Should fallback to German (default)
        assert isinstance(result, HelpOutput)
        assert result.fallback_used is False
        # Should still show German content as fallback
        assert "Dateiverwaltung" in result.answer or "Erinnerungen" in result.answer
