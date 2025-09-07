import pytest
from unittest.mock import AsyncMock, patch
from backend.llm_providers.openai_service import OpenAIServiceProvider, generate_image_tool

@pytest.mark.asyncio
async def test_provider_generate_response():
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

        provider = OpenAIServiceProvider()
        result = await provider.generate_response(
            api_key="test_key",
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}]
        )

        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}]
        )
        assert result["type"] == "text"
        assert result["text"] == "Test response"

@pytest.mark.asyncio
async def test_generate_image_tool_wrapper():
    # This tests the standalone wrapper function that is used for tool registration
    with patch('backend.llm_providers.openai_service.OpenAIServiceProvider.generate_image') as mock_generate_image:
        mock_generate_image.return_value = {
            "image_url": "http://example.com/image.png",
            "usage": {},
            "cost": {}
        }

        api_key = "test_key"
        prompt = "A cat"

        result = await generate_image_tool(api_key, prompt)

        mock_generate_image.assert_called_once_with(
            api_key, "dall-e-3", prompt, size="1024x1024", quality="standard"
        )
        assert result["url"] == "http://example.com/image.png"
