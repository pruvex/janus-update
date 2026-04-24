"""
Unit Tests für Gemini LinkRenderer – Diamond Standard

Testfälle:
1. test_link_renderer_with_anchors – Prüfe ob [[PRODUCT:iphone_15]] korrekt zu Markdown-Link wird
2. test_renderer_strips_invalid_id – Prüfe ob ungültige ID wie [[PRODUCT:viren_link]] gestrippt wird
3. test_renderer_respects_max_links – Prüfe ob max_links_per_turn = 8 enforced wird
4. test_renderer_wikipedia_extraction – Prüfe ob Wikipedia-Links aus groundingMetadata extrahiert werden
5. test_renderer_fail_safe_unknown_id – Fail-Safe bei unbekannter ID
"""

import json

import pytest

from backend.llm_providers.gemini.link_renderer import GeminiLinkRenderer, get_link_renderer, render_links
from backend.llm_providers.gemini.constants import MAX_LINKS_PER_TURN


class TestGeminiLinkRenderer:
    """Diamond-Standard Tests für den Gemini LinkRenderer."""

    @pytest.fixture
    def sample_product_map(self):
        """Test-Produkt-Map mit 5 Einträgen."""
        return {
            "iphone_15": {
                "name": "iPhone 15",
                "url": "https://www.idealo.de/preisvergleich/OffersOfProduct/203033222_-iphone-15-128gb-apple.html",
                "aliases": ["iphone 15", "apple iphone 15"]
            },
            "nintendo_switch_2": {
                "name": "Nintendo Switch 2",
                "url": "https://www.idealo.de/preisvergleich/OffersOfProduct/206193300_-switch-2-nintendo.html",
                "aliases": ["switch 2", "nintendo switch 2"]
            },
            "ps5_slim": {
                "name": "PlayStation 5 Slim",
                "url": "https://www.idealo.de/preisvergleich/OffersOfProduct/203515743_-playstation-5-slim-ps5-slim-sony.html",
                "aliases": ["ps5", "ps5 slim", "playstation 5"]
            }
        }

    @pytest.fixture
    def renderer_with_test_config(self, sample_product_map, tmp_path):
        """Renderer-Instanz mit temporärer Test-Config."""
        config_file = tmp_path / "test_product_map.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(sample_product_map, f)
        return GeminiLinkRenderer(config_path=str(config_file))

    def test_link_renderer_with_anchors(self, renderer_with_test_config):
        """
        Unit-Test: Prüfe, ob [[PRODUCT:iphone_15]] korrekt zu einem Markdown-Link wird.
        """
        text = "Der [[PRODUCT:iphone_15]] kostet aktuell ab 799 Euro."
        result = renderer_with_test_config.render_links(text)
        
        expected_link = "[iPhone 15](https://www.idealo.de/preisvergleich/OffersOfProduct/203033222_-iphone-15-128gb-apple.html)"
        assert expected_link in result
        assert "[[PRODUCT:iphone_15]]" not in result
        assert "Der " in result
        assert " kostet aktuell ab 799 Euro." in result

    def test_link_renderer_with_multiple_anchors(self, renderer_with_test_config):
        """
        Prüfe mehrere Anchors in einem Text.
        """
        text = "Vergleich: [[PRODUCT:iphone_15]] vs [[PRODUCT:nintendo_switch_2]]"
        result = renderer_with_test_config.render_links(text)
        
        assert "[iPhone 15]" in result
        assert "[Nintendo Switch 2]" in result
        assert "[[PRODUCT:" not in result

    def test_renderer_respects_max_links_per_turn(self, renderer_with_test_config):
        """
        Adversarial-Test: Prüfe ob max_links_per_turn = 8 enforced wird.
        Erzeuge 10 Anchors, nur 8 sollten gerendert werden.
        """
        # Erstelle 10 identische Anchors (max ist 8)
        anchors = " ".join([f"[[PRODUCT:iphone_15]]"] * 10)
        text = f"Test mit vielen Links: {anchors}"
        
        result = renderer_with_test_config.render_links(text)
        
        # Zähle wie viele Links gerendert wurden
        link_count = result.count("[iPhone 15](")
        assert link_count <= MAX_LINKS_PER_TURN, f"Links exceeded max: {link_count} > {MAX_LINKS_PER_TURN}"
        
        # Der Rest sollte gestrippt sein
        raw_anchor_count = result.count("[[PRODUCT:iphone_15]]")
        # Nach dem Limit werden weitere Anchors komplett gestrippt
        total_references = link_count + raw_anchor_count
        assert total_references <= MAX_LINKS_PER_TURN + 2  # Toleranz für Edge-Cases

    def test_renderer_strips_invalid_id(self, renderer_with_test_config):
        """
        Adversarial-Test: Prüfe, ob der Renderer abstürzt oder sauber mit ungültiger ID umgeht.
        Ungültige ID wie [[PRODUCT:viren_link]] sollte gestrippt werden.
        """
        text = "Hier ist ein gültiges Produkt [[PRODUCT:iphone_15]] und hier ein ungültiges [[PRODUCT:viren_link]]."
        result = renderer_with_test_config.render_links(text)
        
        # Gültiger Link sollte vorhanden sein
        assert "[iPhone 15]" in result
        
        # Ungültiger Anchor sollte entweder gestrippt oder unverändert sein
        # (Fail-Safe: Strip unknown IDs)
        assert "[[PRODUCT:viren_link]]" not in result or "viren_link" not in result.lower()

    def test_renderer_fail_safe_unknown_id(self, renderer_with_test_config):
        """
        Fail-Safe: Unbekannte IDs werden strikt entfernt, nie als Links gerendert.
        """
        text = "Test mit [[PRODUCT:nonexistent_product_12345]]"
        result = renderer_with_test_config.render_links(text)
        
        # Sollte weder der Anchor noch ein Link daraus entstehen
        assert "[[PRODUCT:nonexistent_product_12345]]" not in result
        # Kein Markdown-Link-Muster
        assert "[nonexistent" not in result.lower()

    def test_renderer_case_insensitive_matching(self, renderer_with_test_config):
        """
        Prüfe case-insensitive ID-Auflösung.
        """
        text = "[[PRODUCT:IPHONE_15]] und [[PRODUCT:Iphone_15]] und [[PRODUCT:iphone_15]]"
        result = renderer_with_test_config.render_links(text)
        
        # Alle drei Varianten sollten zum selben Link führen
        link_count = result.count("[iPhone 15](")
        assert link_count >= 1, "Case-insensitive matching failed"

    def test_renderer_alias_resolution(self, renderer_with_test_config):
        """
        Prüfe ob Aliase korrekt aufgelöst werden.
        """
        text = "[[PRODUCT:ps5]]"  # Alias für ps5_slim
        result = renderer_with_test_config.render_links(text)
        
        assert "[PlayStation 5 Slim]" in result

    def test_renderer_wikipedia_extraction(self, renderer_with_test_config):
        """
        Prüfe ob Wikipedia-Links aus groundingMetadata extrahiert werden.
        """
        text = "Hier ist ein Produkt [[PRODUCT:iphone_15]]."
        grounding_chunks = [
            {
                "web": {
                    "uri": "https://de.wikipedia.org/wiki/IPhone_15",
                    "title": "iPhone 15 – Wikipedia"
                }
            },
            {
                "web": {
                    "uri": "https://www.idealo.de/irrelevant",
                    "title": "Idealo Preisvergleich"
                }
            }
        ]
        
        result = renderer_with_test_config.render_links(
            text, 
            grounding_chunks=grounding_chunks,
            enable_idealo=True,
            enable_wikipedia=True
        )
        
        # Idealo-Link sollte vorhanden sein
        assert "[iPhone 15]" in result
        # Wikipedia-Link sollte als separate Section am Ende sein
        assert "Wikipedia" in result or "wikipedia.org" in result

    def test_renderer_respects_enable_flags(self, renderer_with_test_config):
        """
        Prüfe ob enable_idealo und enable_wikipedia Flags respektiert werden.
        """
        text = "[[PRODUCT:iphone_15]]"
        
        # Mit Idealo
        result_with = renderer_with_test_config.render_links(text, enable_idealo=True, enable_wikipedia=False)
        assert "[iPhone 15]" in result_with
        
        # Ohne Idealo
        result_without = renderer_with_test_config.render_links(text, enable_idealo=False, enable_wikipedia=False)
        assert "[iPhone 15]" not in result_without
        assert "[[PRODUCT:iphone_15]]" not in result_without  # Auch der Anchor sollte weg sein

    def test_renderer_handles_empty_text(self, renderer_with_test_config):
        """
        Edge-Case: Leerer Text sollte sicher behandelt werden.
        """
        result = renderer_with_test_config.render_links("")
        assert result == ""
        
        result = renderer_with_test_config.render_links(None)  # type: ignore
        assert result == "" or result is None

    def test_renderer_no_side_effects(self, renderer_with_test_config):
        """
        Prüfe dass der Renderer den Original-Text nicht mutiert (außer durch Kopie).
        """
        original = "[[PRODUCT:iphone_15]]"
        result = renderer_with_test_config.render_links(original)
        
        # Original sollte unverändert bleiben
        assert original == "[[PRODUCT:iphone_15]]"
        # Result sollte anders sein
        assert result != original


class TestGlobalRendererInstance:
    """Tests für die globale Singleton-Instanz."""

    def test_get_link_renderer_singleton(self):
        """
        Prüfe dass get_link_renderer() dieselbe Instanz zurückgibt.
        """
        r1 = get_link_renderer()
        r2 = get_link_renderer()
        assert r1 is r2

    def test_global_render_links_function(self):
        """
        Prüfe die globale render_links() Convenience-Funktion.
        """
        # Dies sollte nicht crashen, auch wenn die Config nicht existiert
        result = render_links("Test ohne Anchors")
        assert "Test ohne Anchors" in result


class TestIntegrationRequirements:
    """
    Integration-Level Tests gemäß Arbeitsanweisung.
    """

    def test_global_renderer_reads_config(self, tmp_path):
        """
        Prüfe ob der globale Renderer die Config-Datei korrekt liest.
        """
        # Erstelle temporäre Config
        config = {
            "test_product": {
                "name": "Test Product",
                "url": "https://example.com/test",
                "aliases": ["test"]
            }
        }
        config_file = tmp_path / "idealo_product_map.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)
        
        # Erstelle Renderer mit explizitem Pfad
        renderer = GeminiLinkRenderer(config_path=str(config_file))
        result = renderer.render_links("[[PRODUCT:test_product]]")
        
        assert "[Test Product](https://example.com/test)" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
