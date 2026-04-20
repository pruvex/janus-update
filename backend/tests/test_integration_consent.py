import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.data.models import AppState
from backend.services import llm_gateway
from backend.services.policy_engine import PolicyEngine
from backend.services.tool_executor import ToolExecutor


@pytest.mark.asyncio
async def test_consent_option_one_bypass_reaches_gateway_and_executor(
    db_session,
    isolated_workspace,
):
    target_file = isolated_workspace / "to_delete.txt"
    target_file.write_text("delete me", encoding="utf-8")

    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "tc-delete",
                        "function": {
                            "name": "filesystem.delete_file",
                            "arguments": json.dumps({"path": "to_delete.txt"}),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "ok ok ok ok ok ok ok ok ok ok ok ok",
                "finish_reason": "STOP",
            },
        ]
    )
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    captured_bypass = []
    original_execute_tool_calls = executor.execute_tool_calls

    async def _capture_execute(tool_calls, bypass_policy=False):
        captured_bypass.append(bool(bypass_policy))
        return await original_execute_tool_calls(tool_calls, bypass_policy=bypass_policy)

    executor.execute_tool_calls = _capture_execute

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        blocked_response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "delete file"}],
            context_manager=MagicMock(),
            db=db_session,
            user_prompt="",
            chat_id=1,
            tool_executor=executor,
            max_tool_rounds=2,
            bypass_policy=False,
        )

    assert blocked_response["text"].startswith("ok")
    assert captured_bypass == [False]
    assert target_file.exists()

    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "tc-delete-2",
                        "function": {
                            "name": "filesystem.delete_file",
                            "arguments": json.dumps({"path": "to_delete.txt"}),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "done done done done done done done done",
                "finish_reason": "STOP",
            },
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        bypass_response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "1"}],
            context_manager=MagicMock(),
            db=db_session,
            user_prompt="",
            chat_id=1,
            tool_executor=executor,
            max_tool_rounds=2,
            bypass_policy=True,
        )

    assert bypass_response["text"].startswith("done")
    assert captured_bypass[-1] is True
    assert not target_file.exists()


@pytest.mark.asyncio
async def test_consent_option_two_persists_permission_and_third_attempt_skips_prompt(
    db_session,
    isolated_workspace,
):
    blocked_file = isolated_workspace / "blocked.txt"
    blocked_file.write_text("blocked", encoding="utf-8")
    always_file = isolated_workspace / "always.txt"
    always_file.write_text("always", encoding="utf-8")

    provider = MagicMock()
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "tc-block",
                        "function": {
                            "name": "filesystem.delete_file",
                            "arguments": json.dumps({"path": "blocked.txt"}),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "blocked blocked blocked blocked blocked blocked blocked blocked",
                "finish_reason": "STOP",
            },
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "delete file"}],
            context_manager=MagicMock(),
            db=db_session,
            user_prompt="",
            chat_id=2,
            tool_executor=executor,
            max_tool_rounds=2,
            bypass_policy=False,
        )

    assert blocked_file.exists()

    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "tc-grant",
                        "function": {
                            "name": "system.grant_permission",
                            "arguments": json.dumps({"tool_name": "delete_file"}),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "grant grant grant grant grant grant grant grant",
                "finish_reason": "STOP",
            },
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "2"}],
            context_manager=MagicMock(),
            db=db_session,
            user_prompt="",
            chat_id=2,
            tool_executor=executor,
            max_tool_rounds=2,
            bypass_policy=False,
        )

    key = "permission:delete_file"
    state = db_session.query(AppState).filter(AppState.key == key).first()
    assert state is not None
    assert state.value == "always_allow"
    assert PolicyEngine.evaluate("delete_file", db_session) == "ALLOW"

    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "tc-delete-final",
                        "function": {
                            "name": "filesystem.delete_file",
                            "arguments": json.dumps({"path": "always.txt"}),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "final final final final final final final final",
                "finish_reason": "STOP",
            },
        ]
    )

    captured_tool_results = {}

    def _capture_prepare(*, chat_history, raw_assistant_response, tool_results):
        captured_tool_results["tool_results"] = list(tool_results)
        return []

    provider.prepare_history_for_second_call = MagicMock(side_effect=_capture_prepare)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        final_response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "delete again"}],
            context_manager=MagicMock(),
            db=db_session,
            user_prompt="",
            chat_id=2,
            tool_executor=executor,
            max_tool_rounds=2,
            bypass_policy=False,
        )

    assert final_response["text"].startswith("final")
    assert not always_file.exists()
    parsed = json.loads(captured_tool_results["tool_results"][0]["content"])
    assert parsed["status"] == "ok"
