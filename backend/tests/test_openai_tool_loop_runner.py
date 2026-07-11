from pathlib import Path

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.llm_providers.shared.tool_loop_runner import ToolLoopRunner


def test_transport_tool_loop_runner_enabled_defaults_false(monkeypatch):
    monkeypatch.delenv("TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", raising=False)
    import importlib

    import backend.llm_providers.shared.tool_loop_runner as runner_module

    importlib.reload(runner_module)
    assert runner_module.TRANSPORT_TOOL_LOOP_RUNNER_ENABLED is False


def test_transport_tool_loop_runner_enabled_reads_truthy_env(monkeypatch):
    monkeypatch.setenv("TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", "true")
    import importlib

    import backend.llm_providers.shared.tool_loop_runner as runner_module

    importlib.reload(runner_module)
    assert runner_module.TRANSPORT_TOOL_LOOP_RUNNER_ENABLED is True


@pytest.mark.asyncio
async def test_tool_loop_runner_resolves_model_prepares_tools_and_runs_one_round(monkeypatch):
    monkeypatch.setattr(
        ToolLoopRunner,
        "resolve_tool_execution_model",
        staticmethod(lambda **kwargs: (kwargs["model"], False)),
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
                    "raw_assistant_response": {"role": "assistant"},
                    "usage": {"input_tokens": 1, "output_tokens": 2},
                    "cost": {"total_cost": 0.01},
                }
            return {"type": "text", "text": "done", "usage": {}, "cost": {}}

        def prepare_history_for_second_call(self, **kwargs):
            return [{"role": "system", "content": "next"}]

    fake_service = FakeService()
    fake_executor = AsyncMock(
        return_value=[{"skill_id": "filesystem.list_directory", "status": "ok", "content": "{}"}]
    )

    from backend.llm_providers.shared.tool_loop_runner import ToolLoopContext

    context = ToolLoopContext(
        provider="openai",
        model="gpt-5.4-nano",
        api_key="test",
        chat_history=[],
        user_prompt="liste C:\\temp",
        allowed_skill_ids=["filesystem.list_directory"],
        tool_executor=MagicMock(execute_tool_calls=fake_executor),
        max_tool_rounds=3,
    )

    async def handle_non_tool_response(response, loop_context, round_force):
        from backend.llm_providers.shared.tool_loop_runner import NonToolResponseAction

        return NonToolResponseAction(kind="return", response=response)

    result = await ToolLoopRunner().run(
        service=fake_service,
        context=context,
        sanitize_generate_response_kwargs=lambda kwargs, *keys: dict(kwargs or {}),
        prepare_history_for_second_call=fake_service.prepare_history_for_second_call,
        handle_non_tool_response=handle_non_tool_response,
        filter_tools_by_skill_ids=lambda allowed_skill_ids: [
            {"name": "filesystem.list_directory", "description": "", "parameters": {}}
        ],
        build_tool_definitions_for_llm=lambda tools: [
            {"type": "function", "function": {"name": "filesystem.list_directory", "parameters": {}}}
        ],
        prevalidate_tool_calls=lambda tool_calls, user_prompt="": {
            "valid_calls": tool_calls,
            "immediate_results": {},
            "system_hints": [],
        },
    )

    assert result["text"] == "done"
    assert fake_service.calls == 2
    fake_executor.assert_awaited_once()
    assert context.all_tool_results == [
        {"skill_id": "filesystem.list_directory", "status": "ok", "content": "{}"}
    ]


def test_openai_gateway_dispatches_flag_off_to_legacy_and_flag_on_to_runner():
    gateway_path = Path("backend/llm_providers/openai/gateway.py")
    source = gateway_path.read_text(encoding="utf-8")

    assert "if TRANSPORT_TOOL_LOOP_RUNNER_ENABLED:" in source
    assert "return await self._run_full_tool_loop_with_runner(**kwargs)" in source
    assert "return await self._run_legacy_tool_loop(**kwargs)" in source
