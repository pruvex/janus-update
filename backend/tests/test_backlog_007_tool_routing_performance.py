import pytest

from backend.llm_providers.shared import utils as shared_utils
from backend.tool_registry import register_all_tools


def _function_names(definitions):
    names = []
    for item in definitions:
        function = item.get("function") if isinstance(item, dict) else None
        names.append((function or item).get("name"))
    return names


def test_allowed_skill_ids_are_canonical_and_stable():
    register_all_tools()

    normalized = shared_utils._normalize_allowed_skill_ids(
        [
            "filesystem_list_directory",
            "filesystem.list_directory",
            "list_directory",
            "filesystem.read_file",
            "filesystem_read_file",
        ]
    )

    assert normalized == ["filesystem.list_directory", "filesystem.read_file"]


def test_filtered_tool_payload_has_no_alias_duplicates():
    register_all_tools()

    filtered = shared_utils._filter_tools_by_skill_ids(
        [
            "filesystem_list_directory",
            "filesystem.list_directory",
            "list_directory",
            "filesystem.read_file",
            "filesystem_read_file",
        ]
    )
    definitions = shared_utils._build_tool_definitions_for_llm(filtered)
    names = _function_names(definitions)

    assert names == ["filesystem.list_directory", "filesystem.read_file"]
    assert len(names) == len(set(names))


def test_tool_manager_definition_cache_canonicalizes_aliases():
    register_all_tools()
    from backend.services.tool_manager import tool_manager

    alias_defs = tool_manager.get_tool_definitions(
        ["filesystem_list_directory", "list_directory", "filesystem.list_directory"]
    )
    canonical_defs = tool_manager.get_tool_definitions(["filesystem.list_directory"])
    alias_names = _function_names(alias_defs)
    canonical_names = _function_names(canonical_defs)

    assert alias_names == ["filesystem_list_directory"]
    assert canonical_names == ["filesystem_list_directory"]
    assert len(alias_names) == len(set(alias_names))


@pytest.mark.asyncio
async def test_openai_tool_loop_builds_filtered_tool_payload_once(monkeypatch):
    from backend.llm_providers.openai.gateway import OpenAIGateway

    calls = {"filter": 0, "build": 0}

    def fake_filter(allowed_skill_ids):
        calls["filter"] += 1
        assert allowed_skill_ids == ["filesystem.list_directory"]
        return [{"name": "filesystem.list_directory", "description": "", "parameters": {}}]

    def fake_build(tools):
        calls["build"] += 1
        return [{"type": "function", "function": {"name": "filesystem.list_directory", "parameters": {}}}]

    monkeypatch.setattr(shared_utils, "_filter_tools_by_skill_ids", fake_filter)
    monkeypatch.setattr(shared_utils, "_build_tool_definitions_for_llm", fake_build)
    monkeypatch.setattr(
        shared_utils,
        "_prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls, "immediate_results": {}, "system_hints": []},
    )

    class FakeService:
        def __init__(self):
            self.calls = 0

        async def generate_response(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return {
                    "type": "tool_code",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "filesystem.list_directory", "arguments": "{}"},
                        }
                    ],
                    "usage": {},
                    "cost": {},
                }
            return {"type": "text", "text": "done", "usage": {}, "cost": {}}

        def prepare_history_for_second_call(self, **kwargs):
            return [{"role": "system", "content": "next"}]

    class FakeExecutor:
        async def execute_tool_calls(self, calls):
            return [{"skill_id": "filesystem.list_directory", "status": "ok", "content": "{}"}]

    gateway = OpenAIGateway()
    gateway.service = FakeService()

    response = await gateway._run_full_tool_loop(
        provider="openai",
        model="gpt-5.4-nano",
        api_key="test",
        chat_history=[],
        user_prompt="liste C:\\temp",
        allowed_skill_ids=["filesystem.list_directory"],
        tool_executor=FakeExecutor(),
        max_tool_rounds=3,
    )

    assert response["text"] == "done"
    assert calls == {"filter": 1, "build": 1}


@pytest.mark.asyncio
async def test_gemini_tool_loop_builds_filtered_tool_payload_once(monkeypatch):
    from backend.llm_providers.gemini.gateway import GeminiGateway
    from backend.llm_providers.shared import moa as shared_moa

    calls = {"filter": 0, "build": 0}

    def fake_filter(allowed_skill_ids):
        calls["filter"] += 1
        assert allowed_skill_ids == ["filesystem.list_directory"]
        return [{"name": "filesystem.list_directory", "description": "", "parameters": {}}]

    def fake_build(tools):
        calls["build"] += 1
        return [{"type": "function", "function": {"name": "filesystem.list_directory", "parameters": {}}}]

    monkeypatch.setattr(shared_utils, "_filter_tools_by_skill_ids", fake_filter)
    monkeypatch.setattr(shared_utils, "_build_tool_definitions_for_llm", fake_build)
    monkeypatch.setattr(shared_moa, "resolve_moa_model", lambda **kwargs: (kwargs["user_base_model"], False))
    monkeypatch.setattr(
        shared_utils,
        "_prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls, "immediate_results": {}, "system_hints": []},
    )

    class FakeService:
        def __init__(self):
            self.calls = 0

        async def generate_response(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return {
                    "type": "tool_code",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "filesystem.list_directory", "arguments": "{}"},
                        }
                    ],
                    "raw_assistant_response": {},
                    "usage": {},
                    "cost": {},
                    "grounding_metadata": {},
                }
            return {"type": "text", "text": "done", "usage": {}, "cost": {}, "grounding_metadata": {}}

        def prepare_history_for_second_call(self, **kwargs):
            return [{"role": "system", "content": "next"}]

    class FakeExecutor:
        async def execute_tool_calls(self, calls):
            return [{"skill_id": "filesystem.list_directory", "status": "ok", "content": "{}"}]

    gateway = GeminiGateway()
    gateway.service = FakeService()

    response = await gateway._run_simple_tool_loop(
        provider="gemini",
        model="gemini-2.5-flash",
        api_key="test",
        chat_history=[],
        user_prompt="liste C:\\temp",
        allowed_skill_ids=["filesystem.list_directory"],
        tool_executor=FakeExecutor(),
        provider_service=gateway.service,
        max_tool_rounds=3,
    )

    assert response["text"] == "done"
    assert calls == {"filter": 1, "build": 1}
