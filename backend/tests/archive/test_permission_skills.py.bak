import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.data import crud, schemas
from backend.data.models import SkillTelemetry
from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.permission_service import grant_permission, revoke_permission
from backend.services.policy_engine import PolicyEngine
from backend.services.tool_executor import ToolExecutor


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


@pytest.mark.parametrize("requested_skill", ["filesystem.delete_file", "delete_file"])
def test_grant_permission_returns_skill_response_contract_and_normalizes_targets(db_session, assert_skill_response_contract, requested_skill):
    payload = grant_permission(skill_id=requested_skill, db=db_session)
    assert_skill_response_contract(payload)
    assert payload["status"] == "ok"
    assert payload["data"]["skill_id"] == "filesystem.delete_file"
    assert PolicyEngine.has_permanent_permission("filesystem.delete_file", db_session) is True


def test_grant_permission_blocks_meta_skill_escalation(db_session, assert_skill_response_contract):
    payload = grant_permission(skill_id="system.grant_permission", db=db_session)
    assert_skill_response_contract(payload)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "PERMISSION_GRANT_NOT_ALLOWED"


@pytest.mark.parametrize("requested_skill", ["filesystem.delete_file", "delete_file"])
def test_revoke_permission_returns_skill_response_contract(db_session, assert_skill_response_contract, requested_skill):
    PolicyEngine.grant_permanent_permission("filesystem.delete_file", db_session)
    payload = revoke_permission(skill_id=requested_skill, db=db_session)
    assert_skill_response_contract(payload)
    assert payload["status"] == "ok"
    assert payload["data"]["skill_id"] == "filesystem.delete_file"
    assert PolicyEngine.has_permanent_permission("filesystem.delete_file", db_session) is False


@pytest.mark.asyncio
async def test_permission_skill_rate_limit_exceeded_for_second_call_in_same_turn():
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    results = await executor.execute_tool_calls(
        [
            {
                "id": "grant-1",
                "function": {
                    "name": "system.grant_permission",
                    "arguments": json.dumps({"skill_id": "communication.read_email"}),
                },
            },
            {
                "id": "grant-2",
                "function": {
                    "name": "system.grant_permission",
                    "arguments": json.dumps({"skill_id": "communication.send_email"}),
                },
            },
        ]
    )

    payload_first = json.loads(results[0]["content"])
    payload_second = json.loads(results[1]["content"])
    assert payload_first["status"] in {"ok", "error"}
    assert payload_second["status"] == "error"
    assert payload_second["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_permission_grant_logs_success_telemetry(db_session):
    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
        additional_context={"trace_id": "trace-permission-ok", "chat_id": 7},
    )

    result = await executor.execute_tool_call(
        "system.grant_permission",
        {"skill_id": "filesystem.delete_file"},
    )

    payload = json.loads(result["content"])
    assert payload["status"] == "ok"
    rows = db_session.query(SkillTelemetry).filter(SkillTelemetry.trace_id == "trace-permission-ok").all()
    assert len(rows) == 1
    assert rows[0].skill_id == "system.grant_permission"
    assert rows[0].success is True
    assert rows[0].error_code is None
    assert rows[0].arguments_json["skill_id"] == "filesystem.delete_file"


@pytest.mark.asyncio
async def test_permission_grant_logs_error_telemetry_for_meta_skill_block(db_session):
    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
        additional_context={"trace_id": "trace-permission-error", "chat_id": 8},
    )

    result = await executor.execute_tool_call(
        "system.grant_permission",
        {"skill_id": "system.grant_permission"},
    )

    payload = json.loads(result["content"])
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "PERMISSION_GRANT_NOT_ALLOWED"
    rows = db_session.query(SkillTelemetry).filter(SkillTelemetry.trace_id == "trace-permission-error").all()
    assert len(rows) == 1
    assert rows[0].skill_id == "system.grant_permission"
    assert rows[0].success is False
    assert rows[0].error_code == "PERMISSION_GRANT_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_orchestrator_always_allow_resumes_blocked_skill_deterministically(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Policy Resume")
    orchestrator_instance._set_policy_pending_data(
        chat.id,
        {
            "pending": True,
            "blocked_skill_id": "filesystem.delete_file",
            "blocked_arguments": {"path": "danger.txt"},
            "resolved_name": "delete_file",
        },
    )

    execute_tool_calls = AsyncMock(
        side_effect=[
            [
                {
                    "role": "tool",
                    "name": "system.grant_permission",
                    "content": json.dumps({"status": "ok", "data": {"skill_id": "filesystem.delete_file"}}),
                }
            ],
            [
                {
                    "role": "tool",
                    "name": "filesystem.delete_file",
                    "content": json.dumps({"status": "ok", "data": {"deleted": True}}),
                }
            ],
        ]
    )
    monkeypatch.setattr("backend.services.chat_orchestrator.ToolExecutor.execute_tool_calls", execute_tool_calls)

    request = schemas.ChatRequest(
        prompt="2",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    response = await orchestrator_instance.handle_chat_request(request)

    assert response.text.startswith("✅")
    assert execute_tool_calls.await_count == 2
    first_call = execute_tool_calls.await_args_list[0].args[0]
    second_call = execute_tool_calls.await_args_list[1].args[0]
    assert json.loads(first_call[0]["function"]["arguments"])["skill_id"] == "filesystem.delete_file"
    assert second_call[0]["function"]["name"] == "filesystem.delete_file"
    assert orchestrator_instance._get_policy_pending_data(chat.id) is None
