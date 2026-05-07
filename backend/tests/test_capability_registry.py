"""Unit tests for CapabilityRegistry — FEAT-HELP-001.

Tests: Load, Discovery, Overview, How-To, Navigation, Orphan-Detection
"""

import json
import pytest
import tempfile
from pathlib import Path

from backend.services.capability_registry import CapabilityRegistry


class TestCapabilityRegistryLoad:
    """Tests for registry loading (§8.1 Unit Tests)."""

    def test_registry_loads_without_error(self, tmp_path: Path):
        """Registry loads successfully from valid JSON."""
        # Create test registry
        registry_data = {
            "version": "1.0.0",
            "categories": {
                "test_cat": {
                    "display_name": {"de": "Test", "en": "Test"},
                    "icon": "🧪",
                    "description": {"de": "Test category", "en": "Test category"},
                    "abilities": [],
                    "ui_locations": {}
                }
            }
        }
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps(registry_data), encoding="utf-8")

        # Create empty skills dir
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Load
        reg = CapabilityRegistry(str(registry_file), str(skills_dir))
        reg.load()

        assert reg._registry["version"] == "1.0.0"
        assert "test_cat" in reg.all_categories()

    def test_registry_handles_missing_file_gracefully(self, tmp_path: Path):
        """Missing registry file doesn't crash — logs error and uses empty registry."""
        registry_file = tmp_path / "nonexistent.json"
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        reg = CapabilityRegistry(str(registry_file), str(skills_dir))
        reg.load()

        assert reg._registry["version"] == "0.0.0"
        assert reg.all_categories() == []

    def test_registry_handles_invalid_json_gracefully(self, tmp_path: Path):
        """Invalid JSON doesn't crash — logs error and uses empty registry."""
        registry_file = tmp_path / "registry.json"
        registry_file.write_text("not valid json", encoding="utf-8")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        reg = CapabilityRegistry(str(registry_file), str(skills_dir))
        reg.load()

        assert reg._registry["version"] == "0.0.0"


class TestCapabilityRegistryDiscovery:
    """Tests for skill discovery and validation (§5.2 Auto-Discovery)."""

    def test_auto_discovery_finds_skills(self, tmp_path: Path):
        """Scans skills directory and extracts skill IDs."""
        # Create test skills
        system_dir = tmp_path / "skills" / "system"
        system_dir.mkdir(parents=True)

        skill1 = {"skill": "system.routing", "capabilities": ["routing"]}
        skill2 = {"skill": "system.weather", "capabilities": ["weather"]}

        (system_dir / "routing.json").write_text(json.dumps(skill1), encoding="utf-8")
        (system_dir / "weather.json").write_text(json.dumps(skill2), encoding="utf-8")

        # Create registry with matching skill_refs
        registry_data = {
            "version": "1.0.0",
            "categories": {
                "test": {
                    "display_name": "Test",
                    "icon": "🧪",
                    "description": "Test",
                    "abilities": [
                        {"id": "a1", "skill_refs": ["system.routing"], "how_to": "Test"}
                    ],
                    "ui_locations": {}
                }
            }
        }
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps(registry_data), encoding="utf-8")

        # Load
        reg = CapabilityRegistry(str(registry_file), str(tmp_path / "skills"))
        reg.load()

        assert "system.routing" in reg._available_skills
        assert "system.weather" in reg._available_skills

    def test_auto_discovery_logs_orphan_warning(self, tmp_path: Path, caplog):
        """Unknown skill_refs trigger CAPABILITY_REGISTRY_ORPHAN log."""
        import logging

        # Create test skill
        system_dir = tmp_path / "skills" / "system"
        system_dir.mkdir(parents=True)

        skill = {"skill": "system.routing"}
        (system_dir / "routing.json").write_text(json.dumps(skill), encoding="utf-8")

        # Create registry with orphan reference
        registry_data = {
            "version": "1.0.0",
            "categories": {
                "test": {
                    "display_name": "Test",
                    "icon": "🧪",
                    "description": "Test",
                    "abilities": [
                        {"id": "a1", "skill_refs": ["system.orphan"], "how_to": "Test"}
                    ],
                    "ui_locations": {}
                }
            }
        }
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps(registry_data), encoding="utf-8")

        # Load with logging capture
        reg = CapabilityRegistry(str(registry_file), str(tmp_path / "skills"))
        
        with caplog.at_level(logging.WARNING, logger="janus_backend"):
            reg.load()

        # Verify orphan warning was logged
        assert "CAPABILITY_REGISTRY_ORPHAN" in caplog.text
        assert "system.orphan" in caplog.text

    def test_auto_discovery_no_orphans_for_valid_refs(self, tmp_path: Path, caplog):
        """No orphan warnings for valid skill_refs."""
        import logging

        # Create test skill
        system_dir = tmp_path / "skills" / "system"
        system_dir.mkdir(parents=True)

        skill = {"skill": "system.routing"}
        (system_dir / "routing.json").write_text(json.dumps(skill), encoding="utf-8")

        # Create registry with valid reference
        registry_data = {
            "version": "1.0.0",
            "categories": {
                "test": {
                    "display_name": "Test",
                    "icon": "🧪",
                    "description": "Test",
                    "abilities": [
                        {"id": "a1", "skill_refs": ["system.routing"], "how_to": "Test"}
                    ],
                    "ui_locations": {}
                }
            }
        }
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps(registry_data), encoding="utf-8")

        # Load with logging capture
        reg = CapabilityRegistry(str(registry_file), str(tmp_path / "skills"))
        
        with caplog.at_level(logging.WARNING, logger="janus_backend"):
            reg.load()

        # Verify no orphan warning for valid ref
        assert "CAPABILITY_REGISTRY_ORPHAN" not in caplog.text


class TestCapabilityRegistryOverview:
    """Tests for get_overview (§8.1 Unit Tests)."""

    @pytest.fixture
    def sample_registry(self, tmp_path: Path):
        """Create a sample registry for testing."""
        registry_data = {
            "version": "1.0.0",
            "categories": {
                "file_management": {
                    "display_name": {"de": "Dateien", "en": "Files"},
                    "icon": "📁",
                    "description": {"de": "Dateiverwaltung", "en": "File management"},
                    "abilities": [
                        {
                            "id": "file.upload",
                            "label": {"de": "Hochladen", "en": "Upload"},
                            "skill_refs": ["system.upload"],
                            "how_to": {"de": "Ziehe Dateien", "en": "Drag files"}
                        }
                    ],
                    "ui_locations": {
                        "files": {
                            "label": {"de": "Dateien", "en": "Files"},
                            "action": {"type": "open_module", "payload": {"module": "files"}}
                        }
                    }
                }
            }
        }
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps(registry_data), encoding="utf-8")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        return str(registry_file), str(skills_dir)

    def test_get_overview_returns_all_categories(self, sample_registry):
        """Overview contains all categories with localized data."""
        reg = CapabilityRegistry(*sample_registry)
        reg.load()

        overview = reg.get_overview(language="de")

        assert "categories" in overview
        assert "file_management" in overview["categories"]
        assert overview["categories"]["file_management"]["display_name"] == "Dateien"
        assert overview["categories"]["file_management"]["ability_count"] == 1

    def test_get_overview_uses_fallback_language(self, sample_registry):
        """Missing language falls back to 'de'."""
        reg = CapabilityRegistry(*sample_registry)
        reg.load()

        # Request non-existent language 'fr'
        overview = reg.get_overview(language="fr")

        # Should fallback to 'de'
        assert overview["categories"]["file_management"]["display_name"] == "Dateien"


class TestCapabilityRegistryHowTo:
    """Tests for get_how_to (§8.1 Unit Tests)."""

    @pytest.fixture
    def sample_registry(self, tmp_path: Path):
        """Create a sample registry for testing."""
        registry_data = {
            "version": "1.0.0",
            "categories": {
                "test": {
                    "display_name": "Test",
                    "icon": "🧪",
                    "description": "Test",
                    "abilities": [
                        {
                            "id": "file.upload",
                            "label": "Upload",
                            "skill_refs": ["system.upload"],
                            "how_to": {"de": "Ziehe Dateien hinein", "en": "Drag files in"}
                        }
                    ],
                    "ui_locations": {}
                }
            }
        }
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps(registry_data), encoding="utf-8")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        return str(registry_file), str(skills_dir)

    def test_get_how_to_returns_correct_ability_instruction(self, sample_registry):
        """How-to for valid ability returns instruction."""
        reg = CapabilityRegistry(*sample_registry)
        reg.load()

        how_to = reg.get_how_to("file.upload", language="de")
        assert how_to == "Ziehe Dateien hinein"

    def test_get_how_to_returns_en_when_de_missing(self, sample_registry):
        """How-to falls back to 'en' when 'de' is missing."""
        # Modify ability to have only 'en'
        registry_file = Path(sample_registry[0])
        data = json.loads(registry_file.read_text(encoding="utf-8"))
        data["categories"]["test"]["abilities"][0]["how_to"] = {"en": "English only"}
        registry_file.write_text(json.dumps(data), encoding="utf-8")

        reg = CapabilityRegistry(*sample_registry)
        reg.load()

        # Request 'de' -> should fallback to 'en'
        how_to = reg.get_how_to("file.upload", language="de")
        assert how_to == "English only"

    def test_get_how_to_returns_none_for_unknown_ability(self, sample_registry):
        """Unknown ability returns None."""
        reg = CapabilityRegistry(*sample_registry)
        reg.load()

        how_to = reg.get_how_to("file.nonexistent", language="de")
        assert how_to is None


class TestCapabilityRegistryNavigation:
    """Tests for get_navigation (§8.1 Unit Tests)."""

    @pytest.fixture
    def sample_registry(self, tmp_path: Path):
        """Create a sample registry for testing."""
        registry_data = {
            "version": "1.0.0",
            "categories": {
                "file_management": {
                    "display_name": {"de": "Dateiverwaltung", "en": "File Management"},
                    "icon": "📁",
                    "description": "Test",
                    "abilities": [],
                    "ui_locations": {
                        "files": {
                            "label": {"de": "Dateien", "en": "Files"},
                            "action": {"type": "open_module", "payload": {"module": "files"}}
                        }
                    }
                }
            }
        }
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps(registry_data), encoding="utf-8")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        return str(registry_file), str(skills_dir)

    def test_get_navigation_matches_by_category_id(self, sample_registry):
        """Navigation matches by category ID."""
        reg = CapabilityRegistry(*sample_registry)
        reg.load()

        result = reg.get_navigation("Wo finde ich file_management?", language="de")
        assert result is not None
        assert result["action"]["type"] == "open_module"

    def test_get_navigation_matches_by_display_name(self, sample_registry):
        """Navigation matches by display name."""
        reg = CapabilityRegistry(*sample_registry)
        reg.load()

        result = reg.get_navigation("Zeig mir die Dateiverwaltung", language="de")
        assert result is not None
        assert result["action"]["payload"]["module"] == "files"

    def test_get_navigation_returns_none_for_unknown_query(self, sample_registry):
        """Unknown query returns None."""
        reg = CapabilityRegistry(*sample_registry)
        reg.load()

        result = reg.get_navigation("Völlig unbekannter Begriff xyz123", language="de")
        assert result is None


class TestCapabilityRegistryEdgeCases:
    """Additional edge case tests."""

    def test_empty_skills_dir_graceful(self, tmp_path: Path):
        """Empty skills directory doesn't crash."""
        registry_data = {"version": "1.0.0", "categories": {}}
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps(registry_data), encoding="utf-8")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        reg = CapabilityRegistry(str(registry_file), str(skills_dir))
        reg.load()

        assert reg._available_skills == set()
        assert reg.all_categories() == []

    def test_skills_in_subdirectories_found(self, tmp_path: Path):
        """Skills in nested subdirectories are discovered."""
        # Create nested skill structure
        nested_dir = tmp_path / "skills" / "knowledge" / "deep"
        nested_dir.mkdir(parents=True)

        skill = {"skill": "knowledge.deep.search"}
        (nested_dir / "deep_search.json").write_text(json.dumps(skill), encoding="utf-8")

        registry_data = {"version": "1.0.0", "categories": {}}
        registry_file = tmp_path / "registry.json"
        registry_file.write_text(json.dumps(registry_data), encoding="utf-8")

        reg = CapabilityRegistry(str(registry_file), str(tmp_path / "skills"))
        reg.load()

        assert "knowledge.deep.search" in reg._available_skills


class TestRealCapabilityRegistrySkillRefs:
    """Sanity: shipped registry lists skills the SkillSelector universe must include."""

    def test_system_weather_is_in_planner_universe(self):
        backend_root = Path(__file__).resolve().parent.parent
        registry_path = backend_root / "data" / "capability_registry.json"
        skills_dir = backend_root / "skills"
        reg = CapabilityRegistry(str(registry_path), str(skills_dir))
        reg.load()
        groups = reg.get_capability_groups(allowed_skill_ids=None)
        universe = {sid for skills in groups.values() for sid in skills}
        assert "system.weather" in universe
