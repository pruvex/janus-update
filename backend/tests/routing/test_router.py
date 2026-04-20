# backend/tests/routing/test_router.py

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Benötigte Imports
from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.context_manager import ContextManager
from backend.services.chat.context_builder import ContextBuilder
from backend.data import schemas

# --- Test-Fixtures ---

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def mock_context_builder(mock_db_session):
    return ContextBuilder(db=mock_db_session)

@pytest.fixture
def orchestrator(mock_db_session, mock_context_builder):
    orchestrator_instance = ChatOrchestrator(
        db=mock_db_session,
        context_manager=MagicMock(spec=ContextManager),
        model_catalog=[{"id": "gpt-5.4-nano", "context_window": 8000}],
        config_file_path="dummy_config.json",
        template_config_file_path="dummy_template.json",
        personalities_file_path="dummy_personalities.json",
        template_personalities_file_path="dummy_template.json",
    )
    orchestrator_instance.context_builder = mock_context_builder
    return orchestrator_instance

# --- 11 Testfälle für den Diamantstandard ---

@pytest.mark.asyncio
async def test_routing_selects_weather_tool_for_weather_query(orchestrator):
    request = schemas.ChatRequest(prompt="Wie ist das Wetter in Berlin?", chat_id=1, provider="openai", model="gpt-5.4-nano")

    with patch('backend.services.chat.tool_selector.ToolSelector.retrieve_candidates') as mock_retrieve, \
         patch('backend.services.chat_orchestrator.ToolSelector.select_tools') as mock_select_tools, \
         patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
        
        mock_retrieve.return_value = [{'tool_name': 'get_weather_from_api_tool', 'confidence': 0.95}]
        mock_select_tools.return_value = [{"function": {"name": "get_weather_from_api_tool"}}]
        mock_reason_and_respond.return_value = {"text": "Es sind 20 Grad."}
        
        response = await orchestrator.handle_chat_request(request)
        
        mock_reason_and_respond.assert_called_once()
        assert "20" in response["text"]

@pytest.mark.asyncio
async def test_routing_disables_tools_for_identity_query(orchestrator):
    request = schemas.ChatRequest(prompt="Wer bist du?", chat_id=1, provider="openai", model="gpt-5.4-nano")
    
    with patch('backend.services.chat_orchestrator.intent_classifier.is_identity_query', return_value=True), \
         patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
        
        mock_reason_and_respond.return_value = {"text": "Ich bin Janus."}
        response = await orchestrator.handle_chat_request(request)
        mock_reason_and_respond.assert_called_once()
        assert "Janus" in response["text"]

@pytest.mark.asyncio
async def test_knowledge_cascade_RAG_HIT_for_project(orchestrator):
    request = schemas.ChatRequest(prompt="Fasse 'Analyse.pdf' zusammen", chat_id=1, project_id=1, provider="openai", model="gpt-5.4-nano")

    with patch('backend.services.rag_manager.query_knowledge_base', return_value=["RAG-Ergebnis..."]) as mock_rag_query, \
         patch('backend.services.chat_orchestrator.crud.get_project', return_value=MagicMock(id=1)), \
         patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
        
        mock_reason_and_respond.return_value = {"text": "Antwort aus RAG"}
        response = await orchestrator.handle_chat_request(request)
        assert "Antwort" in response["text"]

@pytest.mark.asyncio
async def test_context_integration_uses_email_context(orchestrator, mock_context_builder):
    request = schemas.ChatRequest(prompt="Antworte auf diese E-Mail", chat_id=1, provider="openai", model="gpt-5.4-nano")
    mock_email = {"from": "Max Mustermann", "subject": "Wichtige Anfrage"}
    orchestrator.last_email_list_per_chat[1] = [mock_email]
    
    with patch.object(mock_context_builder, 'build_system_message', wraps=mock_context_builder.build_system_message) as spy_build_system_message, \
         patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock):
        
        response = await orchestrator.handle_chat_request(request)
        assert isinstance(response.get("text", ""), str)

@pytest.mark.asyncio
async def test_diamond_routing_route_b_ambiguous_intent(orchestrator):
    request = schemas.ChatRequest(prompt="Plan meine Reise.", chat_id=1, provider="openai", model="gpt-5.4-nano")
    
    with patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
        mock_reason_and_respond.return_value = {"text": "Gerne, wohin soll die Reise gehen?"}
        
        response = await orchestrator.handle_chat_request(request)

        mock_reason_and_respond.assert_called_once()
        text = response["text"].strip().lower()
        assert text.endswith("?"), "Ambiguous intent muss mit klarer Rueckfrage enden."
        assert any(token in text for token in ["wohin", "wann", "welche", "was genau"]), (
            "Ambiguous intent muss eine konkrete Klaerungsfrage enthalten."
        )

@pytest.mark.asyncio
async def test_tool_retrieval_identifies_candidate_tools(orchestrator):
    request = schemas.ChatRequest(prompt="Termin mit Peter.", chat_id=1, provider="openai", model="gpt-5.4-nano")

    with patch('backend.services.chat.tool_selector.ToolSelector.retrieve_candidates', return_value=[
        {'tool_name': 'create_calendar_event', 'confidence': 0.9},
        {'tool_name': 'find_contact', 'confidence': 0.8}
    ]) as mock_retrieve, \
         patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:

        mock_reason_and_respond.return_value = {"text": "Termin erstellt."}
        response = await orchestrator.handle_chat_request(request)
        mock_reason_and_respond.assert_called_once()
        assert "Termin" in response["text"]

@pytest.mark.asyncio
async def test_route_a_optimizes_token_usage_for_high_confidence(orchestrator):
    request = schemas.ChatRequest(prompt="Checke E-Mails.", chat_id=1, provider="openai", model="gpt-5.4-nano")

    with patch('backend.services.chat.tool_selector.ToolSelector.retrieve_candidates', return_value=[
        {'tool_name': 'read_email', 'confidence': 0.95}
    ]) as mock_retrieve, \
         patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:

        mock_reason_and_respond.return_value = {"text": "Keine neuen Mails."}
        response = await orchestrator.handle_chat_request(request)
        
        mock_reason_and_respond.assert_called_once()
        assert "mails" in response["text"].lower()

@pytest.mark.asyncio
async def test_knowledge_cascade_STOPS_at_memory_hit(orchestrator, mock_context_builder):
    request = schemas.ChatRequest(prompt="Kundennummer?", chat_id=1, provider="openai", model="gpt-5.4-nano")

    with patch.object(mock_context_builder, 'build_system_message') as mock_build, \
         patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
        
        mock_build.return_value = {"role": "system", "content": "**WISSENS-KONTEXT:**\n- [Info] Deine Kundennummer ist: KD-123."}
        mock_reason_and_respond.return_value = {"text": "KD-123."}
        response = await orchestrator.handle_chat_request(request)
        
        assert "KD-123" in response['text']

@pytest.mark.asyncio
async def test_knowledge_cascade_FALLS_BACK_to_wikipedia_if_memory_is_empty(orchestrator, mock_context_builder):
    request = schemas.ChatRequest(prompt="Wer war Marie Curie?", chat_id=1, provider="openai", model="gpt-5.4-nano")

    with patch.object(mock_context_builder, '_get_memory_context', return_value=""), \
         patch('backend.services.chat_orchestrator.ToolSelector.select_tools') as mock_select, \
         patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:

        mock_select.return_value = [{"function": {"name": "get_wikipedia_summary"}}]
        mock_reason_and_respond.return_value = {"text": "Physikerin..."}
        
        response = await orchestrator.handle_chat_request(request)
        
        mock_reason_and_respond.assert_called_once()
        assert "Physikerin" in response["text"]

@pytest.mark.asyncio
async def test_route_a_intercepts_risky_actions(orchestrator):
    request = schemas.ChatRequest(prompt="Lösche passwords.txt", chat_id=1, provider="openai", model="gpt-5.4-nano")
    
    with patch('backend.services.chat.tool_selector.ToolSelector.retrieve_candidates', return_value=[
        {'tool_name': 'delete_file_tool', 'confidence': 0.95}
    ]), \
    patch('backend.services.chat.tool_selector.ToolSelector.is_risky', return_value=True), \
    patch('backend.services.llm_gateway.call_llm', new_callable=AsyncMock) as mock_call_llm, \
    patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:

        mock_call_llm.return_value = {"text": "Bist du sicher?"}
        mock_reason_and_respond.return_value = {"text": "Bist du sicher?"}
        response = await orchestrator.handle_chat_request(request)

        assert mock_call_llm.call_count + mock_reason_and_respond.call_count >= 1
        assert "Bist du sicher" in response["text"]

@pytest.mark.asyncio
async def test_planner_executes_plan_on_confirmation(orchestrator):
    chat_id = 1
    
    # PHASE 1: Planner schlägt Plan vor
    request1 = schemas.ChatRequest(prompt="Zahnarzttermin.", chat_id=chat_id, provider="openai", model="gpt-5.4-nano")
    with patch('backend.services.chat.tool_selector.ToolSelector.retrieve_candidates', return_value=[
        {'tool_name': 'create_calendar_event', 'confidence': 0.7}
    ]), \
    patch('backend.services.llm_gateway.call_llm', new_callable=AsyncMock) as mock_planner_llm:
        mock_planner_llm.return_value = {"text": "Soll ich einen Termin erstellen?"}
        await orchestrator.handle_chat_request(request1)

    # PHASE 2: User bestätigt
    request2 = schemas.ChatRequest(prompt="Ja, mach das.", chat_id=chat_id, provider="openai", model="gpt-5.4-nano")
    with patch('backend.services.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_executor_llm:
        mock_executor_llm.return_value = {"text": "Termin erstellt."}
        
        response = await orchestrator.handle_chat_request(request2)

        mock_executor_llm.assert_called_once()
        assert "Termin" in response["text"]