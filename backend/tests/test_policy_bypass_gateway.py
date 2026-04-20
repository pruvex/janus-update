from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services import llm_gateway


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name, model_name", [
    ("openai", "gpt-5.4-nano"),
    ("gemini", "gemini-3-flash-preview"),
    ("ollama", "llama3.1:8b"),
])
async def test_reason_and_respond_filters_tools_by_allowed_skill_ids(provider_name, model_name):
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "done done done done done done done done",
            "finish_reason": "STOP",
        }
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "query_knowledge_base": _Tool("query_knowledge_base"),
        "delete_file": _Tool("delete_file"),
    }

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "query_knowledge_base": "knowledge.query",
                "delete_file": "filesystem.delete_file",
            }.get(name, name),
        )

        await llm_gateway.reason_and_respond(
            provider=provider_name,
            model=model_name,
            api_key="dummy",
            chat_history=[{"role": "user", "content": "frage"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="",
            chat_id=1,
            tool_executor=tool_executor,
            allowed_skill_ids=["knowledge.query"],
            max_tool_rounds=3,
            bypass_policy=False,
        )

    call_kwargs = provider.generate_response.await_args.kwargs
    tools_sent = call_kwargs.get("tools") or []
    assert len(tools_sent) == 1
    assert tools_sent[0]["name"] == "knowledge.query"
    if provider_name == "openai":
        assert call_kwargs.get("force_tool_name") == "knowledge_query"
    else:
        assert call_kwargs.get("force_tool_name") == "knowledge.query"
    assert call_kwargs.get("tool_choice") == {
        "type": "function",
        "function": {
            "name": call_kwargs.get("force_tool_name"),
        },
    }


@pytest.mark.asyncio
async def test_reason_and_respond_tool_filter_returns_empty_list_when_no_match():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "done done done done done done done done",
            "finish_reason": "STOP",
        }
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "query_knowledge_base": _Tool("query_knowledge_base"),
        "delete_file": _Tool("delete_file"),
    }

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "query_knowledge_base": "knowledge.query",
                "delete_file": "filesystem.delete_file",
            }.get(name, name),
        )

        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "frage"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="",
            chat_id=1,
            tool_executor=tool_executor,
            allowed_skill_ids=["non.existent.skill"],
            max_tool_rounds=3,
            bypass_policy=False,
        )

    call_kwargs = provider.generate_response.await_args.kwargs
    tools_sent = call_kwargs.get("tools") or []
    assert len(tools_sent) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name, model_name", [
    ("openai", "gpt-5.4-nano"),
    ("gemini", "gemini-3-flash-preview"),
    ("ollama", "llama3.1:8b"),
])
async def test_reason_and_respond_keeps_multiple_allowed_skills_visible(provider_name, model_name):
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "done done done done done done done done",
            "finish_reason": "STOP",
        }
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "get_country_info_tool": _Tool("get_country_info_tool"),
        "get_distance_and_route_tool": _Tool("get_distance_and_route_tool"),
        "search_past_conversation_summaries_tool": _Tool("search_past_conversation_summaries_tool"),
    }

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "get_country_info_tool": "system.country_info",
                "get_distance_and_route_tool": "system.routing",
                "search_past_conversation_summaries_tool": "memory.search_summaries",
            }.get(name, name),
        )

        await llm_gateway.reason_and_respond(
            provider=provider_name,
            model=model_name,
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Japan und Tokio-Kyoto"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Japan und Tokio-Kyoto",
            chat_id=1,
            tool_executor=tool_executor,
            allowed_skill_ids=["system.country_info", "system.routing", "memory.search_summaries"],
            max_tool_rounds=2,
            bypass_policy=False,
        )

    call_kwargs = provider.generate_response.await_args_list[0].kwargs
    tools_sent = call_kwargs.get("tools") or []
    tool_names = [tool.get("name") for tool in tools_sent]
    assert len(tools_sent) == 3
    assert "system.country_info" in tool_names
    assert "system.routing" in tool_names
    assert "memory.search_summaries" in tool_names


@pytest.mark.asyncio
async def test_reason_and_respond_does_not_inject_single_skill_round_rule_into_system_messages():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "done done done done done done done done",
            "finish_reason": "STOP",
        }
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[
                {"role": "system", "content": "Du bist Janus."},
                {"role": "user", "content": "Ich plane eine Reise nach Japan."},
            ],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Ich plane eine Reise nach Japan.",
            chat_id=1,
            tool_executor=MagicMock(),
            allowed_skill_ids=[],
            max_tool_rounds=1,
            bypass_policy=False,
        )

    call_kwargs = provider.generate_response.await_args.kwargs
    messages_sent = call_kwargs.get("messages") or []
    assert messages_sent
    assert messages_sent[0]["role"] == "system"
    assert "REGEL: Du erhaeltst in dieser Runde NUR EINEN Skill." not in messages_sent[0]["content"]


@pytest.mark.asyncio
async def test_reason_and_respond_uses_skill_selector_top_k_before_first_call():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "done done done done done done done done",
            "finish_reason": "STOP",
        }
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "websearch_wrapper": _Tool("websearch_wrapper"),
        "get_latest_news_rss": _Tool("get_latest_news_rss"),
        "get_wikipedia_summary": _Tool("get_wikipedia_summary"),
        "delete_file": _Tool("delete_file"),
    }

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "websearch_wrapper": "system.websearch",
                "get_latest_news_rss": "system.rss_news",
                "get_wikipedia_summary": "system.wikipedia_summary",
                "delete_file": "filesystem.delete_file",
            }.get(name, name),
        )
        selector_mock = MagicMock()
        selector_mock.get_relevant_skills.return_value = ["system.websearch"]
        mp.setattr(llm_gateway, "SkillSelector", lambda: selector_mock)

        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Wie hoch ist der Goldpreis heute?"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie hoch ist der Goldpreis heute?",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=1,
            bypass_policy=False,
        )

    call_kwargs = provider.generate_response.await_args.kwargs
    tools_sent = call_kwargs.get("tools") or []
    tool_names = [tool.get("name") for tool in tools_sent]
    assert tool_names == ["system.websearch"]


@pytest.mark.asyncio
async def test_reason_and_respond_falls_back_to_websearch_when_selector_returns_no_skills():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "done done done done done done done done",
            "finish_reason": "STOP",
        }
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "websearch_wrapper": _Tool("websearch_wrapper"),
        "get_latest_news_rss": _Tool("get_latest_news_rss"),
        "get_wikipedia_summary": _Tool("get_wikipedia_summary"),
        "delete_file": _Tool("delete_file"),
    }

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "websearch_wrapper": "system.websearch",
                "get_latest_news_rss": "system.rss_news",
                "get_wikipedia_summary": "system.wikipedia_summary",
                "delete_file": "filesystem.delete_file",
            }.get(name, name),
        )
        selector_mock = MagicMock()
        selector_mock.get_relevant_skills.return_value = []
        mp.setattr(llm_gateway, "SkillSelector", lambda: selector_mock)

        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Irgendwas unklar"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Irgendwas unklar",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=1,
            bypass_policy=False,
        )

    call_kwargs = provider.generate_response.await_args.kwargs
    tools_sent = call_kwargs.get("tools") or []
    tool_names = [tool.get("name") for tool in tools_sent]
    assert tool_names == ["system.websearch"]


@pytest.mark.asyncio
async def test_reason_and_respond_forwards_bypass_to_executor_once():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "function": {"name": "delete_file", "arguments": '{"path":"foo.txt"}'},
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
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "tool_call_id": "call-1",
                "role": "tool",
                "name": "delete_file",
                "content": "{\"status\":\"ok\",\"data\":{}}",
            }
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "hi"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=True,
        )

    assert response["text"].startswith("done")
    tool_executor.execute_tool_calls.assert_awaited_once()
    _, kwargs = tool_executor.execute_tool_calls.await_args
    assert kwargs["bypass_policy"] is True


@pytest.mark.asyncio
async def test_reason_and_respond_resets_bypass_after_first_tool_round():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "function": {"name": "delete_file", "arguments": '{"path":"foo.txt"}'},
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool-1"},
            },
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-2",
                        "function": {"name": "delete_file", "arguments": '{"path":"foo-2.txt"}'},
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool-2"},
            },
            {
                "type": "text",
                "text": "done done done done done done done done",
                "finish_reason": "STOP",
            },
        ]
    )
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "tool_call_id": "call-1",
                "role": "tool",
                "name": "delete_file",
                "content": "{\"status\":\"ok\",\"data\":{}}",
            }
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "hi"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=True,
        )

    assert response["text"].startswith("done")
    assert tool_executor.execute_tool_calls.await_count == 2
    first_call_kwargs = tool_executor.execute_tool_calls.await_args_list[0].kwargs
    second_call_kwargs = tool_executor.execute_tool_calls.await_args_list[1].kwargs
    assert first_call_kwargs["bypass_policy"] is True
    assert second_call_kwargs["bypass_policy"] is False


@pytest.mark.asyncio
async def test_reason_and_respond_repairs_hallucinated_tool_name_before_executor_call():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "function": {"name": "file_delete", "arguments": '{"path":"foo.txt"}'},
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
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "tool_call_id": "call-1",
                "role": "tool",
                "name": "delete_file",
                "content": '{"status":"ok","data":{"deleted":true}}',
            }
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "delete file"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert response["text"].startswith("done")
    called_tool_calls = tool_executor.execute_tool_calls.await_args.args[0]
    assert called_tool_calls[0]["function"]["name"] == "filesystem.delete_file"


@pytest.mark.asyncio
async def test_reason_and_respond_returns_malformed_request_without_executor_dispatch():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-bad",
                        "function": {"name": "knowledge.open_document", "arguments": "{}"},
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
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "open document"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert response["text"].startswith("done")
    assert tool_executor.execute_tool_calls.await_count == 0


@pytest.mark.asyncio
async def test_reason_and_respond_websearch_synthesis_does_not_append_pdf_without_create_pdf():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "Der aktuelle Goldpreis liegt bei ca. 4.236,05 €.",
            "finish_reason": "STOP",
        }
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[
                {"role": "user", "content": "Wie hoch ist der Goldpreis heute?"},
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "content": '{"status":"ok","data":{"text":"Goldpreis heute 4.236,05 €","urls":["https://www.goldpreis.de/","https://example.com/report.pdf"],"file_path":"C:\\\\fake\\\\report.pdf"}}',
                },
            ],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie hoch ist der Goldpreis heute?",
            chat_id=1,
            tool_executor=MagicMock(),
            max_tool_rounds=1,
            bypass_policy=False,
            disable_tools=True,
        )

    assert response["text"] == "Der aktuelle Goldpreis liegt bei ca. 4.236,05 €."
    assert "report.pdf" not in response["text"]


@pytest.mark.asyncio
async def test_reason_and_respond_generic_country_prompt_does_not_force_country_tool():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "ok ok ok ok ok ok ok ok",
            "finish_reason": "STOP",
        }
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "get_country_info_tool": _Tool("get_country_info_tool"),
        "websearch_wrapper": _Tool("websearch_wrapper"),
    }

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "get_country_info_tool": "system.country_info",
                "websearch_wrapper": "system.websearch",
            }.get(name, name),
        )

        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Erzähl mir was über ein Land."}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Erzähl mir was über ein Land.",
            chat_id=1,
            tool_executor=MagicMock(),
            max_tool_rounds=2,
            bypass_policy=False,
        )

    first_call_kwargs = provider.generate_response.await_args_list[0].kwargs
    assert first_call_kwargs.get("force_tool_name") is None
    tools_sent = first_call_kwargs.get("tools") or []
    tool_names = [tool.get("name") for tool in tools_sent]
    assert "system.country_info" in tool_names
    assert "system.websearch" in tool_names


@pytest.mark.asyncio
async def test_reason_and_respond_adds_invalid_arguments_recovery_hint():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-invalid",
                        "function": {"name": "filesystem.delete_file", "arguments": '{"path":123}'},
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

    captured_history = {}

    def _capture_prepare(*, chat_history, raw_assistant_response, tool_results):
        captured_history["messages"] = list(chat_history)
        captured_history["tool_results"] = list(tool_results)
        return []

    provider.prepare_history_for_second_call = MagicMock(side_effect=_capture_prepare)

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "tool_call_id": "call-invalid",
                "role": "tool",
                "name": "filesystem.delete_file",
                "content": (
                    '{"status":"error","error":{"code":"INVALID_ARGUMENTS",'
                    '"message":"path must be string"}}'
                ),
            }
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "delete file"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert response["text"].startswith("done")
    assert any(
        "Bitte korrigiere die Parameter" in str(msg.get("content", ""))
        for msg in captured_history.get("messages", [])
        if msg.get("role") == "system"
    )


@pytest.mark.asyncio
async def test_reason_and_respond_breaks_on_repeated_invalid_tool_signature():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "invalid-1",
                        "function": {"name": "ghost_tool", "arguments": "{}"},
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool-1"},
            },
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "invalid-2",
                        "function": {"name": "ghost_tool", "arguments": "{}"},
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool-2"},
            },
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "invalid-3",
                        "function": {"name": "ghost_tool", "arguments": "{}"},
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool-3"},
            },
        ]
    )
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "do thing"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=5,
            bypass_policy=False,
        )

    assert "wiederholt derselbe ungültige Tool-Aufruf" in response["text"]
    assert response.get("tool_limit_reached") is True
    assert tool_executor.execute_tool_calls.await_count == 0


@pytest.mark.asyncio
async def test_reason_and_respond_does_not_mark_tool_limit_when_no_valid_tool_executed():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "invalid-1",
                        "function": {"name": "ghost_tool", "arguments": "{}"},
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool-1"},
            },
            {
                "type": "text",
                "text": "done done done done done done done done",
                "finish_reason": "STOP",
            },
        ]
    )
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "mach was"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=1,
            bypass_policy=False,
        )

    assert response["text"].startswith("done")
    assert response.get("tool_limit_reached") is False
    assert tool_executor.execute_tool_calls.await_count == 0


@pytest.mark.asyncio
async def test_reason_and_respond_appends_pdf_path_from_tool_history():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "Die Erstellung ist abgeschlossen.",
            "finish_reason": "STOP",
        }
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[
                {"role": "user", "content": "Bitte PDF erstellen."},
                {
                    "role": "tool",
                    "name": "system.create_pdf",
                    "content": (
                        '{"status":"ok","data":'
                        '{"file_path":"C:\\\\Users\\\\pruve\\\\Documents\\\\agent_execution.pdf"}}'
                    ),
                },
            ],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Bitte PDF erstellen.",
            chat_id=1,
            tool_executor=MagicMock(),
            disable_tools=True,
            max_tool_rounds=1,
            bypass_policy=False,
        )

    assert "Gespeicherte PDF-Datei(en):" in response["text"]
    assert "C:\\Users\\pruve\\Documents\\agent_execution.pdf" in response["text"]


@pytest.mark.asyncio
async def test_reason_and_respond_ollama_first_round_keeps_tools_enabled():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "done done done done done done done done",
            "finish_reason": "STOP",
        }
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "get_distance_and_route_tool": _Tool("get_distance_and_route_tool"),
    }

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {"get_distance_and_route_tool": "system.routing"}.get(name, name),
        )

        await llm_gateway.reason_and_respond(
            provider="ollama",
            model="llama3.1:8b",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Wie weit ist es von Berlin nach Hamburg?"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie weit ist es von Berlin nach Hamburg?",
            chat_id=1,
            tool_executor=MagicMock(),
            max_tool_rounds=2,
            bypass_policy=False,
        )

    first_call_kwargs = provider.generate_response.await_args.kwargs
    assert first_call_kwargs.get("tools")
    assert first_call_kwargs.get("call_type") is None
    assert first_call_kwargs.get("force_tool_name") is None


@pytest.mark.asyncio
async def test_reason_and_respond_country_intent_does_not_force_or_filter_tools():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "ok ok ok ok ok ok ok ok",
            "finish_reason": "STOP",
        }
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "get_country_info_tool": _Tool("get_country_info_tool"),
        "websearch_wrapper": _Tool("websearch_wrapper"),
    }

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "get_country_info_tool": "system.country_info",
                "websearch_wrapper": "system.websearch",
            }.get(name, name),
        )

        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Wie viele Einwohner hat Japan?"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie viele Einwohner hat Japan?",
            chat_id=1,
            tool_executor=MagicMock(),
            max_tool_rounds=2,
            bypass_policy=False,
        )

    first_call_kwargs = provider.generate_response.await_args_list[0].kwargs
    assert first_call_kwargs.get("force_tool_name") is None
    tools_sent = first_call_kwargs.get("tools") or []
    tool_names = [tool.get("name") for tool in tools_sent]
    assert "system.country_info" in tool_names
    assert "system.websearch" in tool_names


@pytest.mark.asyncio
async def test_reason_and_respond_combined_geo_intent_does_not_force_country_tool_in_round1():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "ok ok ok ok ok ok ok ok",
            "finish_reason": "STOP",
        }
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "get_country_info_tool": _Tool("get_country_info_tool"),
        "get_distance_and_route_tool": _Tool("get_distance_and_route_tool"),
    }

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "get_country_info_tool": "system.country_info",
                "get_distance_and_route_tool": "system.routing",
            }.get(name, name),
        )

        await llm_gateway.reason_and_respond(
            provider="gemini",
            model="gemini-3-flash-preview",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Wie viele Einwohner hat Japan und wie weit ist es von Tokio nach Kyoto?"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie viele Einwohner hat Japan und wie weit ist es von Tokio nach Kyoto?",
            chat_id=1,
            tool_executor=MagicMock(),
            max_tool_rounds=2,
            bypass_policy=False,
        )

    first_call_kwargs = provider.generate_response.await_args_list[0].kwargs
    assert first_call_kwargs.get("force_tool_name") is None


@pytest.mark.asyncio
async def test_reason_and_respond_combined_geo_intent_no_geo_pair_filter_keeps_nonduplicate_country_calls():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "c1",
                        "function": {
                            "name": "system.country_info",
                            "arguments": '{"country":"Japan","language":"de"}',
                        },
                    },
                    {
                        "id": "c2",
                        "function": {
                            "name": "system.country_info",
                            "arguments": '{"country":"Japan,language:","language":"de"}',
                        },
                    },
                    {
                        "id": "r1",
                        "function": {
                            "name": "system.routing",
                            "arguments": '{"origin":"Tokio, Japan","destination":"Kyoto, Japan","mode":"driving"}',
                        },
                    },
                    {
                        "id": "r2",
                        "function": {
                            "name": "system.routing",
                            "arguments": '{"origin":"Tokio, Japan","destination":"Kyoto, Japan","mode":"driving"}',
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
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "get_country_info_tool": _Tool("get_country_info_tool"),
        "get_distance_and_route_tool": _Tool("get_distance_and_route_tool"),
    }

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "get_country_info_tool": "system.country_info",
                "get_distance_and_route_tool": "system.routing",
                "system.country_info": "system.country_info",
                "system.routing": "system.routing",
            }.get(name, name),
        )

        await llm_gateway.reason_and_respond(
            provider="gemini",
            model="gemini-3-flash-preview",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Wie viele Einwohner hat Japan und wie weit ist es von Tokio nach Kyoto?"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie viele Einwohner hat Japan und wie weit ist es von Tokio nach Kyoto?",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    executed_calls = tool_executor.execute_tool_calls.await_args.args[0]
    executed_names = [call.get("function", {}).get("name") for call in executed_calls]
    assert executed_names.count("system.country_info") == 2
    assert executed_names.count("system.routing") == 1


@pytest.mark.asyncio
async def test_reason_and_respond_country_intent_does_not_block_websearch_tool_calls_before_executor():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "function": {
                            "name": "system.websearch",
                            "arguments": '{"query":"Japan population"}',
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
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "get_country_info_tool": _Tool("get_country_info_tool"),
        "websearch_wrapper": _Tool("websearch_wrapper"),
    }

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {
                "get_country_info_tool": "system.country_info",
                "websearch_wrapper": "system.websearch",
                "system.websearch": "system.websearch",
            }.get(name, name),
        )

        response = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Einwohner von Japan?"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Einwohner von Japan?",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert response["text"].startswith("done")
    assert tool_executor.execute_tool_calls.await_count == 1


def test_limit_local_tool_definitions_prioritizes_system_routing(monkeypatch):
    tool_definitions = [
        {"name": f"misc.tool_{idx}", "description": "", "parameters": {"type": "object", "properties": {}}}
        for idx in range(10)
    ] + [
        {"name": "memory.save_core_fact", "description": "", "parameters": {"type": "object", "properties": {}}},
        {"name": "get_distance_and_route_tool", "description": "", "parameters": {"type": "object", "properties": {}}},
    ]

    monkeypatch.setattr(
        llm_gateway.tool_manager,
        "get_skill_id",
        lambda name: "system.routing" if name == "get_distance_and_route_tool" else name,
    )

    limited = llm_gateway._limit_local_tool_definitions(tool_definitions, limit=10)
    limited_names = [tool.get("name") for tool in limited]

    assert "get_distance_and_route_tool" in limited_names


def test_limit_local_tool_definitions_prioritizes_system_local_business(monkeypatch):
    tool_definitions = [
        {"name": f"misc.tool_{idx}", "description": "", "parameters": {"type": "object", "properties": {}}}
        for idx in range(10)
    ] + [
        {"name": "system.local_business", "description": "", "parameters": {"type": "object", "properties": {}}},
    ]

    monkeypatch.setattr(
        llm_gateway.tool_manager,
        "get_skill_id",
        lambda name: "system.local_business" if name == "system.local_business" else name,
    )

    limited = llm_gateway._limit_local_tool_definitions(tool_definitions, limit=10)
    limited_names = [tool.get("name") for tool in limited]

    assert "system.local_business" in limited_names


def test_ensure_forced_tool_visible_reinserts_forced_tool_when_limit_drops_it(monkeypatch):
    limited = [
        {"name": f"misc.tool_{idx}", "description": "", "parameters": {"type": "object", "properties": {}}}
        for idx in range(9)
    ] + [
        {"name": "system.routing", "description": "", "parameters": {"type": "object", "properties": {}}},
    ]
    source_pool = limited + [
        {"name": "system.local_business", "description": "", "parameters": {"type": "object", "properties": {}}},
    ]

    monkeypatch.setattr(
        llm_gateway.tool_manager,
        "get_skill_id",
        lambda name: name,
    )

    updated = llm_gateway._ensure_forced_tool_visible(
        source_pool[:10],
        source_pool,
        {"skill_id": "system.local_business", "provider_tool_name": "system.local_business"},
        limit=10,
    )

    updated_names = [tool.get("name") for tool in updated]
    assert "system.local_business" in updated_names
    assert len(updated_names) == 10


@pytest.mark.asyncio
async def test_reason_and_respond_ollama_switches_to_synthesis_after_tool_round():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-route-1",
                        "function": {
                            "name": "system.routing",
                            "arguments": '{"origin":"Berlin","destination":"Hamburg"}',
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
    provider.prepare_history_for_second_call = MagicMock(
        return_value=[
            {"role": "user", "content": "Wie weit ist es?"},
            {
                "role": "tool",
                "name": "system.routing",
                "content": '{"status":"ok","data":{"distance_km":289.0}}',
            },
        ]
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "get_distance_and_route_tool": _Tool("get_distance_and_route_tool"),
    }

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "tool_call_id": "call-route-1",
                "role": "tool",
                "name": "system.routing",
                "content": '{"status":"ok","data":{"distance_km":289.0}}',
            }
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {"get_distance_and_route_tool": "system.routing"}.get(name, name),
        )

        response = await llm_gateway.reason_and_respond(
            provider="ollama",
            model="llama3.1:8b",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Wie weit ist es?"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie weit ist es?",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert response["text"].startswith("done")
    assert provider.generate_response.await_count == 2
    second_call_kwargs = provider.generate_response.await_args_list[1].kwargs
    assert second_call_kwargs.get("tools") is None
    assert second_call_kwargs.get("call_type") == "synthesis"


@pytest.mark.asyncio
async def test_reason_and_respond_ollama_appends_missing_google_maps_links_from_tool_history():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-route-1",
                        "function": {
                            "name": "get_distance_and_route_tool",
                            "arguments": '{"origin":"Köln, Deutschland","destination":"Paris, Frankreich","mode":"driving"}',
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "Etappe 1: ca. 487 km in 5 Std. 26 Min.",
                "finish_reason": "STOP",
            },
        ]
    )
    provider.prepare_history_for_second_call = MagicMock(
        return_value=[
            {"role": "user", "content": "Route Köln Paris"},
            {
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"distance_km":487.3,"duration_text":"5 Std. 26 Min.","map_link":"https://www.google.com/maps/dir/?api=1&origin=K%C3%B6ln%2C+Deutschland&destination=Paris%2C+Frankreich&travelmode=driving"}}',
            },
        ]
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {
        "get_distance_and_route_tool": _Tool("get_distance_and_route_tool"),
    }

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "tool_call_id": "call-route-1",
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"distance_km":487.3,"duration_text":"5 Std. 26 Min.","map_link":"https://www.google.com/maps/dir/?api=1&origin=K%C3%B6ln%2C+Deutschland&destination=Paris%2C+Frankreich&travelmode=driving"}}',
            }
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {"get_distance_and_route_tool": "system.routing"}.get(name, name),
        )

        response = await llm_gateway.reason_and_respond(
            provider="ollama",
            model="llama3.1:8b",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Wie weit ist es von Köln nach Paris?"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie weit ist es von Köln nach Paris?",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert "Google Maps Links:" in response["text"]
    assert "https://www.google.com/maps/dir/?api=1&origin=K%C3%B6ln%2C+Deutschland&destination=Paris%2C+Frankreich" in response["text"]


@pytest.mark.asyncio
async def test_reason_and_respond_ollama_skips_expensive_final_synthesis_when_budget_is_low():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        return_value={
            "type": "text",
            "text": "knappes Budget Ergebnis",
            "finish_reason": "STOP",
        }
    )
    provider.prepare_history_for_second_call = MagicMock(return_value=[])

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(
            llm_gateway,
            "should_skip_expensive_synthesis",
            lambda budget, provider: True,
        )

        response = await llm_gateway.reason_and_respond(
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "mach was"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="mach was",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=1,
            bypass_policy=False,
        )

    assert response["text"] == "knappes Budget Ergebnis"
    call_kwargs = provider.generate_response.await_args.kwargs
    assert call_kwargs.get("call_type") is None


@pytest.mark.asyncio
async def test_reason_and_respond_gemini_dedupes_duplicate_tool_calls_before_execution():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-country-1",
                        "function": {
                            "name": "system.country_info",
                            "arguments": '{"country":"Japan","language":"de"}',
                        },
                    },
                    {
                        "id": "call-country-2",
                        "function": {
                            "name": "system.country_info",
                            "arguments": '{"country":"Japan","language":"de"}',
                        },
                    },
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "ok",
                "finish_reason": "STOP",
            },
            {
                "type": "text",
                "text": "done",
                "finish_reason": "STOP",
            },
        ]
    )
    provider.prepare_history_for_second_call = MagicMock(return_value=[{"role": "user", "content": "country"}])

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {"get_country_info_tool": _Tool("get_country_info_tool")}
    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {"get_country_info_tool": "system.country_info"}.get(name, name),
        )

        await llm_gateway.reason_and_respond(
            provider="gemini",
            model="gemini-3-flash-preview",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Wie viele Einwohner hat Japan?"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie viele Einwohner hat Japan?",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    executed_calls = tool_executor.execute_tool_calls.await_args.args[0]
    assert len(executed_calls) == 1


@pytest.mark.asyncio
async def test_reason_and_respond_ollama_appends_route_summary_when_final_text_is_rate_limit_apology():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-route-1",
                        "function": {
                            "name": "get_distance_and_route_tool",
                            "arguments": '{"origin":"Köln, Deutschland","destination":"Paris, Frankreich","mode":"driving"}',
                        },
                    },
                    {
                        "id": "call-route-2",
                        "function": {
                            "name": "get_distance_and_route_tool",
                            "arguments": '{"origin":"Paris, Frankreich","destination":"Mailand, Italien","mode":"driving"}',
                        },
                    },
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "Ich entschuldige mich, aber ich kann diese Frage nicht beantworten, da die Anzahl der Aufrufe für den Skill 'system.routing' pro Turn überschritten wurde.",
                "finish_reason": "STOP",
            },
        ]
    )
    provider.prepare_history_for_second_call = MagicMock(
        return_value=[
            {"role": "user", "content": "Route Köln Paris Mailand"},
            {
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"origin":"Köln, Deutschland","destination":"Paris, Frankreich","distance_km":487.3,"duration":"5 Std. 26 Min.","maps_link":"https://www.google.com/maps/dir/?api=1&origin=K%C3%B6ln%2C+Deutschland&destination=Paris%2C+Frankreich&travelmode=driving"}}',
            },
            {
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"origin":"Paris, Frankreich","destination":"Mailand, Italien","distance_km":850.0,"duration":"9 Std. 28 Min.","maps_link":"https://www.google.com/maps/dir/?api=1&origin=Paris%2C+Frankreich&destination=Mailand%2C+Italien&travelmode=driving"}}',
            },
        ]
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {"get_distance_and_route_tool": _Tool("get_distance_and_route_tool")}

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "tool_call_id": "call-route-1",
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"origin":"Köln, Deutschland","destination":"Paris, Frankreich","distance_km":487.3,"duration":"5 Std. 26 Min.","maps_link":"https://www.google.com/maps/dir/?api=1&origin=K%C3%B6ln%2C+Deutschland&destination=Paris%2C+Frankreich&travelmode=driving"}}',
            },
            {
                "tool_call_id": "call-route-2",
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"origin":"Paris, Frankreich","destination":"Mailand, Italien","distance_km":850.0,"duration":"9 Std. 28 Min.","maps_link":"https://www.google.com/maps/dir/?api=1&origin=Paris%2C+Frankreich&destination=Mailand%2C+Italien&travelmode=driving"}}',
            },
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {"get_distance_and_route_tool": "system.routing"}.get(name, name),
        )

        response = await llm_gateway.reason_and_respond(
            provider="ollama",
            model="llama3.1:8b",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Route Köln Paris Mailand"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Route Köln Paris Mailand",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert "Routenuebersicht (aus Tool-Ergebnissen):" in response["text"]
    assert "Köln, Deutschland -> Paris, Frankreich" in response["text"]
    assert "Paris, Frankreich -> Mailand, Italien" in response["text"]


@pytest.mark.asyncio
async def test_reason_and_respond_ollama_appends_route_summary_when_text_has_only_city_names():
    provider = MagicMock()
    provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call-route-1",
                        "function": {
                            "name": "get_distance_and_route_tool",
                            "arguments": '{"origin":"Köln, Deutschland","destination":"Paris, Frankreich","mode":"driving"}',
                        },
                    },
                    {
                        "id": "call-route-2",
                        "function": {
                            "name": "get_distance_and_route_tool",
                            "arguments": '{"origin":"Paris, Frankreich","destination":"Mailand, Italien","mode":"driving"}',
                        },
                    },
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": (
                    "Die Städte, die du nacherfragt hast sind, Köln, Deutschland und "
                    "Paris, Frankreich und Mailand, Italien."
                ),
                "finish_reason": "STOP",
            },
        ]
    )
    provider.prepare_history_for_second_call = MagicMock(
        return_value=[
            {"role": "user", "content": "Route Köln Paris Mailand"},
            {
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"origin":"Köln, Deutschland","destination":"Paris, Frankreich","distance_km":487.3,"duration":"5 Std. 26 Min.","maps_link":"https://www.google.com/maps/dir/?api=1&origin=K%C3%B6ln%2C+Deutschland&destination=Paris%2C+Frankreich&travelmode=driving"}}',
            },
            {
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"origin":"Paris, Frankreich","destination":"Mailand, Italien","distance_km":850.0,"duration":"9 Std. 28 Min.","maps_link":"https://www.google.com/maps/dir/?api=1&origin=Paris%2C+Frankreich&destination=Mailand%2C+Italien&travelmode=driving"}}',
            },
        ]
    )

    class _Tool:
        def __init__(self, name: str):
            self.name = name

    fake_tools = {"get_distance_and_route_tool": _Tool("get_distance_and_route_tool")}

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "tool_call_id": "call-route-1",
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"origin":"Köln, Deutschland","destination":"Paris, Frankreich","distance_km":487.3,"duration":"5 Std. 26 Min.","maps_link":"https://www.google.com/maps/dir/?api=1&origin=K%C3%B6ln%2C+Deutschland&destination=Paris%2C+Frankreich&travelmode=driving"}}',
            },
            {
                "tool_call_id": "call-route-2",
                "role": "tool",
                "name": "get_distance_and_route_tool",
                "content": '{"status":"ok","data":{"origin":"Paris, Frankreich","destination":"Mailand, Italien","distance_km":850.0,"duration":"9 Std. 28 Min.","maps_link":"https://www.google.com/maps/dir/?api=1&origin=Paris%2C+Frankreich&destination=Mailand%2C+Italien&travelmode=driving"}}',
            },
        ]
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(llm_gateway, "get_provider", lambda _provider_name: provider)
        mp.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: fake_tools)
        mp.setattr(
            llm_gateway.tool_manager,
            "get_skill_id",
            lambda name: {"get_distance_and_route_tool": "system.routing"}.get(name, name),
        )

        response = await llm_gateway.reason_and_respond(
            provider="ollama",
            model="llama3.1:8b",
            api_key="dummy",
            chat_history=[{"role": "user", "content": "Route Köln Paris Mailand"}],
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Route Köln Paris Mailand",
            chat_id=1,
            tool_executor=tool_executor,
            max_tool_rounds=3,
            bypass_policy=False,
        )

    assert "Routenuebersicht (aus Tool-Ergebnissen):" in response["text"]
    assert "487.3 km" in response["text"]
    assert "850.0 km" in response["text"]
