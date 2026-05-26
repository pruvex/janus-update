# backend/tests/test_orchestrator_logic.py

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.data import crud, models, schemas
from backend.data.schemas import AgentSpec
from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.orchestrator.schemas import ExecutionResponse, OrchestratorContext
from backend.utils.story_constraints import _count_sentences


@pytest.fixture
def orchestrator_instance(db_session, tmp_path):
    template_config = tmp_path / "template_config.json"
    template_config.write_text(json.dumps({"active_personality": "ai_assistant"}), encoding="utf-8")
    template_personalities = tmp_path / "template_personalities.json"
    template_personalities.write_text(
        json.dumps([{"id": "ai_assistant", "prompt": "Du bist Janus."}], ensure_ascii=False),
        encoding="utf-8",
    )

    return ChatOrchestrator(
        db=db_session,
        context_manager=MagicMock(),
        model_catalog={"gpt-5.4-nano": {}},
        config_file_path=str(tmp_path / "config.json"),
        template_config_file_path=str(template_config),
        personalities_file_path=str(tmp_path / "personalities.json"),
        template_personalities_file_path=str(template_personalities),
    )


@pytest.mark.asyncio
async def test_fact_extraction_skipped_for_greeting(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Greeting Skip")

    monkeypatch.setattr(
        "backend.services.llm_gateway.reason_and_respond",
        AsyncMock(return_value={"type": "text", "text": "Hallo!", "usage": {}, "cost": {}}),
    )

    with patch("backend.services.chat_orchestrator.intent_classifier.is_greeting", return_value=True), patch(
        "backend.services.chat_orchestrator.asyncio.create_task"
    ) as mock_create_task:
        request = schemas.ChatRequest(
            prompt="Hallo",
            chat_id=chat.id,
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
        )
        await orchestrator_instance.handle_chat_request(request)

    mock_create_task.assert_not_called()


@pytest.mark.asyncio
async def test_fact_extraction_called_for_non_greeting(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Fact Extraction")

    monkeypatch.setattr(
        "backend.services.llm_gateway.reason_and_respond",
        AsyncMock(return_value={"type": "text", "text": "Das ist interessant.", "usage": {}, "cost": {}}),
    )

    with patch("backend.services.chat_orchestrator.intent_classifier.is_greeting", return_value=False), patch(
        "backend.services.chat_orchestrator.asyncio.create_task"
    ) as mock_create_task:
        request = schemas.ChatRequest(
            prompt="Ich komme aus Deutschland.",
            chat_id=chat.id,
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
        )
        await orchestrator_instance.handle_chat_request(request)

    mock_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_agent_factory_passes_api_key(orchestrator_instance, monkeypatch):
    planning_round = {"idx": 0}

    async def _fake_plan(**kwargs):
        planning_round["idx"] += 1
        if planning_round["idx"] == 1:
            skills = ["system.country_info", "system.routing"]
        elif planning_round["idx"] == 2:
            skills = ["system.routing"]
        else:
            skills = []
        return AgentSpec(
            name="Plan",
            goal="Test",
            required_skills=skills,
            instructions="Use routing",
            max_iterations=3,
        )

    run_specs = []

    async def _fake_run(**kwargs):
        run_specs.append(list(kwargs["spec"].required_skills))
        skill = kwargs["spec"].required_skills[0]
        return {
            "text": f"{skill} done",
            "trace_id": f"trace-{skill}",
            "raw_response": {"tool_limit_reached": True},
        }

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=_fake_run))
    monkeypatch.setattr(
        "backend.services.orchestrator.execution_engine.llm_gateway.reason_and_respond",
        AsyncMock(return_value={"type": "text", "text": "Syntheseantwort", "usage": {}, "cost": {}}),
    )

    await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=1,
        user_text="Check routes",
        relevant_skill_ids=["system.routing"],
        provider="openai",
        model="gpt-5.4-nano",
        api_key="secret",
    )

    plan_call = orchestrator_instance.agent_planner.plan
    assert plan_call.await_count == 2
    assert plan_call.await_args_list[0].kwargs.get("api_key") == "secret"
    assert run_specs == [["system.country_info"], ["system.routing"]]


@pytest.mark.asyncio
async def test_generic_fallback_message_no_longer_uses_faden_verloren(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Fallback Check")

    run_tool_loop_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="",
            raw_response={"text": ""},
            tool_calls=[],
            is_agent_flow=False,
        )
    )
    monkeypatch.setattr(
        orchestrator_instance.execution_engine,
        "run_tool_loop",
        run_tool_loop_mock,
    )

    request = schemas.ChatRequest(
        prompt="Plane bitte meine Reise in mehreren Schritten.",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    await orchestrator_instance.handle_chat_request(request)

    fallback_summary = str(run_tool_loop_mock.await_args.kwargs.get("fallback_summary") or "")
    assert "Faden verloren" not in fallback_summary
    assert "Ich konnte diesmal keine stabile Antwort erzeugen" in fallback_summary


@pytest.mark.asyncio
async def test_agent_factory_prefers_reasoning_model_on_rolf_for_ollama(orchestrator_instance, monkeypatch):
    async def _fake_plan(**_kwargs):
        return AgentSpec(
            name="Plan",
            goal="Test",
            required_skills=[],
            instructions="Stop",
            max_iterations=1,
        )

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(
        "backend.services.orchestrator.execution_engine.load_config_data",
        lambda: {
            "ollama_nodes": [
                {
                    "id": "rolf",
                    "name": "Rolf GPU",
                    "url": "http://rolf:11434",
                    "active": True,
                }
            ]
        },
    )
    monkeypatch.setattr(
        "backend.services.orchestrator.execution_engine.load_model_catalog",
        lambda: {
            "mistral-nemo:12b": {
                "provider": "ollama",
                "reasoning_capability": "high",
            },
            "qwen2.5:14b": {
                "provider": "ollama",
                "reasoning_capability": "high",
            },
        },
    )

    result = await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=99,
        user_text="Nutze Agentic-Tools bitte stabil.",
        relevant_skill_ids=["system.routing"],
        provider="ollama",
        model="llama3.1:8b",
        api_key="secret",
    )

    assert result.is_agent_flow is True
    plan_call = orchestrator_instance.agent_planner.plan
    assert plan_call.await_count == 1
    assert plan_call.await_args_list[0].kwargs.get("model") == "mistral-nemo:12b"


@pytest.mark.asyncio
async def test_ollama_vague_country_prompt_drops_tools(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Ollama Smalltalk V2")

    run_tool_loop_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="Klar, ich kann dir etwas ueber Laender erzaehlen.",
            raw_response={"text": "Klar, ich kann dir etwas ueber Laender erzaehlen."},
            tool_calls=[],
            is_agent_flow=False,
        )
    )
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)

    request = schemas.ChatRequest(
        prompt="Kennst du ein schönes Land?",
        chat_id=chat.id,
        provider="ollama",
        model="llama3.1:8b",
        api_key="",
    )

    await orchestrator_instance.handle_chat_request(request)

    gateway_kwargs = run_tool_loop_mock.await_args.kwargs.get("gateway_kwargs") or {}
    assert gateway_kwargs.get("tools_override") == []


@pytest.mark.asyncio
async def test_openai_live_web_query_forces_system_websearch(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="OpenAI Websearch Guardrail")

    run_tool_loop_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="Bitcoin Kurs geladen.",
            raw_response={"text": "Bitcoin Kurs geladen."},
            tool_calls=[],
            is_agent_flow=False,
        )
    )
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)

    request = schemas.ChatRequest(
        prompt="Wie ist der aktuelle Bitcoin Kurs?",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    await orchestrator_instance.handle_chat_request(request)

    gateway_kwargs = run_tool_loop_mock.await_args.kwargs.get("gateway_kwargs") or {}
    allowed = gateway_kwargs.get("allowed_skill_ids") or []
    requested = gateway_kwargs.get("requested_skills") or []
    assert "system.websearch" in allowed, f"system.websearch missing from allowed_skill_ids: {allowed}"
    assert "system.websearch" in requested, f"system.websearch missing from requested_skills: {requested}"


@pytest.mark.asyncio
async def test_gemini_live_web_query_forces_system_websearch(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Gemini Websearch Guardrail")

    run_tool_loop_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="Bitcoin Kurs geladen.",
            raw_response={"text": "Bitcoin Kurs geladen."},
            tool_calls=[],
            is_agent_flow=False,
        )
    )
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)

    request = schemas.ChatRequest(
        prompt="Wie ist der aktuelle Bitcoin Kurs?",
        chat_id=chat.id,
        provider="gemini",
        model="gemini-3-flash-preview",
        api_key="dummy",
    )

    await orchestrator_instance.handle_chat_request(request)

    gateway_kwargs = run_tool_loop_mock.await_args.kwargs.get("gateway_kwargs") or {}
    allowed = gateway_kwargs.get("allowed_skill_ids") or []
    requested = gateway_kwargs.get("requested_skills") or []
    assert "system.websearch" in allowed, f"system.websearch missing from allowed_skill_ids: {allowed}"
    assert "system.websearch" in requested, f"system.websearch missing from requested_skills: {requested}"


@pytest.mark.asyncio
async def test_ollama_live_web_query_forces_system_websearch(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Ollama Websearch Guardrail")

    run_tool_loop_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="Bitcoin Kurs geladen.",
            raw_response={"text": "Bitcoin Kurs geladen."},
            tool_calls=[],
            is_agent_flow=False,
        )
    )
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)

    request = schemas.ChatRequest(
        prompt="Wie ist der aktuelle Bitcoin Kurs?",
        chat_id=chat.id,
        provider="ollama",
        model="qwen2.5:14b@test",
        api_key="ollama",
    )

    await orchestrator_instance.handle_chat_request(request)

    gateway_kwargs = run_tool_loop_mock.await_args.kwargs.get("gateway_kwargs") or {}
    allowed = gateway_kwargs.get("allowed_skill_ids") or []
    requested = gateway_kwargs.get("requested_skills") or []
    assert "system.websearch" in allowed, f"system.websearch missing from allowed_skill_ids: {allowed}"
    assert "system.websearch" in requested, f"system.websearch missing from requested_skills: {requested}"


@pytest.mark.asyncio
async def test_video_intent_prioritizes_video_search_with_websearch_fallback(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Video Guardrail Recall Override")

    run_tool_loop_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="Hier ist ein Video.",
            raw_response={"text": "Hier ist ein Video."},
            tool_calls=[],
            is_agent_flow=False,
        )
    )
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)

    request = schemas.ChatRequest(
        prompt="Zeig mir ein Video fuer meinen Pizzateig.",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    await orchestrator_instance.handle_chat_request(request)

    gateway_kwargs = run_tool_loop_mock.await_args.kwargs.get("gateway_kwargs") or {}
    allowed = gateway_kwargs.get("allowed_skill_ids") or []
    requested = gateway_kwargs.get("requested_skills") or []
    assert allowed == ["video.search", "system.websearch"], (
        f"Video intent should prioritize video.search with websearch fallback, got: {allowed}"
    )
    assert requested == ["video.search", "system.websearch"], (
        f"Video intent should request video.search then websearch fallback, got: {requested}"
    )


@pytest.mark.asyncio
async def test_image_pdf_prompt_allows_generate_image_and_create_pdf(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Image PDF Flow")

    run_tool_loop_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="Bild und PDF erstellt.",
            raw_response={"text": "Bild und PDF erstellt."},
            tool_calls=[],
            is_agent_flow=False,
        )
    )
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)

    request = schemas.ChatRequest(
        prompt="Erstell mir ein Bild von einem kleinen Affen und speichere es in einer PDF namens Affen_Bericht.pdf",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    await orchestrator_instance.handle_chat_request(request)

    gateway_kwargs = run_tool_loop_mock.await_args.kwargs.get("gateway_kwargs") or {}
    allowed_skill_ids = gateway_kwargs.get("allowed_skill_ids") or []
    requested_skills = gateway_kwargs.get("requested_skills") or []
    assert "system.generate_image" in allowed_skill_ids
    assert "system.create_pdf" in allowed_skill_ids
    assert "system.generate_image" in requested_skills
    assert "system.create_pdf" in requested_skills


@pytest.mark.asyncio
async def test_run_tool_loop_continues_after_image_when_pdf_requested(orchestrator_instance):
    reason_and_respond_fn = AsyncMock(
        side_effect=[
            {
                "tool_calls": [
                    {
                        "function": {
                            "name": "system.generate_image",
                            "arguments": json.dumps({"prompt": "kleiner Affe"}),
                        }
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "Ich erstelle ein Bild."},
            },
            {
                "tool_calls": [
                    {
                        "function": {
                            "name": "system.create_pdf",
                            "arguments": json.dumps(
                                {
                                    "filename": "Affen_Bericht.pdf",
                                    "content": "![Bild](/user_images/affe.png)\\n\\nKurze Beschreibung.",
                                    "location": "Documents",
                                }
                            ),
                        }
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "Ich erstelle nun das PDF."},
            },
            {"text": "Fertig.", "tool_calls": []},
        ]
    )
    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        side_effect=[
            [
                {
                    "name": "system.generate_image",
                    "role": "tool",
                    "content": json.dumps({"status": "ok", "data": {"local_image_path": "/user_images/affe.png"}}),
                }
            ],
            [
                {
                    "name": "system.create_pdf",
                    "role": "tool",
                    "content": json.dumps({"status": "ok", "data": {"filename": "Affen_Bericht.pdf"}}),
                }
            ],
        ]
    )

    result = await orchestrator_instance.execution_engine.run_tool_loop(
        orchestrator_context=OrchestratorContext(history=[], memories=[]),
        tool_executor=tool_executor,
        gateway_kwargs={
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "api_key": "dummy",
            "chat_history": [],
            "user_prompt": "Erstell ein Bild und dann PDF namens Affen_Bericht.pdf",
            "reason_and_respond_fn": reason_and_respond_fn,
            "requested_skills": ["system.generate_image", "system.create_pdf"],
        },
        fallback_summary="fallback",
        current_limit=3,
        bypass_policy_this_turn=False,
        set_policy_pending=lambda *_args, **_kwargs: None,
        chat_id=1,
    )

    assert tool_executor.execute_tool_calls.await_count == 2
    assert result.text == "PDF erstellt."


@pytest.mark.asyncio
async def test_run_tool_loop_does_not_apply_ollama_image_regex_fallback_for_non_ollama(orchestrator_instance):
    reason_and_respond_fn = AsyncMock(
        return_value={
            "text": "A cute small monkey in a forest.",
            "tool_calls": [],
        }
    )
    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    result = await orchestrator_instance.execution_engine.run_tool_loop(
        orchestrator_context=OrchestratorContext(history=[], memories=[]),
        tool_executor=tool_executor,
        gateway_kwargs={
            "provider": "gemini",
            "model": "gemini-3-flash-preview",
            "api_key": "dummy",
            "chat_history": [],
            "user_prompt": "Erstelle ein Bild von einem Affen.",
            "reason_and_respond_fn": reason_and_respond_fn,
            "requested_skills": ["system.generate_image"],
        },
        fallback_summary="fallback",
        current_limit=3,
        bypass_policy_this_turn=False,
        set_policy_pending=lambda *_args, **_kwargs: None,
        chat_id=1,
    )

    assert tool_executor.execute_tool_calls.await_count == 0
    assert result.text == "A cute small monkey in a forest."


@pytest.mark.asyncio
@patch("backend.services.orchestrator.storybook_pipeline.create_pdf_from_markdown")
@patch("backend.services.orchestrator.storybook_pipeline.generate_image_tool", new_callable=AsyncMock)
@patch("backend.services.orchestrator.storybook_pipeline.get_provider")
async def test_run_storybook_macro_generates_pdf(mock_get_provider, mock_generate_image_tool, mock_create_pdf, orchestrator_instance):
    story_json = {
        "title": "Der kleine Hase",
        "chapters": [
            {
                "chapter_title": "Kapitel 1",
                "text_above": "An einem Morgen traf der Hase den Igel.",
                "image_prompt": "A cute rabbit sharing berries with a hedgehog, children book illustration",
                "text_below": "Sie wurden sofort Freunde.",
            }
        ],
    }
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(return_value={"text": f"```json\n{json.dumps(story_json)}\n```"})
    mock_get_provider.return_value = mock_provider

    mock_generate_image_tool.return_value = {
        "status": "ok",
        "data": {
            "markdown_image": "![Illustration](/user_images/test.png)",
            "local_image_path": "/user_images/test.png",
        },
    }
    mock_create_pdf.return_value = {"status": "ok", "data": {"file_path": "C:/Docs/Der_kleine_Hase.pdf"}}

    response = await orchestrator_instance._run_storybook_macro(
        "Eine Geschichte über einen Hasen",
        schemas.ChatRequest(prompt="", provider="openai", model="gpt-5.4-nano", api_key="dummy"),
        api_key="dummy",
    )

    mock_get_provider.assert_called_once()
    mock_generate_image_tool.assert_awaited()
    mock_create_pdf.assert_called_once()
    args, kwargs = mock_create_pdf.call_args
    assert kwargs.get("layout_profile") == "bilderbuch"
    assert "![Illustration]" in kwargs.get("content", "")
    assert "Der kleine Hase" in kwargs.get("content", "")
    assert "Dein Kinderbuch ist fertig" in response.text


@pytest.mark.asyncio
@patch("backend.services.orchestrator.storybook_pipeline.create_pdf_from_markdown")
@patch("backend.services.orchestrator.storybook_pipeline.generate_image_tool", new_callable=AsyncMock)
@patch("backend.services.orchestrator.storybook_pipeline.get_provider")
async def test_run_storybook_macro_stabilizes_animal_image_prompts(mock_get_provider, mock_generate_image_tool, mock_create_pdf, orchestrator_instance):
    story_json = {
        "title": "Der kleine Hase",
        "chapters": [
            {
                "chapter_title": "Kapitel 1",
                "text_above": "An einem Morgen traf der Hase den Igel.",
                "image_prompt": "A cute rabbit and a hedgehog in a sunny meadow, children book illustration",
                "text_below": "Sie wurden sofort Freunde.",
            }
        ],
    }
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(return_value={"text": f"```json\n{json.dumps(story_json)}\n```"})
    mock_get_provider.return_value = mock_provider

    mock_generate_image_tool.return_value = {
        "status": "ok",
        "data": {
            "markdown_image": "![Illustration](/user_images/test.png)",
            "local_image_path": "/user_images/test.png",
        },
    }
    mock_create_pdf.return_value = {"status": "ok", "data": {"file_path": "C:/Docs/Der_kleine_Hase.pdf"}}

    await orchestrator_instance._run_storybook_macro(
        "Eine Geschichte über einen Hasen und einen Igel als Bilderbuch mit PDF",
        schemas.ChatRequest(prompt="", provider="openai", model="gpt-5.4-nano", api_key="dummy"),
        api_key="dummy",
    )

    prompt = mock_generate_image_tool.await_args.kwargs["prompt"]
    assert "same animal characters" in prompt
    assert "Do not depict them as human children" in prompt


@pytest.mark.asyncio
@patch("backend.services.orchestrator.storybook_pipeline.create_pdf_from_markdown")
@patch("backend.services.orchestrator.storybook_pipeline.generate_image_tool", new_callable=AsyncMock)
@patch("backend.services.orchestrator.storybook_pipeline.get_provider")
async def test_run_storybook_macro_prefers_requested_title_for_gemini(
    mock_get_provider,
    mock_generate_image_tool,
    mock_create_pdf,
    orchestrator_instance,
):
    story_json = {
        "title": "Hoppel und Piekser: Ein apfelstarkes Abenteuer",
        "chapters": [
            {
                "chapter_title": "Kapitel 1",
                "text_above": "Hoppel trifft Piekser auf der Wiese.",
                "image_prompt": "A cute rabbit and a hedgehog in a sunny meadow, children book illustration",
                "text_below": "Sie wollen Freunde werden.",
            }
        ],
    }
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(return_value={"text": f"```json\n{json.dumps(story_json)}\n```"})
    mock_get_provider.return_value = mock_provider
    mock_generate_image_tool.return_value = {
        "status": "ok",
        "data": {
            "markdown_image": "![Illustration](/user_images/test.png)",
            "local_image_path": "/user_images/test.png",
        },
    }
    mock_create_pdf.return_value = {"status": "ok", "data": {"file_path": "C:/Docs/Der_kleine_Hase.pdf"}}

    await orchestrator_instance._run_storybook_macro(
        "Bitte erstelle ein Kinderbuch mit PDF. Der Titel des Buchs soll 'Der kleine Hase' sein.",
        schemas.ChatRequest(prompt="", provider="gemini", model="gemini-3-flash-preview", api_key="dummy"),
        api_key="dummy",
    )

    kwargs = mock_create_pdf.call_args.kwargs
    assert kwargs.get("filename") == "Der_kleine_Hase.pdf"
    assert "# Der kleine Hase" in kwargs.get("content", "")


@pytest.mark.asyncio
@patch("backend.services.orchestrator.storybook_pipeline.create_pdf_from_markdown")
@patch("backend.services.orchestrator.storybook_pipeline.generate_image_tool", new_callable=AsyncMock)
@patch("backend.services.orchestrator.storybook_pipeline.get_provider")
async def test_run_storybook_macro_uses_requested_unquoted_title_for_gemini_filename(
    mock_get_provider,
    mock_generate_image_tool,
    mock_create_pdf,
    orchestrator_instance,
):
    story_json = {
        "title": "Kinder",
        "chapters": [
            {
                "chapter_title": "Kapitel 1",
                "text_above": "Hoppel trifft Piekser auf der Wiese.",
                "image_prompt": "A cute rabbit and a hedgehog in a sunny meadow, children book illustration",
                "text_below": "Sie wollen Freunde werden.",
            }
        ],
    }
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(return_value={"text": f"```json\n{json.dumps(story_json)}\n```"})
    mock_get_provider.return_value = mock_provider
    mock_generate_image_tool.return_value = {
        "status": "ok",
        "data": {
            "markdown_image": "![Illustration](/user_images/test.png)",
            "local_image_path": "/user_images/test.png",
        },
    }
    mock_create_pdf.return_value = {"status": "ok", "data": {"file_path": "C:/Docs/Der_kleine_Hase.pdf"}}

    await orchestrator_instance._run_storybook_macro(
        "Bitte erstelle ein Kinderbuch mit PDF. Der Name des Buchs soll Der kleine Hase sein.",
        schemas.ChatRequest(prompt="", provider="gemini", model="gemini-3-flash-preview", api_key="dummy"),
        api_key="dummy",
    )

    kwargs = mock_create_pdf.call_args.kwargs
    assert kwargs.get("filename") == "Der_kleine_Hase.pdf"
    assert "# Der kleine Hase" in kwargs.get("content", "")


@pytest.mark.asyncio
@patch("backend.services.orchestrator.storybook_pipeline.create_pdf_from_markdown")
@patch("backend.services.orchestrator.storybook_pipeline.generate_image_tool", new_callable=AsyncMock)
@patch("backend.services.orchestrator.storybook_pipeline.get_provider")
async def test_run_storybook_macro_uses_quoted_story_title_for_gemini_filename(
    mock_get_provider,
    mock_generate_image_tool,
    mock_create_pdf,
    orchestrator_instance,
):
    story_json = {
        "title": "Kinder",
        "chapters": [
            {
                "chapter_title": "Kapitel 1",
                "text_above": "Hoppel trifft Piekser auf der Wiese.",
                "image_prompt": "A cute rabbit and a hedgehog in a sunny meadow, children book illustration",
                "text_below": "Sie wollen Freunde werden.",
            }
        ],
    }
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(return_value={"text": f"```json\n{json.dumps(story_json)}\n```"})
    mock_get_provider.return_value = mock_provider
    mock_generate_image_tool.return_value = {
        "status": "ok",
        "data": {
            "markdown_image": "![Illustration](/user_images/test.png)",
            "local_image_path": "/user_images/test.png",
        },
    }
    mock_create_pdf.return_value = {"status": "ok", "data": {"file_path": "C:/Docs/Der_kleine_Hase.pdf"}}

    await orchestrator_instance._run_storybook_macro(
        "Bitte erstelle die Geschichte 'Der kleine Hase' als Kinderbuch mit PDF.",
        schemas.ChatRequest(prompt="", provider="gemini", model="gemini-3-flash-preview", api_key="dummy"),
        api_key="dummy",
    )

    kwargs = mock_create_pdf.call_args.kwargs
    assert kwargs.get("filename") == "Der_kleine_Hase.pdf"
    assert "# Der kleine Hase" in kwargs.get("content", "")
    assert mock_generate_image_tool.await_args.kwargs["prompt"].lower().count("der kleine hase") == 0


@pytest.mark.asyncio
@patch("backend.services.orchestrator.storybook_pipeline.create_pdf_from_markdown")
@patch("backend.services.orchestrator.storybook_pipeline.generate_image_tool", new_callable=AsyncMock)
@patch("backend.services.orchestrator.storybook_pipeline.get_provider")
async def test_run_storybook_macro_respects_requested_three_sentences_per_gemini_chapter(
    mock_get_provider,
    mock_generate_image_tool,
    mock_create_pdf,
    orchestrator_instance,
):
    story_json = {
        "title": "Irgendein anderer Titel",
        "chapters": [
            {
                "chapter_title": "Kapitel 1",
                "text_above": (
                    "An einem sonnigen Morgen hoppelte Hoppel durch die Wiese. "
                    "Er schnupperte an Blumen. "
                    "Dann hörte er plötzlich ein Rascheln hinter einem Blatt."
                ),
                "image_prompt": "A cute rabbit and a hedgehog in a sunny meadow, children book illustration",
                "text_below": (
                    "Piekser kam vorsichtig hervor und blinzelte ins Licht. "
                    "Die beiden sahen sich an und lächelten. "
                    "Dann fragte Hoppel, ob sie zusammen spielen wollen."
                ),
            }
        ],
    }
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(return_value={"text": f"```json\n{json.dumps(story_json)}\n```"})
    mock_get_provider.return_value = mock_provider
    mock_generate_image_tool.return_value = {
        "status": "ok",
        "data": {
            "markdown_image": "![Illustration](/user_images/test.png)",
            "local_image_path": "/user_images/test.png",
        },
    }
    mock_create_pdf.return_value = {"status": "ok", "data": {"file_path": "C:/Docs/Der_kleine_Hase.pdf"}}

    await orchestrator_instance._run_storybook_macro(
        "Bitte erstelle ein Kinderbuch mit PDF. Der Titel des Buchs soll 'Der kleine Hase' sein. Bitte mindestens 3 Sätze pro Kapitel.",
        schemas.ChatRequest(prompt="", provider="gemini", model="gemini-3-flash-preview", api_key="dummy"),
        api_key="dummy",
    )

    content = mock_create_pdf.call_args.kwargs.get("content", "")
    assert "# Der kleine Hase" in content
    chapter_one = content.split("## Kapitel 1", 1)[1]
    assert _count_sentences(chapter_one) >= 3


@pytest.mark.asyncio
@patch("backend.services.orchestrator.storybook_pipeline.create_pdf_from_markdown")
@patch("backend.services.orchestrator.storybook_pipeline.generate_image_tool", new_callable=AsyncMock)
@patch("backend.services.orchestrator.storybook_pipeline.get_provider")
async def test_run_storybook_macro_compacts_gemini_late_chapter_tail_more_aggressively(
    mock_get_provider,
    mock_generate_image_tool,
    mock_create_pdf,
    orchestrator_instance,
):
    story_json = {
        "title": "Kinder",
        "chapters": [
            {
                "chapter_title": "Kapitel 1",
                "text_above": "Kurz.",
                "image_prompt": "A cute rabbit and a hedgehog in a sunny meadow, children book illustration",
                "text_below": "Kurz.",
            },
            {
                "chapter_title": "Kapitel 2",
                "text_above": "Kurz.",
                "image_prompt": "A rabbit helps a hedgehog cross a stream, children book illustration",
                "text_below": "Kurz.",
            },
            {
                "chapter_title": "Kapitel 3",
                "text_above": "Hinter dem Bach fanden sie einen versteckten Garten voller wilder Blaubeeren und roter Erdbeeren. Die Sonne neigte sich langsam dem Horizont entgegen.",
                "image_prompt": "A bunny and a hedgehog sitting together in a field of wild strawberries and blueberries, children book illustration",
                "text_below": "Sie erzählten sich lustige Geschichten, bis der Mond am Himmel aufging und die ersten Sterne funkelten. Müde, aber sehr glücklich, kuschelten sie sich unter einer großen Wurzel zusammen. Dann flüsterten sie, dass dieser Tag für immer in ihren Herzen bleiben würde.",
            },
        ],
    }
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(return_value={"text": f"```json\n{json.dumps(story_json)}\n```"})
    mock_get_provider.return_value = mock_provider
    mock_generate_image_tool.return_value = {
        "status": "ok",
        "data": {
            "markdown_image": "![Illustration](/user_images/test.png)",
            "local_image_path": "/user_images/test.png",
        },
    }
    mock_create_pdf.return_value = {"status": "ok", "data": {"file_path": "C:/Docs/Der_kleine_Hase.pdf"}}

    await orchestrator_instance._run_storybook_macro(
        "Bitte erstelle die Geschichte 'Der kleine Hase' als Kinderbuch mit PDF. Bitte mindestens 3 Sätze pro Kapitel.",
        schemas.ChatRequest(prompt="", provider="gemini", model="gemini-3-flash-preview", api_key="dummy"),
        api_key="dummy",
    )

    content = mock_create_pdf.call_args.kwargs.get("content", "")
    chapter_three = content.split("## Kapitel 3", 1)[1]
    assert _count_sentences(chapter_three) >= 3
    assert any(keyword in chapter_three.lower() for keyword in ["wurzel", "nest", "moos", "kuschelten"])


@pytest.mark.asyncio
@patch("backend.services.orchestrator.storybook_pipeline.create_pdf_from_markdown")
@patch("backend.services.orchestrator.storybook_pipeline.generate_image_tool", new_callable=AsyncMock)
@patch("backend.services.orchestrator.storybook_pipeline.get_provider")
async def test_run_storybook_macro_rebuilds_gemini_scene_prompts_with_visual_details(
    mock_get_provider,
    mock_generate_image_tool,
    mock_create_pdf,
    orchestrator_instance,
):
    story_json = {
        "title": "Kinder",
        "chapters": [
            {
                "chapter_title": "Kapitel 2",
                "text_above": "Die beiden Freunde fanden einen versteckten Garten voller Beeren neben dem Bach.",
                "image_prompt": "A rabbit and hedgehog in a forest path, children book illustration",
                "text_below": "Zwischen Erdbeeren und Blaubeeren lachten sie glücklich und sammelten ihren süßen Schatz.",
            },
            {
                "chapter_title": "Kapitel 3",
                "text_above": "Am Abend bauten sie sich ein weiches Nest aus trockenem Gras, Moos und Wurzeln.",
                "image_prompt": "A rabbit and hedgehog at sunset, children book illustration",
                "text_below": "Dann kuschelten sie sich gemütlich in ihr kleines Nest und schauten in den warmen Himmel.",
            },
        ],
    }
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(return_value={"text": f"```json\n{json.dumps(story_json)}\n```"})
    mock_get_provider.return_value = mock_provider
    mock_generate_image_tool.return_value = {
        "status": "ok",
        "data": {
            "markdown_image": "![Illustration](/user_images/test.png)",
            "local_image_path": "/user_images/test.png",
        },
    }
    mock_create_pdf.return_value = {"status": "ok", "data": {"file_path": "C:/Docs/Der_kleine_Hase.pdf"}}

    await orchestrator_instance._run_storybook_macro(
        "Bitte erstelle die Geschichte 'Der kleine Hase' als Kinderbuch mit PDF. Bitte mindestens 3 Sätze pro Kapitel.",
        schemas.ChatRequest(prompt="", provider="gemini", model="gemini-3-flash-preview", api_key="dummy"),
        api_key="dummy",
    )

    prompts = [call.kwargs["prompt"].lower() for call in mock_generate_image_tool.await_args_list]
    assert any("berries" in prompt and "blueberries" in prompt for prompt in prompts)
    assert any("cozy nest" in prompt and "soft moss" in prompt for prompt in prompts)
    assert all("chapter title:" not in prompt for prompt in prompts)
    assert all("kapitel 2" not in prompt and "kapitel 3" not in prompt for prompt in prompts)
    assert all("no visible text whatsoever" in prompt for prompt in prompts)
    assert all("no letters, words, captions, subtitles" in prompt for prompt in prompts)


@pytest.mark.asyncio
async def test_handle_chat_request_triggers_storybook_macro(orchestrator_instance, monkeypatch):
    response = ExecutionResponse(text="ok", tool_calls=[], is_agent_flow=False)
    run_macro = AsyncMock(return_value=response)
    monkeypatch.setattr(ChatOrchestrator, "_run_storybook_macro", run_macro)
    orchestrator_instance.status_sync = MagicMock()
    orchestrator_instance.status_sync.persist_assistant_message = MagicMock()
    orchestrator_instance.status_sync.build_api_response = MagicMock(return_value={"text": "ok"})

    request = schemas.ChatRequest(
        prompt="Bitte schreibe eine Kinderbuch Geschichte mit Illustrationen und speichere sie als PDF",
        chat_id=42,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    result = await orchestrator_instance.handle_chat_request(request)

    run_macro.assert_awaited_once()
    orchestrator_instance.status_sync.persist_assistant_message.assert_called_once()
    orchestrator_instance.status_sync.build_api_response.assert_called_once_with(execution_response=response)
    assert result == {"text": "ok"}


def test_persist_orchestrator_kpi_creates_db_row(orchestrator_instance):
    orchestrator_instance._persist_orchestrator_kpi(
        provider="ollama",
        model="gemma2:27b",
        chat_id=None,
        is_meta_agent_run=True,
        t_phase1_research_ms=101.5,
        t_phase2_pdf_ms=202.5,
        t_final_response_ms=303.5,
        retry_path="meta_phase2_forced",
        retry_count=1,
        success=True,
        error_code=None,
    )

    row = (
        orchestrator_instance.db.query(models.OrchestratorKPI)
        .order_by(models.OrchestratorKPI.id.desc())
        .first()
    )
    assert row is not None
    assert row.provider == "ollama"
    assert row.t_phase1_research_ms == pytest.approx(101.5)
    assert row.retry_path == "meta_phase2_forced"


def test_orchestrator_kpi_dashboard_aggregates_percentiles_and_retry_error_rate(db_session):
    crud.create_orchestrator_kpi(
        db_session,
        provider="ollama",
        model="gemma2:27b",
        chat_id=None,
        is_meta_agent_run=True,
        t_phase1_research_ms=100,
        t_phase2_pdf_ms=200,
        t_final_response_ms=500,
        retry_path="meta_phase2_forced",
        retry_count=1,
        success=True,
        error_code=None,
    )
    crud.create_orchestrator_kpi(
        db_session,
        provider="ollama",
        model="gemma2:27b",
        chat_id=None,
        is_meta_agent_run=True,
        t_phase1_research_ms=300,
        t_phase2_pdf_ms=400,
        t_final_response_ms=700,
        retry_path="meta_phase2_forced",
        retry_count=1,
        success=False,
        error_code="TIMEOUT",
    )

    now = datetime.now()
    dashboard = crud.get_orchestrator_kpi_dashboard(db_session, now.year, now.month)

    assert dashboard["total_runs"] >= 2
    ollama_metrics = dashboard["providers"]["ollama"]
    assert ollama_metrics["t_phase1_research_ms"]["p50"] == pytest.approx(200.0)
    assert ollama_metrics["t_phase2_pdf_ms"]["p95"] == pytest.approx(390.0)
    retry_metrics = dashboard["retry_paths"]["meta_phase2_forced"]
    assert retry_metrics["error_rate"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_gemma_routing_trigger_forces_agent_factory_despite_local_skip_signal(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Gemma Routing Trigger")

    run_agent_factory_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="routing handled",
            raw_response={"text": "routing handled"},
            tool_calls=[],
            is_agent_flow=True,
            agent_payload={"trace_id": "trace-gemma-routing"},
        )
    )
    run_tool_loop_mock = AsyncMock()

    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_agent_factory", run_agent_factory_mock)
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)
    monkeypatch.setattr("backend.services.chat_orchestrator.intent_classifier.should_skip_planner", lambda _text: True)

    request = schemas.ChatRequest(
        prompt="wie weit ist es von münchen nach köln",
        chat_id=chat.id,
        provider="ollama",
        model="gemma2:27b",
        api_key="",
    )

    await orchestrator_instance.handle_chat_request(request)

    run_agent_factory_mock.assert_awaited_once()
    kwargs = run_agent_factory_mock.await_args.kwargs
    assert kwargs.get("user_text") == "wie weit ist es von münchen nach köln"
    assert kwargs.get("model") == "gemma2:27b"
    run_tool_loop_mock.assert_not_awaited()


def test_is_complex_document_request_detection(orchestrator_instance):
    assert orchestrator_instance.is_complex_document_request(
        "Erstelle ein PDF-Dokument mit Hauptstadt und Einwohnerzahl von Schweden."
    ) is True
    assert orchestrator_instance.is_complex_document_request("Erstelle ein PDF-Dokument.") is False
    assert orchestrator_instance.is_complex_document_request("Wie ist die Hauptstadt von Schweden?") is False


def test_normalize_meta_facts_filters_tool_json_artifacts(orchestrator_instance):
    phase1_context = "\n".join(
        [
            "[system.country_info] Die Hauptstadt von Schweden ist Stockholm.",
            "[system.routing] Stockholm hat ca. 975.000 Einwohner.",
            "```json",
            '{"name": "system.route_directions", "parameters": {"start": "Berlin", "destination": "Stockholm"}}',
            "```",
            "[system.routing] Die Entfernung von Berlin nach Stockholm beträgt etwa 600 Kilometer.",
        ]
    )

    facts = orchestrator_instance._normalize_meta_facts(phase1_context)

    assert facts == [
        "Die Hauptstadt von Schweden ist Stockholm.",
        "Stockholm hat ca. 975.000 Einwohner.",
        "Die Entfernung von Berlin nach Stockholm beträgt etwa 600 Kilometer.",
    ]


def test_meta_phase1_facts_weak_for_routing_only_context(orchestrator_instance):
    facts = [
        "Routenuebersicht (aus Tool-Ergebnissen): 1. Stockholm -> Oslo: 525.9 km, 7 Std. 4 Min.",
        "Google Maps Links: https://www.google.com/maps/dir/?api=1&origin=Stockholm&destination=Oslo&travelmode=driving",
    ]

    assert orchestrator_instance._is_meta_phase1_facts_weak(facts) is True


def test_meta_phase2_prompt_uses_request_fallback_for_routing_only_phase1(orchestrator_instance):
    phase1_context = (
        "Routenuebersicht (aus Tool-Ergebnissen):\n"
        "1. Stockholm -> Oslo: 525.9 km, 7 Std. 4 Min.\n"
        "2. Stockholm -> Kopenhagen: 655.0 km, 7 Std. 38 Min."
    )
    user_prompt = (
        "Erstelle ein umfangreiches PDF ueber skandinavische Hauptstaedte, ihre aktuellen Bevoelkerungszahlen, "
        "Klimazonen, Handelsbeziehungen, drei Kulturdenkmaeler pro Stadt und politische Fuehrungsstruktur."
    )

    prompt = orchestrator_instance._build_meta_phase2_json_only_prompt(
        phase1_context,
        requested_filename="skandinavien.pdf",
        original_user_text=user_prompt,
    )

    assert "Nutzeranfrage (Fallback-Kontext):" in prompt
    assert "Nutzeranfrage (Pflichtanforderungen):" in prompt
    assert "Pflichtabschnitte laut Nutzeranfrage:" in prompt
    assert "Klimazonen" in prompt
    assert "parameter.filename EXAKT 'skandinavien.pdf'" in prompt


def test_meta_phase2_prompt_uses_topic_gap_fallback_when_facts_only_cover_capitals(orchestrator_instance):
    phase1_context = "\n".join(
        [
            "Schweden: Hauptstadt Stockholm, Einwohner ca. 10.605.098, Region Europe.",
            "Norwegen: Hauptstadt Oslo, Einwohner ca. 5.606.944, Region Europe.",
        ]
    )
    user_prompt = (
        "Erstelle ein umfangreiches PDF ueber skandinavische Hauptstaedte, ihre aktuellen Bevoelkerungszahlen, "
        "Klimazonen, Handelsbeziehungen, drei Kulturdenkmaeler pro Stadt und politische Fuehrungsstruktur."
    )

    prompt = orchestrator_instance._build_meta_phase2_json_only_prompt(
        phase1_context,
        requested_filename="skandinavien.pdf",
        original_user_text=user_prompt,
    )

    assert "Nutzeranfrage (Pflichtanforderungen):" in prompt
    assert "Nutzeranfrage (Fallback-Kontext):" in prompt
    assert "Pflichtabschnitte laut Nutzeranfrage:" in prompt
    assert "Handelsbeziehungen" in prompt
    assert "Kulturdenkmaeler" in prompt


def test_get_meta_provider_profile_respects_provider_defaults():
    gemini_profile = ChatOrchestrator._get_meta_provider_profile("gEmiNi")
    assert gemini_profile["phase2_allow_planner"] is False
    assert gemini_profile["phase1_max_tokens"] == 120
    default_profile = ChatOrchestrator._get_meta_provider_profile("unknown")
    assert default_profile["phase2_allow_planner"] is True


def test_meta_phase2_prompt_respects_provider_caps(orchestrator_instance):
    meta_profile = {
        "phase2_facts_max_tokens": 2,
        "phase2_requirements_max_tokens": 1,
        "phase2_request_fallback_max_tokens": 2,
    }
    prompt = orchestrator_instance._build_meta_phase2_json_only_prompt(
        phase1_context="",
        requested_filename="test.pdf",
        original_user_text="eins zwei drei vier",
        meta_profile=meta_profile,
    )
    assert "Fakten: Keine" in prompt
    assert "Nutzeranfrage (Pflichtanforderungen):" in prompt
    assert "Nutzeranfrage (Fallback-Kontext):" in prompt


def test_build_meta_pdf_markdown_content_keeps_requested_sections_even_with_sparse_facts(orchestrator_instance):
    phase1_context = "Schweden: Hauptstadt Stockholm, Einwohner ca. 10.605.098, Region Europe."
    user_prompt = (
        "Erstelle ein PDF ueber skandinavische Hauptstaedte, Bevoelkerung, Klimazonen, "
        "Handelsbeziehungen, drei Kulturdenkmaeler pro Stadt und politische Fuehrungsstruktur."
    )

    markdown = orchestrator_instance._build_meta_pdf_markdown_content(
        phase1_context=phase1_context,
        original_user_text=user_prompt,
    )

    assert "## Hauptstaedte" in markdown
    assert "## Bevoelkerung" in markdown
    assert "## Klimazonen" in markdown
    assert "## Handelsbeziehungen" in markdown
    assert "## Kulturdenkmaeler" in markdown
    assert "## Politische Fuehrungsstruktur" in markdown
    assert "Keine belastbaren Fakten aus der Recherche verfuegbar" in markdown


@pytest.mark.asyncio
async def test_meta_phase2_forced_run_falls_back_to_direct_pdf_generation_on_exception(orchestrator_instance, monkeypatch):
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=TimeoutError("timeout")))
    monkeypatch.setattr(
        orchestrator_instance,
        "_run_meta_agent_direct_pdf_generation",
        AsyncMock(
            return_value=ExecutionResponse(
                text="Deterministische PDF-Erstellung erfolgreich:\n- C:\\Users\\pruve\\Documents\\die.pdf",
                raw_response={},
                tool_calls=[],
                is_agent_flow=True,
                agent_payload={"trace_id": "direct-fallback"},
            )
        ),
    )

    request = schemas.ChatRequest(
        prompt="Erstelle ein PDF ueber Skandinavien.",
        chat_id=1,
        provider="ollama",
        model="mistral-nemo:12b@localhost",
        api_key="",
    )

    result = await orchestrator_instance._run_meta_agent_production_fallback(
        phase1_context="Schweden: Hauptstadt Stockholm.",
        requested_filename="die.pdf",
        original_user_text=request.prompt,
        request=request,
        api_key="",
    )

    assert result.is_agent_flow is True
    assert "Deterministische PDF-Erstellung erfolgreich" in str(result.text or "")


def test_should_force_scandinavia_country_coverage_detects_scandinavian_prompt(orchestrator_instance):
    prompt = "Erstelle ein umfangreiches PDF ueber die skandinavischen Hauptstaedte und ihre Bevoelkerung."
    assert orchestrator_instance._should_force_scandinavia_country_coverage(prompt) is True


def test_country_query_candidates_include_aliases_for_daenemark(orchestrator_instance):
    candidates = orchestrator_instance._country_query_candidates("Dänemark")
    assert candidates == ["Dänemark", "Daenemark", "Denmark"]


def test_capital_matches_expected_accepts_copenhagen_variant(orchestrator_instance):
    assert orchestrator_instance._capital_matches_expected(actual_capital="Copenhagen", expected_capital="Kopenhagen") is True
    assert orchestrator_instance._capital_matches_expected(actual_capital="Avarua", expected_capital="Kopenhagen") is False


def test_normalize_meta_facts_filters_noise_lines(orchestrator_instance):
    phase1_context = "\n".join(
        [
            "Hallo! Gerne teile ich Informationen zu den skandinavischen Hauptstädten:",
            "Bitte gib mir Start und Ziel deiner Reise, damit ich Distanz und Dauer berechnen kann.",
            "[system.country_info] Schweden: Hauptstadt Stockholm, Einwohner ca. 10.605.098, Region Europe.",
            "[system.routing] 1. Kopenhagen -> Stockholm: 654.4 km, 7 Std. 38 Min.",
            "Google Maps Links: https://www.google.com/maps/dir/?api=1&origin=Kopenhagen&destination=Stockholm&travelmode=driving",
        ]
    )

    facts = orchestrator_instance._normalize_meta_facts(phase1_context)

    assert "Schweden: Hauptstadt Stockholm, Einwohner ca. 10.605.098, Region Europe." in facts
    assert "1. Kopenhagen -> Stockholm: 654.4 km, 7 Std. 38 Min." in facts
    assert all("Hallo!" not in item for item in facts)
    assert all("Google Maps Links" not in item for item in facts)

def test_collect_meta_topic_instructions_matches_keywords(orchestrator_instance):
    prompt = "Erstelle ein PDF ueber Klima, Handel und Kultur in Skandinavien."
    instructions = orchestrator_instance._collect_meta_topic_instructions(prompt)
    assert any("Klimazonen" in text for text in instructions)
    assert any("Handelsbeziehungen" in text for text in instructions)
    assert any("Kulturdenkmäler" in text for text in instructions)


def test_meta_research_prompt_includes_topic_instructions(orchestrator_instance):
    prompt = "Beschreibe Klima, Handel und Kultur in Skandinavien." \
        "Erstelle ein pdf mit diesen Abschnitten."
    text = orchestrator_instance._build_meta_research_prompt(prompt)
    assert "Klimazonen" in text
    assert "Handelsbeziehungen" in text
    assert "Kulturdenkmäler" in text

@pytest.mark.asyncio
async def test_meta_research_fallback_appends_deterministic_scandinavia_country_facts(orchestrator_instance, monkeypatch):
    monkeypatch.setattr(
        orchestrator_instance.agent_runtime,
        "run",
        AsyncMock(
            return_value={
                "text": "Routenuebersicht (aus Tool-Ergebnissen): 1. Stockholm -> Oslo: 525.9 km.",
                "trace_id": "phase1-trace",
                "trace_ids": ["phase1-trace"],
                "phase_outputs": ["[system.routing] Stockholm -> Oslo: 525.9 km"],
                "raw_response": {},
            }
        ),
    )
    monkeypatch.setattr(
        orchestrator_instance,
        "_collect_scandinavia_country_facts",
        AsyncMock(
            return_value=[
                "[system.country_info] Schweden: Hauptstadt Stockholm, Einwohner ca. 10.500.000, Region Europe.",
                "[system.country_info] Norwegen: Hauptstadt Oslo, Einwohner ca. 5.500.000, Region Europe.",
            ]
        ),
    )

    request = schemas.ChatRequest(
        prompt="Erstelle ein umfangreiches PDF ueber die skandinavischen Hauptstaedte.",
        chat_id=1,
        provider="ollama",
        model="gemma2:27b",
        api_key="",
    )

    result = await orchestrator_instance._run_meta_agent_research_fallback(
        user_text=request.prompt,
        request=request,
        api_key="",
        skip_final_synthesis=True,
    )

    text = str(result.text or "")
    assert "[system.routing]" in text
    assert "[system.country_info] Schweden" in text
    assert "[system.country_info] Norwegen" in text


@pytest.mark.asyncio
async def test_ollama_meta_agent_runs_two_phases_for_complex_document_request(orchestrator_instance, monkeypatch, caplog):
    chat = crud.create_chat(orchestrator_instance.db, title="Meta Agent Schweden")
    prompt = (
        "Erstelle mir ein kurzes PDF-Dokument über Schweden. "
        "Es soll die Hauptstadt, die Einwohnerzahl und die Entfernung von Berlin zur schwedischen Hauptstadt enthalten. "
        "Die Datei soll schweden.pdf heißen."
    )

    run_agent_factory_mock = AsyncMock(
        side_effect=[
            ExecutionResponse(
                text="Stockholm ist die Hauptstadt. Schweden hat ca. 10,5 Mio. Einwohner. Berlin-Stockholm: ca. 810 km.",
                raw_response={"text": "phase1"},
                tool_calls=[],
                is_agent_flow=True,
                agent_payload={
                    "trace_id": "meta-phase-1",
                    "required_skills": ["system.country_info", "system.routing"],
                },
            ),
            ExecutionResponse(
                text="PDF erstellt: schweden_kurzinfo.pdf",
                raw_response={"text": "phase2"},
                tool_calls=[],
                is_agent_flow=True,
                agent_payload={"trace_id": "meta-phase-2"},
            ),
        ]
    )
    run_tool_loop_mock = AsyncMock()

    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_agent_factory", run_agent_factory_mock)
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)
    monkeypatch.setattr(orchestrator_instance, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    caplog.set_level("INFO", logger="janus_backend")
    request = schemas.ChatRequest(
        prompt=prompt,
        chat_id=chat.id,
        provider="ollama",
        model="llama3.1:8b",
        api_key="",
    )

    response = await orchestrator_instance.handle_chat_request(request)

    response_text = str(response.get("text") or "")
    assert "Hier sind die recherchierten Fakten:" in response_text
    assert "Deine PDF 'schweden_kurzinfo.pdf' wurde erfolgreich erstellt." in response_text
    assert run_agent_factory_mock.await_count == 2
    phase1_kwargs = run_agent_factory_mock.await_args_list[0].kwargs
    phase2_kwargs = run_agent_factory_mock.await_args_list[1].kwargs
    assert phase1_kwargs.get("relevant_skill_ids") == ["system.country_info", "system.routing"]
    assert phase2_kwargs.get("relevant_skill_ids") == ["system.create_pdf"]
    assert "Fuehre KEINE Dokumenterstellung" in str(phase1_kwargs.get("user_text") or "")
    phase2_user_text = str(phase2_kwargs.get("user_text") or "")
    assert "JSON-ONLY-OVR" in phase2_user_text
    assert "SCHREIBE KEINEN TEXT! NUR DAS JSON!" in phase2_user_text
    assert "Fakten: Stockholm ist die Hauptstadt" in phase2_user_text
    assert "parameter.filename EXAKT 'schweden.pdf'" in phase2_user_text
    assert "[system.country_info]" not in phase2_user_text
    run_tool_loop_mock.assert_not_awaited()

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "META-AGENT PHASE 1 START (Recherche)" in log_text
    assert "META-AGENT PHASE 2 START (Produktion)" in log_text


@pytest.mark.asyncio
async def test_ollama_meta_agent_phase1_forces_research_when_planner_returns_empty_skills(
    orchestrator_instance,
    monkeypatch,
):
    chat = crud.create_chat(orchestrator_instance.db, title="Meta Agent Forced Research")
    prompt = (
        "Erstelle mir ein kurzes PDF-Dokument über Schweden. "
        "Es soll die Hauptstadt, die Einwohnerzahl und die Entfernung von Berlin zur schwedischen Hauptstadt enthalten."
    )

    run_agent_factory_mock = AsyncMock(
        side_effect=[
            ExecutionResponse(
                text="Keine Recherche ausgefuehrt.",
                raw_response={"text": "phase1-empty"},
                tool_calls=[],
                is_agent_flow=True,
                agent_payload={"trace_id": "meta-phase-1", "required_skills": []},
            ),
            ExecutionResponse(
                text="PDF erstellt: schweden_kurzinfo.pdf",
                raw_response={"text": "phase2"},
                tool_calls=[],
                is_agent_flow=True,
                agent_payload={"trace_id": "meta-phase-2"},
            ),
        ]
    )
    forced_runtime_mock = AsyncMock(
        return_value={
            "text": "Stockholm ist die Hauptstadt. Schweden hat ca. 10,5 Mio. Einwohner. Berlin-Stockholm: ca. 810 km.",
            "trace_id": "forced-research-trace",
            "trace_ids": ["forced-research-trace"],
            "raw_response": {"tool_calls": [{"function": {"name": "system.country_info"}}]},
        }
    )

    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_agent_factory", run_agent_factory_mock)
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", forced_runtime_mock)
    monkeypatch.setattr(orchestrator_instance, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    request = schemas.ChatRequest(
        prompt=prompt,
        chat_id=chat.id,
        provider="ollama",
        model="llama3.1:8b",
        api_key="",
    )

    response = await orchestrator_instance.handle_chat_request(request)

    response_text = str(response.get("text") or "")
    assert "Hier sind die recherchierten Fakten:" in response_text
    assert "Deine PDF 'schweden_kurzinfo.pdf' wurde erfolgreich erstellt." in response_text
    assert run_agent_factory_mock.await_count == 2
    forced_runtime_mock.assert_awaited_once()
    forced_spec = forced_runtime_mock.await_args.kwargs["spec"]
    assert forced_spec.required_skills == ["system.country_info", "system.routing"]

    phase2_kwargs = run_agent_factory_mock.await_args_list[1].kwargs
    phase2_user_text = str(phase2_kwargs.get("user_text") or "")
    assert "JSON-ONLY-OVR" in phase2_user_text
    assert "Fakten: Stockholm ist die Hauptstadt" in phase2_user_text


@pytest.mark.asyncio
async def test_ollama_meta_agent_fast_path_bypasses_planner_roundtrips_for_gemma(
    orchestrator_instance,
    monkeypatch,
):
    chat = crud.create_chat(orchestrator_instance.db, title="Meta Agent Fast Path")
    prompt = (
        "Erstelle mir ein kurzes PDF-Dokument über Schweden. "
        "Es soll die Hauptstadt, die Einwohnerzahl und die Entfernung von Berlin zur schwedischen Hauptstadt enthalten."
    )

    run_agent_factory_mock = AsyncMock()
    forced_runtime_mock = AsyncMock(
        side_effect=[
            {
                "text": "Stockholm ist die Hauptstadt. Schweden hat ca. 10,5 Mio. Einwohner. Berlin-Stockholm: ca. 810 km.",
                "trace_id": "forced-phase1-trace",
                "trace_ids": ["forced-phase1-trace"],
                "raw_response": {"tool_calls": [{"function": {"name": "system.country_info"}}]},
            },
            {
                "text": "PDF erstellt: Schweden_Facts.pdf\n\nGespeicherte PDF-Datei(en):\n- C:\\Users\\pruve\\Documents\\Schweden_Facts.pdf",
                "trace_id": "forced-phase2-trace",
                "trace_ids": ["forced-phase2-trace"],
                "raw_response": {"tool_calls": [{"function": {"name": "system.create_pdf"}}]},
            },
        ]
    )

    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_agent_factory", run_agent_factory_mock)
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", forced_runtime_mock)
    monkeypatch.setattr(orchestrator_instance, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    request = schemas.ChatRequest(
        prompt=prompt,
        chat_id=chat.id,
        provider="ollama",
        model="gemma2:27b",
        api_key="",
    )

    response = await orchestrator_instance.handle_chat_request(request)

    run_agent_factory_mock.assert_not_awaited()
    assert forced_runtime_mock.await_count == 2
    phase1_spec = forced_runtime_mock.await_args_list[0].kwargs["spec"]
    phase2_spec = forced_runtime_mock.await_args_list[1].kwargs["spec"]
    assert phase1_spec.required_skills == ["system.country_info", "system.routing"]
    assert phase2_spec.required_skills == ["system.create_pdf"]
    response_text = str(response.get("text") or "")
    assert "Hier sind die recherchierten Fakten:" in response_text
    assert "Deine PDF 'Schweden_Facts.pdf' wurde erstellt und liegt unter:" in response_text
    assert "C:\\Users\\pruve\\Documents\\Schweden_Facts.pdf" in response_text
    assert forced_runtime_mock.await_args_list[0].kwargs.get("skip_final_synthesis") is True
    assert forced_runtime_mock.await_args_list[1].kwargs.get("skip_final_synthesis") is True


def test_extract_requested_pdf_filename_infers_country_name_when_no_explicit_filename():
    filename = ChatOrchestrator._extract_requested_pdf_filename(
        "Erstelle bitte ein PDF über Dänemark mit Hauptstadt und Entfernung von Berlin."
    )

    assert filename == "daenemark.pdf"


@pytest.mark.asyncio
async def test_ollama_meta_agent_fast_path_does_not_claim_pdf_success_without_confirmed_path(
    orchestrator_instance,
    monkeypatch,
):
    chat = crud.create_chat(orchestrator_instance.db, title="Meta Agent Fast Path No PDF")
    prompt = (
        "Erstelle mir ein kurzes PDF-Dokument über Schweden. "
        "Es soll die Hauptstadt, die Einwohnerzahl und die Entfernung von Berlin zur schwedischen Hauptstadt enthalten."
    )

    run_agent_factory_mock = AsyncMock()
    forced_runtime_mock = AsyncMock(
        side_effect=[
            {
                "text": "[system.country_info] Stockholm ist die Hauptstadt von Schweden.\n[system.routing] Distanz Berlin-Stockholm: 1392,6 km.",
                "trace_id": "forced-phase1-trace",
                "trace_ids": ["forced-phase1-trace"],
                "raw_response": {"tool_calls": [{"function": {"name": "system.country_info"}}]},
            },
            {
                "text": "https://www.google.com/maps/dir/?api=1&origin=Berlin&destination=Stockholm&travelmode=driving.",
                "trace_id": "forced-phase2-trace",
                "trace_ids": ["forced-phase2-trace"],
                "raw_response": {"tool_calls": []},
            },
        ]
    )

    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_agent_factory", run_agent_factory_mock)
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", forced_runtime_mock)
    monkeypatch.setattr(orchestrator_instance, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    request = schemas.ChatRequest(
        prompt=prompt,
        chat_id=chat.id,
        provider="ollama",
        model="gemma2:27b",
        api_key="",
    )

    response = await orchestrator_instance.handle_chat_request(request)
    response_text = str(response.get("text") or "")

    run_agent_factory_mock.assert_not_awaited()
    assert "Hier sind die recherchierten Fakten:" in response_text
    assert "wurde erstellt und liegt unter" in response_text


@pytest.mark.asyncio
async def test_execution_engine_does_not_block_websearch_fallback_tool_calls(orchestrator_instance, monkeypatch):
    monkeypatch.setattr(
        "backend.services.orchestrator.execution_engine.llm_gateway.reason_and_respond",
        AsyncMock(
            return_value={
                "text": "tool phase",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "function": {
                            "name": "system.websearch",
                            "arguments": '{"query":"Einwohner Nimmerland"}',
                        },
                    }
                ],
            }
        ),
    )

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(return_value=[])

    result = await orchestrator_instance.execution_engine.run_tool_loop(
        orchestrator_context=OrchestratorContext(history=[{"role": "user", "content": "Wie viele Einwohner hat Nimmerland?"}]),
        tool_executor=tool_executor,
        gateway_kwargs={
            "provider": "gemini",
            "user_prompt": "Wie viele Einwohner hat Nimmerland?",
            "chat_history": [{"role": "user", "content": "Wie viele Einwohner hat Nimmerland?"}],
        },
        fallback_summary="fallback",
        current_limit=1,
        bypass_policy_this_turn=False,
        set_policy_pending=lambda *_args, **_kwargs: None,
        chat_id=1,
    )

    assert result.text
    called_tool_calls = tool_executor.execute_tool_calls.await_args.args[0]
    assert len(called_tool_calls) == 1
    assert called_tool_calls[0]["function"]["name"] == "system.websearch"


@pytest.mark.asyncio
async def test_execution_engine_atomic_loop_runs_multiple_rounds_for_schweden_pdf_prompt(
    orchestrator_instance,
    monkeypatch,
    caplog,
):
    prompt = (
        "Erstelle mir ein kurzes PDF-Dokument über Schweden. "
        "Es soll die Hauptstadt, die Einwohnerzahl und die Entfernung von Berlin zur schwedischen Hauptstadt enthalten."
    )
    planning_round = {"idx": 0}

    async def _fake_plan(**_kwargs):
        planning_round["idx"] += 1
        idx = planning_round["idx"]
        if idx == 1:
            skills = ["system.country_info", "system.routing", "system.create_pdf"]
        elif idx == 2:
            skills = ["system.routing", "system.create_pdf"]
        elif idx == 3:
            skills = ["system.create_pdf"]
        else:
            skills = []
        return AgentSpec(
            name="Schweden-Planer",
            goal="Schweden-Fakten sammeln und PDF erstellen",
            required_skills=skills,
            instructions="Arbeite sequentiell.",
            max_iterations=4,
        )

    async def _fake_run(**kwargs):
        current_skill = str(kwargs["spec"].required_skills[0])
        return {
            "text": f"{current_skill} done",
            "trace_id": f"trace-{current_skill}",
            "raw_response": {
                "tool_limit_reached": True,
                "tool_calls": [
                    {
                        "id": f"tc-{current_skill}",
                        "function": {"name": current_skill, "arguments": "{}"},
                    }
                ],
            },
        }

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=_fake_run))
    monkeypatch.setattr(
        orchestrator_instance.execution_engine,
        "_run_final_synthesis",
        AsyncMock(return_value="Synthese abgeschlossen."),
    )

    caplog.set_level("INFO", logger="janus_backend")
    result = await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=42,
        user_text=prompt,
        relevant_skill_ids=["system.country_info", "system.routing", "system.create_pdf"],
        provider="ollama",
        model="gemma2:27b",
        api_key="dummy",
    )

    assert result.is_agent_flow is True
    assert planning_round["idx"] >= 4
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "ATOMIC LOOP RUNDE 1: Planung CountryInfo" in log_text
    assert "ATOMIC LOOP RUNDE 2: Planung Routing" in log_text
    assert "ATOMIC LOOP RUNDE 3: Planung system.create_pdf" in log_text
    assert log_text.count("ATOMIC LOOP: [NEUER LOOP]") >= 2


@pytest.mark.asyncio
async def test_execution_engine_marks_skip_fact_extraction_on_country_not_found(orchestrator_instance, monkeypatch):
    monkeypatch.setattr(
        "backend.services.orchestrator.execution_engine.llm_gateway.reason_and_respond",
        AsyncMock(
            return_value={
                "text": "tool phase",
                "tool_calls": [
                    {
                        "id": "call-country",
                        "function": {
                            "name": "system.country_info",
                            "arguments": '{"country":"Nimmerland","language":"de"}',
                        },
                    }
                ],
            }
        ),
    )

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "name": "system.country_info",
                "content": '{"status":"error","error":{"code":"NOT_FOUND","message":"Keine Daten"}}',
            }
        ]
    )

    result = await orchestrator_instance.execution_engine.run_tool_loop(
        orchestrator_context=OrchestratorContext(history=[{"role": "user", "content": "Einwohner von Nimmerland?"}]),
        tool_executor=tool_executor,
        gateway_kwargs={
            "provider": "gemini",
            "user_prompt": "Einwohner von Nimmerland?",
            "chat_history": [{"role": "user", "content": "Einwohner von Nimmerland?"}],
        },
        fallback_summary="fallback",
        current_limit=1,
        bypass_policy_this_turn=False,
        set_policy_pending=lambda *_args, **_kwargs: None,
        chat_id=1,
    )

    assert isinstance(result.raw_response, dict)
    assert result.raw_response.get("skip_fact_extraction") is True


@pytest.mark.asyncio
async def test_agent_factory_atomic_loop_japan_rounds_and_logs(orchestrator_instance, monkeypatch, caplog):
    planning_round = {"idx": 0}

    async def _fake_plan(**kwargs):
        planning_round["idx"] += 1
        if planning_round["idx"] == 1:
            skills = ["system.country_info", "system.routing"]
        else:
            skills = ["system.routing", "knowledge.query"]
        return AgentSpec(
            name="Reise-Planer",
            goal="Japan Infos und Route",
            required_skills=skills,
            instructions="Plane sequentiell.",
            max_iterations=3,
        )

    executed = []

    async def _fake_run(**kwargs):
        step_skill = kwargs["spec"].required_skills[0]
        executed.append(step_skill)
        return {
            "text": f"TASK_COMPLETE {step_skill}",
            "trace_id": f"trace-{len(executed)}",
            "raw_response": {"tool_limit_reached": True},
        }

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=_fake_run))
    monkeypatch.setattr(
        "backend.services.orchestrator.execution_engine.llm_gateway.reason_and_respond",
        AsyncMock(return_value={"type": "text", "text": "Saubere Synthese", "usage": {}, "cost": {}}),
    )

    caplog.set_level("INFO", logger="janus_backend")
    result = await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=77,
        user_text="Ich plane eine Reise nach Japan. Einwohner/Währung? Distanz Tokio-Kyoto?",
        relevant_skill_ids=["system.country_info", "system.routing"],
        provider="gemini",
        model="gemini-3-flash-preview",
        api_key="secret",
    )

    assert result.is_agent_flow is True
    assert executed == ["system.country_info", "system.routing"]
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "ATOMIC LOOP RUNDE 1: Planung CountryInfo" in log_text
    assert "ATOMIC LOOP RUNDE 1: Executing CountryInfo" in log_text
    assert "ATOMIC LOOP RUNDE 1: Task Complete CountryInfo" in log_text
    assert "ATOMIC LOOP: [NEUER LOOP]" in log_text
    assert "ATOMIC LOOP RUNDE 2: Planung Routing" in log_text
    assert "ATOMIC LOOP RUNDE 2: Executing Routing" in log_text
    assert "ATOMIC LOOP RUNDE 2: Task Complete Routing" in log_text
    assert "ATOMIC LOOP: [EXIT] Grund=ALL_INITIAL_SKILLS_COMPLETED" in log_text


@pytest.mark.asyncio
async def test_agent_factory_exits_immediately_on_text_only_step(orchestrator_instance, monkeypatch, caplog):
    async def _fake_plan(**_kwargs):
        return AgentSpec(
            name="Text-Agent",
            goal="Antwort ohne Tool",
            required_skills=["system.routing"],
            instructions="Wenn schon klar, antworte direkt.",
            max_iterations=2,
        )

    async def _fake_run(**_kwargs):
        return {
            "text": "Hier ist die finale Antwort ohne weiteren Tool-Call.",
            "trace_id": "trace-text-only",
            "raw_response": {
                "tool_calls": [],
            },
        }

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=_fake_run))

    caplog.set_level("INFO", logger="janus_backend")
    result = await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=55,
        user_text="Gib mir direkt die Antwort.",
        relevant_skill_ids=["system.routing"],
        provider="openai",
        model="gpt-5.4-nano",
        api_key="secret",
    )

    assert result.is_agent_flow is True
    assert result.text == "Hier ist die finale Antwort ohne weiteren Tool-Call."
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "ATOMIC LOOP: [EXIT] Grund=TEXT_ONLY_STEP" in log_text


@pytest.mark.asyncio
async def test_agent_factory_treats_executed_tool_marker_as_real_tool_step(orchestrator_instance, monkeypatch, caplog):
    planning_round = {"idx": 0}

    async def _fake_plan(**_kwargs):
        planning_round["idx"] += 1
        if planning_round["idx"] == 1:
            skills = ["system.local_business"]
        else:
            skills = []
        return AgentSpec(
            name="Local-Business-Agent",
            goal="Restaurants finden",
            required_skills=skills,
            instructions="Nutze den Skill genau einmal.",
            max_iterations=2,
        )

    async def _fake_run(**_kwargs):
        return {
            "text": "**Ristorante Roma**\nAdresse: Teststraße 1",
            "trace_id": "trace-local-business",
            "raw_response": {
                "text": "**Ristorante Roma**\nAdresse: Teststraße 1",
                "executed_tool_call": True,
            },
        }

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=_fake_run))
    monkeypatch.setattr(
        orchestrator_instance.execution_engine,
        "_run_atomic_clean_synthesis",
        AsyncMock(return_value="[system.local_business] **Ristorante Roma**\nAdresse: Teststraße 1"),
    )

    caplog.set_level("INFO", logger="janus_backend")
    result = await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=56,
        user_text="Finde mir ein italienisches Restaurant in Berlin Prenzlauer Berg.",
        relevant_skill_ids=["system.local_business"],
        provider="ollama",
        model="gemma2:27b@test",
        api_key="secret",
    )

    assert result.is_agent_flow is True
    assert "Ristorante Roma" in result.text
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "ATOMIC LOOP RUNDE 1: Executing system.local_business" in log_text
    assert "ATOMIC LOOP: [EXIT] Grund=TEXT_ONLY_STEP" not in log_text


@pytest.mark.asyncio
async def test_agent_factory_returns_single_local_business_step_output_without_clean_synthesis(
    orchestrator_instance,
    monkeypatch,
    caplog,
):
    planning_round = {"idx": 0}

    async def _fake_plan(**_kwargs):
        planning_round["idx"] += 1
        if planning_round["idx"] == 1:
            skills = ["system.local_business"]
        else:
            skills = []
        return AgentSpec(
            name="Local-Business-Agent",
            goal="Restaurants finden",
            required_skills=skills,
            instructions="Nutze den Skill genau einmal.",
            max_iterations=2,
        )

    async def _fake_run(**_kwargs):
        return {
            "text": "**Ristorante Roma**\nAdresse: Teststraße 1",
            "trace_id": "trace-local-business",
            "raw_response": {
                "text": "**Ristorante Roma**\nAdresse: Teststraße 1",
                "executed_tool_call": True,
            },
        }

    clean_synthesis = AsyncMock(return_value="SHOULD_NOT_BE_USED")

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=_fake_run))
    monkeypatch.setattr(
        orchestrator_instance.execution_engine,
        "_run_atomic_clean_synthesis",
        clean_synthesis,
    )

    caplog.set_level("INFO", logger="janus_backend")
    result = await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=56,
        user_text="Finde mir ein italienisches Restaurant in Berlin Prenzlauer Berg.",
        relevant_skill_ids=["system.local_business"],
        provider="ollama",
        model="gemma2:27b@test",
        api_key="secret",
    )

    assert result.is_agent_flow is True
    assert result.text == "**Ristorante Roma**\nAdresse: Teststraße 1"
    clean_synthesis.assert_not_awaited()
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "ATOMIC LOOP: [EXIT] Grund=NO_TOOLS_PLANNED_AFTER_STEP" in log_text


@pytest.mark.asyncio
async def test_agent_factory_marks_fatal_skill_error_final_and_does_not_retry(
    orchestrator_instance,
    monkeypatch,
    caplog,
):
    async def _fake_plan(**_kwargs):
        return AgentSpec(
            name="PDF-Agent",
            goal="Datei pruefen",
            required_skills=["filesystem.read_file"],
            instructions="Nutze den Skill genau einmal.",
            max_iterations=2,
        )

    run_specs = []

    async def _fake_run(**kwargs):
        run_specs.append(list(kwargs["spec"].required_skills))
        return {
            "text": "Fehlgeschlagen",
            "trace_id": "trace-fail",
            "raw_response": {
                "tool_errors": [
                    {
                        "error": {
                            "code": "READ_BINARY_FILE",
                            "message": "Datei ist binaer und kann nicht als Text gelesen werden.",
                        }
                    }
                ]
            },
        }

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=_fake_run))

    caplog.set_level("INFO", logger="janus_backend")
    result = await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=44,
        user_text="Lies die erstellte PDF.",
        relevant_skill_ids=["filesystem.read_file"],
        provider="openai",
        model="gpt-5.4-nano",
        api_key="secret",
    )

    assert run_specs == [["filesystem.read_file"]]
    assert result.is_agent_flow is False
    assert orchestrator_instance.agent_planner.plan.await_count >= 2

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "Fataler Fehler" in log_text
    assert "final gesperrt" in log_text


@pytest.mark.asyncio
async def test_agent_factory_clean_synthesis_payload_excludes_agent_meta_prompts(orchestrator_instance, monkeypatch):
    planning_round = {"idx": 0}

    async def _fake_plan(**kwargs):
        planning_round["idx"] += 1
        skills = ["system.country_info"] if planning_round["idx"] == 1 else []
        return AgentSpec(
            name="Plan",
            goal="Nur Fakten",
            required_skills=skills,
            instructions="Nutze nur Tool-Fakten.",
            max_iterations=2,
        )

    async def _fake_run(**kwargs):
        return {
            "text": "Bevölkerung: 123",
            "trace_id": "trace-1",
            "raw_response": {"tool_limit_reached": True},
        }

    captured = {}

    async def _fake_synthesis(**kwargs):
        captured["chat_history"] = list(kwargs.get("chat_history") or [])
        return {"type": "text", "text": "Japan hat 123 Einwohner.", "usage": {}, "cost": {}}

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=_fake_run))
    monkeypatch.setattr(
        "backend.services.orchestrator.execution_engine.llm_gateway.reason_and_respond",
        AsyncMock(side_effect=_fake_synthesis),
    )

    result = await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=3,
        user_text="Wie viele Einwohner hat Japan?",
        relevant_skill_ids=["system.country_info"],
        provider="openai",
        model="gpt-5.4-nano",
        api_key="secret",
    )

    assert result.is_agent_flow is True
    history = captured["chat_history"]
    assert len(history) == 2
    assert history[0]["role"] == "system"
    assert "FAKTEN:" in history[0]["content"]
    assert "Du bist der Spezial-Agent" not in history[0]["content"]
    assert "Task-Queue" not in history[0]["content"]
    assert "TASK_COMPLETE" not in history[0]["content"]
    assert history[1] == {"role": "user", "content": "Wie viele Einwohner hat Japan?"}


@pytest.mark.asyncio
async def test_agent_factory_pdf_round_exits_to_final_synthesis_when_next_plan_is_empty(
    orchestrator_instance,
    monkeypatch,
    caplog,
):
    planning_round = {"idx": 0}
    executed = []

    async def _fake_plan(**_kwargs):
        planning_round["idx"] += 1
        skills = ["create_pdf", "filesystem.read_file"] if planning_round["idx"] == 1 else []
        return AgentSpec(
            name="PDF-Agent",
            goal="Erstelle Dokument",
            required_skills=skills,
            instructions="Erst Tool, dann Abschlussantwort.",
            max_iterations=3,
        )

    async def _fake_run(**_kwargs):
        executed.append(_kwargs["spec"].required_skills[0])
        return {
            "text": "PDF '/workspace/reiseplan.pdf' erfolgreich erstellt.",
            "trace_id": "trace-pdf-1",
            "raw_response": {"tool_limit_reached": True},
        }

    monkeypatch.setattr(orchestrator_instance.agent_planner, "plan", AsyncMock(side_effect=_fake_plan))
    monkeypatch.setattr(orchestrator_instance.agent_runtime, "run", AsyncMock(side_effect=_fake_run))
    monkeypatch.setattr(
        "backend.services.orchestrator.execution_engine.llm_gateway.reason_and_respond",
        AsyncMock(
            return_value={
                "type": "text",
                "text": "Die PDF wurde erfolgreich erstellt und im Workspace gespeichert.",
                "usage": {},
                "cost": {},
            }
        ),
    )

    caplog.set_level("INFO", logger="janus_backend")
    result = await orchestrator_instance.execution_engine.run_agent_factory(
        enabled=True,
        chat_id=12,
        user_text="Erstelle eine PDF mit meinem Reiseplan.",
        relevant_skill_ids=["create_pdf"],
        provider="openai",
        model="gpt-5.4-nano",
        api_key="secret",
    )

    assert result.is_agent_flow is True
    assert "PDF wurde erfolgreich erstellt" in result.text
    assert executed == ["create_pdf"]
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "ATOMIC LOOP: [NEUER LOOP]" in log_text
    assert "ATOMIC LOOP: [EXIT] Keine weiteren Skills geplant. Starte finale Synthese." in log_text
    assert "Planung filesystem.read_file" not in log_text
    assert "Planung knowledge.open_document" not in log_text
    assert "Planung knowledge.edit_pdf" not in log_text


def test_trigger_fact_extraction_respects_skip_flag(orchestrator_instance):
    with patch("backend.services.chat_orchestrator.asyncio.create_task") as mock_create_task:
        orchestrator_instance._trigger_fact_extraction(
            chat_id=1,
            user_text="Wie viele Einwohner hat Nimmerland?",
            final_text="Keine Daten gefunden.",
            api_key="dummy",
            provider="gemini",
            skip_fact_extraction=True,
        )

    mock_create_task.assert_not_called()


def test_trigger_fact_extraction_skips_invalid_assistant_output(orchestrator_instance):
    with patch("backend.services.chat_orchestrator.asyncio.create_task") as mock_create_task:
        orchestrator_instance._trigger_fact_extraction(
            chat_id=2,
            user_text="Wie viele Einwohner hat Nimmerland?",
            final_text="Keine Daten gefunden.",
            api_key="dummy",
            provider="gemini",
        )

    mock_create_task.assert_not_called()


@pytest.mark.asyncio
async def test_ollama_vague_knowledge_prompt_drops_tools(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Ollama Vague Query V2")

    run_tool_loop_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="Die Sonne ist ein Stern.",
            raw_response={"text": "Die Sonne ist ein Stern."},
            tool_calls=[],
            is_agent_flow=False,
        )
    )
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)

    request = schemas.ChatRequest(
        prompt="Was weißt du über die Sonne?",
        chat_id=chat.id,
        provider="ollama",
        model="llama3.1:8b",
        api_key="",
    )

    await orchestrator_instance.handle_chat_request(request)

    gateway_kwargs = run_tool_loop_mock.await_args.kwargs.get("gateway_kwargs") or {}
    assert gateway_kwargs.get("tools_override") == []
