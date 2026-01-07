from unittest.mock import AsyncMock, patch

import pytest
from backend.llm_providers.openai_service import OpenAIServiceProvider


@pytest.mark.asyncio
async def test_provider_generate_response():
    with patch("openai.AsyncOpenAI") as mock_async_openai:
        mock_client = AsyncMock()
        mock_async_openai.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message = AsyncMock()
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.refusal = False # Set refusal to False for this test
        mock_response.usage = AsyncMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIServiceProvider()
        result = await provider.generate_response(
            api_key="test_key",
            model="gpt-5-nano",
            messages=[{"role": "user", "content": "Hello"}],
        )

        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-5-nano", messages=[{"role": "user", "content": "Hello"}]
        )
        assert result["type"] == "text"
        assert result["text"] == "Test response"


@pytest.mark.skip(reason="Benötigt Refactoring der Mocks")
@pytest.mark.asyncio
async def test_provider_generate_image():
    # This test now checks if the main provider class correctly calls the new capability class.
    with patch(
        "backend.llm_providers.capabilities.openai_image_generation.OpenAIImageGeneration.generate_image"
    ) as mock_generate_image_impl:
        # The mocked implementation will return this dictionary
        mock_generate_image_impl.return_value = {
            "image_url": "http://example.com/image.png",
            "usage": {},
            "cost": {},
            "text": None,
        }

        provider = OpenAIServiceProvider()
        api_key = "test_key"
        prompt = "A cat"
        model = "dall-e-3"
        kwargs = {"size": "1024x1024", "quality": "standard"}

        # Call the method on the main provider
        result = await provider.generate_image(api_key, model, prompt, **kwargs)

        # Assert that the internal implementation was called correctly
        mock_generate_image_impl.assert_called_once_with(api_key, model, prompt, **kwargs)
        # Assert that the main provider returns the result from the implementation
        assert result["image_url"] == "http://example.com/image.png"
