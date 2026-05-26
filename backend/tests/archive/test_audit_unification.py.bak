import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import event

from backend.data import crud, schemas
from backend.data.models import Document
from backend.services.chat_orchestrator import ChatOrchestrator


@pytest.mark.asyncio
async def test_audit_status_single_write_and_deep_history_filename_resolution(db_session, tmp_path, monkeypatch):
    """Audit path must resolve filename from deep history and persist status via a single DB update."""
    chat = crud.create_chat(db_session, title="Audit Unification")

    pdf_path = tmp_path / "deep_history_audit.pdf"
    pdf_path.write_text("dummy", encoding="utf-8")
    crud.create_document(db_session, filename="deep_history_audit.pdf", file_path=str(pdf_path))

    crud.create_message(
        db_session,
        chat.id,
        "user",
        "SYSTEM-INSTRUKTION FÜR DATEI-UPLOAD 'deep_history_audit.pdf'",
    )
    # Push the upload marker far back in history so resolver must scan deep history.
    for idx in range(20):
        crud.create_message(db_session, chat.id, "user", f"Zwischennachricht {idx}")

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
            goal="Audit status synthesis",
            required_skills=["knowledge.query"],
        )

    async def _fake_run(**_kwargs):
        return {
            "text": json.dumps(
                {
                    "audit_summary": "Audit durch Agent abgeschlossen",
                    "modifications_list": [{"search": "alt", "replace": "neu"}],
                },
                ensure_ascii=False,
            ),
            "trace_id": "trace-audit-unification",
        }

    monkeypatch.setattr(orchestrator.agent_planner, "plan", _fake_plan)
    monkeypatch.setattr(orchestrator.agent_runtime, "run", _fake_run)
    monkeypatch.setattr(orchestrator, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    update_statements = []

    def _capture_updates(conn, cursor, statement, parameters, context, executemany):
        stmt = str(statement or "").lower()
        if "update" in stmt and "documents" in stmt and "audit_status" in stmt:
            update_statements.append(stmt)

    event.listen(db_session.bind, "before_cursor_execute", _capture_updates)
    try:
        request = schemas.ChatRequest(
            prompt="Analysiere und erstelle eine mehrschrittige Audit-Auswertung.",
            chat_id=chat.id,
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
        )
        response = await orchestrator.handle_chat_request(request)
    finally:
        event.remove(db_session.bind, "before_cursor_execute", _capture_updates)

    assert isinstance(response.get("text", ""), str)
    assert response.get("agent", {}).get("name") == "Audit-Agent"

    persisted_doc = db_session.query(Document).filter(Document.filename == "deep_history_audit.pdf").first()
    assert persisted_doc is not None
    assert persisted_doc.audit_status == "warning"

    assert len(update_statements) == 1
