import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.services.llm_gateway import reason_and_respond, _aggregate_usage, _aggregate_cost
from backend.services.tool_executor import ToolExecutor

@pytest.fixture
def mock_tool_executor():
    """Mock ToolExecutor for testing."""
    executor = AsyncMock(spec=ToolExecutor)
    executor.db = MagicMock()
    executor.api_key = "test_api_key"
    executor.provider = "test_provider"
    executor.model = "test_model"
    executor.additional_context = {}
    return executor

@pytest.fixture
def mock_context_manager():
    """Mock ContextManager for testing."""
    return MagicMock()

@pytest.fixture
def mock_db_session():
    """Mock SQLAlchemy Session for testing."""
    return MagicMock()

@pytest.mark.asyncio
async def test_aggregate_usage():
    usage1 = {"input_tokens": 10, "output_tokens": 5, "query_count": 1}
    usage2 = {"input_tokens": 20, "output_tokens": 10, "image_quality": "high"}
    
    aggregated = _aggregate_usage(usage1, usage2)
    assert aggregated == {"input_tokens": 30, "output_tokens": 15, "query_count": 1, "image_quality": "high"}

    usage3 = {"input_tokens": 5, "output_tokens": 2}
    aggregated_again = _aggregate_usage(aggregated, usage3)
    assert aggregated_again == {"input_tokens": 35, "output_tokens": 17, "query_count": 1, "image_quality": "high"}


@pytest.mark.asyncio
async def test_aggregate_cost():
    cost1 = {"total_cost": 0.05, "image_cost": 0.03}
    cost2 = {"total_cost": 0.10, "query_cost": 0.02}
    
    aggregated = _aggregate_cost(cost1, cost2)
    assert aggregated["total_cost"] == pytest.approx(0.15)
    assert aggregated["image_cost"] == pytest.approx(0.03)
    assert aggregated["query_cost"] == pytest.approx(0.02)

    cost3 = {"total_cost": 0.01}
    aggregated_again = _aggregate_cost(aggregated, cost3)
    assert aggregated_again["total_cost"] == pytest.approx(0.16)
    assert aggregated_again["image_cost"] == pytest.approx(0.03)
    assert aggregated_again["query_cost"] == pytest.approx(0.02)


@pytest.mark.asyncio
async def test_reason_and_respond_with_llm_cost_aggregation(
    mock_tool_executor, mock_context_manager, mock_db_session
):
    # Mock the initial LLM call to return some usage and cost
    mock_llm_response = {
        "type": "text",
        "text": "Initial LLM response",
        "usage": {"input_tokens": 10, "output_tokens": 5},
        "cost": {"total_cost": 0.01, "llm_cost": 0.01},
    }
    
    # Mock call_llm to return the mock_llm_response
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("backend.services.llm_gateway.call_llm", AsyncMock(return_value=mock_llm_response))
        
        result = await reason_and_respond(
            provider="gemini",
            model="gemini-pro",
            api_key="test_key",
            chat_history=[],
            context_manager=mock_context_manager,
            db=mock_db_session,
            user_prompt="Hello",
            chat_id=123,
            tool_executor=mock_tool_executor,
        )

        assert result["type"] == "text"
        assert result["text"] == "Initial LLM response"
        assert result["usage"] == {"input_tokens": 10, "output_tokens": 5}
        assert result["cost"] == {"total_cost": 0.01, "llm_cost": 0.01}


@pytest.mark.asyncio
async def test_reason_and_respond_with_tool_cost_aggregation_single_tool(
    mock_tool_executor, mock_context_manager, mock_db_session
):
    # Mock the initial LLM call to propose a tool
    mock_llm_response_tool_code = {
        "type": "tool_code",
        "tool_name": "perform_websearch",
        "tool_args": {"query": "test query"},
        "raw_assistant_response": {"role": "assistant", "content": "", "tool_calls": [{"id": "call_123", "function": {"name": "perform_websearch", "arguments": "{\"query\": \"test query\"}"}}]},
        "usage": {"input_tokens": 20, "output_tokens": 10}, # Cost of LLM proposing the tool
        "cost": {"total_cost": 0.02, "llm_cost": 0.02},
    }

    # Mock the tool execution result
    mock_tool_execution_result = {
        "role": "tool",
        "name": "perform_websearch",
        "content": json.dumps({
            "text": "Websearch result",
            "urls": [],
            "usage": {"query_count": 1, "api_calls": 1},
            "cost": {"total_cost": 0.005, "query_cost": 0.005},
        }),
        "tool_call_id": "call_123"
    }
    
    # Mock tool_executor.execute_tool_call
    mock_tool_executor.execute_tool_call = AsyncMock(return_value=mock_tool_execution_result)

    # Mock call_llm for the recursive call (after tool execution)
    # The LLM is called again after the tool to summarize. This call should not propose tools.
    mock_llm_response_final = {
        "type": "text",
        "text": "Final response after websearch",
        "usage": {"input_tokens": 15, "output_tokens": 8}, # Cost of final LLM summary
        "cost": {"total_cost": 0.015, "llm_cost": 0.015},
    }

    with pytest.MonkeyPatch().context() as mp:
        call_llm_mock = AsyncMock()
        # First call: propose tool
        call_llm_mock.side_effect = [mock_llm_response_tool_code, mock_llm_response_final]
        mp.setattr("backend.services.llm_gateway.call_llm", call_llm_mock)

        result = await reason_and_respond(
            provider="gemini",
            model="gemini-pro",
            api_key="test_key",
            chat_history=[],
            context_manager=mock_context_manager,
            db=mock_db_session,
            user_prompt="Search the web for test query",
            chat_id=123,
            tool_executor=mock_tool_executor,
        )

        assert result["type"] == "text"
        assert result["text"] == "Final response after websearch"
        
        # Expected aggregated usage:
        # Initial LLM: {"input_tokens": 20, "output_tokens": 10}
        # Tool:        {"query_count": 1, "api_calls": 1}
        # Final LLM:   {"input_tokens": 15, "output_tokens": 8}
        expected_usage = {"input_tokens": 35, "output_tokens": 18, "query_count": 1, "api_calls": 1}
        assert result["usage"] == expected_usage

        # Expected aggregated cost:
        # Initial LLM: {"total_cost": 0.02, "llm_cost": 0.02}
        # Tool:        {"total_cost": 0.005, "query_cost": 0.005}
        # Final LLM:   {"total_cost": 0.015, "llm_cost": 0.015}
        expected_cost = {"total_cost": pytest.approx(0.04), "llm_cost": pytest.approx(0.035), "query_cost": pytest.approx(0.005)}
        assert result["cost"] == expected_cost

        # Ensure call_llm was called twice (once for tool proposal, once for final response)
        call_llm_mock.call_count == 2
        # Ensure tool_executor.execute_tool_call was called
        mock_tool_executor.execute_tool_call.assert_called_once_with("perform_websearch", {"query": "test query"})
