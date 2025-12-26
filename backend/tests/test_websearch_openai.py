import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from backend.services.websearch import perform_websearch
from backend.services.cost_calculator import USD_TO_EUR_CONVERSION_RATE

# Mock für das Responses API Modell
class MockAnnotation:
    def __init__(self, url):
        self.url = url

class MockOutputText:
    def __init__(self, text, annotations=None):
        self.text = text
        self.annotations = annotations if annotations is not None else []

class MockResponsesCreateResponse:
    def __init__(self, output_text_content, urls=None):
        annotations = [MockAnnotation(url) for url in urls] if urls else []
        self.output_text = MockOutputText(output_text_content, annotations)
        
    def model_dump(self):
        return {
            "output_text": {
                "text": self.output_text.text,
                "annotations": [{"url": ann.url} for ann in self.output_text.annotations]
            }
        }


@pytest.mark.asyncio
async def test_openai_websearch_responses_api():
    """
    Testet die OpenAI Websuche mit der Responses API, Überprüfung der Textausgabe,
    URL-Extraktion und Kostenverfolgung.
    """
    query = "Wetter in Berlin"
    api_key = "test_openai_key"
    model = "gpt-4o-mini" # Aktuelles GPT Modell
    provider = "openai"

    mock_responses_create_response = MockResponsesCreateResponse(
        output_text_content="Das Wetter in Berlin ist sonnig. Mehr Infos auf example.com und test.org.",
        urls=["https://www.example.com", "https://www.test.org"]
    )

    with patch("backend.services.websearch.AsyncOpenAI", autospec=True) as mock_async_openai_class:
        mock_client_instance = MagicMock()
        mock_async_openai_class.return_value = mock_client_instance
        mock_client_instance.responses = MagicMock()
        mock_client_instance.responses.create = AsyncMock(return_value=mock_responses_create_response)

        with patch("backend.utils.config_loader.load_model_catalog") as mock_load_model_catalog:
            mock_load_model_catalog.return_value = {"id": "openai-websearch", "name": "Web Search", "provider": "openai", "type": "websearch", "cost_per_query": 0.01}
            
            result = await perform_websearch(query=query, api_key=api_key, provider=provider, model=model)

            # Überprüfe den Aufruf von openai.AsyncOpenAI.responses.create
            mock_client_instance.responses.create.assert_called_once_with(
                model=model,
                tools=[{"type": "web_search"}],
                input=query,
            )

            # Überprüfe die Textausgabe
            assert "Das Wetter in Berlin ist sonnig" in result["text"]
            assert "Mehr Infos auf example.com und test.org." in result["text"]

            # Überprüfe die URL-Extraktion
            assert "https://www.example.com" in result["urls"]
            assert "https://www.test.org" in result["urls"]
            assert len(result["urls"]) == 2

            # Überprüfe die Kosten
            assert "cost" in result
            assert "total_cost" in result["cost"]
            # 0.01 USD * 0.9009 (USD_TO_EUR_CONVERSION_RATE)
            assert pytest.approx(result["cost"]["total_cost"], 0.00000001) == 0.01 * USD_TO_EUR_CONVERSION_RATE
            
            # Überprüfe die Usage
            assert "usage" in result
            assert "query_count" in result["usage"]
            assert result["usage"]["query_count"] == 1
