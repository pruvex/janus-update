import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services import llm_gateway
from backend.services.tool_executor import ToolExecutor


@pytest.mark.asyncio
async def test_gateway_malformed_request_generates_contract_and_recovery_hint(
    db_session,
    isolated_workspace,
):
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "tc-bad-json",
                        "function": {
                            "name": "filesystem.read_file",
                            "arguments": "{invalid-json",
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "fixed fixed fixed fixed fixed fixed fixed fixed",
                "finish_reason": "STOP",
            },
        ]
    )

    captured = {}

    def _capture_prepare(*, chat_history, raw_assistant_response, tool_results):
        captured["chat_history"] = list(chat_history)
        captured["tool_results"] = list(tool_results)
        return []

    provider.prepare_history_for_second_call = MagicMock(side_effect=_capture_prepare)

    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )
    executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "read file"}],
            context_manager=MagicMock(),
            db=db_session,
            user_prompt="",
            chat_id=11,
            tool_executor=executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert response["text"].startswith("fixed")
    assert executor.execute_tool_calls.await_count == 0

    tool_payload = json.loads(captured["tool_results"][0]["content"])
    assert tool_payload["status"] == "error"
    assert tool_payload["error"]["code"] == "MALFORMED_REQUEST"
    assert any(
        "Tool-Request war formal ungültig" in str(msg.get("content", ""))
        for msg in captured["chat_history"]
        if msg.get("role") == "system"
    )


@pytest.mark.asyncio
async def test_gateway_multi_tool_cascade_collects_skill_responses(
    db_session,
    isolated_workspace,
):
    (isolated_workspace / "notes.txt").write_text("hello integration", encoding="utf-8")

    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "tc-list",
                        "function": {
                            "name": "filesystem.list_directory",
                            "arguments": json.dumps({"path": "."}),
                        },
                    },
                    {
                        "id": "tc-read",
                        "function": {
                            "name": "filesystem.read_file",
                            "arguments": json.dumps({"path": "notes.txt"}),
                        },
                    },
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

    captured = {}

    def _capture_prepare(*, chat_history, raw_assistant_response, tool_results):
        captured["tool_results"] = list(tool_results)
        return []

    provider.prepare_history_for_second_call = MagicMock(side_effect=_capture_prepare)

    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "list then read"}],
            context_manager=MagicMock(),
            db=db_session,
            user_prompt="",
            chat_id=12,
            tool_executor=executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert response["text"].startswith("done")
    assert len(captured["tool_results"]) == 2
    parsed = [json.loads(item["content"]) for item in captured["tool_results"]]
    assert all(p.get("status") == "ok" for p in parsed)
    names = {item["name"] for item in captured["tool_results"]}
    assert names == {"filesystem.list_directory", "filesystem.read_file"}
