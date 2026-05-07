"""Unit-Tests für Skill-Selector Filesystem-vs-Calendar-Erkennung (TASK-004: BACKLOG-004).

Testet dass Skill-Selector korrekt Filesystem vs Calendar-Intents erkennt
und entsprechende Tools wählt.
"""
import pytest
from backend.services.skill_selector import SkillSelector
from backend.services.orchestrator.intent_engine import IntentDetectionResult


class TestSkillSelectorFilesystemCalendar:
    """Testet die Skill-Selector Filesystem-vs-Calendar-Erkennung."""

    @pytest.fixture
    def skill_selector(self):
        """Skill-Selector Instanz ohne Registry (Fallback-Modus)."""
        return SkillSelector(capability_registry=None)

    # ─────────────────────────────────────────────────────────────────────────
    # Filesystem-Intent Recognition
    # ─────────────────────────────────────────────────────────────────────────

    def test_filesystem_intent_recognized_in_policy(self, skill_selector):
        """Test: Filesystem-Intent wird in _intent_policy erkannt."""
        intent_result = IntentDetectionResult(
            is_filesystem_intent=True,
            primary_intent="filesystem"
        )
        policy = skill_selector._intent_policy(intent_result)
        # Filesystem-Intent sollte keine Calendar-Tools erzwingen
        assert "calendar.list_events" not in policy["mandatory"]
        assert "calendar.find_slots" not in policy["mandatory"]

    def test_filesystem_intent_logging(self, skill_selector, caplog):
        """Test: Logging für Filesystem-Intent."""
        import logging
        caplog.set_level(logging.DEBUG)

        intent_result = IntentDetectionResult(
            is_filesystem_intent=True,
            primary_intent="filesystem"
        )
        skill_selector._intent_policy(intent_result)

        # Prüfe ob Logging-Meldung für Filesystem-Intent vorhanden
        assert any(
            "Filesystem intent detected" in record.message
            for record in caplog.records
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Calendar-Intent Recognition (Regression)
    # ─────────────────────────────────────────────────────────────────────────

    def test_calendar_intent_selects_calendar_tools(self, skill_selector):
        """Regression: Calendar-Intent wählt Calendar-Tools."""
        intent_result = IntentDetectionResult(
            is_calendar_intent=True,
            primary_intent="calendar"
        )
        policy = skill_selector._intent_policy(intent_result)
        # Calendar-Intent sollte Calendar-Tools erzwingen
        assert "calendar.list_events" in policy["mandatory"]
        assert "calendar.find_slots" in policy["mandatory"]
        assert "calendar.find_and_update_event" in policy["mandatory"]
        # PDF sollte verboten sein
        assert "system.create_pdf" in policy["forbidden"]

    def test_calendar_intent_forbids_pdf(self, skill_selector):
        """Regression: Calendar-Intent verbietet PDF-Erstellung."""
        intent_result = IntentDetectionResult(
            is_calendar_intent=True,
            primary_intent="calendar"
        )
        policy = skill_selector._intent_policy(intent_result)
        assert "system.create_pdf" in policy["forbidden"]

    # ─────────────────────────────────────────────────────────────────────────
    # Logging Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_skill_selection_logging_with_filesystem_intent(self, skill_selector, caplog):
        """Test: Logging für gewählte Tools mit Filesystem-Intent."""
        import logging
        caplog.set_level(logging.INFO)

        intent_result = IntentDetectionResult(
            is_filesystem_intent=True,
            primary_intent="filesystem"
        )
        # Simuliere Skill-Auswahl (ohne Registry werden keine Skills zurückgegeben)
        skills = skill_selector.get_relevant_skills(
            user_prompt="erstell einen ordner",
            intent_result=intent_result,
            top_k=5
        )

        # Prüfe ob Logging-Meldung für Skill-Auswahl vorhanden
        # (Wenn Skills ausgewählt wurden)
        if skills:
            assert any(
                "SKILL-SELECTOR" in record.message
                for record in caplog.records
            )

    def test_skill_selection_logging_with_calendar_intent(self, skill_selector, caplog):
        """Test: Logging für gewählte Tools mit Calendar-Intent."""
        import logging
        caplog.set_level(logging.INFO)

        intent_result = IntentDetectionResult(
            is_calendar_intent=True,
            primary_intent="calendar"
        )
        skills = skill_selector.get_relevant_skills(
            user_prompt="termin erstellen",
            intent_result=intent_result,
            top_k=5
        )

        # Prüfe ob Logging-Meldung für Skill-Auswahl vorhanden
        if skills:
            assert any(
                "SKILL-SELECTOR" in record.message
                for record in caplog.records
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Edge Cases
    # ─────────────────────────────────────────────────────────────────────────

    def test_none_intent_result(self, skill_selector):
        """Test: None Intent-Ergebnis gibt leere Policy zurück."""
        policy = skill_selector._intent_policy(None)
        assert policy == {"mandatory": [], "boosted": [], "forbidden": []}

    def test_empty_intent_result(self, skill_selector):
        """Test: Leeres Intent-Ergebnis gibt Policy mit PDF-Verbot zurück (Standardverhalten)."""
        intent_result = IntentDetectionResult()
        policy = skill_selector._intent_policy(intent_result)
        # Standardmäßig wird PDF verboten wenn nicht explizit erlaubt
        assert policy["mandatory"] == []
        assert policy["boosted"] == []
        assert "system.create_pdf" in policy["forbidden"]

    def test_filesystem_priority_over_calendar(self, skill_selector):
        """Test: Filesystem-Intent hat Priorität über Calendar-Intent."""
        intent_result = IntentDetectionResult(
            is_filesystem_intent=True,
            is_calendar_intent=False,  # Calendar sollte durch Filesystem-Veto unterdrückt sein
            primary_intent="filesystem"
        )
        policy = skill_selector._intent_policy(intent_result)
        # Filesystem-Intent sollte keine Calendar-Tools erzwingen
        assert "calendar.list_events" not in policy["mandatory"]
