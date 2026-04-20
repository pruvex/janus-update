import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.tool_registry import register_all_tools
from backend.services.tool_manager import tool_manager


def get_tool_schema(skill_id: str):
    mapping = tool_manager.get_skill_mapping()
    legacy_name = next((legacy for legacy, mapped in mapping.items() if mapped == skill_id), skill_id)
    tool_def = tool_manager.get_tool(legacy_name) or tool_manager.get_tool(skill_id)
    if tool_def is None:
        tool_def = next(
            (
                candidate
                for tool_name, candidate in tool_manager.get_all_tools().items()
                if tool_manager.get_skill_id(tool_name) == skill_id
            ),
            None,
        )
    if tool_def is None:
        raise AssertionError(f"Tool for skill '{skill_id}' not found.")
    return tool_def.llm_definition.get("parameters")


def main() -> None:
    register_all_tools()

    # 1) Schema-Check: knowledge.list_documents
    list_docs_schema = get_tool_schema("knowledge.list_documents")
    assert isinstance(list_docs_schema, dict), "knowledge.list_documents schema must be a JSON object/dict"
    print("knowledge.list_documents schema:")
    print(json.dumps(list_docs_schema, ensure_ascii=False, indent=2))

    # 2) Schema-Check: system.websearch (provider optional field must exist)
    websearch_schema = get_tool_schema("system.websearch")
    assert isinstance(websearch_schema, dict), "system.websearch schema must be a JSON object/dict"
    properties = websearch_schema.get("properties") or {}
    assert "provider" in properties, "system.websearch schema must include optional 'provider'"
    print("system.websearch schema:")
    print(json.dumps(websearch_schema, ensure_ascii=False, indent=2))

    # 3) Execution-Simulation (Dry): validate args_schema instantiation
    websearch_tool = next(
        (
            tool_def
            for tool_name, tool_def in tool_manager.get_all_tools().items()
            if tool_manager.get_skill_id(tool_name) == "system.websearch"
        ),
        None,
    )
    if websearch_tool is None:
        raise AssertionError("system.websearch tool is not registered.")

    payload = websearch_tool.args_schema(**{"query": "test", "provider": "google"})
    assert payload.query == "test"
    assert payload.provider == "google"
    print("Dry validation payload:")
    print(payload.model_dump())

    print("repro_issue_13: PASS")


if __name__ == "__main__":
    main()
