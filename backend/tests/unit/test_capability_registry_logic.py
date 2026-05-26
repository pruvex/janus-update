"""Unit tests for CapabilityRegistry filter logic (TASK-069.7).

These tests verify the deterministic filtering, deduplication, and
validation rules of `get_verified_capabilities_for_overview()` without
loading the real registry JSON or skill files.
"""

import pytest
from backend.services.capability_registry import CapabilityRegistry


class TestCapabilityRegistryFilterLogic:
    """Test suite for CapabilityRegistry.get_verified_capabilities_for_overview."""

    @pytest.fixture
    def empty_registry(self):
        """Return a CapabilityRegistry with no loaded data."""
        reg = CapabilityRegistry(registry_path="/dev/null", skills_dir="/dev/null")
        reg._registry = {"categories": {}}
        reg._available_skills = set()
        return reg

    def _make_category(self, abilities: list) -> dict:
        """Helper to build a minimal category dict."""
        return {
            "display_name": {"de": "Test-Kategorie", "en": "Test Category"},
            "abilities": abilities,
        }

    def test_filter_status_verified(self, empty_registry):
        """Only abilities with status='verified' are returned."""
        reg = empty_registry
        reg._registry = {
            "categories": {
                "test": self._make_category([
                    {
                        "id": "test.verified",
                        "label": {"de": "Verifiziert", "en": "Verified"},
                        "how_to": {"de": "So geht's.", "en": "How to."},
                        "status": "verified",
                        "confidence": 1.0,
                    },
                    {
                        "id": "test.draft",
                        "label": {"de": "Entwurf", "en": "Draft"},
                        "how_to": {"de": "So geht's.", "en": "How to."},
                        "status": "draft",
                        "confidence": 1.0,
                    },
                ])
            }
        }
        result = reg.get_verified_capabilities_for_overview("de")
        ids = [r["id"] for r in result]
        assert "test.verified" in ids
        assert "test.draft" not in ids

    def test_filter_confidence_threshold(self, empty_registry):
        """Confidence >= 0.70 passes; 0.69 is skipped."""
        reg = empty_registry
        reg._registry = {
            "categories": {
                "test": self._make_category([
                    {
                        "id": "test.high",
                        "label": {"de": "Hoch", "en": "High"},
                        "how_to": {"de": "So.", "en": "So."},
                        "status": "verified",
                        "confidence": 0.70,
                    },
                    {
                        "id": "test.low",
                        "label": {"de": "Niedrig", "en": "Low"},
                        "how_to": {"de": "So.", "en": "So."},
                        "status": "verified",
                        "confidence": 0.69,
                    },
                ])
            }
        }
        result = reg.get_verified_capabilities_for_overview("de")
        ids = [r["id"] for r in result]
        assert "test.high" in ids
        assert "test.low" not in ids

    def test_deduplication(self, empty_registry):
        """Duplicate IDs are returned only once."""
        reg = empty_registry
        reg._registry = {
            "categories": {
                "cat_a": self._make_category([
                    {
                        "id": "test.dupe",
                        "label": {"de": "Dupe", "en": "Dupe"},
                        "how_to": {"de": "So.", "en": "So."},
                        "status": "verified",
                        "confidence": 1.0,
                    }
                ]),
                "cat_b": self._make_category([
                    {
                        "id": "test.dupe",
                        "label": {"de": "Dupe", "en": "Dupe"},
                        "how_to": {"de": "So.", "en": "So."},
                        "status": "verified",
                        "confidence": 1.0,
                    }
                ]),
            }
        }
        result = reg.get_verified_capabilities_for_overview("de")
        assert len(result) == 1
        assert result[0]["id"] == "test.dupe"

    def test_missing_required_fields(self, empty_registry):
        """Entries missing label or how_to are skipped."""
        reg = empty_registry
        reg._registry = {
            "categories": {
                "test": self._make_category([
                    {
                        "id": "test.complete",
                        "label": {"de": "Komplett", "en": "Complete"},
                        "how_to": {"de": "So.", "en": "So."},
                        "status": "verified",
                        "confidence": 1.0,
                    },
                    {
                        "id": "test.no_label",
                        "how_to": {"de": "So.", "en": "So."},
                        "status": "verified",
                        "confidence": 1.0,
                    },
                    {
                        "id": "test.no_how_to",
                        "label": {"de": "Label", "en": "Label"},
                        "status": "verified",
                        "confidence": 1.0,
                    },
                ])
            }
        }
        result = reg.get_verified_capabilities_for_overview("de")
        ids = [r["id"] for r in result]
        assert "test.complete" in ids
        assert "test.no_label" not in ids
        assert "test.no_how_to" not in ids

    def test_unknown_category_mapped_to_sonstiges(self, empty_registry):
        """Categories not in ALLOWED_CATEGORIES are normalized to 'Sonstiges' by the Registry."""
        reg = empty_registry
        reg._registry = {
            "categories": {
                "fremd": {
                    "display_name": {"de": "Fremde Kategorie", "en": "Foreign Category"},
                    "abilities": [
                        {
                            "id": "test.fremd",
                            "label": {"de": "Fremd", "en": "Foreign"},
                            "how_to": {"de": "So.", "en": "So."},
                            "status": "verified",
                            "confidence": 1.0,
                        }
                    ],
                }
            }
        }
        result = reg.get_verified_capabilities_for_overview("de")
        assert len(result) == 1
        assert result[0]["category"] == "Sonstiges"
