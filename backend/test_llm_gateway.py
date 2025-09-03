import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tenacity import RetryError, stop_after_attempt, wait_exponential
import openai
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import json
import uuid

from backend.llm_gateway import call_llm, _call_openai_api, _call_gemini_api, _calculate_and_log_cost, _call_gemini_image_generation_api, generate_image_tool

# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('backend.llm_gateway.logger') as mock_log:
        yield mock_log

# Mock MODEL_PRICES for consistent testing
@pytest.fixture(autouse=True)
def mock_model_prices():
    with patch('backend.llm_gateway.MODEL_PRICES') as mock_prices:
        mock_prices.get.side_effect = lambda model_id: {
            "test-openai-model": {"provider": "openai", "cost_per_token_input": 0.000001, "cost_per_token_output": 0.000002},
            "test-gemini-model": {"provider": "gemini", "cost_per_token_input": 0.000003, "cost_per_token_output": 0.000006},
            "dall-e-3-standard": {"provider": "openai", "cost_per_image": 0.04},
            "gemini-image-model": {"provider": "gemini", "cost_per_image": 0.02}
        }.get(model_id)
        yield mock_prices

# Mock _calculate_and_log_cost to simplify tests
@pytest.fixture(autouse=True)
def mock_calculate_and_log_cost():
    with patch('backend.llm_gateway._calculate_and_log_cost') as mock_calc:
        mock_calc.return_value = ({"input_tokens": 10, "output_tokens": 20}, {"total_cost": 0.00005})
        yield mock_calc

@pytest.mark.asyncio
@patch('openai.AsyncOpenAI')
async def test_call_openai_api_success(mock_openai_client_class):
    mock_client = AsyncMock()
    mock_openai_client_class.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="OpenAI response", tool_calls=None))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=20)
    )

    result = await _call_openai_api("test_key", "test-openai-model", [], {})

    assert result["type"] == "text"
    assert result["text"] == "OpenAI response"
    mock_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
@patch('openai.AsyncOpenAI')
async def test_call_openai_api_tool_call(mock_openai_client_class):
    mock_client = AsyncMock()
    mock_openai_client_class.return_value = mock_client
    
    tool_function_mock = MagicMock()
    tool_function_mock.name = "test_tool"
    tool_function_mock.arguments = '{"arg1": "val1"}'
    tool_call_mock = MagicMock()
    tool_call_mock.function = tool_function_mock
    message_mock = MagicMock()
    message_mock.tool_calls = [tool_call_mock]

    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=message_mock)],
        usage=MagicMock(prompt_tokens=10, completion_tokens=20)
    )

    result = await _call_openai_api("test_key", "test-openai-model", [], {})

    assert result["type"] == "tool_code"
    assert result["tool_name"] == "test_tool"
    assert result["tool_args"] == {"arg1": "val1"}

@pytest.mark.asyncio
@patch('openai.AsyncOpenAI')
async def test_call_openai_api_retry_success(mock_openai_client_class):
    mock_client = AsyncMock()
    mock_openai_client_class.return_value = mock_client
    
    mock_client.chat.completions.create.side_effect = [
        Exception("Connection error"), 
        Exception("Rate limit"), 
        MagicMock(
            choices=[MagicMock(message=MagicMock(content="OpenAI response after retry", tool_calls=None))],
            usage=MagicMock(prompt_tokens=10, completion_tokens=20)
        )
    ]

    result = await _call_openai_api("test_key", "test-openai-model", [], {})

    assert result["type"] == "text"
    assert result["text"] == "OpenAI response after retry"
    assert mock_client.chat.completions.create.call_count == 3

@pytest.mark.asyncio
@patch('openai.AsyncOpenAI')
async def test_call_openai_api_retry_failure(mock_openai_client_class):
    mock_client = AsyncMock()
    mock_openai_client_class.return_value = mock_client
    
    mock_client.chat.completions.create.side_effect = Exception("Persistent connection error") 

    with pytest.raises(Exception):
        await _call_openai_api("test_key", "test-openai-model", [], {})
    
    assert mock_client.chat.completions.create.call_count == 3

@pytest.mark.asyncio
@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
async def test_call_gemini_api_success(mock_configure, mock_generative_model_class):
    mock_model = AsyncMock()
    mock_generative_model_class.return_value = mock_model
    mock_model.generate_content_async.return_value = MagicMock(text="Gemini response")
    
    mock_model.count_tokens = MagicMock(side_effect=[
        MagicMock(total_tokens=10),
        MagicMock(total_tokens=20)
    ])

    result = await _call_gemini_api("test_key", "test-gemini-model", [], {})

    assert result["type"] == "text"
    assert result["text"] == "Gemini response"
    mock_model.generate_content_async.assert_called_once()

@pytest.mark.asyncio
@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
async def test_call_gemini_api_resource_exhausted(mock_configure, mock_generative_model_class):
    mock_model = AsyncMock()
    mock_generative_model_class.return_value = mock_model
    mock_model.generate_content_async.side_effect = ResourceExhausted("Quota exceeded")

    result = await _call_gemini_api("test_key", "test-gemini-model", [], {})

    assert result["type"] == "text"
    assert "Anfragelimit für die Gemini API wurde überschritten" in result["text"]
    assert mock_model.generate_content_async.call_count == 1

@pytest.mark.asyncio
@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
async def test_call_gemini_api_retry_success(mock_configure, mock_generative_model_class):
    mock_model = AsyncMock()
    mock_generative_model_class.return_value = mock_model
    
    mock_model.generate_content_async.side_effect = [
        Exception("Transient error"),
        Exception("Another transient error"),
        MagicMock(text="Gemini response after retry")
    ]
    mock_model.count_tokens = MagicMock(side_effect=[
        MagicMock(total_tokens=10),
        MagicMock(total_tokens=20)
    ])

    result = await _call_gemini_api("test_key", "test-gemini-model", [], {})

    assert result["type"] == "text"
    assert result["text"] == "Gemini response after retry"
    assert mock_model.generate_content_async.call_count == 3

@pytest.mark.asyncio
@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
async def test_call_gemini_api_retry_failure(mock_configure, mock_generative_model_class):
    mock_model = AsyncMock()
    mock_generative_model_class.return_value = mock_model
    
    mock_model.generate_content_async.side_effect = Exception("Persistent error")

    with pytest.raises(Exception):
        await _call_gemini_api("test_key", "test-gemini-model", [], {})
    
    assert mock_model.generate_content_async.call_count == 3

@pytest.mark.asyncio
@patch('backend.llm_gateway._call_openai_api')
@patch('backend.llm_gateway._call_gemini_api')
async def test_call_llm_openai(mock_gemini_api, mock_openai_api):
    mock_openai_api.return_value = {"type": "text", "text": "OpenAI response"}
    result = await call_llm("openai", "test-openai-model", "prompt", "key")
    assert result["text"] == "OpenAI response"
    mock_openai_api.assert_called_once()
    mock_gemini_api.assert_not_called()

@pytest.mark.asyncio
@patch('backend.llm_gateway._call_openai_api')
@patch('backend.llm_gateway._call_gemini_api')
async def test_call_llm_gemini(mock_gemini_api, mock_openai_api):
    mock_gemini_api.return_value = {"type": "text", "text": "Gemini response"}
    result = await call_llm("gemini", "test-gemini-model", "prompt", "key")
    assert result["text"] == "Gemini response"
    mock_gemini_api.assert_called_once()
    mock_openai_api.assert_not_called()

@pytest.mark.asyncio
@patch('backend.llm_gateway._call_openai_api', side_effect=RetryError(last_attempt=MagicMock(exception=Exception("Test Retry Error"))))
@patch('backend.llm_gateway._call_gemini_api')
async def test_call_llm_retry_error_handling(mock_gemini_api, mock_openai_api):
    result = await call_llm("openai", "test-openai-model", "prompt", "key")
    assert result["type"] == "text"
    assert "Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen." in result["text"]
    assert mock_openai_api.call_count == 1

# === KORRIGIERTER TEST BEGINNT HIER ===
@pytest.mark.asyncio
@patch('uuid.uuid4', return_value=uuid.UUID('00000000-0000-0000-0000-000000000001'))
@patch('backend.llm_gateway.image_manager.save_image_from_bytes')
@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
async def test_call_gemini_image_generation_api_success(mock_configure, mock_generative_model_class, mock_save_image, mock_uuid):
    # 1. Konfiguriere den Mock für die save_image_from_bytes Funktion
    # Der Rückgabewert muss mit der gemockten UUID übereinstimmen.
    expected_url = "/user_images/00000000-0000-0000-0000-000000000001.png"
    mock_save_image.return_value = expected_url
    
    # 2. Konfiguriere den Mock für das GenerativeModel
    mock_model = AsyncMock()
    mock_generative_model_class.return_value = mock_model
    
    # 3. Dies ist der entscheidende Teil:
    # Wir erstellen eine 'async def'-Funktion, die die erwartete Datenstruktur zurückgibt.
    # Wenn wir diese Funktion als 'side_effect' zuweisen, gibt der Mock-Aufruf
    # ein 'awaitable' Coroutine-Objekt zurück, was den `TypeError` behebt.
    async def mock_generate_content_side_effect(*args, **kwargs):
        # Simulierte Antwort von der Gemini API
        return MagicMock(
            candidates=[
                MagicMock(content=MagicMock(parts=[
                    MagicMock(inline_data=MagicMock(data=b"image_data"))
                ]))
            ]
        )
    mock_model.generate_content_async.side_effect = mock_generate_content_side_effect

    # 4. Führe die zu testende Funktion aus
    result = await _call_gemini_image_generation_api("test_key", "gemini-image-model", "a cat")

    # 5. Überprüfe die Ergebnisse
    assert result["text"] == ""
    assert result["image_url"] == expected_url
    
    # 6. Überprüfe, ob die Mocks korrekt aufgerufen wurden
    mock_model.generate_content_async.assert_awaited_once_with("a cat")
    expected_filename = "00000000-0000-0000-0000-000000000001.png"
    mock_save_image.assert_called_once_with(b"image_data", expected_filename)
# === KORRIGIERTER TEST ENDET HIER ===


@pytest.mark.asyncio
@patch('openai.AsyncOpenAI')
async def test_generate_image_tool_success(mock_openai_client_class):
    mock_client = AsyncMock()
    mock_openai_client_class.return_value = mock_client
    mock_client.images.generate.return_value = MagicMock(
        data=[MagicMock(url="http://example.com/dalle_image.png")],
        created=12345
    )

    result = await generate_image_tool("test_key", "a dog", "1024x1024", "standard", "url")

    assert result["url"] == "http://example.com/dalle_image.png"
    assert result["created"] == 12345
    mock_client.images.generate.assert_called_once()