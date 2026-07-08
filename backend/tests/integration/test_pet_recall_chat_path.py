import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.api.routers.chat import get_orchestrator
from backend.data import crud, schemas
from backend.dependencies import api_key_auth
from backend.main import app
from backend.services.chat_orchestrator import ChatOrchestrator


@pytest.mark.asyncio
async def test_api_chat_pet_recall_returns_tasso_and_garfield(test_client, db_session, tmp_path, monkeypatch):
    chat = crud.create_chat(db_session, title="Pet Recall Regression")

    template_config = tmp_path / "template_config.json"
    template_config.write_text(json.dumps({"active_personality": "ai_assistant"}), encoding="utf-8")
    template_personalities = tmp_path / "template_personalities.json"
    template_personalities.write_text(
        json.dumps([{"id": "ai_assistant", "prompt": "Du bist Janus."}], ensure_ascii=False),
        encoding="utf-8",
    )

    orchestrator = ChatOrchestrator(
        db=db_session,
        context_manager=MagicMock(),
        model_catalog={"gpt-5.4-nano": {}},
        config_file_path=str(tmp_path / "config.json"),
        template_config_file_path=str(template_config),
        personalities_file_path=str(tmp_path / "personalities.json"),
        template_personalities_file_path=str(template_personalities),
    )

    monkeypatch.setattr(orchestrator, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    gateway_mock = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "tc-memory-read",
                        "function": {
                            "name": "memory.read",
                            "arguments": json.dumps({"query": "was weißt du über olis haustiere?"}, ensure_ascii=False),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": None},
                "usage": {},
                "cost": {},
            },
            {
                "type": "text",
                "text": "",
                "tool_calls": [],
                "raw_assistant_response": {"role": "assistant", "content": ""},
                "usage": {},
                "cost": {},
            },
        ]
    )

    async def _memory_read_tool_results(self, tool_calls, bypass_policy=False):
        return [
            {
                "role": "tool",
                "tool_call_id": "tc-memory-read",
                "name": "memory.read",
                "_skill_id": "memory.read",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "memories": [
                                {"fact": "Oliver Schwab hat einen Hund namens tasso"},
                                {"fact": "Oliver Schwab hat eine Katze namens garfield"},
                                {"fact": "Katze Garfield mag Thunfisch \u00fcberhaupt nicht"},
                                {"fact": "Hund Tasso ist ein podenco"},
                                {"fact": "Hund Tasso frisst gerne thunfisch"},
                            ]
                        },
                    },
                    ensure_ascii=False,
                ),
            }
        ]

    monkeypatch.setattr("backend.services.llm_gateway.reason_and_respond", gateway_mock)
    monkeypatch.setattr(
        "backend.services.chat_orchestrator.ToolExecutor.execute_tool_calls",
        _memory_read_tool_results,
    )

    app.dependency_overrides[api_key_auth] = lambda: None
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    try:
        response = test_client.post(
            "/api/chat",
            json={
                "prompt": "was weißt du über olis haustiere?",
                "chat_id": chat.id,
                "provider": "openai",
                "model": "gpt-5.4-nano",
                "api_key": "dummy",
            },
        )
    finally:
        app.dependency_overrides.pop(api_key_auth, None)
        app.dependency_overrides.pop(get_orchestrator, None)

    assert response.status_code == 200
    body = response.json()
    text = str(body.get("text") or "")
    assert "Tasso" in text
    assert "Garfield" in text
    assert "Podenco" in text or "podenco" in text
    assert "Thunfisch" in text or "thunfisch" in text
    assert "mag Thunfisch \u00fcberhaupt nicht" in text


@pytest.mark.asyncio
async def test_api_chat_contact_recall_forces_memory_fallback_over_gemini_free_text(
    test_client, db_session, tmp_path, monkeypatch
):
    chat = crud.create_chat(db_session, title="Chris Recall Regression")

    template_config = tmp_path / "template_config.json"
    template_config.write_text(json.dumps({"active_personality": "ai_assistant"}), encoding="utf-8")
    template_personalities = tmp_path / "template_personalities.json"
    template_personalities.write_text(
        json.dumps([{"id": "ai_assistant", "prompt": "Du bist Janus."}], ensure_ascii=False),
        encoding="utf-8",
    )

    orchestrator = ChatOrchestrator(
        db=db_session,
        context_manager=MagicMock(),
        model_catalog={"gemini-3-flash-preview": {}},
        config_file_path=str(tmp_path / "config.json"),
        template_config_file_path=str(template_config),
        personalities_file_path=str(tmp_path / "personalities.json"),
        template_personalities_file_path=str(template_personalities),
    )

    monkeypatch.setattr(orchestrator, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    gateway_mock = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "tc-memory-read",
                        "function": {
                            "name": "memory.read",
                            "arguments": json.dumps({"query": "Was weißt du über Chris?"}, ensure_ascii=False),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": None},
                "usage": {},
                "cost": {},
            },
            {
                "type": "text",
                "text": (
                    "Chris ist 1,95 m groß, hat blaue Augen, blondes Haar, "
                    "trägt eine Brille und ein Piercing."
                ),
                "tool_calls": [],
                "raw_assistant_response": {"role": "assistant", "content": ""},
                "usage": {},
                "cost": {},
            },
        ]
    )

    async def _memory_read_tool_results(self, tool_calls, bypass_policy=False):
        return [
            {
                "role": "tool",
                "tool_call_id": "tc-memory-read",
                "name": "memory.read",
                "_skill_id": "memory.read",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "memories": [
                                {"fact": "Chris mag kimchi"},
                                {"fact": "Chris ernährt sich vegetarisch"},
                                {"fact": "Chris ist ein großer Star-Wars-Fan"},
                                {"fact": "Chris baut gerne Star-Wars-Modelle"},
                                {"fact": "Chris verbringt gerne Zeit im Garten"},
                            ]
                        },
                    },
                    ensure_ascii=False,
                ),
            }
        ]

    monkeypatch.setattr("backend.services.llm_gateway.reason_and_respond", gateway_mock)
    monkeypatch.setattr(
        "backend.services.chat_orchestrator.ToolExecutor.execute_tool_calls",
        _memory_read_tool_results,
    )

    app.dependency_overrides[api_key_auth] = lambda: None
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    try:
        response = test_client.post(
            "/api/chat",
            json={
                "prompt": "Was weißt du über Chris?",
                "chat_id": chat.id,
                "provider": "gemini",
                "model": "gemini-3-flash-preview",
                "api_key": "dummy",
            },
        )
    finally:
        app.dependency_overrides.pop(api_key_auth, None)
        app.dependency_overrides.pop(get_orchestrator, None)

    assert response.status_code == 200
    body = response.json()
    text = str(body.get("text") or "")
    assert "kimchi" in text.lower()
    assert "vegetar" in text.lower()
    assert "star-wars" in text.lower() or "star wars" in text.lower()
    assert "garten" in text.lower()
    assert "1,95" not in text
    assert "blaue augen" not in text.lower()
    assert "brille" not in text.lower()
    assert "piercing" not in text.lower()
