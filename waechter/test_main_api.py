# waechter/test_main_api.py
from unittest.mock import patch, MagicMock, AsyncMock

def test_chat_text_response(test_client, db_session):
    with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason:
        mock_reason.return_value = {
            "type": "text", "text": "Mocked response.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "cost": {"total_cost": 0.0001}
        }
        response = test_client.post("/api/chat", json={
            "prompt": "Hello", "provider": "openai", "model": "gpt-4o-mini"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Mocked response."

def test_chat_image_tool_call(test_client, db_session):
    with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason,         patch('backend.tool_registry.TOOL_REGISTRY') as mock_tool_registry,         patch('backend.image_manager.save_image_from_url', new_callable=AsyncMock) as mock_save,         patch('backend.llm_gateway.generate_image_tool', new_callable=AsyncMock) as mock_generate_image_tool: # Direct patch

        mock_reason.return_value = {
            "type": "tool_code", "tool_name": "generate_image_tool",
            "tool_args": {"prompt": "a cat"}
        }
        
        # Configure the direct mock for generate_image_tool
        mock_generate_image_tool.return_value = {
            "url": "http://example.com/cat.png", "usage": {}, "cost": {"total_cost": 0.04}
        }

        mock_tool = MagicMock()
        mock_tool.func = mock_generate_image_tool # Assign the mocked function
        mock_tool_registry.get.return_value = mock_tool
        
        mock_save.return_value = "/user_images/mocked_cat.png"

        response = test_client.post("/api/chat", json={
            "prompt": "draw a cat", "provider": "openai", "model": "gpt-4o-mini"
        })

        assert response.status_code == 200
        data = response.json()
        assert "Bild wurde erfolgreich generiert" in data["text"]
        assert data["image_url"] == "/user_images/mocked_cat.png"
        mock_generate_image_tool.assert_called_once_with(api_key="mock_api_key", prompt="a cat", size="1024x1024", quality="standard", response_format="url") # Assert on the directly mocked function