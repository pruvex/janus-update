# backend/tests/test_orchestrator_logic.py

from unittest.mock import MagicMock, patch

import pytest
from backend.data import schemas
from backend.services import chat_orchestrator
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def orchestrator_instance(mock_db_session):
    """Fixture to create an instance of ChatOrchestrator with mocked dependencies."""
    with (
        patch("backend.services.chat_orchestrator.ChatOrchestrator._load_config", return_value={}),
        patch("backend.services.chat_orchestrator.ChatOrchestrator._save_config"),
        patch(
            "backend.services.chat_orchestrator.ChatOrchestrator._load_personalities",
            return_value=[],
        ),
        patch(
            "backend.services.chat_orchestrator.ChatOrchestrator._check_budget_and_raise_if_exceeded"
        ),
    ):
        orchestrator = chat_orchestrator.ChatOrchestrator(
            db=mock_db_session,
            context_manager=MagicMock(),
            model_catalog={"gpt-4o-mini": {}},
            config_file_path="dummy",
            template_config_file_path="dummy",
            personalities_file_path="dummy",
            template_personalities_file_path="dummy",
        )
        yield orchestrator


@pytest.mark.skip(reason="Orchestrator logic for skipping facts needs review")
@pytest.mark.asyncio
@patch("backend.data.crud.get_messages_by_chat_id", return_value=[])
@patch("backend.data.crud.create_message")
@patch("keyring.get_password", return_value="dummy_api_key")
@patch("backend.utils.intent_classifier.is_greeting", return_value=False)
@patch("backend.services.llm_gateway.reason_and_respond")
@patch("asyncio.create_task")
async def test_fact_extraction_skipped_when_core_memory_tool_used(
    mock_create_task,
    mock_reason_and_respond,
    mock_is_greeting,
    mock_keyring,
    mock_create_message,
    mock_get_messages,
    orchestrator_instance,
):
    """
    Ensures that background fact extraction is SKIPPED when the save_core_memory_fact was used.
    """
    pass


@pytest.mark.skip(reason="Refactoring: Test needs update for new Orchestrator")
@pytest.mark.asyncio
@patch("backend.data.crud.get_messages_by_chat_id", return_value=[])
@patch("backend.data.crud.create_message")
@patch("keyring.get_password", return_value="dummy_api_key")
@patch("backend.utils.intent_classifier.is_greeting", return_value=False)
@patch("backend.services.llm_gateway.reason_and_respond")
@patch("asyncio.create_task")
async def test_fact_extraction_called_when_no_core_memory_tool_used(
    mock_create_task,
    mock_reason_and_respond,
    mock_is_greeting,
    mock_keyring,
    mock_create_message,
    mock_get_messages,
    orchestrator_instance,
):
    """
    Ensures that background fact extraction IS CALLED for a normal conversation.
    """
    # ARRANGE
    mock_reason_and_respond.return_value = {
        "type": "text",  # Simulate a simple text response
        "text": "Das ist interessant.",
        "usage": {},
        "cost": {},
    }

    chat_request = schemas.ChatRequest(
        chat_id=1,
        content=[schemas.ContentPart(type="text", text="Ich komme aus Deutschland.")],
        provider="openai",
        model="gpt-4o-mini",
    )

    # ACT
    await orchestrator_instance.handle_chat_request(chat_request)

    # ASSERT
    # Check if at least one of the created tasks was for `extract_and_save_fact`
    was_extraction_called = any(
        call.args[0].__qualname__ == "extract_and_save_fact"
        for call in mock_create_task.call_args_list
    )
    assert was_extraction_called, "Fact extraction SHOULD have been called."
