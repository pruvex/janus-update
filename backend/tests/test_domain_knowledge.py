import json
from unittest.mock import MagicMock

import pytest

from backend.services.tool_executor import ToolExecutor
from backend.services.tool_manager import tool_manager


@pytest.mark.asyncio
async def test_knowledge_query_returns_metadata_contract(monkeypatch, assert_skill_response_contract):
    class _FakeCollection:
        def query(self, query_texts, n_results, where=None):
            return {
                "documents": [["Berlin ist die Hauptstadt."]],
                "metadatas": [[{"filename": "wissen.pdf", "page": 3}]],
            }

    monkeypatch.setattr("backend.services.rag_manager._get_or_create_collection", lambda _name: _FakeCollection())

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call("knowledge.query", {"query_text": "Hauptstadt"})
    payload = json.loads(result["content"])
    assert_skill_response_contract(payload)
    assert payload["status"] == "ok"
    assert payload["data"]["hit_count"] == 1
    assert payload["data"]["hits"][0]["source"] == "wissen.pdf"
    assert payload["data"]["hits"][0]["page"] == 3


@pytest.mark.asyncio
async def test_knowledge_edit_pdf_success_contract(monkeypatch, assert_skill_response_contract):
    async def _fake_edit_pdf_text_in_place(**_kwargs):
        return {
            "status": "ok",
            "data": {
                "result": "Erfolg: 1 Stellen bereinigt.",
                "quality_gate": "passed",
            },
        }

    tool_def = tool_manager.get_tool("edit_pdf_text_in_place")
    assert tool_def is not None
    monkeypatch.setattr(tool_def, "func", _fake_edit_pdf_text_in_place)

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call(
        "knowledge.edit_pdf",
        {
            "original_filename": "audit.pdf",
            "modifications": [{"search": "alt", "replace": "neu"}],
        },
    )
    payload = json.loads(result["content"])
    assert_skill_response_contract(payload)
    assert payload["status"] == "ok"
    assert payload["data"]["quality_gate"] == "passed"


@pytest.mark.asyncio
async def test_knowledge_edit_pdf_not_found_error_contract(monkeypatch, assert_skill_response_contract):
    async def _fake_edit_pdf_text_in_place(**_kwargs):
        return {
            "status": "error",
            "error": {
                "code": "search_terms_missing",
                "message": "Einige Suchtexte wurden nicht gefunden.",
            },
        }

    tool_def = tool_manager.get_tool("edit_pdf_text_in_place")
    assert tool_def is not None
    monkeypatch.setattr(tool_def, "func", _fake_edit_pdf_text_in_place)

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call(
        "knowledge.edit_pdf",
        {
            "original_filename": "audit.pdf",
            "modifications": [{"search": "nicht-da", "replace": "neu"}],
        },
    )
    payload = json.loads(result["content"])
    assert_skill_response_contract(payload)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "search_terms_missing"


@pytest.mark.asyncio
async def test_knowledge_hardened_edit_success_contract(monkeypatch, assert_skill_response_contract):
    async def _fake_internal(skill_id, args):
        if skill_id == "filesystem.create_directory":
            return {"status": "ok", "data": {"result": "dir created"}}
        if skill_id == "filesystem.move_file":
            return {"status": "ok", "data": {"result": "moved"}}
        if skill_id == "knowledge.edit_pdf":
            return {"status": "ok", "data": {"quality_gate": "passed"}}
        return {"status": "error", "error": {"code": "UNKNOWN_INTERNAL"}}

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )
    monkeypatch.setattr("backend.services.knowledge_composite.shutil.copy2", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(executor, "call_internal_skill", _fake_internal)

    result = await executor.execute_tool_call(
        "knowledge.hardened_edit",
        {
            "original_filename": "workspace/demo.pdf",
            "modifications": [{"search": "alt", "replace": "neu"}],
            "backup_directory": "workspace/backups",
        },
    )

    payload = json.loads(result["content"])
    assert_skill_response_contract(payload)
    assert payload["status"] == "ok"
    assert payload["data"]["operation"] == "knowledge.hardened_edit"
