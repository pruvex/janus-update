import json
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.data import contact_schemas, crud, schemas
from backend.data.models import Contact
from backend.services.chat_orchestrator import ChatOrchestrator


@pytest.mark.asyncio
async def test_invalid_tool_result_json_logs_traceback_and_aborts_turn(db_session, tmp_path, monkeypatch, caplog):
    """Invalid tool-result JSON must produce an error traceback and controlled turn failure message."""
    chat = crud.create_chat(db_session, title="Error Resilience")

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
        return_value={
            "type": "tool_code",
            "tool_calls": [
                {
                    "id": "tc-invalid-json",
                    "function": {
                        "name": "knowledge.query",
                        "arguments": json.dumps({"query_text": "Kairo"}),
                    },
                }
            ],
            "raw_assistant_response": {"role": "assistant", "content": "tool"},
        }
    )

    async def _invalid_tool_results(self, tool_calls, bypass_policy=False):
        return [
            {
                "role": "tool",
                "tool_call_id": "tc-invalid-json",
                "name": "knowledge.query",
                "content": "{invalid-json",
            }
        ]

    monkeypatch.setattr("backend.services.llm_gateway.reason_and_respond", gateway_mock)
    monkeypatch.setattr("backend.services.chat_orchestrator.ToolExecutor.execute_tool_calls", _invalid_tool_results)

    request = schemas.ChatRequest(
        prompt="Bitte prüfe das Dokument.",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    with caplog.at_level(logging.ERROR, logger="janus_backend"):
        response = await orchestrator.handle_chat_request(request)

    assert "Die Aktion konnte nicht abgeschlossen werden" in response.get("text", "")
    parse_error_logs = [
        record for record in caplog.records if "invalid tool result JSON" in record.getMessage()
    ]
    assert parse_error_logs, "Expected JSON parse error log was not emitted."
    assert any(record.exc_info for record in parse_error_logs), "Expected traceback (exc_info) in JSON parse error log."


def test_update_contact_duplicate_email_no_keyerror(db_session):
    """Regression: update_contact must not crash after popping duplicate email from updates."""
    first = Contact(name="A", email="dup@example.com")
    second = Contact(name="B", email="b@example.com")
    db_session.add(first)
    db_session.add(second)
    db_session.commit()
    db_session.refresh(second)

    updated = crud.update_contact(db_session, second.id, {"email": "dup@example.com"})

    assert updated is not None
    refreshed = db_session.query(Contact).filter(Contact.id == second.id).first()
    assert refreshed is not None
    assert "dup@example.com" in str(refreshed.notes or "")


def test_create_contact_rich_fields_roundtrip(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Rita Example",
            contact_type="organization",
            category="Business",
            email="rita@example.com",
            phone="+49 30 123456",
            preferences=["Terrasse", "Mittagsmenue"],
            dislikes=["Laut"],
            personal_details=["Stammkundin seit 2024"],
            proposal_status="confirmed",
            proposal_source_context="manuell",
            proposal_last_outcome="imported",
            memory_sync_status="ready",
        ),
    )

    assert created is not None
    assert created.contact_type == "organization"
    assert created.preferences == ["Terrasse", "Mittagsmenue"]
    assert created.dislikes == ["Laut"]
    assert created.personal_details == ["Stammkundin seit 2024"]
    assert created.proposal_status == "confirmed"
    assert created.proposal_source_context == "manuell"
    assert created.proposal_last_outcome == "imported"
    assert created.memory_sync_status == "ready"


def test_get_contact_applies_safe_defaults_for_legacy_rich_fields(db_session):
    legacy = Contact(
        name="Legacy Contact",
        email="legacy@example.com",
        contact_type=None,
        preferences=None,
        dislikes=None,
        personal_details=None,
        proposal_status=None,
        proposal_source_context=None,
        proposal_last_outcome=None,
        memory_sync_status=None,
    )
    db_session.add(legacy)
    db_session.commit()
    db_session.refresh(legacy)

    response = crud.get_contact(db_session, legacy.id)

    assert response is not None
    assert response.contact_type == "private_person"
    assert response.preferences == []
    assert response.dislikes == []
    assert response.personal_details == []
    assert response.proposal_status == "confirmed"
    assert response.memory_sync_status == "unlinked"
