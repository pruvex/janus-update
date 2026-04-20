import json
from unittest.mock import AsyncMock, patch

import pytest

from backend.data import crud
from backend.data.models import AppState, Document
from backend.services.tool_executor import ToolExecutor
from backend.services.tool_manager import tool_manager
from backend.utils.config_loader import load_config_data


def _auth_headers():
    internal_key = load_config_data().get("api_key")
    assert internal_key, "Interner API-Key fehlt in Test-Konfiguration."
    return {"X-Janus-Internal-Key": internal_key}


@pytest.mark.asyncio
async def test_journey_a_ampel_faktencheck_sets_warning_and_refresh_command(
    test_client,
    db_session,
    isolated_workspace,
    monkeypatch,
):
    source_pdf = isolated_workspace / "aegypten.pdf"
    source_pdf.write_text("Kairo ist die Hauptstadt von Ägypten.", encoding="utf-8")
    doc = crud.create_document(db_session, filename="aegypten.pdf", file_path=str(source_pdf))

    headers = _auth_headers()
    chat_create = test_client.post("/api/chats", json={"title": "Journey A"}, headers=headers)
    assert chat_create.status_code == 200
    chat_id = chat_create.json()["id"]

    captured_tool_names = []
    original_execute_tool_calls = ToolExecutor.execute_tool_calls

    async def _capture_execute_tool_calls(self, tool_calls, bypass_policy=False):
        captured_tool_names.extend((tc.get("function") or {}).get("name") for tc in tool_calls)
        return await original_execute_tool_calls(self, tool_calls, bypass_policy=bypass_policy)

    async def _fake_query_knowledge_base(**_kwargs):
        return {
            "status": "ok",
            "data": {
                "hit_count": 1,
                "hits": [{"source": "aegypten.pdf", "page": 1, "excerpt": "Kairo"}],
            },
        }

    async def _fake_edit_pdf_text_in_place(**_kwargs):
        return {
            "status": "ok",
            "data": {"result": "Korrektur gespeichert", "quality_gate": "passed"},
        }

    query_tool = tool_manager.get_tool("query_knowledge_base")
    edit_tool = tool_manager.get_tool("edit_pdf_text_in_place")
    assert query_tool is not None
    assert edit_tool is not None

    monkeypatch.setattr(ToolExecutor, "execute_tool_calls", _capture_execute_tool_calls)
    monkeypatch.setattr(query_tool, "func", _fake_query_knowledge_base)
    monkeypatch.setattr(edit_tool, "func", _fake_edit_pdf_text_in_place)
    monkeypatch.setattr("backend.services.chat_orchestrator.ChatOrchestrator._trigger_fact_extraction", lambda *args, **kwargs: None)

    gateway_mock = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "ja-audit-query",
                        "function": {
                            "name": "knowledge.query",
                            "arguments": json.dumps({"query_text": "Aegypten"}),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {"type": "text", "text": "Audit gestartet", "finish_reason": "STOP"},
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "ja-factcheck-query",
                        "function": {
                            "name": "knowledge.query",
                            "arguments": json.dumps({"query_text": "Kairo"}),
                        },
                    },
                    {
                        "id": "ja-factcheck-edit",
                        "function": {
                            "name": "knowledge.edit_pdf",
                            "arguments": json.dumps(
                                {
                                    "original_filename": "aegypten.pdf",
                                    "modifications": [
                                        {
                                            "search": "Kairo ist Hauptstadt.",
                                            "replace": "Kairo ist die Hauptstadt von Ägypten.",
                                        }
                                    ],
                                }
                            ),
                        },
                    },
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "audit_summary": "Faktencheck abgeschlossen",
                        "modifications_list": [
                            {
                                "search": "Kairo ist Hauptstadt.",
                                "replace": "Kairo ist die Hauptstadt von Ägypten.",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                "finish_reason": "STOP",
            },
        ]
    )

    with patch("backend.services.llm_gateway.reason_and_respond", gateway_mock), patch(
        "keyring.get_password", return_value="dummy_api_key"
    ):
        response_audit = test_client.post(
            "/api/chat",
            json={
                "prompt": "SYSTEM-INSTRUKTION FÜR DATEI-UPLOAD 'aegypten.pdf'",
                "provider": "openai",
                "model": "gpt-5.4-nano",
                "chat_id": chat_id,
            },
            headers=headers,
        )
        assert response_audit.status_code == 200

        response_factcheck = test_client.post(
            "/api/chat",
            json={
                "prompt": "1",
                "provider": "openai",
                "model": "gpt-5.4-nano",
                "chat_id": chat_id,
            },
            headers=headers,
        )

    assert response_factcheck.status_code == 200
    payload = response_factcheck.json()
    assert payload.get("ui_command", {}).get("ui_action") == "refresh_documents"
    refreshed_doc = db_session.query(Document).filter(Document.id == doc.id).first()
    assert refreshed_doc is not None
    assert refreshed_doc.audit_status == "warning"
    assert "knowledge.query" in captured_tool_names
    assert "knowledge.edit_pdf" in captured_tool_names


@pytest.mark.asyncio
async def test_journey_b_security_bypass_then_policy_rearms(
    test_client,
    db_session,
    isolated_workspace,
    monkeypatch,
):
    first_file = isolated_workspace / "first.txt"
    first_file.write_text("delete me", encoding="utf-8")
    second_file = isolated_workspace / "second.txt"
    second_file.write_text("delete me too", encoding="utf-8")

    headers = _auth_headers()
    chat_create = test_client.post("/api/chats", json={"title": "Journey B"}, headers=headers)
    assert chat_create.status_code == 200
    chat_id = chat_create.json()["id"]

    captured_gateway_bypass = []
    captured_executor_bypass = []

    original_execute_tool_calls = ToolExecutor.execute_tool_calls

    async def _capture_execute_tool_calls(self, tool_calls, bypass_policy=False):
        captured_executor_bypass.append(bool(bypass_policy))
        return await original_execute_tool_calls(self, tool_calls, bypass_policy=bypass_policy)

    monkeypatch.setattr(ToolExecutor, "execute_tool_calls", _capture_execute_tool_calls)
    monkeypatch.setattr("backend.services.chat_orchestrator.ChatOrchestrator._trigger_fact_extraction", lambda *args, **kwargs: None)

    gateway_mock = AsyncMock(
        side_effect=[
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "jb-delete-1",
                        "function": {
                            "name": "filesystem.delete_file",
                            "arguments": json.dumps({"path": "first.txt"}),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "Sicherheitsabfrage: 1 einmalig, 2 immer, 3 abbrechen.",
                "finish_reason": "STOP",
            },
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "jb-delete-2",
                        "function": {
                            "name": "filesystem.delete_file",
                            "arguments": json.dumps({"path": "first.txt"}),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "Datei gelöscht.",
                "finish_reason": "STOP",
            },
            {
                "type": "tool_code",
                "tool_calls": [
                    {
                        "id": "jb-delete-3",
                        "function": {
                            "name": "filesystem.delete_file",
                            "arguments": json.dumps({"path": "second.txt"}),
                        },
                    }
                ],
                "raw_assistant_response": {"role": "assistant", "content": "tool"},
            },
            {
                "type": "text",
                "text": "Erneute Sicherheitsabfrage erforderlich.",
                "finish_reason": "STOP",
            },
        ]
    )

    async def _capture_gateway(**kwargs):
        captured_gateway_bypass.append(bool(kwargs.get("bypass_policy")))
        return await gateway_mock(**kwargs)

    with patch("backend.services.llm_gateway.reason_and_respond", _capture_gateway), patch(
        "keyring.get_password", return_value="dummy_api_key"
    ):
        blocked = test_client.post(
            "/api/chat",
            json={
                "prompt": "Lösche first.txt",
                "provider": "openai",
                "model": "gpt-5.4-nano",
                "chat_id": chat_id,
            },
            headers=headers,
        )
        assert blocked.status_code == 200
        assert first_file.exists()

        pending_key = f"policy_pending:{chat_id}"
        pending = db_session.query(AppState).filter(AppState.key == pending_key).first()
        assert pending is not None

        allowed_once = test_client.post(
            "/api/chat",
            json={
                "prompt": "1",
                "provider": "openai",
                "model": "gpt-5.4-nano",
                "chat_id": chat_id,
            },
            headers=headers,
        )
        assert allowed_once.status_code == 200
        assert not first_file.exists()

        third_try = test_client.post(
            "/api/chat",
            json={
                "prompt": "Lösche second.txt",
                "provider": "openai",
                "model": "gpt-5.4-nano",
                "chat_id": chat_id,
            },
            headers=headers,
        )
        assert third_try.status_code == 200

    assert second_file.exists(), "Policy-Bypass darf nicht in den nächsten Turn leaken."
    assert True in captured_gateway_bypass, "Bypass muss mindestens einmal an Gateway gehen."
    assert True in captured_executor_bypass, "Bypass muss mindestens einmal an Executor gehen."
    assert captured_executor_bypass[-1] is False, "Nach One-Time muss Policy wieder aktiv sein."


@pytest.mark.asyncio
async def test_journey_c_wissens_suche_magic_returns_doc_id_and_page(
    test_client,
    db_session,
    isolated_workspace,
):
    source_pdf = isolated_workspace / "kairo_guide.pdf"
    source_pdf.write_text("Kairo liegt am Nil.", encoding="utf-8")
    doc = crud.create_document(db_session, filename="kairo_guide.pdf", file_path=str(source_pdf))

    class _FakeCollection:
        def query(self, query_texts, n_results, include):
            return {
                "documents": [["Kairo liegt am Nil.", "Alexandria liegt am Mittelmeer."]],
                "metadatas": [
                    [
                        {"document_id": doc.id, "page": 7},
                        {"document_id": doc.id, "page": 2},
                    ]
                ],
            }

    with patch("backend.services.rag_manager._get_or_create_collection", return_value=_FakeCollection()):
        response = test_client.get(
            "/api/rag/search-ids",
            params={"query": "Kairo"},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    payload = response.json()
    assert {"id": doc.id, "page": 7} in payload
    assert all(item["page"] != 2 for item in payload), "Nur Inhalte mit Query-Treffer dürfen zurückkommen."
