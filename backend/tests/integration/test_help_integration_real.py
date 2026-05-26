"""Real-Orchestrator Integration Test for Help Fast-Path (TASK-069.8).

This test verifies that the real ChatOrchestrator (not mocks) correctly
triggers the Help Fast-Path for capability overview queries, skipping
LLM generation entirely.

Test approach:
- Initialize a real ChatOrchestrator instance with real CapabilityRegistry and HelpSkill
- Mock only the LLM provider (BaseProvider) to prevent network calls
- Call orchestrator.handle_chat_request("Was kannst du?", ...)
- Assertions:
  - skip_llm_generation == True
  - Output starts with "## Das kann ich aktuell"
  - LLM provider call_count == 0
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from backend.data import schemas
from backend.services.chat_orchestrator import ChatOrchestrator


@pytest.mark.asyncio
async def test_capability_overview_real_orchestrator_fast_path(db_session, tmp_path, monkeypatch):
    """
    TASK-069.8: Verify real ChatOrchestrator triggers Help Fast-Path for "Was kannst du?".

    This test uses a real ChatOrchestrator instance (not mocks) to verify that:
    1. The Fast-Path logic correctly detects the capability_overview intent
    2. The LLM generation is skipped (skip_llm_generation == True)
    3. The response is generated deterministically by HelpSkill
    4. No LLM provider call is made (network safety)
    """
    # Setup config files (required by ChatOrchestrator)
    template_config = tmp_path / "template_config.json"
    template_config.write_text(json.dumps({"active_personality": "ai_assistant"}), encoding="utf-8")
    template_personalities = tmp_path / "template_personalities.json"
    template_personalities.write_text(
        json.dumps([{"id": "ai_assistant", "prompt": "Du bist Janus."}], ensure_ascii=False),
        encoding="utf-8",
    )

    # Create real ChatOrchestrator with real CapabilityRegistry and HelpSkill
    orchestrator = ChatOrchestrator(
        db=db_session,
        context_manager=MagicMock(),
        model_catalog={"gpt-5.4-nano": {}},
        config_file_path=str(tmp_path / "config.json"),
        template_config_file_path=str(template_config),
        personalities_file_path=str(tmp_path / "personalities.json"),
        template_personalities_file_path=str(template_personalities),
    )

    # Mock the LLM gateway to prevent network calls
    # This mock should NEVER be called if Fast-Path works correctly
    llm_gateway_mock = AsyncMock(
        return_value={
            "type": "text",
            "text": "This should never be returned because Fast-Path skips LLM",
            "raw_assistant_response": {"role": "assistant", "content": "should not be called"},
        }
    )
    monkeypatch.setattr("backend.services.llm_gateway.reason_and_respond", llm_gateway_mock)

    # Monkeypatch fact extraction to avoid side effects
    monkeypatch.setattr(orchestrator, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    # Create a chat for the request
    from backend.data import crud
    chat = crud.create_chat(db_session, title="Help Test")

    # Request that should trigger Help Fast-Path
    request = schemas.ChatRequest(
        prompt="Was kannst du?",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    # Call the real orchestrator
    response = await orchestrator.handle_chat_request(request)

    # CRITICAL ASSERTIONS

    # 1. LLM provider was NOT called (Fast-Path skipped LLM generation)
    assert llm_gateway_mock.call_count == 0, \
        f"LLM gateway was called {llm_gateway_mock.call_count} times, expected 0 (Fast-Path should skip LLM)"

    # 2. Response contains the deterministic HelpSkill output
    response_text = response.get("text", "")
    assert response_text.startswith("## Das kann ich aktuell"), \
        f"Response should start with '## Das kann ich aktuell', got: {response_text[:100]}"

    # 3. Response contains verified capabilities (not generic LLM text)
    assert "Dateien" in response_text or "Erinnerungen" in response_text or "Kalender" in response_text, \
        f"Response should contain verified capabilities, got: {response_text[:200]}"

    # 4. Response does NOT contain the mock LLM text
    assert "This should never be returned" not in response_text, \
        "Response should not contain mock LLM text (Fast-Path failed)"


@pytest.mark.asyncio
async def test_capability_overview_fast_path_fails_without_intent_logic(db_session, tmp_path, monkeypatch):
    """
    TASK-069.8: Negative test - verify test fails if Fast-Path logic is disabled.

    This test intentionally disables the Fast-Path logic to prove that
    the test would fail without it. This validates that the positive test
    actually proves the Fast-Path is working.
    """
    from backend.data import crud

    # Setup config files
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

    # Mock LLM gateway (will be called because we disable Fast-Path)
    llm_gateway_mock = AsyncMock(
        return_value={
            "type": "text",
            "text": "LLM response (Fast-Path disabled)",
            "raw_assistant_response": {"role": "assistant", "content": "LLM response"},
        }
    )
    monkeypatch.setattr("backend.services.llm_gateway.reason_and_respond", llm_gateway_mock)

    # Monkeypatch fact extraction
    monkeypatch.setattr(orchestrator, "_trigger_fact_extraction", lambda *args, **kwargs: None)

    # INTENTIONALLY DISABLE Fast-Path logic by making _resolve_help_intent return None
    original_resolve = orchestrator._resolve_help_intent
    monkeypatch.setattr(orchestrator, "_resolve_help_intent", lambda intents: None)

    chat = crud.create_chat(db_session, title="Help Test Negative")
    request = schemas.ChatRequest(
        prompt="Was kannst du?",
        chat_id=chat.id,
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    response = await orchestrator.handle_chat_request(request)

    # With Fast-Path disabled, LLM SHOULD be called
    assert llm_gateway_mock.call_count > 0, \
        "With Fast-Path disabled, LLM gateway should have been called"

    # Response should be the LLM response, not HelpSkill output
    response_text = response.get("text", "")
    assert "LLM response" in response_text, \
        "With Fast-Path disabled, response should be from LLM"
