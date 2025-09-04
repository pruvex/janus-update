import pytest
from unittest.mock import AsyncMock, patch
from backend.llm_providers import openai_service

@pytest.mark.asyncio
async def test_call_openai_api_text_response():
    with patch('openai.AsyncOpenAI') as mock_async_openai:
        mock_client = AsyncMock()
        mock_async_openai.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message = AsyncMock()
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = AsyncMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_client.chat.completions.create.return_value = mock_response

        api_key = "test_key"
        model_id = "gpt-4"
        chat_history = [{"role": "user", "content": "Hello"}]
        model_info = {}
        tools = []

        result = await openai_service._call_openai_api(api_key, model_id, chat_history, model_info, tools)

        mock_client.chat.completions.create.assert_called_once_with(
            model=model_id,
            messages=chat_history
        )
        assert result["type"] == "text"
        assert result["text"] == "Test response"

@pytest.mark.asyncio
async def test_generate_image_tool():
    with patch('openai.AsyncOpenAI') as mock_async_openai:
        mock_client = AsyncMock()
        mock_async_openai.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.created = 12345
        mock_response.data = [AsyncMock()]
        mock_response.data[0].url = "http://example.com/image.png"
        mock_client.images.generate.return_value = mock_response

        api_key = "test_key"
        prompt = "A cat"

        result = await openai_service.generate_image_tool(api_key, prompt)

        mock_client.images.generate.assert_called_once_with(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url"
        )
        assert result["url"] == "http://example.com/image.png"
