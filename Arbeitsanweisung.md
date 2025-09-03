Schritt 1: llm_gateway.py anpassen
Ändern Sie die Funktion _call_gemini_image_generation_api, um image_manager.save_image_from_bytes zu verwenden.
Ersetzen Sie diesen Codeblock:
code
Python
# llm_gateway.py -> _call_gemini_image_generation_api

        image_url = None
        if image_data:
            file_name = f"{uuid.uuid4()}.png"
            file_path = os.path.join(IMAGE_DIR, file_name)
            with open(file_path, 'wb') as f:
                f.write(image_data)
            image_url = f"/user_images/{file_name}"
            logger.info(f"_call_gemini_image_generation_api: Image saved to {file_path}")
Mit diesem korrigierten Codeblock:
code
Python
# llm_gateway.py -> _call_gemini_image_generation_api (KORRIGIERT)

        image_url = None
        if image_data:
            # Verwende den image_manager, um die Konsistenz zu wahren
            file_name = f"{uuid.uuid4()}.png"
            image_url = image_manager.save_image_from_bytes(image_data, file_name)
            logger.info(f"_call_gemini_image_generation_api: Image saved. URL: {image_url}")
(Hinweis: Ich nehme an, Ihre save_image_from_bytes Funktion akzeptiert einen Dateinamen und gibt den Web-Pfad zurück. Passen Sie dies bei Bedarf an Ihre tatsächliche Implementierung an.)
Schritt 2: test_llm_gateway.py anpassen
Ihr Test ist schon fast perfekt. Wir müssen nur sicherstellen, dass der return_value des Mocks mit dem gemockten uuid übereinstimmt, damit die assert-Anweisung erfolgreich ist.
Ersetzen Sie diesen Codeblock:
code
Python
# test_llm_gateway.py -> test_call_gemini_image_generation_api_success

@pytest.mark.asyncio
@patch('backend.llm_gateway.image_manager.save_image_from_bytes', return_value="/user_images/generated.png")
@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
@patch('uuid.uuid4', return_value=uuid.UUID('00000000-0000-0000-0000-000000000001')) # Added UUID mock
async def test_call_gemini_image_generation_api_success(mock_configure, mock_generative_model_class, mock_save_image_from_bytes, mock_uuid):
    mock_model = AsyncMock()
    mock_generative_model_class.return_value = mock_model
    
    # Use an async def function as side_effect to ensure it's awaitable
    async def mock_generate_content_async_side_effect(*args, **kwargs):
        return MagicMock(
            candidates=[MagicMock(content=MagicMock(parts=[MagicMock(inline_data=MagicMock(data=b"image_data"))]))]
        )
    mock_model.generate_content_async.side_effect = mock_generate_content_async_side_effect

    result = await _call_gemini_image_generation_api("test_key", "gemini-image-model", "a cat")

    assert result["text"] == ""
    assert result["image_url"] == "/user_images/00000000-0000-0000-0000-000000000001.png" # Assert with mocked UUID
    mock_save_image_from_bytes.assert_called_once_with(b"image_data")
Mit diesem korrigierten Codeblock:
code
Python
# test_llm_gateway.py -> test_call_gemini_image_generation_api_success (KORRIGIERT)

@pytest.mark.asyncio
# Der return_value des Mocks muss mit dem gemockten UUID übereinstimmen
@patch('backend.llm_gateway.image_manager.save_image_from_bytes', return_value="/user_images/00000000-0000-0000-0000-000000000001.png")
@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
@patch('uuid.uuid4', return_value=uuid.UUID('00000000-0000-0000-0000-000000000001'))
async def test_call_gemini_image_generation_api_success(mock_configure, mock_generative_model_class, mock_save_image_from_bytes, mock_uuid):
    mock_model = AsyncMock()
    mock_generative_model_class.return_value = mock_model
    
    async def mock_generate_content_async_side_effect(*args, **kwargs):
        return MagicMock(
            candidates=[MagicMock(content=MagicMock(parts=[MagicMock(inline_data=MagicMock(data=b"image_data"))]))]
        )
    mock_model.generate_content_async.side_effect = mock_generate_content_async_side_effect

    result = await _call_gemini_image_generation_api("test_key", "gemini-image-model", "a cat")

    assert result["text"] == ""
    # Diese Assertion wird nun erfolgreich sein
    assert result["image_url"] == "/user_images/00000000-0000-0000-0000-000000000001.png"
    
    # Wir müssen auch prüfen, dass die Funktion mit den richtigen Argumenten aufgerufen wurde
    expected_filename = "00000000-0000-0000-0000-000000000001.png"
    mock_save_image_from_bytes.assert_called_once_with(b"image_data", expected_filename)