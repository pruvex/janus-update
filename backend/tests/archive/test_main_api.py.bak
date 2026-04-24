import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
import json

from backend.data.schemas import AgentSpec
from backend.dependencies import api_key_auth
from backend.main import app
from backend.api.routers.chat import get_orchestrator
from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.orchestrator.schemas import ExecutionResponse

# Client Fixture (falls nicht in conftest, hier zur Sicherheit, aber conftest ist besser)
# Wir nutzen den aus conftest via Parameter


@pytest.fixture(autouse=True)
def bypass_api_key_auth_for_main_api_tests():
    app.dependency_overrides[api_key_auth] = lambda: None
    yield
    app.dependency_overrides.pop(api_key_auth, None)

def test_chat_text_response(test_client, db_session):
    # Create a chat to get a valid chat_id
    chat_response = test_client.post("/api/chats", json={"title": "Test Chat"})
    assert chat_response.status_code == 200
    chat_id = chat_response.json()["id"]

    with patch(
        "backend.services.orchestrator.execution_engine.OrchestratorExecutionEngine.run_agent_factory",
        new_callable=AsyncMock,
    ) as mock_run_agent_factory:
        mock_run_agent_factory.return_value = ExecutionResponse(
            text="Mocked response.",
            agent_payload={"name": "Atomic Agent", "trace_id": "trace-1", "required_skills": ["system.country_info"]},
            tool_calls=[],
            is_agent_flow=True,
        )

        # FIX: Wir müssen auch sicherstellen, dass er NICHT in den Image-Zweig abbiegt
        with patch("backend.utils.intent_classifier._is_image_generation_request", return_value=False):
            response = test_client.post(
                "/api/chat",
                json={
                    "prompt": "Hello",
                    "provider": "openai",
                    "model": "gpt-5.4-nano",  # Using internal model alias
                    "chat_id": chat_id,
                },
            )
            assert response.status_code == 200
            payload = ExecutionResponse.model_validate(response.json())
            assert payload.text == "Mocked response."
            assert payload.sender == "model"


@pytest.mark.parametrize(
    "provider, model", [("openai", "gpt-5.4-nano"), ("gemini", "gemini-3-flash-preview")]
)
def test_chat_image_shortcut(test_client, db_session, provider, model):
    # Create a chat to get a valid chat_id
    chat_response = test_client.post("/api/chats", json={"title": "Test Image Chat"})
    assert chat_response.status_code == 200
    chat_id = chat_response.json()["id"]

    with patch(
        "backend.services.chat_orchestrator.ChatOrchestrator.handle_chat_request",
        new_callable=AsyncMock,
    ) as mock_handle:
        mock_handle.return_value = {
            "sender": "model",
            "text": "Bild wurde erfolgreich generiert.",
            "image_url": f"/user_images/{provider}_test.png",
        }

        response = test_client.post(
            "/api/chat",
            json={
                "prompt": f"zeichne ein bild von einem frosch mit {provider}",
                "provider": provider,
                "model": model,
                "chat_id": chat_id,
            },
        )

        assert response.status_code == 200
        payload = ExecutionResponse.model_validate(response.json())
        assert "Bild wurde erfolgreich" in payload.text
        assert payload.image_url == f"/user_images/{provider}_test.png"
        assert payload.sender == "model"
        mock_handle.assert_called_once()

def test_chat_budget_exceeded(test_client, db_session):
    chat_response = test_client.post("/api/chats", json={"title": "Budget Chat"})
    assert chat_response.status_code == 200
    chat_id = chat_response.json()["id"]

    with patch(
        "backend.services.chat_orchestrator.ChatOrchestrator.handle_chat_request",
        new_callable=AsyncMock,
    ) as mock_handle:
        mock_handle.side_effect = HTTPException(status_code=429, detail="Budget exceeded")

        response = test_client.post(
            "/api/chat",
            json={
                "prompt": "Bitte antworte.",
                "provider": "openai",
                "model": "gpt-5.4-nano",
                "chat_id": chat_id,
            },
        )

    assert response.status_code == 500
    assert "Budget exceeded" in response.json().get("detail", "")


def test_chat_api_wired_to_atomic_loop_and_single_skill_clamping(test_client, db_session):
    chat_response = test_client.post("/api/chats", json={"title": "Atomic Wiring"})
    assert chat_response.status_code == 200
    chat_id = chat_response.json()["id"]

    planner_round = {"idx": 0}
    observed_allowed_skill_ids = []

    async def _fake_plan(*_args, **_kwargs):
        planner_round["idx"] += 1
        if planner_round["idx"] == 1:
            skills = ["system.country_info", "system.routing"]
        elif planner_round["idx"] == 2:
            skills = ["system.routing"]
        else:
            skills = []
        return AgentSpec(
            name="Atomic Planner",
            goal="Route with country context",
            required_skills=skills,
            instructions="Plane sequentiell",
            max_iterations=3,
        )

    async def _fake_reason_and_respond(*_args, **kwargs):
        observed_allowed_skill_ids.append(list(kwargs.get("allowed_skill_ids") or []))
        return {
            "type": "text",
            "text": "TASK_COMPLETE",
            "usage": {},
            "cost": {},
            "tool_limit_reached": True,
        }

    with patch(
        "backend.services.agent_planner.AgentPlanner.plan",
        new_callable=AsyncMock,
        side_effect=_fake_plan,
    ), patch(
        "backend.services.agent_runtime.llm_gateway.reason_and_respond",
        new_callable=AsyncMock,
        side_effect=_fake_reason_and_respond,
    ), patch(
        "backend.services.orchestrator.execution_engine.OrchestratorExecutionEngine.run_tool_loop",
        new_callable=AsyncMock,
    ) as legacy_loop_mock, patch(
        "backend.services.chat_orchestrator.ChatOrchestrator._trigger_fact_extraction",
        return_value=None,
    ):
        response = test_client.post(
            "/api/chat",
            json={
                "prompt": "Plane mir Japan mit Distanz Tokio-Kyoto",
                "provider": "openai",
                "model": "gpt-5.4-nano",
                "chat_id": chat_id,
            },
        )

    assert response.status_code == 200
    payload = ExecutionResponse.model_validate(response.json())
    assert isinstance(payload.text, str) and payload.text.strip()
    assert legacy_loop_mock.await_count == 0
    assert observed_allowed_skill_ids[:2] == [["system.country_info"], ["system.routing"]]


def test_orchestrator_kpi_dashboard_endpoint_returns_payload(test_client):
    response = test_client.get("/api/orchestrator/kpis")
    assert response.status_code == 200
    payload = response.json()
    assert "period" in payload
    assert "providers" in payload
    assert "retry_paths" in payload


def _build_test_orchestrator(db_session, tmp_path):
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


@pytest.mark.parametrize(
    "user_choice,mock_side_effects,expected_text_prefix,expected_calls",
    [
        (
            "1",
            [
                [
                    {
                        "role": "tool",
                        "name": "filesystem.delete_file",
                        "content": json.dumps({"status": "ok", "data": {"deleted": True}}),
                    }
                ]
            ],
            "✅",
            1,
        ),
        (
            "2",
            [
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
            ],
            "✅",
            2,
        ),
        (
            "3",
            [],
            "Okay, ich habe die Aktion abgebrochen.",
            0,
        ),
    ],
)
def test_chat_api_policy_choices_resume_deterministically(test_client, db_session, tmp_path, monkeypatch, user_choice, mock_side_effects, expected_text_prefix, expected_calls):
    chat_response = test_client.post("/api/chats", json={"title": f"Policy {user_choice}"})
    assert chat_response.status_code == 200
    chat_id = chat_response.json()["id"]

    orchestrator = _build_test_orchestrator(db_session, tmp_path)
    orchestrator._set_policy_pending_data(
        chat_id,
        {
            "pending": True,
            "blocked_skill_id": "filesystem.delete_file",
            "blocked_arguments": {"path": "danger.txt"},
            "resolved_name": "delete_file",
        },
    )

    monkeypatch.setitem(app.dependency_overrides, get_orchestrator, lambda: orchestrator)
    execute_mock = AsyncMock(side_effect=mock_side_effects)
    monkeypatch.setattr("backend.services.chat_orchestrator.ToolExecutor.execute_tool_calls", execute_mock)

    response = test_client.post(
        "/api/chat",
        json={
            "prompt": user_choice,
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "chat_id": chat_id,
            "api_key": "dummy",
        },
    )

    assert response.status_code == 200
    payload = ExecutionResponse.model_validate(response.json())
    assert payload.text.startswith(expected_text_prefix)
    assert execute_mock.await_count == expected_calls
    assert orchestrator._get_policy_pending_data(chat_id) is None

    if user_choice == "1":
        first_call = execute_mock.await_args_list[0].args[0]
        assert first_call[0]["function"]["name"] == "filesystem.delete_file"
    if user_choice == "2":
        first_call = execute_mock.await_args_list[0].args[0]
        second_call = execute_mock.await_args_list[1].args[0]
        assert json.loads(first_call[0]["function"]["arguments"])["skill_id"] == "filesystem.delete_file"
        assert second_call[0]["function"]["name"] == "filesystem.delete_file"
