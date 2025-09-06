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
