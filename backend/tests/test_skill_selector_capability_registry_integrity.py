"""Diamond integrity tests for skill selection and capability registry.

Covers TEST-RUN-2026-05-20-019 / TestSpec 08:
skill refs must point to real skill manifests, help output must use
user-facing capability categories, and representative intents must route to
the expected capability family.
"""

import json
from pathlib import Path

import pytest

from backend.services.capability_registry import CapabilityRegistry
from backend.services.help_skill import HelpSkill
from backend.services.orchestrator.intent_engine import IntentDetectionResult
from backend.services.skill_selector import SkillSelector


BACKEND_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = BACKEND_ROOT / "data" / "capability_registry.json"
SKILLS_DIR = BACKEND_ROOT / "skills"


@pytest.fixture()
def real_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry(str(REGISTRY_PATH), str(SKILLS_DIR))
    registry.load()
    return registry


def _load_skill_manifests() -> dict[str, Path]:
    manifests: dict[str, Path] = {}
    for manifest_path in SKILLS_DIR.rglob("*.json"):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        skill_id = str(data.get("skill") or "").strip()
        if skill_id:
            manifests.setdefault(skill_id, manifest_path)
    return manifests


def test_real_capability_registry_has_no_orphan_skill_refs(real_registry: CapabilityRegistry):
    """TC-001/TC-006: every registry skill_ref resolves to a shipped skill."""
    skill_manifests = _load_skill_manifests()
    orphan_refs: list[str] = []

    for category_id, category in real_registry._registry.get("categories", {}).items():
        for ability in category.get("abilities", []):
            for skill_ref in ability.get("skill_refs", []):
                if skill_ref not in skill_manifests:
                    orphan_refs.append(f"{category_id}.{ability.get('id')} -> {skill_ref}")

    assert orphan_refs == []


def test_skill_manifests_are_parseable_and_canonical():
    """TC-002: skill JSON files expose stable domain.action identifiers."""
    skill_manifests = _load_skill_manifests()

    assert skill_manifests
    for skill_id, manifest_path in skill_manifests.items():
        domain, separator, action = skill_id.partition(".")
        assert separator == ".", f"{manifest_path} uses non-canonical skill id {skill_id!r}"
        assert domain and action, f"{manifest_path} has incomplete skill id {skill_id!r}"


def test_help_overview_uses_categories_not_raw_tool_dump(real_registry: CapabilityRegistry):
    """TC-003/SEC-001: capability help is grouped for users, not dumped as tools."""
    answer = HelpSkill(real_registry).handle(
        query="Was kannst du mit Dateien, Kalender und Recherche?",
        intent_type="capability_overview",
        language="de",
    ).answer

    assert "Dateien & Dokumente" in answer
    assert "Kalender & Termine" in answer
    assert "Wissen & Recherche" in answer
    assert "filesystem.list_directory" not in answer
    assert "calendar.list_events" not in answer
    assert "system.websearch" not in answer


def test_weather_intent_selects_weather_without_calendar_or_filesystem(
    real_registry: CapabilityRegistry,
    monkeypatch: pytest.MonkeyPatch,
):
    """TC-004: weather prompt is pinned to the weather capability family."""
    selector = SkillSelector(capability_registry=real_registry)
    monkeypatch.setattr(selector, "_semantic_search", lambda *, prompt, top_k: [])

    skills = selector.get_relevant_skills(
        "Wie ist das Wetter morgen in Koeln?",
        intent_result=IntentDetectionResult(is_weather_intent=True, primary_intent="weather"),
    )

    assert "system.weather" in skills
    assert all(not skill.startswith("calendar.") for skill in skills)
    assert all(not skill.startswith("filesystem.") for skill in skills)


def test_filesystem_intent_selects_filesystem_without_web_or_calendar(
    real_registry: CapabilityRegistry,
    monkeypatch: pytest.MonkeyPatch,
):
    """TC-005: filesystem prompt stays in the filesystem capability family."""
    selector = SkillSelector(capability_registry=real_registry)
    monkeypatch.setattr(selector, "_semantic_search", lambda *, prompt, top_k: ["system.websearch"])

    skills = selector.get_relevant_skills(
        "Liste den Test-Workspace auf",
        intent_result=IntentDetectionResult(is_filesystem_intent=True, primary_intent="filesystem"),
    )

    assert "filesystem.list_directory" in skills
    assert "filesystem.list_workspaces" in skills
    assert "system.websearch" not in skills
    assert all(not skill.startswith("calendar.") for skill in skills)

