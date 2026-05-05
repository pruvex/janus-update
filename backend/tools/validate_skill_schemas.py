#!/usr/bin/env python3
"""
Skill Schema Validator

Validates that JSON skill manifests match their corresponding Python function signatures.
"""

import inspect
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))


# Mapping from skill names (from JSON "skill" field) to Python functions
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


def extract_json_parameters(json_path: Path) -> Optional[Set[str]]:
    """Extract parameter names from a skill JSON manifest."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check for input_schema (new format)
        if "input_schema" in data and "properties" in data["input_schema"]:
            return set(data["input_schema"]["properties"].keys())
        
        # Check for parameters with properties (common format)
        if "parameters" in data and isinstance(data["parameters"], dict):
            if "properties" in data["parameters"]:
                return set(data["parameters"]["properties"].keys())
            # If parameters is a dict but doesn't have properties, treat its keys as parameter names
            return set(data["parameters"].keys())
        
        # No parameters defined
        return set()
    except Exception as e:
        print(f"Error reading {json_path}: {e}")
        return None


def get_python_function_parameters(func_path: str) -> Optional[tuple[Set[str], bool]]:
    """Get parameter names from a Python function using inspect.
    
    Returns:
        Tuple of (parameter_names, has_var_kwargs) where has_var_kwargs is True
        if the function accepts **kwargs.
    """
    try:
        import importlib.util
        
        module_path, func_name = func_path.split(":")
        
        # Convert module path to file path
        module_file = module_path.replace(".", "/") + ".py"
        if not os.path.exists(module_file):
            # Try adding backend prefix
            module_file = "backend/" + module_file
        
        spec = importlib.util.spec_from_file_location(module_path, module_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {module_file}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        func = getattr(module, func_name)
        
        sig = inspect.signature(func)
        has_var_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in sig.parameters.values()
        )
        # Exclude **kwargs and *args
        params = {
            name for name, param in sig.parameters.items()
            if param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        }
        return params, has_var_kwargs
    except Exception as e:
        print(f"Error inspecting {func_path}: {e}")
        return None


def validate_skill(json_path: Path) -> List[str]:
    """Validate a single skill JSON against its Python function."""
    errors = []
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        skill_name = data.get("skill")
        if not skill_name:
            errors.append(f"No 'skill' field in {json_path}")
            return errors
        
        # Get JSON parameters
        json_params = extract_json_parameters(json_path)
        if json_params is None:
            errors.append(f"Failed to extract JSON parameters from {json_path}")
            return errors
        
        # Find corresponding Python function
        func_path = SKILL_FUNCTION_MAP.get(skill_name)
        if not func_path:
            # Skip if no mapping defined
            print(f"⚠ No mapping for skill '{skill_name}' in {json_path}")
            return errors
        
        # Get Python parameters
        result = get_python_function_parameters(func_path)
        if result is None:
            errors.append(f"Failed to inspect Python function {func_path}")
            return errors
        
        python_params, has_var_kwargs = result
        
        # Compare parameters
        if has_var_kwargs:
            # Function accepts **kwargs, so any JSON parameters are valid
            print(f"✓ {skill_name}: Parameters match (function accepts **kwargs)")
        else:
            # Function doesn't accept **kwargs, parameters must match exactly
            if json_params != python_params:
                errors.append(
                    f"Parameter mismatch for '{skill_name}' ({json_path}):\n"
                    f"  JSON parameters: {sorted(json_params)}\n"
                    f"  Python parameters: {sorted(python_params)}"
                )
            else:
                print(f"✓ {skill_name}: Parameters match")
    
    except Exception as e:
        errors.append(f"Error validating {json_path}: {e}")
    
    return errors


def main():
    """Main validation function."""
    skills_dir = Path(__file__).parent.parent / "skills"
    
    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}")
        sys.exit(1)
    
    # Find all JSON manifests
    json_files = list(skills_dir.rglob("*.json"))
    
    print(f"Found {len(json_files)} skill JSON files")
    print("=" * 60)
    
    all_errors = []
    
    for json_path in sorted(json_files):
        errors = validate_skill(json_path)
        all_errors.extend(errors)
    
    print("=" * 60)
    
    if all_errors:
        print(f"\n❌ Validation failed with {len(all_errors)} error(s):")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✓ All validated skills passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
