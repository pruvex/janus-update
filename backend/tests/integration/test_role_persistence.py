import json
from unittest.mock import MagicMock

import pytest

from backend.data import crud, schemas
from backend.data.models import Message
from backend.services.chat_orchestrator import ChatOrchestrator


@pytest.mark.asyncio
async def test_role_roundtrip_model_to_assistant_prompt(db_session, tmp_path, monkeypatch):
    """Ensures model-origin messages persist as assistant and stay assistant in prompt history."""
    chat = crud.create_chat(db_session, title="Role Persistence")

    persisted_text = "Persisted assistant message"
    crud.create_message(db_session, chat.id, "model", persisted_text)

    stored_msg = (
        db_session.query(Message)
        .filter(Message.chat_id == chat.id, Message.content == persisted_text)
        .order_by(Message.id.desc())
        .first()
    )
    assert stored_msg is not None
    assert stored_msg.role == "assistant"

    template_config = tmp_path / "template_config.json"
    template_config.write_text(json.dumps({"active_personality": "ai_assistant"}), encoding="utf-8")
    template_personalities = tmp_path / "template_personalities.json"
    template_personalities.write_text(
        json.dumps([{"id": "ai_assistant", "prompt": "Du bist Janus."}], ensure_ascii=False),
        encoding="utf-8",
    )

    config_file = tmp_path / "config.json"
    personalities_file = tmp_path / "personalities.json"

    orchestrator = ChatOrchestrator(
        db=db_session,
        context_manager=MagicMock(),
        model_catalog={"gpt-5.4-nano": {}},
        config_file_path=str(config_file),
        template_config_file_path=str(template_config),
        personalities_file_path=str(personalities_file),
        template_personalities_file_path=str(template_personalities),
    )

    captured = {}

    async def _fake_reason_and_respond(**kwargs):
        captured["chat_history"] = kwargs["chat_history"]
        return {"type": "text", "text": "Alles klar.", "usage": {}, "cost": {}}

    monkeypatch.setattr(
        "backend.services.llm_gateway.reason_and_respond",
        _fake_reason_and_respond,
    )
    monkeypatch.setattr(orchestrator, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    request = schemas.ChatRequest(
        prompt="Kurzer Check",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    response = await orchestrator.handle_chat_request(request)

    assert isinstance(response.get("text", ""), str)
    assert "chat_history" in captured

    role_for_persisted_message = None
    for entry in captured["chat_history"]:
        if entry.get("content") == persisted_text:
            role_for_persisted_message = entry.get("role")
            break

    assert role_for_persisted_message == "assistant"
