import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.data import crud, schemas
from backend.data.models import Document, Message
from backend.services.chat_orchestrator import ChatOrchestrator


@pytest.mark.asyncio
async def test_agent_flow_keeps_audit_guardrails_and_persistence(db_session, tmp_path, monkeypatch):
    """Agent results must still pass full orchestration guardrails (audit update + DB persistence)."""
    chat = crud.create_chat(db_session, title="Agent Audit Continuity")

    pdf_path = tmp_path / "audit_context.pdf"
    pdf_path.write_text("Dummy content", encoding="utf-8")
    crud.create_document(db_session, filename="audit_context.pdf", file_path=str(pdf_path))

    crud.create_message(
        db_session,
        chat.id,
        "user",
        "SYSTEM-INSTRUKTION FÜR DATEI-UPLOAD 'audit_context.pdf'",
    )

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

    monkeypatch.setattr(orchestrator.agent_planner, "should_use_agent", lambda _text: True)

    async def _fake_plan(**_kwargs):
        return SimpleNamespace(
            name="Audit-Agent",
            goal="Check audit context",
            required_skills=["knowledge.query"],
        )

    async def _fake_run(**_kwargs):
        return {
            "text": json.dumps(
                {
                    "audit_summary": "Agent hat Audit abgeschlossen",
                    "modifications_list": [
                        {"search": "alt", "replace": "neu"}
                    ],
                },
                ensure_ascii=False,
            ),
            "trace_id": "agent-trace-1",
        }

    monkeypatch.setattr(orchestrator.agent_planner, "plan", _fake_plan)
    monkeypatch.setattr(orchestrator.agent_runtime, "run", _fake_run)
    monkeypatch.setattr(orchestrator, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    request = schemas.ChatRequest(
        prompt="Analysiere und erstelle eine strukturierte Auswertung.",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    api_response = await orchestrator.handle_chat_request(request)

    assert isinstance(api_response.get("text", ""), str)
    assert api_response.get("agent", {}).get("name") == "Audit-Agent"

    persisted_assistant = (
        db_session.query(Message)
        .filter(Message.chat_id == chat.id, Message.role == "assistant")
        .order_by(Message.id.desc())
        .first()
    )
    assert persisted_assistant is not None
    assert "audit_summary" in (persisted_assistant.content or "")

    doc_after = db_session.query(Document).filter(Document.filename == "audit_context.pdf").first()
    assert doc_after is not None
    assert doc_after.audit_status == "warning"
