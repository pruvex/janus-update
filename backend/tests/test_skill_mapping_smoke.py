import json
from pathlib import Path


def test_skill_router_resolves_all_mapping_entries(skill_router_instance):
    mapping_path = Path("c:/KI/Janus-Projekt/documentation/skill_mapping.json")
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))

    unresolved = []
    for legacy_name, raw_entry in mapping.items():
        if isinstance(raw_entry, dict):
            skill_name = str(
                raw_entry.get("skill")
                or raw_entry.get("skill_id")
                or raw_entry.get("name")
                or legacy_name
            )
        else:
            skill_name = str(raw_entry)
        try:
            resolved_from_legacy = skill_router_instance.resolve_tool_name(legacy_name)
            resolved_from_skill = skill_router_instance.resolve_tool_name(skill_name)
            assert resolved_from_legacy == resolved_from_skill
        except Exception as exc:
            unresolved.append({"legacy": legacy_name, "skill": skill_name, "error": str(exc)})

    assert not unresolved, f"Dead skill mappings found: {unresolved}"
