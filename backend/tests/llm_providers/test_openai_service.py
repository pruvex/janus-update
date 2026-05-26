from unittest.mock import AsyncMock, patch

import pytest
from backend.llm_providers.openai.service import OpenAIServiceProvider


# Simple class to mock usage data without Mock comparison issues
class UsageMock:
    def __init__(self, prompt_tokens, completion_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


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
        # Use simple class for usage to avoid Mock comparison issues in cost_calculator
        mock_response.usage = UsageMock(prompt_tokens=10, completion_tokens=5)
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIServiceProvider()
        result = await provider.generate_response(
            api_key="test_key",
            model="gpt-5.4-nano",
            messages=[{"role": "user", "content": "Hello"}],
        )

        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-5.4-nano", messages=[{"role": "user", "content": "Hello"}]
        )
        assert result["type"] == "text"
        assert result["text"] == "Test response"


@pytest.mark.asyncio
async def test_provider_generate_image():
    with patch(
        "backend.llm_providers.capabilities.openai_image_generation.OpenAIImageGeneration.generate_image",
        new_callable=AsyncMock,
    ) as mock_generate_image_impl:
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

        result = await provider.generate_image(
            api_key=api_key,
            model=model,
            prompt=prompt,
            narrative_prompt="A cinematic cat portrait.",
            preset_context={"style": "test"},
            **kwargs,
        )

        mock_generate_image_impl.assert_awaited_once_with(
            api_key=api_key,
            model=model,
            prompt=prompt,
            narrative_prompt="A cinematic cat portrait.",
            preset_context={"style": "test"},
            image_bytes_list=None,
            **kwargs,
        )
        assert result["image_url"] == "http://example.com/image.png"
