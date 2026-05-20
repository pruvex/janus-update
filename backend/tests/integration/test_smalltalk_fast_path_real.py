import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.data import crud, schemas
from backend.services.chat_orchestrator import ChatOrchestrator


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prompt", "expected_prefix"),
    [
        ("hey!!", "Hey!"),
        ("wie gehts dir?", "Mir geht's gut"),
    ],
)
async def test_smalltalk_fast_path_skips_llm_for_openai(db_session, tmp_path, monkeypatch, prompt, expected_prefix):
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

    llm_gateway_mock = AsyncMock(
        return_value={
            "type": "text",
            "text": "LLM should not answer smalltalk",
            "raw_assistant_response": {"role": "assistant", "content": "should not be called"},
        }
    )
    monkeypatch.setattr("backend.services.llm_gateway.reason_and_respond", llm_gateway_mock)

    chat = crud.create_chat(db_session, title="Smalltalk Test")
    request = schemas.ChatRequest(
        prompt=prompt,
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    response = await orchestrator.handle_chat_request(request)

    assert llm_gateway_mock.call_count == 0
    assert response.get("text", "").startswith(expected_prefix)
