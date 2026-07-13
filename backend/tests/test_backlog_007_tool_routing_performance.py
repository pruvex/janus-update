import json
from unittest.mock import AsyncMock, MagicMock, patch

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

    assert alias_names == ["filesystem.list_directory"]
    assert canonical_names == ["filesystem.list_directory"]
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


@pytest.mark.asyncio
async def test_gemini_tool_loop_defaults_system_websearch_to_flash_without_visible_override(monkeypatch):
    from backend.llm_providers.gemini.gateway import GeminiGateway
    from backend.llm_providers.shared import moa as shared_moa

    monkeypatch.setattr(
        shared_utils,
        "_filter_tools_by_skill_ids",
        lambda allowed_skill_ids: [{"name": "system.websearch", "description": "", "parameters": {}}],
    )
    monkeypatch.setattr(
        shared_utils,
        "_build_tool_definitions_for_llm",
        lambda tools: [{"type": "function", "function": {"name": "system.websearch", "parameters": {}}}],
    )
    monkeypatch.setattr(
        shared_utils,
        "_prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls, "immediate_results": {}, "system_hints": []},
    )
    monkeypatch.setattr(
        shared_moa,
        "resolve_moa_model",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("resolve_moa_model should not be used for system.websearch")),
    )

    seen_models = []

    class FakeService:
        async def generate_response(self, **kwargs):
            seen_models.append(kwargs["model"])
            return {"type": "text", "text": "done", "usage": {}, "cost": {}, "grounding_metadata": {}}

    gateway = GeminiGateway()
    gateway.service = FakeService()

    response = await gateway._run_simple_tool_loop(
        provider="gemini",
        model="gemini-3.1-pro-preview",
        api_key="test",
        chat_history=[],
        user_prompt="liste die relevantesten Quellen",
        allowed_skill_ids=["system.websearch"],
        tool_executor=AsyncMock(),
        provider_service=gateway.service,
        max_tool_rounds=3,
    )

    assert response["text"] == "done"
    assert seen_models == ["gemini-3-flash-preview"]


@pytest.mark.asyncio
async def test_gemini_tool_loop_honors_visible_override_for_system_websearch(monkeypatch):
    from backend.llm_providers.gemini.gateway import GeminiGateway
    from backend.llm_providers.shared import moa as shared_moa

    monkeypatch.setattr(
        shared_utils,
        "_filter_tools_by_skill_ids",
        lambda allowed_skill_ids: [{"name": "system.websearch", "description": "", "parameters": {}}],
    )
    monkeypatch.setattr(
        shared_utils,
        "_build_tool_definitions_for_llm",
        lambda tools: [{"type": "function", "function": {"name": "system.websearch", "parameters": {}}}],
    )
    monkeypatch.setattr(
        shared_utils,
        "_prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls, "immediate_results": {}, "system_hints": []},
    )
    monkeypatch.setattr(
        shared_moa,
        "resolve_moa_model",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("resolve_moa_model should not be used for system.websearch")),
    )

    seen_models = []

    class FakeService:
        async def generate_response(self, **kwargs):
            seen_models.append(kwargs["model"])
            return {"type": "text", "text": "done", "usage": {}, "cost": {}, "grounding_metadata": {}}

    gateway = GeminiGateway()
    gateway.service = FakeService()

    response = await gateway._run_simple_tool_loop(
        provider="gemini",
        model="gemini-3.1-pro-preview",
        api_key="test",
        chat_history=[{"role": "system", "content": "MODEL_OVERRIDE: gemini-3.1-pro-preview"}],
        user_prompt="liste die relevantesten Quellen",
        allowed_skill_ids=["system.websearch"],
        tool_executor=AsyncMock(),
        provider_service=gateway.service,
        max_tool_rounds=3,
    )

    assert response["text"] == "done"
    assert seen_models == ["gemini-3.1-pro-preview", "gemini-3.1-pro-preview"]


@pytest.mark.asyncio
async def test_gemini_tool_loop_persists_grouped_attribution_metadata(monkeypatch):
    from backend.llm_providers.gemini.gateway import GeminiGateway
    from backend.llm_providers.shared import moa as shared_moa

    monkeypatch.setattr(
        shared_utils,
        "_filter_tools_by_skill_ids",
        lambda allowed_skill_ids: [{"name": "filesystem.list_directory", "description": "", "parameters": {}}],
    )
    monkeypatch.setattr(
        shared_utils,
        "_build_tool_definitions_for_llm",
        lambda tools: [{"type": "function", "function": {"name": "filesystem.list_directory", "parameters": {}}}],
    )
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
                    "usage": {"input_tokens": 10, "output_tokens": 2},
                    "cost": {"total_cost": 0.003},
                    "grounding_metadata": {
                        "web_search_queries": ["switch 2 release"],
                        "groundingChunks": [{"web": {"uri": "https://example.com/release"}}],
                    },
                }
            return {
                "type": "text",
                "text": "done",
                "usage": {"input_tokens": 6, "output_tokens": 4},
                "cost": {"total_cost": 0.004},
                "grounding_metadata": {},
            }

        def prepare_history_for_second_call(self, **kwargs):
            return [{"role": "system", "content": "next"}]

    class FakeExecutor:
        async def execute_tool_calls(self, calls):
            return [{"skill_id": "filesystem.list_directory", "status": "ok", "content": "{}"}]

    gateway = GeminiGateway()
    gateway.service = FakeService()

    with patch(
        "backend.services.cost_service.create_cost_entry",
        side_effect=[object(), object()],
    ) as create_cost_entry_mock:
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
            db=object(),
            chat_id=321,
        )

    assert response["text"] == "done"
    assert create_cost_entry_mock.call_count == 2
    websearch_kwargs = create_cost_entry_mock.call_args_list[0].kwargs
    conversation_kwargs = create_cost_entry_mock.call_args_list[1].kwargs
    assert websearch_kwargs["source_type"] == "websearch"
    assert websearch_kwargs["attribution_component"] == "grounding_websearch"
    assert websearch_kwargs["attribution_status"] == "intern attribuiert"
    assert conversation_kwargs["source_type"] == "conversation"
    assert conversation_kwargs["attribution_component"] == "conversation"
    assert conversation_kwargs["attribution_status"] == "intern attribuiert"
    assert conversation_kwargs["amount"] == pytest.approx(0.007)
    assert conversation_kwargs["attribution_session_id"] == "321"
    assert conversation_kwargs["attribution_group_id"] == websearch_kwargs["attribution_group_id"]
    assert conversation_kwargs["attribution_request_id"] == websearch_kwargs["attribution_request_id"]
    assert websearch_kwargs["amount"] == 0.01
    assert websearch_kwargs["attribution_metadata"]["websearch_query_count"] == 1
    assert conversation_kwargs["attribution_metadata"]["request_kind"] == "simple_tool_loop"
    assert response["_cost_attribution"]["attribution_status"] == "intern attribuiert"


@pytest.mark.asyncio
async def test_tool_executor_enforces_gemini_flash_default_for_websearch_without_visible_override(monkeypatch):
    from backend.services.tool_executor import ToolExecutor
    from backend.services.tool_manager import tool_manager

    register_all_tools()

    captured = {}

    async def _fake_websearch(**kwargs):
        captured.update(kwargs)
        return {"status": "ok", "data": {"query": kwargs["query"], "hits": [], "retrieved_at": "2026-06-03T00:00:00Z"}}

    tool_def = tool_manager.get_tool("system.websearch")
    assert tool_def is not None
    monkeypatch.setattr(tool_def, "func", _fake_websearch)

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="gemini",
        model="gemini-3.1-pro-preview",
        additional_context={"chat_history": []},
    )

    result = await executor.execute_tool_call("system.websearch", {"query": "latest release notes"})
    payload = json.loads(result["content"])

    assert payload["status"] == "ok"
    assert captured["provider"] == "gemini"
    assert captured["model"] == "gemini-3-flash-preview"


@pytest.mark.asyncio
async def test_tool_executor_honors_visible_gemini_override_for_websearch(monkeypatch):
    from backend.services.tool_executor import ToolExecutor
    from backend.services.tool_manager import tool_manager

    register_all_tools()

    captured = {}

    async def _fake_websearch(**kwargs):
        captured.update(kwargs)
        return {"status": "ok", "data": {"query": kwargs["query"], "hits": [], "retrieved_at": "2026-06-03T00:00:00Z"}}

    tool_def = tool_manager.get_tool("system.websearch")
    assert tool_def is not None
    monkeypatch.setattr(tool_def, "func", _fake_websearch)

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="gemini",
        model="gemini-3.1-pro-preview",
        additional_context={
            "chat_history": [{"role": "system", "content": "MODEL_OVERRIDE: gemini-3.1-pro-preview"}]
        },
    )

    result = await executor.execute_tool_call("system.websearch", {"query": "latest release notes"})
    payload = json.loads(result["content"])

    assert payload["status"] == "ok"
    assert captured["provider"] == "gemini"
    assert captured["model"] == "gemini-3.1-pro-preview"


@pytest.mark.asyncio
async def test_tool_executor_forwards_websearch_runtime_context_when_decoupled(monkeypatch):
    from backend.services.tool_executor import ToolExecutor
    from backend.services.tool_manager import tool_manager

    monkeypatch.setenv("TRANSPORT_WEBSEARCH_DECOUPLED", "true")
    register_all_tools()

    captured = {}

    async def _fake_websearch(**kwargs):
        captured.update(kwargs)
        return {"status": "ok", "data": {"query": kwargs["query"], "hits": [], "retrieved_at": "2026-06-03T00:00:00Z"}}

    tool_def = tool_manager.get_tool("system.websearch")
    assert tool_def is not None
    monkeypatch.setattr(tool_def, "func", _fake_websearch)

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="gemini",
        model="gemini-3.1-pro-preview",
        additional_context={"chat_history": []},
    )

    result = await executor.execute_tool_call("system.websearch", {"query": "latest release notes"})
    payload = json.loads(result["content"])

    assert payload["status"] == "ok"
    assert "provider" not in captured
    assert "model" not in captured
    assert captured["websearch_runtime_context"] == {
        "provider": "gemini",
        "model": "gemini-3.1-pro-preview",
        "websearch_fallback_provider": "",
        "chat_history": [],
    }
