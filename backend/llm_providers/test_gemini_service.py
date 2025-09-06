import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.llm_providers import gemini_service

@pytest.mark.asyncio
async def test_call_gemini_api():
    with patch('google.generativeai.GenerativeModel') as mock_gen_model:
        mock_model_instance = AsyncMock()
        mock_gen_model.return_value = mock_model_instance
        
        mock_response = AsyncMock()
        mock_response.text = "Test response"
        mock_model_instance.generate_content_async.return_value = mock_response
        
        # Mock count_tokens
        mock_model_instance.count_tokens.side_effect = [AsyncMock(return_value=MagicMock(total_tokens=10)), AsyncMock(return_value=MagicMock(total_tokens=5))]

        api_key = "test_key"
        model_id = "gemini-pro"
        chat_history = [{"role": "user", "content": "Hello"}]
        model_info = {}

        with patch('google.generativeai.configure') as mock_configure:
            result = await gemini_service._call_gemini_api(api_key, model_id, chat_history, model_info)

            mock_configure.assert_called_once_with(api_key=api_key)
            mock_gen_model.assert_called_once_with(model_id)
            mock_model_instance.generate_content_async.assert_called_once()
            assert result["type"] == "text"
            assert result["text"] == "Test response"

@pytest.mark.asyncio
async def test_call_gemini_image_generation_api():
    with patch('google.generativeai.GenerativeModel') as mock_gen_model:
        mock_model_instance = AsyncMock()
        mock_gen_model.return_value = mock_model_instance

        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data.data = b'image_data'
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]
        mock_model_instance.generate_content_async.return_value = mock_response

        with patch('backend.image_manager.save_image_from_bytes', return_value="/path/to/image.png") as mock_save_image:
            api_key = "test_key"
            model_id = "gemini-pro-vision"
            prompt = "mache ein bild von einem gelben haus"

            with patch('google.generativeai.configure') as mock_configure:
                result = await gemini_service._call_gemini_image_generation_api(api_key, model_id, prompt)

                mock_configure.assert_called_once_with(api_key=api_key)
                mock_gen_model.assert_called_once_with(model_id)
                mock_model_instance.generate_content_async.assert_called_once_with(prompt)
                mock_save_image.assert_called_once_with(b'image_data', description="gelben-haus", file_extension="png")
                assert result["image_url"] == "/path/to/image.png"

def test_extract_image_description_robustness():
    # Test with gemini prefix and common phrases
    prompt1 = "gemini:zeig mir bild blauen hauses"
    expected1 = "blauen-hauses"
    assert gemini_service._extract_image_description(prompt1) == expected1

    # Test with gpt prefix and common phrases
    prompt2 = "gpt:erstelle ein bild eines roten autos"
    expected2 = "roten-autos"
    assert gemini_service._extract_image_description(prompt2) == expected2

    # Test with mixed case and extra spaces
    prompt3 = "Mache EIN Bild VON einem GROSSEN Hund"
    expected3 = "grossen-hund"
    assert gemini_service._extract_image_description(prompt3) == expected3

    # Test with hyphens already present
    prompt4 = "generate an image of a sci-fi-city"
    expected4 = "sci-fi-city"
    assert gemini_service._extract_image_description(prompt4) == expected4

    # Test with only description
    prompt5 = "a beautiful landscape"
    expected5 = "beautiful-landscape"
    assert gemini_service._extract_image_description(prompt5) == expected5

    # Test with redundant phrases at the end
    prompt6 = "ein haus ein"
    expected6 = "haus"
    assert gemini_service._extract_image_description(prompt6) == expected6

    # Test with multiple hyphens
    prompt7 = "test---multiple---hyphens"
    expected7 = "test-multiple-hyphens"
    assert gemini_service._extract_image_description(prompt7) == expected7

    # Test with leading/trailing hyphens
    prompt8 = "-test-hyphens-"
    expected8 = "test-hyphens"
    assert gemini_service._extract_image_description(prompt8) == expected8

    # Test with special characters (should be removed)
    prompt9 = "image of a cat!@#$ with wings"
    expected9 = "cat-with-wings"
    assert gemini_service._extract_image_description(prompt9) == expected9

    # Test with empty string
    prompt10 = ""
    expected10 = ""
    assert gemini_service._extract_image_description(prompt10) == expected10

    # Test with only redundant phrases
    prompt11 = "mache ein bild von"
    expected11 = ""
    assert gemini_service._extract_image_description(prompt11) == expected11

    # Test with only model prefix
    prompt12 = "gemini:"
    expected12 = ""
    assert gemini_service._extract_image_description(prompt12) == expected12
