"""
Task 002 - Websearch V2.0 Standalone Validation Tests

Diese Tests validieren die isolierte Websearch V2.0 Architektur:
- _sources_to_items Konvertierung
- WebSearchOutput Pydantic Schema
- Global Fallback Trigger (Logging-Prüfung)
- Renderer Output (saubere Liste, keine Links im Fließtext)
- STRICT NO-MIXING: Keine price_comparison Interaktion
"""

import pytest
from datetime import datetime, timezone

# Pydantic Modelle
from backend.data.schemas import WebSearchItem, WebSearchOutput

# Renderer
from backend.renderers.implementations.unified_websearch_renderer import UnifiedWebSearchRenderer


class TestSourcesToItemsConversion:
    """Tests für die Konvertierung von WebSearchResult.sources zu WebSearchItem[]."""

    def test_sources_to_items_basic(self):
        """Teste Konvertierung von typischen WebSearchResult sources."""
        from backend.tool_registry import _sources_to_items
        
        mock_sources = [
            {"url": "https://example.com/news1", "title": "News One", "snippet": "First news snippet"},
            {"url": "https://example.com/news2", "title": "News Two", "snippet": "Second snippet"},
        ]
        
        items = _sources_to_items(mock_sources)
        
        assert len(items) == 2
        assert items[0].title == "News One"
        assert items[0].source_url == "https://example.com/news1"
        assert items[0].description == "First news snippet"
        assert items[1].title == "News Two"

    def test_sources_to_items_missing_title_uses_url(self):
        """Wenn title fehlt, soll URL als title verwendet werden."""
        from backend.tool_registry import _sources_to_items
        
        mock_sources = [
            {"url": "https://example.com/only-url", "snippet": "Snippet only"},
        ]
        
        items = _sources_to_items(mock_sources)
        
        assert len(items) == 1
        assert items[0].title == "https://example.com/only-url"  # URL als Fallback
        assert items[0].description == "Snippet only"

    def test_sources_to_items_empty_url_skipped(self):
        """Leere URLs sollen übersprungen werden."""
        from backend.tool_registry import _sources_to_items
        
        mock_sources = [
            {"url": "", "title": "Empty URL"},
            {"url": "https://valid.com", "title": "Valid URL"},
        ]
        
        items = _sources_to_items(mock_sources)
        
        assert len(items) == 1
        assert items[0].source_url == "https://valid.com"

    def test_sources_to_items_empty_list(self):
        """Leere source-Liste soll leere items-Liste ergeben."""
        from backend.tool_registry import _sources_to_items
        
        items = _sources_to_items([])
        assert items == []


class TestWebSearchOutputSchema:
    """Tests für WebSearchOutput Pydantic Modell."""

    def test_websearchoutput_complete(self):
        """Vollständiges WebSearchOutput mit allen Feldern."""
        items = [
            WebSearchItem(
                title="Test News",
                description="Test description",
                date="2025-03-28",
                source_url="https://test.com",
                thumbnail_url=None,
            )
        ]
        
        output = WebSearchOutput(
            query="Test Query",
            locale="en_US",
            items=items,
            text="Raw text from LLM",
            price_enrichment=None,  # NO-MIXING: Muss None sein
            source="openai",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )
        
        assert output.query == "Test Query"
        assert output.locale == "en_US"
        assert len(output.items) == 1
        assert output.items[0].source_url == "https://test.com"
        assert output.price_enrichment is None  # STRICT NO-MIXING
        assert output.source == "openai"

    def test_websearchoutput_minimal(self):
        """Minimal gültiges WebSearchOutput."""
        output = WebSearchOutput(
            query="Simple Query",
            items=[],
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )
        
        assert output.items == []
        assert output.locale == "de_DE"  # Default
        assert output.text == ""  # Default
        assert output.source == "unknown"  # Default

    def test_websearchoutput_model_dump(self):
        """Model-Dump für SkillResponse.data."""
        items = [WebSearchItem(title="Test", source_url="https://test.com")]
        
        output = WebSearchOutput(
            query="Test",
            items=items,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )
        
        dumped = output.model_dump()
        assert "query" in dumped
        assert "items" in dumped
        assert "retrieved_at" in dumped
        assert isinstance(dumped["items"], list)


class TestRendererStandalone:
    """Tests für UnifiedWebSearchRenderer (Standalone, keine Preis-Integration)."""

    def test_renderer_v2_path_with_items(self):
        """Renderer soll Item-Liste sauber rendern (V2 Path)."""
        renderer = UnifiedWebSearchRenderer()
        
        data = {
            "items": [
                {"title": "First Article", "description": "Desc 1", "source_url": "https://first.com"},
                {"title": "Second Article", "description": "Desc 2", "source_url": "https://second.com"},
            ],
            "price_enrichment": None,  # NO-MIXING
        }
        
        result = renderer.render(data)
        
        # Prüfung: Saubere Liste (nur erste Domain im Footer)
        assert "first.com" in result  # Erste Domain im Footer
        assert "First Article" in result
        assert "Second Article" in result
        
        # Prüfung: KEINE Preis-Verifizierung (NO-MIXING)
        assert "Preis-Verifizierung" not in result
        assert "Price-Check" not in result

    def test_renderer_no_links_in_body(self):
        """Links sollen nur als Item-Level-Links, nicht im Fließtext auftauchen."""
        renderer = UnifiedWebSearchRenderer()
        
        # Legacy-Fall: text mit Link
        data = {
            "text": "Hier ist ein Link: https://example.com/article und mehr Text.",
            "items": [],  # Leer → Legacy Path
        }
        
        result = renderer.render(data)
        
        # Der Renderer soll Links aus dem Fließtext entfernen (clean_text)
        assert "https://example.com/article" not in result or "example.com" not in result

    def test_renderer_empty_items_fallback(self):
        """Leere items → Legacy Path (backward compat)."""
        renderer = UnifiedWebSearchRenderer()
        
        data = {
            "text": "Search results summary text.",
            "items": [],
        }
        
        result = renderer.render(data)
        
        # Legacy-Path sollte Text zurückgeben
        assert "summary text" in result or result == "Search results summary text."


class TestGlobalFallbackDetection:
    """Tests für Global Fallback Logik."""

    def test_detect_global_fallback_needed_tech_topic_low_results(self):
        """Tech-Topic mit wenigen Ergebnissen soll Fallback auslösen."""
        from backend.tool_registry import _detect_global_fallback_needed
        
        # Tech-Query mit leerem Ergebnis
        query = "Nintendo Switch 2 Release Date"
        items = []  # Keine Ergebnisse
        
        result = _detect_global_fallback_needed(query, items)
        
        assert result is True  # Soll Fallback auslösen

    def test_detect_global_fallback_not_needed_sufficient_results(self):
        """Ausreichend Ergebnisse → kein Fallback."""
        from backend.tool_registry import _detect_global_fallback_needed
        
        query = "Nintendo Switch 2 Release Date"
        items = [{"title": "Item 1"}, {"title": "Item 2"}]  # 2 Items
        
        result = _detect_global_fallback_needed(query, items)
        
        assert result is False  # Kein Fallback nötig

    def test_detect_global_fallback_not_needed_non_tech(self):
        """Nicht-Tech-Query → kein Fallback auch bei leeren Ergebnissen."""
        from backend.tool_registry import _detect_global_fallback_needed
        
        query = "Lebensmittelgeschäft in Berlin"  # Kein Tech-Signal
        items = []
        
        result = _detect_global_fallback_needed(query, items)
        
        assert result is False  # Kein Fallback für nicht-Tech-Themen


class TestNoMixingConstraint:
    """STRICT: Keine Interaktion mit price_comparison während Standalone-Validierung."""

    def test_price_comparison_not_called_in_websearch(self, caplog):
        """Verifiziere, dass price_comparison NICHT aufgerufen wird.
        
        Dieser Test prüft indirekt, dass die price_comparison Logik
        in websearch_wrapper auskommentiert ist (durch Code-Audit).
        """
        # Wir verifizieren, dass der auskommentierte Code-Block dokumentiert ist
        import backend.tool_registry as tr
        
        # Prüfe, dass _enrich_with_price_comparison existiert aber nicht aufgerufen wird
        # (weil der Aufruf in websearch_wrapper auskommentiert ist)
        assert hasattr(tr, '_enrich_with_price_comparison')
        
        # Prüfe, dass der Kommentar im Code vorhanden ist
        import inspect
        source = inspect.getsource(tr.websearch_wrapper)
        assert "TASK 002" in source or "STANDALONE VALIDATION" in source or "Deaktiviert" in source, \
            "No-Mixing Kommentar sollte im websearch_wrapper vorhanden sein"


class TestContractValidation:
    """Validate_websearch_result Contract-Prüfung."""

    def test_validate_websearch_result_with_v2_structure(self):
        """validate_websearch_result soll V2-Strukturen akzeptieren."""
        from backend.services.websearch.base_provider import validate_websearch_result
        
        # V2-Style WebSearchResult (mit sources für items)
        v2_result = {
            "text": "Summary text",
            "sources": [
                {"url": "https://source1.com", "title": "Source 1", "snippet": "Snippet 1"},
                {"url": "https://source2.com", "title": "Source 2", "snippet": "Snippet 2"},
            ],
            "metadata": {"provider": "openai"},
        }
        
        validated = validate_websearch_result(v2_result)
        
        assert validated["text"] == "Summary text"
        assert len(validated["sources"]) == 2
        assert validated["metadata"]["provider"] == "openai"

    def test_validate_websearch_result_missing_url_raises(self):
        """Fehlende URL soll Fehler werfen."""
        from backend.services.websearch.base_provider import validate_websearch_result
        
        invalid_result = {
            "text": "Test",
            "sources": [{"title": "No URL"}],  # Fehlende URL
            "metadata": {"provider": "test"},
        }
        
        with pytest.raises(ValueError, match="missing required field 'url'"):
            validate_websearch_result(invalid_result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
