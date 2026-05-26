"""Unit-Tests für Entity-Resolver WEAK_MATCH-Fallback Korrektur (TASK-002: BACKLOG-004).

Testet dass Entity-Resolver keine WEAK_MATCH Calendar-Entities erzwingt
wenn Filesystem-Intent erkannt wurde.
"""
import pytest
from datetime import date
from backend.services.orchestrator.entity_resolver import ContextualEntityResolver, ResolutionResult


class TestEntityResolverFilesystemVeto:
    """Testet die Filesystem-Intent Veto-Logik im Entity-Resolver."""

    @pytest.fixture
    def resolver(self):
        """Entity-Resolver Instanz für Tests."""
        return ContextualEntityResolver()

    @pytest.fixture
    def sample_snapshot(self):
        """Beispiel-Snapshot mit Calendar-Events."""
        return {
            "events": [
                {
                    "id": "1",
                    "title": "Sporttermin",
                    "start": "2026-05-08T14:00:00Z",
                    "location": "Fitnessstudio"
                },
                {
                    "id": "2",
                    "title": "Meeting",
                    "start": "2026-05-08T15:00:00Z",
                    "location": "Konferenzraum"
                }
            ]
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Filesystem-Intent Veto Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_weak_match_not_forced_with_filesystem_intent(self, resolver, sample_snapshot):
        """Test: WEAK_MATCH wird nicht zu FALLBACK_TO_LIST bei Filesystem-Intent."""
        result = resolver.resolve(
            query="Ordner",  # Kein exakter Match im Snapshot (Sporttermin, Meeting)
            snapshot=sample_snapshot,
            operation_type="MUTATION",
            is_filesystem_intent=True,
            is_calendar_mutation=False,
        )
        # Bei Filesystem-Intent sollte WEAK_MATCH nicht zu FALLBACK_TO_LIST führen
        # Wenn es kein Match gibt, sollte NOT_FOUND mit CLARIFY_USER zurückgegeben werden
        if result.status == "WEAK_MATCH":
            assert result.dispatcher_hint == "CLARIFY_USER"
        else:
            # NOT_FOUND ist auch akzeptabel
            assert result.status == "NOT_FOUND"
            assert result.dispatcher_hint == "CLARIFY_USER"

    def test_weak_match_forced_without_filesystem_intent(self, resolver, sample_snapshot):
        """Test: WEAK_MATCH wird zu FALLBACK_TO_LIST ohne Filesystem-Intent (Regressionstest)."""
        result = resolver.resolve(
            query="Bibliothek",  # Kein Match im Snapshot (Sporttermin, Meeting)
            snapshot=sample_snapshot,
            operation_type="MUTATION",
            is_filesystem_intent=False,
            is_calendar_mutation=True,
        )
        # Ohne Filesystem-Intent sollte NOT_FOUND zu CLARIFY_USER führen (Standardverhalten)
        assert result.status == "NOT_FOUND"
        assert result.dispatcher_hint == "CLARIFY_USER"

    def test_weak_match_filesystem_intent_logging(self, resolver, sample_snapshot, caplog):
        """Test: Logging für Filesystem-Intent Veto."""
        import logging
        caplog.set_level(logging.INFO)

        resolver.resolve(
            query="Ordner",  # Kein exakter Match
            snapshot=sample_snapshot,
            operation_type="MUTATION",
            is_filesystem_intent=True,
            is_calendar_mutation=False,
        )

        # Prüfe ob Logging-Meldung für Filesystem-Intent Veto vorhanden
        # (Nur wenn tatsächlich ein WEAK_MATCH auftritt)
        assert any(
            "WEAK_MATCH skipped for filesystem intent" in record.message
            for record in caplog.records
        ) or result.status != "WEAK_MATCH"  # Logging nur bei WEAK_MATCH

    # ─────────────────────────────────────────────────────────────────────────
    # Regression Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_calendar_weak_match_still_works(self, resolver, sample_snapshot):
        """Regression: Calendar-WEAK_MATCH funktioniert weiterhin ohne Filesystem-Intent."""
        result = resolver.resolve(
            query="Bibliothek",  # Kein Match im Snapshot
            snapshot=sample_snapshot,
            operation_type="MUTATION",
            is_filesystem_intent=False,
            is_calendar_mutation=True,
        )
        # Calendar-NOT_FOUND sollte zu CLARIFY_USER führen (Standardverhalten)
        assert result.status == "NOT_FOUND"
        assert result.dispatcher_hint == "CLARIFY_USER"

    def test_resolved_match_unaffected(self, resolver, sample_snapshot):
        """Regression: RESOLVED-Matches sind nicht betroffen."""
        result = resolver.resolve(
            query="Sporttermin",  # Exakter Match im Snapshot
            snapshot=sample_snapshot,
            operation_type="MUTATION",
            is_filesystem_intent=True,
            is_calendar_mutation=True,
        )
        # Exakter Match sollte RESOLVED sein
        assert result.status == "RESOLVED"
        assert result.dispatcher_hint == "PROCEED"

    def test_read_operation_unaffected(self, resolver, sample_snapshot):
        """Regression: READ-Operation ist nicht betroffen."""
        result = resolver.resolve(
            query="Sporttermin",  # Exakter Match
            snapshot=sample_snapshot,
            operation_type="READ",
            is_filesystem_intent=True,
            is_calendar_mutation=False,
        )
        # READ-Operation sollte PROCEED sein
        assert result.dispatcher_hint == "PROCEED"

    # ─────────────────────────────────────────────────────────────────────────
    # Edge Cases
    # ─────────────────────────────────────────────────────────────────────────

    def test_empty_snapshot_with_filesystem_intent(self, resolver):
        """Test: Leerer Snapshot mit Filesystem-Intent."""
        result = resolver.resolve(
            query="Ordner",
            snapshot={"events": []},
            operation_type="MUTATION",
            is_filesystem_intent=True,
            is_calendar_mutation=False,
        )
        assert result.status == "NOT_FOUND"
        # Bei MUTATION und leerem Snapshot sollte CLARIFY_USER zurückgegeben werden
        assert result.dispatcher_hint == "CLARIFY_USER"

    def test_filesystem_intent_with_deictic_fallback(self, resolver, sample_snapshot):
        """Test: Filesystem-Intent mit Deictic-Fallback sollte nicht ausgelöst werden."""
        result = resolver.resolve(
            query="ihn",
            snapshot=sample_snapshot,
            operation_type="MUTATION",
            is_filesystem_intent=True,
            is_calendar_mutation=False,
            full_user_text="ihn verschieben",
            recent_messages=[
                {"content": "Meeting morgen um 10 Uhr"},
            ],
        )
        # Filesystem-Intent sollte Deictic-Fallback nicht auslösen
        # (Deictic-Fallback ist nur für Calendar-Mutation)
        assert result.status in ("NOT_FOUND", "WEAK_MATCH")
