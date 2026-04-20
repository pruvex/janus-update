import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.data import crud, schemas
from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.orchestrator.schemas import ExecutionResponse


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
        model_catalog={"gpt-5-nano": {}},
        config_file_path=str(tmp_path / "config.json"),
        template_config_file_path=str(template_config),
        personalities_file_path=str(tmp_path / "personalities.json"),
        template_personalities_file_path=str(template_personalities),
    )


@pytest.mark.asyncio
async def test_local_business_prompt_forces_system_local_business(orchestrator_instance, monkeypatch):
    chat = crud.create_chat(orchestrator_instance.db, title="Local Business Guardrail")

    run_tool_loop_mock = AsyncMock(
        return_value=ExecutionResponse(
            text="Hier sind 4 Restaurants.",
            raw_response={"text": "Hier sind 4 Restaurants."},
            tool_calls=[],
            is_agent_flow=False,
        )
    )
    monkeypatch.setattr(orchestrator_instance.execution_engine, "run_tool_loop", run_tool_loop_mock)
    monkeypatch.setattr(orchestrator_instance, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    request = schemas.ChatRequest(
        prompt="Janus, suche mir bitte exakt 4 gute italienische Restaurants in Berlin Prenzlauer Berg.",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5-nano",
        api_key="dummy",
    )

    await orchestrator_instance.handle_chat_request(request)

    assert run_tool_loop_mock.await_count == 1
    gateway_kwargs = run_tool_loop_mock.await_args.kwargs.get("gateway_kwargs") or {}
    assert gateway_kwargs.get("allowed_skill_ids") == ["system.local_business"]
