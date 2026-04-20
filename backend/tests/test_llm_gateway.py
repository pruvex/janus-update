from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.data import schemas
from backend.services import llm_gateway
from backend.llm_providers.openai.gateway import OpenAIGateway


def test_build_story_character_consistency_rules_for_animals_blocks_human_children():
    rules = llm_gateway._build_story_character_consistency_rules("ein Häschen und ein Igel")

    assert any("same animal characters" in rule for rule in rules)
    assert any("Do not turn them into human children" in rule for rule in rules)


def test_openai_fallback_generate_image_prompt_keeps_rabbit_and_hedgehog_as_animals():
    fallback = OpenAIGateway.build_forced_fallback_tool_call(
        forced_tool={
            "skill_id": "system.generate_image",
            "provider_tool_name": "system_generate_image",
            "image_index": 2,
            "total_image_count": 3,
        },
        user_prompt="Schreibe eine kurze Geschichte für Kinder über ein Häschen und einen Igel. Mach dazu 3 Illustrationen im selben Stil.",
        chat_history=[],
    )

    assert fallback is not None
    args = llm_gateway.json.loads(fallback["function"]["arguments"])
    assert "same animal characters" in args["prompt"]
    assert "Do not turn them into human children" in args["prompt"]


def test_build_final_websearch_synthesis_instruction_for_game_release_lists_requires_genre_premise_and_link():
    instruction = llm_gateway._build_final_websearch_synthesis_instruction(
        "Welche Switch 2 Spiele erscheinen nächsten Monat in Deutschland?"
    )

    assert "Erstelle eine lückenlose Liste ALLER verifizierten, PASSENDEN Titel" in instruction
    assert "Nenne pro Eintrag: Titel, genaues Datum/Fenster und Plattform" in instruction
    assert "anklickbaren Markdown-Link" in instruction
    assert "Never fabricate citations, URLs, or data." in instruction
    assert "Keep lists flat (single level)" in instruction


def test_build_final_websearch_synthesis_instruction_for_combined_release_query_preserves_extra_requirements():
    instruction = llm_gateway._build_final_websearch_synthesis_instruction(
        "Welche Switch 2 Spiele erscheinen nächsten Monat, was ist der Preis und was sind die Top 3 Titel in Deutschland?"
    )

    assert "vollständigen Release-Liste" in instruction
    assert "Gib zuerst einen kurzen Überblick mit den Zusatzinfos" in instruction
    assert "Top 3" in instruction
    assert "Preis/UVP" in instruction
    assert "Lass die vollständige Release-Liste trotz Zusatzinfos niemals weg" in instruction


def test_build_final_websearch_synthesis_instruction_for_realistic_live_prompt_preserves_all_subquestions():
    instruction = llm_gateway._build_final_websearch_synthesis_instruction(
        "wann wurde die switch 2 in deutschland veröffentloicht? was sit die uvp und was die aktuellen strassenpreise? welches sind die 3 beliebtesten spiele auf der switch 2? mach mit eine liste mit den neuerscheinungen in deutschland für die switch 2 im nächsten monat"
    )

    assert "Straßenpreis" in instruction
    assert "beliebtesten Spielen" in instruction
    assert "Veröffentlichung oder dem Launch der Konsole" in instruction
    assert "vollständige Release-Liste" in instruction


def test_build_final_websearch_synthesis_instruction_for_gemini_uses_xml_context_blocks():
    instruction = llm_gateway._build_final_websearch_synthesis_instruction(
        "Welche Switch 2 Spiele erscheinen nächsten Monat in Deutschland?",
        provider="gemini",
        model_id="gemini-3-pro-preview",
        research_context="## Rechercheblock 1\nMario Kart World erscheint am 12. April 2026.",
    )

    assert instruction.startswith("<role>")
    assert "<context>" in instruction
    assert "Dies sind die Suchergebnisse der Websearch:" in instruction
    assert "Mario Kart World erscheint am 12. April 2026." in instruction
    assert "<constraints>" in instruction
    assert "<output_format>" in instruction
    assert "<task>" in instruction


def test_build_openai_research_synthesis_messages_preserves_specialized_websearch_instruction():
    messages = [
        {"role": "system", "content": llm_gateway._build_final_websearch_synthesis_instruction("Welche Switch 2 Spiele erscheinen nächsten Monat in Deutschland?")},
        {"role": "user", "content": "Welche Switch 2 Spiele erscheinen nächsten Monat in Deutschland?"},
        {"role": "tool", "content": '{"status":"ok","data":{"facts":["A erscheint im April 2026"],"sources":[{"url":"https://example.com/a","title":"A Release"}]}}'},
    ]

    compact_messages = OpenAIGateway.build_research_synthesis_messages(messages)

    assert compact_messages
    assert compact_messages[0]["role"] == "system"
    assert "anklickbaren Markdown-Link" in compact_messages[0]["content"]
    assert "pro Spiel exakt dieses Format" in compact_messages[0]["content"]


def test_ensure_release_list_links_in_text_response_appends_matching_source_links():
    response = {
        "type": "text",
        "text": "- **Mario Kart World** — 12. April 2026 — Switch 2\n- **Donkey Kong Bananza** — April 2026 — Switch 2"
    }
    tool_results = [
        {
            "role": "tool",
            "name": "system.websearch",
            "content": llm_gateway.json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "sources": [
                            {
                                "url": "https://example.com/mario-kart-world",
                                "title": "Mario Kart World erscheint im April 2026",
                                "snippet": "Nintendo bestätigt Mario Kart World für Switch 2 im April 2026.",
                            },
                            {
                                "url": "https://example.com/donkey-kong-bananza",
                                "title": "Donkey Kong Bananza Release-Fenster",
                                "snippet": "Donkey Kong Bananza soll im April 2026 für Switch 2 erscheinen.",
                            },
                        ],
                        "urls": [
                            "https://example.com/mario-kart-world",
                            "https://example.com/donkey-kong-bananza",
                        ],
                    },
                },
                ensure_ascii=False,
            ),
        }
    ]

    updated = OpenAIGateway.ensure_release_list_links_in_text_response(
        response,
        user_prompt="Welche Switch 2 Spiele erscheinen nächsten Monat in Deutschland?",
        tool_results=tool_results,
    )

    assert "[Mehr erfahren](https://example.com/mario-kart-world)" in updated["text"]
    assert "[Mehr erfahren](https://example.com/donkey-kong-bananza)" in updated["text"]


def test_build_gemini_websearch_context_block_includes_text_facts_and_sources():
    tool_results = [
        {
            "role": "tool",
            "name": "system.websearch",
            "content": llm_gateway.json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "text": "Mario Kart World erscheint im April 2026. Die UVP liegt bei 79,99 Euro.",
                        "sources": [
                            {
                                "url": "https://example.com/mario-kart-world",
                                "title": "Mario Kart World Release",
                                "snippet": "Mario Kart World erscheint im April 2026 für Switch 2.",
                            },
                            {
                                "url": "https://example.com/preis",
                                "title": "Switch 2 Preisübersicht",
                                "snippet": "Die UVP liegt bei 79,99 Euro.",
                            },
                        ],
                    },
                },
                ensure_ascii=False,
            ),
        }
    ]

    context = llm_gateway._build_gemini_websearch_context_block(tool_results)

    assert "## Rechercheblock 1" in context
    assert "### Recherchetext" in context
    assert "### Verifizierte Fakten" in context
    assert "### Verfügbare Quellen-URLs" in context
    assert "https://example.com/mario-kart-world" in context
    assert "Mario Kart World erscheint im April 2026 für Switch 2." in context
    assert "79,99 Euro" in context


def test_ensure_combined_release_response_structure_adds_overview_and_preserves_release_list():
    response = {
        "type": "text",
        "text": (
            "Nintendo hat neue Details geteilt.\n"
            "- **Mario Kart World** — 12. April 2026 — Switch 2 — [Mehr erfahren](https://example.com/mario-kart-world)\n"
            "- **Donkey Kong Bananza** — April 2026 — Switch 2 — [Mehr erfahren](https://example.com/donkey-kong-bananza)"
        ),
    }
    tool_results = [
        {
            "role": "tool",
            "name": "system.websearch",
            "content": llm_gateway.json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "facts": [
                            "Die Nintendo Switch 2 erscheint am 5. Juni 2026 in Deutschland.",
                            "Die UVP der Nintendo Switch 2 liegt bei 469,99 Euro.",
                            "Im Handel werden Straßenpreise ab 449 Euro beobachtet.",
                            "Mario Kart World zählt zu den beliebtesten Switch-2-Highlights laut Vorbestellübersichten.",
                        ],
                        "sources": [
                            {
                                "url": "https://example.com/mario-kart-world",
                                "title": "Mario Kart World erscheint im April 2026",
                                "snippet": "Mario Kart World erscheint am 12. April 2026 für Switch 2.",
                            },
                            {
                                "url": "https://example.com/donkey-kong-bananza",
                                "title": "Donkey Kong Bananza Release-Fenster",
                                "snippet": "Donkey Kong Bananza soll im April 2026 für Switch 2 erscheinen.",
                            },
                        ],
                    },
                },
                ensure_ascii=False,
            ),
        }
    ]

    updated = OpenAIGateway.ensure_combined_release_response_structure(
        response,
        user_prompt="Wann wurde die Switch 2 in Deutschland veröffentlicht, was ist die UVP, was sind aktuelle Straßenpreise und welche Spiele erscheinen nächsten Monat? Was sind die Top 3 Highlights?",
        tool_results=tool_results,
    )

    assert "## Überblick" in updated["text"]
    assert "## Vollständige Release-Liste" in updated["text"]
    assert "**Konsolen-Launch:** Die Nintendo Switch 2 erscheint am 5. Juni 2026 in Deutschland." in updated["text"]
    assert "**Preis/UVP:** Die UVP der Nintendo Switch 2 liegt bei 469,99 Euro." in updated["text"]
    assert "**Straßenpreis:** Im Handel werden Straßenpreise ab 449 Euro beobachtet." in updated["text"]
    assert "**Top 1:** Mario Kart World zählt zu den beliebtesten Switch-2-Highlights laut Vorbestellübersichten." in updated["text"]
    assert "Mario Kart World" in updated["text"]
    assert "Donkey Kong Bananza" in updated["text"]


def test_normalize_websearch_tool_results_for_synthesis_keeps_raw_text_and_more_sources():
    long_text = " ".join([f"Fakt {idx}: Detail zur Switch 2." for idx in range(1, 120)])
    result = {
        "role": "tool",
        "name": "system.websearch",
        "content": llm_gateway.json.dumps(
            {
                "status": "ok",
                "data": {
                    "text": long_text,
                    "urls": [f"https://example.com/{idx}" for idx in range(1, 9)],
                    "sources": [
                        {
                            "url": f"https://example.com/{idx}",
                            "title": f"Quelle {idx}",
                            "snippet": f"Snippet {idx}",
                        }
                        for idx in range(1, 9)
                    ],
                },
            },
            ensure_ascii=False,
        ),
    }

    normalized = llm_gateway._normalize_websearch_tool_results_for_synthesis([result])
    payload = llm_gateway.json.loads(normalized[0]["content"])
    data = payload["data"]

    assert "text" in data
    assert len(data["text"]) > 1000
    assert len(data["urls"]) == 8
    assert len(data["sources"]) == 8
    assert len(data["facts"]) >= 10


@pytest.mark.asyncio
async def test_reason_and_respond_returns_text_payload_without_tools():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Hallo"}]
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(
        return_value={"type": "text", "text": "Dummy", "usage": {}, "cost": {}}
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ):
        result = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Hallo",
            chat_id=1,
            tool_executor=MagicMock(),
            disable_tools=True,
        )

    assert result["text"] == "Dummy"
    assert result["type"] == "text"
    mock_provider.generate_response.assert_awaited()


@pytest.mark.asyncio
async def test_reason_and_respond_does_not_forward_requested_skills_to_provider():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Hallo"}]
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(
        return_value={"type": "text", "text": "Dummy", "usage": {}, "cost": {}}
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ):
        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Hallo",
            chat_id=1,
            tool_executor=MagicMock(),
            disable_tools=True,
            requested_skills=["system.generate_image"],
        )

    forwarded_kwargs = mock_provider.generate_response.await_args.kwargs
    assert "requested_skills" not in forwarded_kwargs


@pytest.mark.asyncio
async def test_reason_and_respond_forces_generate_image_on_image_pdf_chain_round_one():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Mach Bild+PDF"}]
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(
        return_value={"type": "text", "text": "Dummy", "usage": {}, "cost": {}}
    )
    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(return_value=[])

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.generate_image", "description": "", "parameters": {"type": "object", "properties": {}}},
            {"name": "system.create_pdf", "description": "", "parameters": {"type": "object", "properties": {}}},
        ],
    ):
        await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Erstell Bild und PDF",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.generate_image"],
        )

    initial_call_kwargs = mock_provider.generate_response.await_args_list[0].kwargs
    forwarded_kwargs = initial_call_kwargs
    assert forwarded_kwargs.get("force_tool_name") == "system_generate_image"
    assert forwarded_kwargs.get("tool_choice") == {"type": "function", "function": {"name": "system_generate_image"}}


@pytest.mark.asyncio
async def test_reason_and_respond_retries_forced_tool_when_openai_returns_text_first():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Mach Bild+PDF"}]
    mock_provider = MagicMock()
    queued_responses = [
        {"type": "text", "text": "Ich mache das gleich.", "usage": {"output_tokens": 2500}, "cost": {}},
        {
            "type": "tool_code",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "system_generate_image",
                        "arguments": '{"prompt":"Ein kleiner Affe"}',
                    },
                }
            ],
            "usage": {},
            "cost": {},
            "raw_assistant_response": {"role": "assistant", "content": None},
        },
        {
            "type": "text",
            "text": "Die Tool-Ausführung wurde erfolgreich abgeschlossen und die Antwort ist stabil.",
            "usage": {},
            "cost": {},
        },
    ]

    def _next_response(*_args, **_kwargs):
        if queued_responses:
            return queued_responses.pop(0)
        return {"type": "text", "text": "Finale Antwort.", "usage": {}, "cost": {}}

    mock_provider.generate_response = AsyncMock(side_effect=_next_response)
    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "name": "system.generate_image",
                "content": '{"status":"ok","data":{"markdown_image":"![Affe](/user_images/affe.png)"}}',
            }
        ]
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.generate_image", "description": "", "parameters": {"type": "object", "properties": {}}},
            {"name": "system.create_pdf", "description": "", "parameters": {"type": "object", "properties": {}}},
        ],
    ):
        result = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Erstell Bild und PDF",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.generate_image"],
        )

    assert mock_provider.generate_response.await_count >= 3
    retry_call_kwargs = mock_provider.generate_response.await_args_list[1].kwargs
    assert retry_call_kwargs.get("force_tool_name") == "system_generate_image"
    assert retry_call_kwargs.get("tool_choice") == {"type": "function", "function": {"name": "system_generate_image"}}
    assert result.get("type") == "text"


@pytest.mark.asyncio
async def test_reason_and_respond_keeps_full_second_call_history_for_gemini_websearch():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Welche Switch 2 Spiele erscheinen nächsten Monat?"}]
    captured_second_call = {}
    call_counter = {"count": 0}
    mock_provider = MagicMock()

    async def _generate_response(*args, **kwargs):
        messages = kwargs.get("messages") or []
        call_counter["count"] += 1
        if call_counter["count"] == 1:
            return {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call_ws_1",
                        "type": "function",
                        "function": {
                            "name": "system.websearch",
                            "arguments": '{"query":"Nintendo Switch 2 kommende Spiele Deutschland nächsten Monat Erscheinungsdatum"}',
                        },
                    }
                ],
                "usage": {},
                "cost": {},
                "raw_assistant_response": {"role": "assistant", "content": None},
            }
        captured_second_call["messages"] = messages
        return {"type": "text", "text": "Finale Antwort", "usage": {}, "cost": {}}

    mock_provider.generate_response = AsyncMock(side_effect=_generate_response)
    mock_provider.prepare_history_for_second_call = MagicMock(
        side_effect=lambda *, chat_history, raw_assistant_response, tool_results=None: list(chat_history) + [raw_assistant_response] + list(tool_results or [])
    )
    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "tool_call_id": "call_ws_1",
                "name": "system.websearch",
                "content": '{"status":"ok","data":{"text":"Bestätigte Releases mit Quellen","urls":["https://example.com/release-list"],"sources":[{"url":"https://example.com/release-list","title":"Release List","snippet":"Mario Kart World im April"}]}}',
            }
        ]
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.websearch", "description": "", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
        ],
    ):
        result = await llm_gateway.reason_and_respond(
            provider="gemini",
            model="gemini-3-pro-preview",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Welche Switch 2 Spiele erscheinen nächsten Monat?",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.websearch"],
            max_tool_rounds=2,
        )

    second_call_messages = captured_second_call["messages"]
    assert second_call_messages[0]["role"] == "system"
    assert len(second_call_messages) == 2
    assert second_call_messages[1]["role"] == "user"
    assert second_call_messages[1]["content"].startswith("<role>")
    assert "<context>" in second_call_messages[1]["content"]
    assert "Dies sind die Suchergebnisse der Websearch:" in second_call_messages[1]["content"]
    assert "Mario Kart World im April" in second_call_messages[1]["content"]
    assert "Release List — https://example.com/release-list" in second_call_messages[1]["content"]
    assert result["text"] == "Finale Antwort"


@pytest.mark.asyncio
async def test_reason_and_respond_uses_deterministic_fallback_when_openai_returns_text_twice():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Mach Bild+PDF"}]
    mock_provider = MagicMock()
    queued_responses = [
        {"type": "text", "text": "", "usage": {"output_tokens": 2500}, "cost": {}},
        {"type": "text", "text": "", "usage": {"output_tokens": 2500}, "cost": {}},
        {
            "type": "text",
            "text": "Die Tool-Ausführung wurde erfolgreich abgeschlossen und die Antwort ist stabil.",
            "usage": {},
            "cost": {},
        },
    ]

    def _next_response(*_args, **_kwargs):
        if queued_responses:
            return queued_responses.pop(0)
        return {"type": "text", "text": "Finale Antwort.", "usage": {}, "cost": {}}

    mock_provider.generate_response = AsyncMock(side_effect=_next_response)
    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "tool_call_id": "fallback_forced_generate_image",
                "name": "system.generate_image",
                "content": '{"status":"ok","data":{"markdown_image":"![Affe](/user_images/affe.png)"}}',
            }
        ]
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.generate_image", "description": "", "parameters": {"type": "object", "properties": {}}},
            {"name": "system.create_pdf", "description": "", "parameters": {"type": "object", "properties": {}}},
        ],
    ):
        result = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Erstell Bild und PDF",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.generate_image"],
        )

    assert mock_provider.generate_response.await_count >= 3
    execute_calls = mock_executor.execute_tool_calls.await_args_list
    assert execute_calls
    synthesized_tool_call = execute_calls[0].args[0][0]
    assert synthesized_tool_call["function"]["name"] == "system.generate_image"
    assert result.get("type") == "text"


@pytest.mark.asyncio
async def test_reason_and_respond_uses_deterministic_websearch_fallback_when_openai_returns_text_twice():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Wie hoch ist der Goldpreis heute?"}]
    mock_provider = MagicMock()
    queued_responses = [
        {"type": "text", "text": "Ich suche kurz.", "usage": {"output_tokens": 200}, "cost": {}},
        {"type": "text", "text": "Noch keine Tool-Antwort.", "usage": {"output_tokens": 180}, "cost": {}},
        {
            "type": "text",
            "text": "Der Goldpreis liegt heute bei etwa 4.236,05 €.",
            "usage": {},
            "cost": {},
        },
    ]

    def _next_response(*_args, **_kwargs):
        if queued_responses:
            return queued_responses.pop(0)
        return {"type": "text", "text": "Finale Antwort.", "usage": {}, "cost": {}}

    mock_provider.generate_response = AsyncMock(side_effect=_next_response)
    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "tool_call_id": "fallback_forced_websearch",
                "name": "system.websearch",
                "content": '{"status":"ok","data":{"text":"Goldpreis heute 4.236,05 €","urls":["https://www.goldpreis.de/"]}}',
            }
        ]
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.websearch", "description": "", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
        ],
    ):
        result = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Wie hoch ist der Goldpreis heute?",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.websearch"],
            max_tool_rounds=3,
        )

    execute_calls = mock_executor.execute_tool_calls.await_args_list
    assert execute_calls
    synthesized_tool_call = execute_calls[0].args[0][0]
    assert synthesized_tool_call["function"]["name"] == "system.websearch"
    args = llm_gateway.json.loads(synthesized_tool_call["function"]["arguments"])
    assert args["query"] == "Wie hoch ist der Goldpreis heute? in Euro"
    assert result.get("type") == "text"


@pytest.mark.asyncio
async def test_reason_and_respond_switches_to_final_text_only_after_successful_websearch():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Welche Switch 2 Spiele erscheinen nächsten Monat?"}]
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "call_ws_1",
                        "type": "function",
                        "function": {
                            "name": "system.websearch",
                            "arguments": '{"query":"Nintendo Switch 2 kommende Spiele Deutschland nächsten Monat Erscheinungsdatum"}',
                        },
                    }
                ],
                "usage": {},
                "cost": {},
                "raw_assistant_response": {"role": "assistant", "content": None},
            },
            {
                "type": "text",
                "text": "Hier sind die zuverlässig bestätigten Switch-2-Releases für nächsten Monat.",
                "usage": {},
                "cost": {},
            },
        ]
    )
    mock_provider.prepare_history_for_second_call = MagicMock(return_value=chat_history + [{"role": "tool", "content": "ws-result"}])
    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "tool_call_id": "call_ws_1",
                "name": "system.websearch",
                "content": '{"status":"ok","data":{"text":"Bestätigte Releases mit Quellen","urls":["https://example.com/release-list"]}}',
            }
        ]
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.websearch", "description": "", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
        ],
    ):
        result = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Welche Switch 2 Spiele erscheinen nächsten Monat?",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.websearch"],
            max_tool_rounds=3,
        )

    assert mock_provider.generate_response.await_count == 2
    final_call_kwargs = mock_provider.generate_response.await_args_list[1].kwargs
    assert final_call_kwargs.get("tools") is None
    assert result.get("type") == "text"


def test_openai_fallback_tool_call_uses_provider_safe_name_for_history():
    fallback = OpenAIGateway.build_forced_fallback_tool_call(
        forced_tool={
            "skill_id": "system.generate_image",
            "provider_tool_name": "system_generate_image",
        },
        user_prompt="Erstell ein Bild von einem kleinen Affen.",
        chat_history=[],
    )

    assert fallback is not None
    assert fallback["function"]["name"] == "system_generate_image"


def test_openai_fallback_websearch_uses_query_and_adds_euro_bias_for_price_requests():
    fallback = OpenAIGateway.build_forced_fallback_tool_call(
        forced_tool={
            "skill_id": "system.websearch",
            "provider_tool_name": "system_websearch",
        },
        user_prompt="Wie hoch ist der aktuelle Goldpreis pro Feinunze heute?",
        chat_history=[],
        fallback_text="",
    )

    assert fallback is not None
    assert fallback["function"]["name"] == "system_websearch"
    args = llm_gateway.json.loads(fallback["function"]["arguments"])
    assert args["query"] == "Wie hoch ist der aktuelle Goldpreis pro Feinunze heute? in Euro"


def test_openai_fallback_websearch_canonicalizes_switch_2_price_query():
    fallback = OpenAIGateway.build_forced_fallback_tool_call(
        forced_tool={
            "skill_id": "system.websearch",
            "provider_tool_name": "system_websearch",
        },
        user_prompt="wieviel kostet eine switch 2?",
        chat_history=[],
        fallback_text="",
    )

    assert fallback is not None
    args = llm_gateway.json.loads(fallback["function"]["arguments"])
    assert args["query"] == "Nintendo Switch 2 Preis Euro"


def test_prevalidate_tool_calls_repairs_missing_websearch_query_from_user_prompt():
    tool_calls = [
        {
            "id": "ws_1",
            "type": "function",
            "function": {
                "name": "system_websearch",
                "arguments": "{}",
            },
        }
    ]

    with patch("backend.services.llm_gateway.skill_router.resolve_tool_name", return_value="websearch_wrapper"), patch(
        "backend.services.llm_gateway.tool_manager.get_skill_id",
        side_effect=lambda name: "system.websearch" if name == "websearch_wrapper" else "",
    ), patch(
        "backend.services.llm_gateway.tool_manager.get_tool",
        return_value=MagicMock(args_schema=schemas.WebsearchArgsV2),
    ):
        result = llm_gateway._prevalidate_tool_calls(tool_calls, user_prompt="wieviel kostet eine switch 2?")

    assert result["invalid_signature"] is None
    assert len(result["valid_calls"]) == 1
    args = llm_gateway.json.loads(result["valid_calls"][0]["function"]["arguments"])
    assert args["query"] == "wieviel kostet eine switch 2?"


def test_prevalidate_tool_calls_keeps_only_first_websearch_call_per_round():
    tool_calls = [
        {
            "id": "ws_1",
            "type": "function",
            "function": {
                "name": "system_websearch",
                "arguments": '{"query":"Nintendo Switch 2 release December 2025 games Germany"}',
            },
        },
        {
            "id": "ws_2",
            "type": "function",
            "function": {
                "name": "system_websearch",
                "arguments": '{"query":"Switch 2 games Dezember 2025 Deutschland Veröffentlichung"}',
            },
        },
    ]

    with patch("backend.services.llm_gateway.skill_router.resolve_tool_name", return_value="websearch_wrapper"), patch(
        "backend.services.llm_gateway.tool_manager.get_skill_id",
        side_effect=lambda name: "system.websearch" if name == "websearch_wrapper" else "",
    ), patch(
        "backend.services.llm_gateway.tool_manager.get_tool",
        return_value=MagicMock(args_schema=schemas.WebsearchArgsV2),
    ):
        result = llm_gateway._prevalidate_tool_calls(
            tool_calls,
            user_prompt="welche switch 2 spiele erscheinen nächsten monat in deutschland?",
        )

    assert result["invalid_signature"] is None
    assert len(result["valid_calls"]) == 1
    assert result["system_hints"]
    assert "nur ein system.websearch-Aufruf erlaubt" in result["system_hints"][0]


def test_openai_fallback_create_pdf_uses_current_prompt_filename_and_no_hardcoded_monkey_text():
    history = [
        {
            "role": "tool",
            "name": "system.generate_image",
            "content": '{"status":"ok","data":{"markdown_image":"![Szene](/user_images/hase.png)"}}',
        }
    ]

    fallback = OpenAIGateway.build_forced_fallback_tool_call(
        forced_tool={
            "skill_id": "system.create_pdf",
            "provider_tool_name": "system_create_pdf",
        },
        user_prompt="Schreibe eine kurze Geschichte. Erstelle ein PDF namens der_kleine_hase.pdf.",
        chat_history=history,
        fallback_text="Eine kurze Kindergeschichte über ein Häschen und einen Igel.",
    )

    assert fallback is not None
    args = llm_gateway.json.loads(fallback["function"]["arguments"])
    assert args["filename"] == "der_kleine_hase.pdf"
    assert "Affen sind intelligente Primaten" not in args["content"]
    assert "Häschen" in args["content"] or "Häschen" in args.get("content", "")
    assert "Auftrag:" not in args["content"]
    assert (
        "## Kapitel 1" in args["content"]
        or "Eine kurze Kindergeschichte" in args["content"]
    )
    assert args["layout_profile"] == "bilderbuch"
    assert "der_kleine_hase.pdf" in args["source_prompt"]


def test_extract_requested_pdf_filename_supports_pdf_heisst_without_extension():
    filename = llm_gateway._extract_requested_pdf_filename(
        "Schreibe eine Geschichte für Kinder und die PDF heißt der kleine hase"
    )
    assert filename == "der_kleine_hase.pdf"


@pytest.mark.asyncio
async def test_reason_and_respond_renders_local_business_results_directly_without_extra_roundtrip():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Suche ein italienisches Restaurant in Berlin."}]
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(
        return_value={
            "type": "tool_code",
            "tool_calls": [
                {
                    "id": "lb_1",
                    "type": "function",
                    "function": {
                        "name": "system_local_business",
                        "arguments": '{"query":"italienisches Restaurant","location":"Berlin Prenzlauer Berg","limit":2}',
                    },
                }
            ],
            "raw_assistant_response": {"role": "assistant", "content": None},
            "usage": {},
            "cost": {},
        }
    )
    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "tool_call_id": "lb_1",
                "name": "system.local_business",
                "_skill_id": "system.local_business",
                "content": llm_gateway.json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "query": "italienisches Restaurant",
                            "location": "Berlin Prenzlauer Berg",
                            "businesses": [
                                {
                                    "name": "L'Osteria del Parlamento",
                                    "description": "Bekannt für große Pizza und lebhafte Atmosphäre.",
                                    "category": "Budget",
                                    "address": "Raumerstraße 15, 10437 Berlin",
                                    "opening_hours": "Mo-So 12:00-23:00",
                                    "phone": "+49 30 123456",
                                    "website": "https://www.losteria-parlamento.de/",
                                    "menu_url": "https://www.losteria-parlamento.de/menu",
                                    "reservation_url": "https://www.losteria-parlamento.de/reservieren",
                                },
                                {
                                    "name": "San Marco",
                                    "description": "Traditionelle Pasta und ruhiger Gastraum.",
                                    "category": "Klassisch",
                                    "address": "Schönhauser Allee 102, 10439 Berlin",
                                    "opening_hours": None,
                                    "phone": None,
                                    "website": "https://www.sanmarcoberlin.de/",
                                    "menu_url": None,
                                    "reservation_url": None,
                                },
                            ],
                        },
                        "error": None,
                    },
                    ensure_ascii=False,
                ),
            }
        ]
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.local_business", "description": "", "parameters": {"type": "object", "properties": {}}},
        ],
    ):
        result = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Suche zwei italienische Restaurants im Prenzlauer Berg.",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.local_business"],
        )

    assert "L'Osteria del Parlamento" in result["text"]
    assert "Bekannt für große Pizza und lebhafte Atmosphäre." in result["text"]
    assert "_Budget_" in result["text"]
    assert "Adresse: Raumerstraße 15, 10437 Berlin" in result["text"]
    assert "Öffnungszeiten: Mo-So 12:00-23:00" in result["text"]
    assert "Telefon: +49 30 123456" in result["text"]
    assert "Website: https://www.losteria-parlamento.de/" in result["text"]
    assert "Speisekarte: [Link](https://www.losteria-parlamento.de/menu)" in result["text"]
    assert "Reservierung: [Link](https://www.losteria-parlamento.de/reservieren)" in result["text"]
    assert "maps" not in result["text"].lower()
    assert mock_provider.generate_response.await_count == 1
    assert mock_executor.execute_tool_calls.await_count == 1


@pytest.mark.asyncio
async def test_reason_and_respond_returns_deterministic_local_business_no_result_without_extra_synthesis():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Suche italienische Restaurants in Berlin Prenzlauer Berg."}]
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(
        return_value={
            "type": "tool_code",
            "tool_calls": [
                {
                    "id": "lb_1",
                    "type": "function",
                    "function": {
                        "name": "system_local_business",
                        "arguments": '{"query":"italienische Restaurants","location":"Berlin Prenzlauer Berg","limit":4}',
                    },
                }
            ],
            "raw_assistant_response": {"role": "assistant", "content": None},
            "usage": {},
            "cost": {},
        }
    )
    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "tool_call_id": "lb_1",
                "name": "system.local_business",
                "_skill_id": "system.local_business",
                "content": llm_gateway.json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "query": "italienische Restaurants",
                            "location": "Berlin Prenzlauer Berg",
                            "businesses": [],
                            "result_count": 0,
                        },
                        "error": None,
                    },
                    ensure_ascii=False,
                ),
            }
        ]
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.local_business", "description": "", "parameters": {"type": "object", "properties": {}}},
        ],
    ):
        result = await llm_gateway.reason_and_respond(
            provider="ollama",
            model="gemma2:27b@test",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Suche vier italienische Restaurants im Prenzlauer Berg.",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.local_business"],
            max_tool_rounds=2,
        )

    assert "keine verlässlichen Treffer" in result["text"]
    assert "Berlin Prenzlauer Berg" in result["text"]
    assert mock_provider.generate_response.await_count == 1
    assert mock_executor.execute_tool_calls.await_count == 1


@pytest.mark.asyncio
async def test_reason_and_respond_marks_text_response_after_successful_tool_round_as_executed_tool_call():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Suche ein italienisches Restaurant in Berlin."}]
    mock_provider = MagicMock()
    queued_responses = [
        {
            "type": "tool_code",
            "tool_calls": [
                {
                    "id": "lb_1",
                    "type": "function",
                    "function": {
                        "name": "system_local_business",
                        "arguments": '{"query":"italienisches Restaurant","location":"Berlin Prenzlauer Berg","limit":2}',
                    },
                }
            ],
            "raw_assistant_response": {"role": "assistant", "content": None},
            "usage": {},
            "cost": {},
        },
        {
            "type": "text",
            "text": "Hier sind zwei gute italienische Restaurants in Berlin Prenzlauer Berg.",
            "usage": {},
            "cost": {},
        },
    ]

    mock_provider.generate_response = AsyncMock(side_effect=queued_responses)
    mock_provider.prepare_history_for_second_call = MagicMock(
        side_effect=lambda *, chat_history, raw_assistant_response, tool_results=None: list(chat_history) + list(tool_results or [])
    )
    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "tool_call_id": "lb_1",
                "name": "system.local_business",
                "_skill_id": "find_local_business_tool",
                "content": llm_gateway.json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "query": "italienisches Restaurant",
                            "location": "Berlin Prenzlauer Berg",
                            "businesses": [],
                        },
                        "error": None,
                    },
                    ensure_ascii=False,
                ),
            }
        ]
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.local_business", "description": "", "parameters": {"type": "object", "properties": {}}},
        ],
    ):
        result = await llm_gateway.reason_and_respond(
            provider="ollama",
            model="gemma2:27b@test",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Suche zwei italienische Restaurants im Prenzlauer Berg.",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.local_business"],
            max_tool_rounds=2,
        )

    assert result["text"] == "Hier sind zwei gute italienische Restaurants in Berlin Prenzlauer Berg."
    assert result["executed_tool_call"] is True
    assert result["tool_limit_reached"] is True
    assert mock_provider.generate_response.await_count == 2
    assert mock_executor.execute_tool_calls.await_count == 1


def test_openai_fallback_generate_image_uses_matching_story_scene_prompt():
    fallback = OpenAIGateway.build_forced_fallback_tool_call(
        forced_tool={
            "skill_id": "system.generate_image",
            "provider_tool_name": "system_generate_image",
            "image_index": 3,
            "total_image_count": 3,
        },
        user_prompt="Schreibe eine kurze Geschichte für Kinder über ein niedliches Häschen und einen Igel. Mach dazu 3 Illustrationen im selben Stil. Die PDF heißt der kleine hase",
        chat_history=[],
    )

    assert fallback is not None
    args = llm_gateway.json.loads(fallback["function"]["arguments"])
    assert "Kapitel 3" in args["prompt"]
    assert "teilen sich die letzten Beeren" in args["prompt"]
    assert "neuer Freund" in args["prompt"]
    assert "Keine beliebigen Alternativszenen" in args["prompt"]


@pytest.mark.asyncio
async def test_reason_and_respond_forces_multiple_generate_image_rounds_before_create_pdf():
    chat_history = [{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Story + 3 Bilder + PDF"}]
    mock_provider = MagicMock()
    queued_responses = [
        {
            "type": "tool_code",
            "tool_calls": [{"id": "img_1", "type": "function", "function": {"name": "system_generate_image", "arguments": '{"prompt":"Szene 1"}'}}],
            "raw_assistant_response": {"role": "assistant", "content": None},
            "usage": {},
            "cost": {},
        },
        {
            "type": "tool_code",
            "tool_calls": [{"id": "img_2", "type": "function", "function": {"name": "system_generate_image", "arguments": '{"prompt":"Szene 2"}'}}],
            "raw_assistant_response": {"role": "assistant", "content": None},
            "usage": {},
            "cost": {},
        },
        {
            "type": "tool_code",
            "tool_calls": [{"id": "img_3", "type": "function", "function": {"name": "system_generate_image", "arguments": '{"prompt":"Szene 3"}'}}],
            "raw_assistant_response": {"role": "assistant", "content": None},
            "usage": {},
            "cost": {},
        },
        {
            "type": "tool_code",
            "tool_calls": [{"id": "pdf_1", "type": "function", "function": {"name": "system_create_pdf", "arguments": '{"content":"# Der kleine Hase","filename":"der_kleine_hase.pdf"}'}}],
            "raw_assistant_response": {"role": "assistant", "content": None},
            "usage": {},
            "cost": {},
        },
        {"type": "text", "text": "Fertig.", "usage": {}, "cost": {}},
    ]

    def _next_response(*_args, **_kwargs):
        if queued_responses:
            return queued_responses.pop(0)
        return {"type": "text", "text": "Finale Antwort.", "usage": {}, "cost": {}}

    mock_provider.generate_response = AsyncMock(side_effect=_next_response)
    def _prepare_history(*, chat_history, raw_assistant_response, tool_results=None):
        return list(chat_history) + list(tool_results or [])

    mock_provider.prepare_history_for_second_call = MagicMock(side_effect=_prepare_history)

    mock_executor = MagicMock()
    mock_executor.execute_tool_calls = AsyncMock(
        side_effect=[
            [{"role": "tool", "tool_call_id": "img_1", "name": "system.generate_image", "content": '{"status":"ok","data":{"markdown_image":"![1](/user_images/1.png)"}}'}],
            [{"role": "tool", "tool_call_id": "img_2", "name": "system.generate_image", "content": '{"status":"ok","data":{"markdown_image":"![2](/user_images/2.png)"}}'}],
            [{"role": "tool", "tool_call_id": "img_3", "name": "system.generate_image", "content": '{"status":"ok","data":{"markdown_image":"![3](/user_images/3.png)"}}'}],
            [{"role": "tool", "tool_call_id": "pdf_1", "name": "system.create_pdf", "content": '{"status":"ok","data":{"file_path":"C:/tmp/der_kleine_hase.pdf"}}'}],
        ]
    )

    with patch("backend.services.llm_gateway.get_provider", return_value=mock_provider), patch(
        "backend.services.llm_gateway.tool_manager.get_all_tools", return_value={"dummy": MagicMock()}
    ), patch(
        "backend.services.llm_gateway._filter_tools_by_skill_ids", return_value=[MagicMock()]
    ), patch(
        "backend.services.llm_gateway._build_tool_definitions_for_llm",
        return_value=[
            {"name": "system.generate_image", "description": "", "parameters": {"type": "object", "properties": {}}},
            {"name": "system.create_pdf", "description": "", "parameters": {"type": "object", "properties": {}}},
        ],
    ):
        result = await llm_gateway.reason_and_respond(
            provider="openai",
            model="gpt-5.4-nano",
            api_key="test_key",
            chat_history=chat_history,
            context_manager=MagicMock(),
            db=MagicMock(),
            user_prompt="Erstelle 3 Illustrationen und ein PDF namens der_kleine_hase.pdf.",
            chat_id=1,
            tool_executor=mock_executor,
            disable_tools=False,
            allowed_skill_ids=["system.generate_image", "system.create_pdf"],
        )

    assert result.get("type") == "text"
    forced_names = [
        call.kwargs.get("force_tool_name")
        for call in mock_provider.generate_response.await_args_list
        if call.kwargs.get("force_tool_name")
    ]
    assert forced_names == [
        "system_generate_image",
        "system_generate_image",
        "system_generate_image",
        "system_create_pdf",
    ]


def test_pdf_facts_guard_appends_missing_facts_to_text_response():
    response = {"type": "text", "text": "Die PDF wurde erstellt."}
    history = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "function": {
                        "name": "system.create_pdf",
                        "arguments": '{"content":"# Spanien\\n- Hauptstadt: Madrid\\n- Einwohnerzahl: 47,4 Mio."}',
                    }
                }
            ],
        }
    ]

    updated = llm_gateway._ensure_pdf_facts_in_text_response(response, history)
    assert "Hier sind die recherchierten Fakten" in updated["text"]
    assert "Hauptstadt: Madrid" in updated["text"]


def test_pdf_facts_guard_noop_when_facts_already_present():
    response = {
        "type": "text",
        "text": "Hier sind die recherchierten Fakten:\n- Hauptstadt: Madrid\nDie PDF wurde erstellt.",
    }
    history = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "function": {
                        "name": "system.create_pdf",
                        "arguments": '{"content":"- Hauptstadt: Madrid"}',
                    }
                }
            ],
        }
    ]

    updated = llm_gateway._ensure_pdf_facts_in_text_response(response, history)
    assert updated["text"] == response["text"]


def test_pdf_facts_guard_reads_gemini_parts_function_call_history():
    response = {"type": "text", "text": "Ich habe die Agenten-Ausführung abgeschlossen."}
    history = [
        {
            "role": "model",
            "parts": [
                {
                    "function_call": {
                        "name": "system.create_pdf",
                        "args": {
                            "content": "# Informationen über Indien\n\n* **Hauptstadt:** Neu-Delhi\n* **Einwohnerzahl:** ca. 1,428 Milliarden\n* **Entfernung von Berlin nach Neu-Delhi:** ca. 5.920 km"
                        },
                    }
                }
            ],
        }
    ]

    updated = llm_gateway._ensure_pdf_facts_in_text_response(response, history)
    assert "Hier sind die recherchierten Fakten" in updated["text"]
    assert "Hauptstadt" in updated["text"]
    assert "Neu-Delhi" in updated["text"]
