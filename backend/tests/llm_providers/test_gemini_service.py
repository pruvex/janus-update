import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel
from backend.llm_providers.gemini.service import GeminiServiceProvider


@pytest.mark.asyncio
@patch("backend.llm_providers.gemini.service._calculate_and_log_cost")
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
    mock_calculate_cost.assert_called_once_with(
        "gemini-3-flash-preview",
        {"prompt_tokens": 10, "completion_tokens": 20},
    )
    mock_gen_model.assert_called_once_with(model_name="gemini-3-flash-preview", system_instruction=None)
    assert result["text"] == "Test response"
    assert result["usage"] == {"input_tokens": 10, "output_tokens": 20}


@pytest.mark.asyncio
@patch("backend.llm_providers.gemini.service._calculate_and_log_cost")
@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
async def test_provider_generate_response_keeps_selected_pro_preview_model(mock_configure, mock_gen_model, mock_calculate_cost):
    mock_calculate_cost.return_value = (
        {"input_tokens": 10, "output_tokens": 20},
        {"total_cost": 0.001},
    )

    mock_model_instance = AsyncMock()
    mock_response = MagicMock()
    mock_usage_metadata = MagicMock()
    mock_usage_metadata.prompt_token_count = 10
    mock_usage_metadata.candidates_token_count = 20
    mock_response.usage_metadata = mock_usage_metadata

    mock_part = MagicMock()
    mock_part.function_call = None
    mock_part.text = "Test response"

    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_part]
    mock_response.prompt_feedback.block_reason = None

    mock_model_instance.generate_content_async.return_value = mock_response
    mock_gen_model.return_value = mock_model_instance

    provider = GeminiServiceProvider()
    result = await provider.generate_response("test_key", "gemini-3-pro-preview", [{"role": "user", "content": "Hallo"}])

    mock_gen_model.assert_called_once_with(model_name="gemini-3-pro-preview", system_instruction=None)
    mock_calculate_cost.assert_called_once_with(
        "gemini-3-pro-preview",
        {"prompt_tokens": 10, "completion_tokens": 20},
    )
    assert result["text"] == "Test response"


@pytest.mark.asyncio
@patch("backend.llm_providers.gemini.service._calculate_and_log_cost")
@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
async def test_provider_generate_response_concatenates_multiple_system_messages(mock_configure, mock_gen_model, mock_calculate_cost):
    mock_calculate_cost.return_value = (
        {"input_tokens": 10, "output_tokens": 20},
        {"total_cost": 0.001},
    )

    mock_model_instance = AsyncMock()
    mock_response = MagicMock()
    mock_usage_metadata = MagicMock()
    mock_usage_metadata.prompt_token_count = 10
    mock_usage_metadata.candidates_token_count = 20
    mock_response.usage_metadata = mock_usage_metadata

    mock_part = MagicMock()
    mock_part.function_call = None
    mock_part.text = "Test response"

    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_part]
    mock_response.prompt_feedback.block_reason = None

    mock_model_instance.generate_content_async.return_value = mock_response
    mock_gen_model.return_value = mock_model_instance

    provider = GeminiServiceProvider()
    messages = [
        {"role": "system", "content": "Regel A"},
        {"role": "system", "content": "Regel B"},
        {"role": "user", "content": "Hallo"},
    ]

    result = await provider.generate_response("test_key", "gemini-3-flash-preview", messages)

    mock_gen_model.assert_called_once_with(model_name="gemini-3-flash-preview", system_instruction="Regel A\n\nRegel B")
    assert result["text"] == "Test response"


@pytest.mark.asyncio
async def test_provider_generate_image():
    """Testet die Bildgenerierung (delegiert an ImageGeneration Klasse)."""
    with patch(
        "backend.llm_providers.gemini.capabilities.image_generation.GeminiImageGeneration.generate_image",
        new_callable=AsyncMock,
    ) as mock_generate_image_impl:
        mock_generate_image_impl.return_value = {
            "image_url": "/path/to/image.png",
            "usage": {},
            "cost": {},
            "text": None,
        }

        provider = GeminiServiceProvider()
        result = await provider.generate_image(
            api_key="test_key",
            model="gemini-3-flash-preview",
            prompt="mache ein bild von einem gelben haus",
            narrative_prompt="Ein gelbes Haus bei Sonnenuntergang.",
            preset_context={"has_preset": False},
        )

        mock_generate_image_impl.assert_awaited_once_with(
            api_key="test_key",
            model="gemini-3-flash-preview",
            prompt="Ein gelbes Haus bei Sonnenuntergang.",
            narrative_prompt="Ein gelbes Haus bei Sonnenuntergang.",
            preset_context={"has_preset": False},
            image_bytes_list=None,
        )
        assert result["image_url"] == "/path/to/image.png"


@pytest.mark.asyncio
@patch("backend.llm_providers.gemini.service._calculate_and_log_cost")
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
    mock_tool_call.name = "system.websearch"
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
    assert first_call["function"]["name"] == "system.websearch"

    # Arguments sind JSON-String encoded
    args_dict = json.loads(first_call["function"]["arguments"])
    assert args_dict == {"query": "cats"}

    raw_assistant = result["raw_assistant_response"]
    assert raw_assistant["parts"][0] is mock_part
    assert raw_assistant["_gemini_raw_model_parts"][0] is mock_part

    assert result["usage"] == {"input_tokens": 10, "output_tokens": 5}


def test_gemini_name_mapping_resolves_provider_safe_names_to_canonical_skill():
    provider = GeminiServiceProvider()

    with patch("backend.services.skill_router.skill_router.resolve_tool_name", return_value="calendar.create_event"), \
         patch("backend.services.tool_manager.tool_manager.get_skill_id", return_value="calendar.create_event"):
        assert provider._resolve_gemini_response_tool_name("calendar_create_event") == "calendar.create_event"
        assert provider._gemini_api_function_name_for_history("calendar.create_event") == "calendar_create_event"


@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
def test_gemini_stream_build_request_reuses_signed_raw_parts(
    _mock_configure,
    mock_gen_model,
):
    provider = GeminiServiceProvider()
    signed_part = MagicMock()
    signed_part.text = ""
    signed_part.thought_signature = b"signed"
    function_call = MagicMock()
    function_call.name = "calendar_create_event"
    function_call.args = {"summary": "Termin"}
    signed_part.function_call = function_call

    messages = [
        {"role": "user", "content": "Plane einen Termin"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "calendar.create_event", "arguments": "{\"summary\":\"Termin\"}"},
                }
            ],
            "_gemini_raw_model_parts": [signed_part],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "name": "calendar.create_event",
            "content": "{\"status\":\"ok\"}",
        },
    ]

    _model, contents, _kwargs, _request_options = provider._gemini_stream_build_request(
        api_key="test_key",
        model="gemini-3-flash-preview",
        messages=messages,
        tools=None,
        image_data=None,
        force_no_tools=False,
        force_tool_name=None,
    )

    mock_gen_model.assert_called_once_with(model_name="gemini-3-flash-preview", system_instruction=None)
    assert contents[1]["parts"][0] is signed_part
    assert contents[2]["parts"][0].function_response.name == "calendar_create_event"


@pytest.mark.asyncio
@patch("backend.llm_providers.gemini.service._calculate_and_log_cost")
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


def test_convert_tools_to_gemini_format_resolves_pydantic_defs_refs():
    class Address(BaseModel):
        city: str

    class PersonArgs(BaseModel):
        name: str
        address: Address

    provider = GeminiServiceProvider()
    gemini_tools = provider._convert_tools_to_gemini_format(
        [
            {
                "name": "save_person",
                "description": "save person",
                "parameters": PersonArgs.model_json_schema(),
            }
        ]
    )

    assert len(gemini_tools) == 1
    params = gemini_tools[0]["function_declarations"][0]["parameters"]
    assert "$defs" not in params
    assert "$ref" not in json.dumps(params)
    assert params["properties"]["address"]["type"] == "object"
    assert "city" in params["properties"]["address"]["properties"]


def test_convert_tools_to_gemini_format_falls_back_on_bad_ref(caplog):
    provider = GeminiServiceProvider()
    tool_schema = {
        "type": "object",
        "properties": {"payload": {"$ref": "#/$defs/DoesNotExist"}},
        "$defs": {"SomeOther": {"type": "object", "properties": {}}},
    }

    gemini_tools = provider._convert_tools_to_gemini_format(
        [{"name": "broken_tool", "description": "broken", "parameters": tool_schema}]
    )

    assert len(gemini_tools) == 1
    params = gemini_tools[0]["function_declarations"][0]["parameters"]
    assert params == {"type": "object", "properties": {}}
    assert "sanitization failed" in caplog.text


def test_convert_tools_to_gemini_format_strips_unsupported_validation_keywords():
    provider = GeminiServiceProvider()
    tool_schema = {
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "minLength": 3,
                "pattern": ".*\\S.*",
            },
            "distance": {
                "type": "number",
                "minimum": 0,
            },
        },
        "required": ["origin"],
    }

    gemini_tools = provider._convert_tools_to_gemini_format(
        [{"name": "system.routing", "description": "routing", "parameters": tool_schema}]
    )

    assert len(gemini_tools) == 1
    params = gemini_tools[0]["function_declarations"][0]["parameters"]
    params_json = json.dumps(params)
    assert "minLength" not in params_json
    assert "pattern" not in params_json
    assert "minimum" not in params_json


@pytest.mark.asyncio
@patch("backend.llm_providers.gemini.service._calculate_and_log_cost", return_value=({}, {"total_cost": 0.0}))
@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
async def test_reason_10_stops_after_single_text_fallback(
    _mock_configure,
    mock_gen_model,
    _mock_calculate_cost,
):
    mock_model_instance = AsyncMock()
    mock_response = MagicMock()
    mock_response.prompt_feedback.block_reason = None
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].finish_reason = 10
    mock_response.candidates[0].content.parts = [MagicMock()]
    mock_response.usage_metadata = MagicMock(prompt_token_count=0, candidates_token_count=0)
    mock_model_instance.generate_content_async.return_value = mock_response
    mock_gen_model.return_value = mock_model_instance

    provider = GeminiServiceProvider()
    result = await provider.generate_response(
        api_key="test_key",
        model="gemini-3-flash-preview",
        messages=[{"role": "user", "content": "Erstelle ein PDF."}],
        tools=[{"name": "system.create_pdf"}],
    )

    assert result["type"] == "text"
    assert "Die Tool-Aktion wurde bereits ausgeführt" in result["text"]
    assert mock_model_instance.generate_content_async.await_count == 3
