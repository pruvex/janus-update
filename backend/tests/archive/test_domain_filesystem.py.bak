import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services.tool_executor import ToolExecutor


@pytest.mark.asyncio
async def test_filesystem_crud_contract_flow(isolated_workspace, assert_skill_response_contract):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    rel_path = "notes.txt"

    create_res = await executor.execute_tool_call(
        "filesystem.create_file",
        {"path": rel_path, "content": "Hallo"},
    )
    create_payload = json.loads(create_res["content"])
    assert_skill_response_contract(create_payload)
    assert create_payload["status"] == "ok"

    read_res = await executor.execute_tool_call("filesystem.read_file", {"path": rel_path})
    read_payload = json.loads(read_res["content"])
    assert_skill_response_contract(read_payload)
    assert "Hallo" in read_payload["data"]["output"]

    list_res = await executor.execute_tool_call("filesystem.list_directory", {"path": "."})
    list_payload = json.loads(list_res["content"])
    assert_skill_response_contract(list_payload)
    assert list_payload["status"] == "ok"

    delete_res = await executor.execute_tool_call("filesystem.delete_file", {"path": rel_path})
    delete_payload = json.loads(delete_res["content"])
    assert_skill_response_contract(delete_payload)
    assert delete_payload["status"] == "ok"


@pytest.mark.asyncio
async def test_filesystem_denies_path_outside_workspace_contract(isolated_workspace, assert_skill_response_contract):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    outside_path = str(isolated_workspace.parent / "outside.txt")
    result = await executor.execute_tool_call("filesystem.read_file", {"path": outside_path})
    payload = json.loads(result["content"])
    assert_skill_response_contract(payload)
    assert payload["status"] == "error"
    assert payload["error"]["code"] in {"PERMISSION_DENIED", "MALFORMED_REQUEST", "OPERATION_FAILED"}


@pytest.mark.asyncio
async def test_filesystem_invalid_arguments_maps_to_contract(assert_skill_response_contract):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call("filesystem.delete_file", {"path": 123})
    payload = json.loads(result["content"])
    assert_skill_response_contract(payload)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "INVALID_ARGUMENTS"


@pytest.mark.asyncio
async def test_policy_blocks_filesystem_delete_before_handler_dispatch(monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "REQUIRE_CONSENT",
    )
    executor.execute_tool_call = AsyncMock()

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-policy",
                "function": {
                    "name": "filesystem.delete_file",
                    "arguments": '{"path":"notes.txt"}',
                },
            }
        ],
        bypass_policy=False,
    )

    assert executor.execute_tool_call.await_count == 0
    payload = json.loads(results[0]["content"])
    assert payload["status"] == "permission_required"
    assert payload["error"]["code"] == "USER_CONSENT_NEEDED"


@pytest.mark.asyncio
async def test_executor_returns_sandbox_violation_for_system_path(monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-sandbox",
                "function": {
                    "name": "filesystem.delete_file",
                    "arguments": '{"path":"C:/Windows/System32/forbidden.txt"}',
                },
            }
        ],
        bypass_policy=False,
    )

    payload = json.loads(results[0]["content"])
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "SANDBOX_VIOLATION"


def test_executor_allows_virtual_user_images_path_for_pdf_flow():
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    violation = executor._get_sandbox_violation(
        {
            "image_path": "/user_images/generated_image-14-03-26-16-22-22-356212-6895-14-03-26.png",
            "location": "Documents",
        }
    )
    assert violation is None


@pytest.mark.asyncio
async def test_executor_dry_run_delete_does_not_remove_file(isolated_workspace, monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    target_file = isolated_workspace / "dry_run_keep.txt"
    target_file.write_text("keep-me", encoding="utf-8")

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-dry-run",
                "function": {
                    "name": "filesystem.delete_file",
                    "arguments": '{"path":"dry_run_keep.txt"}',
                },
            }
        ],
        bypass_policy=False,
        dry_run=True,
    )

    payload = json.loads(results[0]["content"])
    assert payload["status"] == "dry_run_success"
    assert payload["data"]["skill_id"] == "filesystem.delete_file"
    assert Path(target_file).exists()
