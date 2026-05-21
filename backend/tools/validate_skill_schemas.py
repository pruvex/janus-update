#!/usr/bin/env python3
"""Validate skill manifests against Janus ToolManager contracts.

The backend has two distinct skill-manifest shapes:

1. Metadata manifests: describe routing, latency, examples and capabilities.
   Their runtime argument schema comes from ToolManager registration.
2. Contract manifests: explicitly declare ``input_schema`` or ``parameters``.
   These must match the ToolManager LLM-facing args schema.

This validator intentionally compares against ToolManager schemas instead of
raw Python function signatures. Function signatures often contain injected
runtime parameters such as ``db``, ``api_key``, ``provider`` or wrapper objects
that are not visible to the LLM and must not be required in skill JSON files.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))


SKILL_FUNCTION_MAP = {
    # Filesystem skills
    "filesystem.read_file": "backend.tools.filesystem_tools:read_file",
    "filesystem.delete_file": "backend.tools.filesystem_tools:delete_file",
    "filesystem.list_directory": "backend.tools.filesystem_tools:list_directory",
    "filesystem.delete_directory": "backend.tools.filesystem_tools:delete_directory",
    "filesystem.create_file": "backend.tools.filesystem_tools:create_file",
    "filesystem.move_file": "backend.tools.filesystem_tools:move_file",
    "filesystem.create_directory": "backend.services.filesystem_manager:create_directory",
    "filesystem.rename_file": "backend.services.filesystem_manager:rename_file",
    "filesystem.find_files": "backend.services.filesystem_manager:find_files",
    "filesystem.list_workspaces": "backend.services.filesystem_manager:list_allowed_workspaces",
    "filesystem.move_files": "backend.services.filesystem_manager:move_files",
    # Calendar skills
    "calendar.create_event": "backend.tools.calendar_tools:create_calendar_event",
    "calendar.delete_event": "backend.tools.calendar_tools:delete_calendar_event",
    "calendar.find_address_and_update_event": "backend.tools.calendar_tools:find_address_and_update_calendar_event",
    "calendar.find_and_update_event": "backend.tools.calendar_tools:find_and_update_calendar_event",
    "calendar.find_slots": "backend.tools.calendar_tools:find_free_time_slots",
    "calendar.list_events": "backend.tools.calendar_tools:get_calendar_events",
    "calendar.update_event": "backend.tools.calendar_tools:update_calendar_event",
    "calendar.update_event_description": "backend.tools.calendar_tools:update_calendar_event_description",
    # Communication skills
    "communication.send_email": "backend.tools.gmail_tools:send_email",
    "communication.read_email": "backend.tools.gmail_tools:read_email",
    "communication.list_emails": "backend.tools.gmail_tools:get_latest_emails",
    "communication.find_contact_and_email": "backend.tool_registry:find_contact_and_send_email_wrapper",
    # Contacts skills
    "contacts.create_or_update": "backend.tools.db_wrappers:create_or_update_contact_tool",
    "contacts.delete": "backend.tools.db_wrappers:delete_contact_by_id_wrapper",
    "contacts.list": "backend.tools.db_wrappers:list_contacts_wrapper",
    # Knowledge skills
    "knowledge.query": "backend.services.rag_manager:query_knowledge_base",
    "knowledge.open_document": "backend.services.tool_executor:open_knowledge_document",
    "knowledge.list_documents": "backend.services.tool_executor:list_knowledge_documents",
    "knowledge.read_full_text": "backend.services.tool_executor:get_full_document_text",
    "knowledge.edit_pdf": "backend.tools.pdf_editor:edit_pdf_text_in_place",
    "knowledge.hardened_edit": "backend.services.knowledge_composite:hardened_edit_pdf",
    # System skills
    "system.websearch": "backend.tool_registry:websearch_wrapper",
    "system.weather": "backend.tools.weather_service:get_weather_from_api_tool",
    "system.wikipedia_summary": "backend.tools.wiki_service:get_wikipedia_summary",
    "system.scrape_website": "backend.services.scraper_service:scrape_website",
    "system.price_comparison": "backend.tools.finance_tools:price_comparison_tool",
    "system.routing": "backend.tools.geo_service:get_distance_and_route_tool",
    "system.local_business": "backend.tools.geo_service:find_local_business_tool",
    "system.country_info": "backend.tools.geo_service:get_country_info_tool",
    "system.create_pdf": "backend.tools.pdf_generator:create_pdf_from_markdown",
    "system.generate_image": "backend.tools.media_tools:generate_image_tool",
    "system.save_mp3": "backend.tools.media_tools:save_mp3_tool",
    "system.grant_permission": "backend.tool_registry:system_grant_permission",
    "system.revoke_permission": "backend.tool_registry:system_revoke_permission",
    "system.rss_news": "backend.tools.rss_service:get_latest_news_rss",
    "video.search": "backend.tools.video_tools:video_search_tool",
    "video.understand": "backend.tools.video_understanding:video_understanding_tool",
    "memory.write": "backend.tools.memory_tools:memory_write_tool",
    "memory.read": "backend.tools.memory_tools:memory_read_tool",
    "memory.update": "backend.tools.memory_tools:memory_update_tool",
    "memory.delete": "backend.tools.memory_tools:memory_delete_tool",
    "memory.history": "backend.tools.memory_tools:memory_history_tool",
}


def _schema_properties(schema: Any) -> Set[str]:
    if isinstance(schema, dict) and isinstance(schema.get("properties"), dict):
        return {str(key) for key in schema["properties"].keys()}
    return set()


def manifest_declares_input_contract(data: Dict[str, Any]) -> bool:
    return "input_schema" in data or "parameters" in data


def extract_json_parameters(json_path: Path) -> Optional[Set[str]]:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if "input_schema" in data:
            return _schema_properties(data.get("input_schema"))
        parameters = data.get("parameters")
        if isinstance(parameters, dict):
            if "properties" in parameters:
                return _schema_properties(parameters)
            return {str(key) for key in parameters.keys()}
        return set()
    except Exception as exc:
        print(f"Error reading {json_path}: {exc}")
        return None


def get_registered_tool_parameters(skill_name: str) -> Optional[Set[str]]:
    try:
        from backend.services.tool_manager import tool_manager
        from backend.tool_registry import register_all_tools

        register_all_tools()
        tool = tool_manager.get_tool(skill_name)
        if tool is None:
            return None
        return _schema_properties(tool.llm_definition.get("parameters"))
    except Exception as exc:
        print(f"Error inspecting registered tool '{skill_name}': {exc}")
        return None


def validate_skill(json_path: Path) -> List[str]:
    errors: List[str] = []

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Error validating {json_path}: {exc}"]

    skill_name = str(data.get("skill") or "").strip()
    if not skill_name:
        return [f"No 'skill' field in {json_path}"]

    description = data.get("description")
    if "description" in data and not isinstance(description, str):
        errors.append(f"Invalid 'description' field in {json_path}")

    declares_input_contract = manifest_declares_input_contract(data)
    if not declares_input_contract:
        print(f"OK {skill_name}: metadata manifest (ToolManager schema is source of truth)")
        return errors

    json_params = extract_json_parameters(json_path)
    if json_params is None:
        return [f"Failed to extract JSON parameters from {json_path}"]

    if skill_name not in SKILL_FUNCTION_MAP:
        if data.get("is_agent_ready") is True:
            errors.append(f"No function mapping for agent-ready skill '{skill_name}' in {json_path}")
        else:
            print(f"OK {skill_name}: non-agent-ready manifest contract is not ToolManager-routable")
        return errors

    registered_params = get_registered_tool_parameters(skill_name)
    if registered_params is None:
        errors.append(f"No registered ToolManager tool for '{skill_name}'")
        return errors

    if json_params != registered_params:
        errors.append(
            f"Parameter mismatch for '{skill_name}' ({json_path}):\n"
            f"  Manifest parameters: {sorted(json_params)}\n"
            f"  Registered ToolManager parameters: {sorted(registered_params)}"
        )
    else:
        print(f"OK {skill_name}: manifest parameters match ToolManager schema")

    return errors


def main() -> None:
    skills_dir = Path(__file__).parent.parent / "skills"

    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}")
        sys.exit(1)

    json_files = sorted(skills_dir.rglob("*.json"))
    print(f"Found {len(json_files)} skill JSON files")
    print("=" * 60)

    all_errors: List[str] = []
    for json_path in json_files:
        all_errors.extend(validate_skill(json_path))

    print("=" * 60)
    if all_errors:
        print(f"\nX Validation failed with {len(all_errors)} error(s):")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)

    print("\nOK All validated skills passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()
