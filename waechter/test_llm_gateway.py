
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Füge das übergeordnete Verzeichnis zum Python-Pfad hinzu, um das Backend-Modul zu finden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import llm_gateway

class TestLlmGateway(unittest.TestCase):

    @patch('openai.AsyncOpenAI')
    @patch('httpx.AsyncClient.post')
    async def test_call_llm(self, mock_httpx_post, mock_openai_async_openai):
        # Mock für OpenAI AsyncOpenAI Client
        mock_openai_client_instance = MagicMock()
        mock_openai_async_openai.return_value.__aenter__.return_value = mock_openai_client_instance
        mock_openai_client_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="mocked LLM answer"))],
            usage=MagicMock(prompt_tokens=10, completion_tokens=20)
        )

        # Mock für httpx.AsyncClient.post (für DALL-E)
        mock_httpx_response = MagicMock()
        mock_httpx_response.status_code = 200
        mock_httpx_response.json.return_value = {"data": [{"url": "http://mocked-image.url"}]}
        mock_httpx_post.return_value = mock_httpx_response

        provider = "openai"
        model = "gpt-4o-mini"
        prompt = "Test prompt"
        api_key = "test-api-key"

        response = await llm_gateway.call_llm(provider, model, prompt, api_key)

        mock_openai_async_openai.assert_called_once_with(api_key=api_key)
        mock_openai_client_instance.chat.completions.create.assert_called_once_with(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            tools=[llm_gateway.dalle_tool],
            tool_choice="auto"
        )

        self.assertEqual(response["text"], "mocked LLM answer")
        self.assertIn("usage", response)
        self.assertIn("cost", response)

if __name__ == '__main__':
    unittest.main()
