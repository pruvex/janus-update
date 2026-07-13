from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm_providers.shared.tool_loop_runner import ToolLoopRunner


def _import_gemini_gateway(monkeypatch):
    fake_vector_module = MagicMock()
    fake_vector_module.vector_service = MagicMock()
    monkeypatch.setitem(sys.modules, "backend.services.vector_service", fake_vector_module)
    from backend.llm_providers.gemini.gateway import GeminiGateway

    return GeminiGateway


def test_transport_tool_loop_runner_enabled_defaults_false(monkeypatch):
    monkeypatch.delenv("TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", raising=False)
    import importlib

    import backend.llm_providers.shared.tool_loop_runner as runner_module

    importlib.reload(runner_module)
    assert runner_module.TRANSPORT_TOOL_LOOP_RUNNER_ENABLED is False


@pytest.mark.asyncio
async def test_gemini_runner_callbacks_accumulate_grounding_cost(monkeypatch):
    from backend.llm_providers.shared.tool_loop_runner import ToolLoopContext, NonToolResponseAction

    class FakeService:
        async def generate_response(self, **kwargs):
            return {
                "type": "text",
                "text": "done",
                "usage": {"input_tokens": 2, "output_tokens": 1},
                "cost": {"total_cost": 0.002},
                "grounding_metadata": {"web_search_queries": ["switch 2 release"]},
            }

        def prepare_history_for_second_call(self, **kwargs):
            return []

    context = ToolLoopContext(
        provider="gemini",
        model="gemini-3-flash-preview",
        api_key="test",
        chat_history=[],
        user_prompt="liste Quellen",
        allowed_skill_ids=["system.websearch"],
        tool_executor=MagicMock(),
        max_tool_rounds=3,
    )

    def on_round_response(response, loop_context):
        grounding_metadata = response.get("grounding_metadata") or {}
        raw_queries = grounding_metadata.get("web_search_queries") or []
        valid_queries = [str(query or "").strip() for query in raw_queries if str(query or "").strip()]
        loop_context.loop_websearch_queries += len(valid_queries)
        loop_context.loop_cost_eur += len(valid_queries) * 0.01

    async def handle_non_tool_response(response, loop_context, round_force):
        return NonToolResponseAction(kind="return", response=response)

    result = await ToolLoopRunner().run(
        service=FakeService(),
        context=context,
        sanitize_generate_response_kwargs=lambda kwargs, *keys: dict(kwargs or {}),
        prepare_history_for_second_call=FakeService().prepare_history_for_second_call,
        handle_non_tool_response=handle_non_tool_response,
        filter_tools_by_skill_ids=lambda allowed_skill_ids: [],
        build_tool_definitions_for_llm=lambda tools: [],
        prevalidate_tool_calls=lambda tool_calls, user_prompt="": {
            "valid_calls": tool_calls,
            "immediate_results": {},
            "system_hints": [],
        },
        resolve_execution_model=lambda loop_context: ("gemini-3-flash-preview", False),
        on_round_response=on_round_response,
    )

    assert result["text"] == "done"
    assert context.loop_websearch_queries == 1
    assert context.loop_cost_eur == pytest.approx(0.012)


@pytest.mark.asyncio
async def test_gemini_gateway_runner_defaults_system_websearch_to_flash(monkeypatch):
    monkeypatch.setenv("TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", "true")
    import importlib

    import backend.llm_providers.shared.tool_loop_runner as runner_module

    importlib.reload(runner_module)

    GeminiGateway = _import_gemini_gateway(monkeypatch)
    from backend.llm_providers.shared import moa as shared_moa
    from backend.llm_providers.shared import utils as shared_utils

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

        def prepare_history_for_second_call(self, **kwargs):
            return list(kwargs.get("chat_history") or [])

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
async def test_gemini_gateway_runner_honors_visible_override_for_system_websearch(monkeypatch):
    monkeypatch.setenv("TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", "true")
    import importlib

    import backend.llm_providers.shared.tool_loop_runner as runner_module

    importlib.reload(runner_module)

    GeminiGateway = _import_gemini_gateway(monkeypatch)
    from backend.llm_providers.shared import moa as shared_moa
    from backend.llm_providers.shared import utils as shared_utils

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

        def prepare_history_for_second_call(self, **kwargs):
            return list(kwargs.get("chat_history") or [])

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
async def test_gemini_gateway_runner_persists_grouped_attribution_metadata(monkeypatch):
    monkeypatch.setenv("TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", "true")
    import importlib

    import backend.llm_providers.shared.tool_loop_runner as runner_module

    importlib.reload(runner_module)

    GeminiGateway = _import_gemini_gateway(monkeypatch)
    from backend.llm_providers.shared import moa as shared_moa
    from backend.llm_providers.shared import utils as shared_utils

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
    assert conversation_kwargs["amount"] == pytest.approx(0.007)
    assert response["_cost_attribution"]["attribution_status"] == "intern attribuiert"


def test_gemini_gateway_dispatches_flag_off_to_legacy_and_flag_on_to_runner():
    gateway_path = Path("backend/llm_providers/gemini/gateway.py")
    source = gateway_path.read_text(encoding="utf-8")

    assert "if TRANSPORT_TOOL_LOOP_RUNNER_ENABLED:" in source
    assert "return await self._run_simple_tool_loop_with_runner(**kwargs)" in source
    assert "return await self._run_legacy_simple_tool_loop(**kwargs)" in source
    assert "resolve_execution_model=resolve_gemini_execution_model" in source
    assert "on_round_response=on_gemini_round_response" in source
