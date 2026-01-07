import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from backend.llm_providers.gemini_service import GeminiServiceProvider


@pytest.mark.asyncio
@patch("backend.llm_providers.gemini_service._calculate_and_log_cost")
@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
async def test_provider_generate_response(mock_configure, mock_gen_model, mock_calculate_cost):
    """Testet einfache Text-Generierung ohne Tools."""
    # Setup Cost Mock
    mock_calculate_cost.return_value = (
        {"input_tokens": 10, "output_tokens": 20},
        {"total_cost": 0.001},
    )

    # Setup Model Mock
    mock_model_instance = AsyncMock()
    mock_response = MagicMock()

    # Mock Usage Metadata
    mock_usage_metadata = MagicMock()
    mock_usage_metadata.prompt_token_count = 10
    mock_usage_metadata.candidates_token_count = 20
    mock_response.usage_metadata = mock_usage_metadata

    # Mock Text Part
    mock_part = MagicMock()
    # WICHTIG: function_call muss explizit None/False sein
    mock_part.function_call = None
    mock_part.text = "Test response"

    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_part]
    mock_response.prompt_feedback.block_reason = None

    mock_model_instance.generate_content_async.return_value = mock_response
    mock_gen_model.return_value = mock_model_instance

    provider = GeminiServiceProvider()
    api_key = "test_key"
    model = "gemini-3-flash-preview"  # Using internal model alias
    messages = [{"role": "user", "content": "Hallo"}]

    result = await provider.generate_response(api_key, model, messages)

    # Asserts
    mock_calculate_cost.assert_called_once_with("gemini-3-flash-preview", 10, 5)
    mock_gen_model.assert_called_once_with(model_name="gemini-3-flash-preview", system_instruction=None)
    assert result["text"] == "Test response"
    assert result["usage"] == {"input_tokens": 10, "output_tokens": 20}


@pytest.mark.skip(reason="Benötigt Refactoring der Mocks")
@pytest.mark.asyncio
async def test_provider_generate_image():
    """Testet die Bildgenerierung (delegiert an ImageGeneration Klasse)."""
    with patch("google.generativeai.GenerativeModel") as mock_gen_model:
        mock_model_instance = AsyncMock()
        mock_gen_model.return_value = mock_model_instance

        mock_response = MagicMock()
        mock_part = MagicMock()
        # Mocking Inline Data (für Bild-Antwort)
        del (
            mock_part.data
        )  # Sicherstellen, dass Attributzugriff auf .data fehlschlägt falls getestet
        mock_part.inline_data.data = b"image_data"

        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]
        mock_model_instance.generate_content_async.return_value = mock_response

        with patch(
            "backend.services.image_manager.save_image_from_bytes",
            return_value="/path/to/image.png",
        ) as mock_save_image:
            provider = GeminiServiceProvider()
            with patch("google.generativeai.configure"):
                result = await provider.generate_image(
                    api_key="test_key",
                    model="gemini-3-flash-preview",  # Using internal model alias
                    prompt="mache ein bild von einem gelben haus",
                )

                # Die Description-Logic ist jetzt simpler (Slugify)
                mock_save_image.assert_called_once_with(
                    b"image_data", description="einem-gelben-haus", file_extension="png"
                )
                assert result["image_url"] == "/path/to/image.png"


@pytest.mark.asyncio
@patch("backend.llm_providers.gemini_service._calculate_and_log_cost")
@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
async def test_provider_generate_response_with_tool_call(
    mock_configure, mock_gen_model, mock_calculate_cost
):
    """Testet, ob Tool-Calls korrekt erkannt und formatiert werden."""
    mock_calculate_cost.return_value = (
        {"input_tokens": 10, "output_tokens": 5},
        {"total_cost": 0.001},
    )

    mock_model_instance = AsyncMock()
    mock_response = MagicMock()

    # MOCK UPDATE: Wir simulieren das Protobuf-Objekt für FunctionCall
    mock_tool_call = MagicMock()
    mock_tool_call.name = "perform_websearch"
    # Die Args kommen als Proto-Map, werden aber im Code zu Dict konvertiert.
    # Wir mocken hier das Verhalten von _proto_to_dict implizit, indem wir
    # annehmen, dass .args im Code verarbeitet wird.
    # Da wir _proto_to_dict nicht mocken können (ist im Modul), müssen wir tricksen:
    # Der Code ruft _proto_to_dict(function_call.args) auf.
    # Wir geben hier ein Dict zurück, da der Helper Checker prüft ob items() existiert.
    mock_tool_call.args = {"query": "cats"}

    mock_part = MagicMock()
    mock_part.function_call = mock_tool_call
    mock_part.text = ""  # Wichtig: Kein Text bei reinem Tool-Call

    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_part]
    mock_response.prompt_feedback.block_reason = None

    mock_usage_metadata = MagicMock()
    mock_usage_metadata.prompt_token_count = 10
    mock_usage_metadata.candidates_token_count = 5
    mock_response.usage_metadata = mock_usage_metadata

    mock_model_instance.generate_content_async.return_value = mock_response
    mock_gen_model.return_value = mock_model_instance

    provider = GeminiServiceProvider()
    api_key = "test_key"
    model = "gemini-3-flash-preview"  # Using internal model alias
    messages = [{"role": "user", "content": "Search for cats"}]
    # Tool-Definition wird über Mocking der Registry gelöst oder hier ignoriert,
    # da convert_tools gemockt werden müsste.
    # Wir patchen convert_tools, um Komplexität zu reduzieren

    with patch.object(provider, "_convert_tools_to_gemini_format", return_value=[MagicMock()]):
        result = await provider.generate_response(api_key, model, messages, tools=[{}])

    # FIX: Anpassung an die neue Rückgabestruktur (Liste von Tool Calls)
    assert result["type"] == "tool_code"

    # Prüfe ob tool_calls eine Liste ist und den richtigen Inhalt hat
    assert "tool_calls" in result
    assert len(result["tool_calls"]) == 1

    first_call = result["tool_calls"][0]
    assert first_call["function"]["name"] == "perform_websearch"

    # Arguments sind JSON-String encoded
    args_dict = json.loads(first_call["function"]["arguments"])
    assert args_dict == {"query": "cats"}

    assert result["usage"] == {"input_tokens": 10, "output_tokens": 5}


@pytest.mark.asyncio
@patch("backend.llm_providers.gemini_service._calculate_and_log_cost")
@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
async def test_provider_generate_response_with_image_data(
    mock_configure, mock_gen_model, mock_calculate_cost
):
    """Testet Multimodal-Input (Text + Bild)."""
    mock_calculate_cost.return_value = (
        {"input_tokens": 100, "output_tokens": 50},
        {"total_cost": 0.002},
    )

    mock_model_instance = AsyncMock()
    mock_response = MagicMock()

    mock_usage_metadata = MagicMock()
    mock_usage_metadata.prompt_token_count = 100
    mock_usage_metadata.candidates_token_count = 50
    mock_response.usage_metadata = mock_usage_metadata

    mock_part = MagicMock()
    mock_part.function_call = None
    mock_part.text = "Image analysis result"

    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_part]
    mock_response.prompt_feedback.block_reason = None
    mock_model_instance.generate_content_async.return_value = mock_response
    mock_gen_model.return_value = mock_model_instance

    provider = GeminiServiceProvider()
    api_key = "test_key"
    model = "gemini-3-flash-preview"  # Using internal model alias
    messages = [{"role": "user", "content": "What is in this image?"}]
    image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    result = await provider.generate_response(
        api_key, model, messages, image_data=image_data, is_image_analysis_request=True
    )

    assert result["text"] == "Image analysis result"
    assert result["usage"] == {"input_tokens": 100, "output_tokens": 50}

    # Verify: Wurde das Bild an Gemini übergeben?
    call_args, call_kwargs = mock_model_instance.generate_content_async.call_args
    sent_history = call_kwargs["contents"]
    assert len(sent_history) == 1
    assert "inline_data" in sent_history[0]["parts"][1]
    assert sent_history[0]["parts"][1].inline_data.mime_type == "image/png"
