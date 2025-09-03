import pytest
from unittest.mock import patch, MagicMock, AsyncMock

def test_chat_text_response(test_client, db_session):
    with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason:
        mock_reason.return_value = {"type": "text", "text": "Mocked response.", "usage": {}, "cost": {}}
        response = test_client.post("/api/chat", json={"prompt": "Hello", "provider": "openai", "model": "gpt-4o-mini"})
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Mocked response."

# WIR MOCKEN DEN OPENAI CLIENT, UM AUTHENTICATION-FEHLER ZU VERMEIDEN
def test_chat_image_tool_call(test_client, db_session):
    with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason, \
         patch('openai.AsyncOpenAI') as mock_openai_client, \
         patch('backend.image_manager.save_image_from_url') as mock_save:
        
        mock_reason.return_value = {"type": "tool_code", "tool_name": "generate_image_tool", "tool_args": {"prompt": "a cat"}}
        
        # Simuliere die Antwort von DALL-E
        mock_image_response = MagicMock()
        mock_image_response.data = [MagicMock(url="http://example.com/cat.png")]
        mock_openai_client.return_value.images.generate = AsyncMock(return_value=mock_image_response)

        mock_save.return_value = "/user_images/mocked_cat.png"

        response = test_client.post("/api/chat", json={"prompt": "draw a cat", "provider": "openai", "model": "gpt-4o-mini"})

        assert response.status_code == 200
        data = response.json()
        assert "Tool 'generate_image_tool' erfolgreich ausgeführt" in data["text"]
        assert data["image_url"] == "/user_images/mocked_cat.png"

@pytest.mark.skip(reason="Needs setup with pre-existing chats, skipping for now")
def test_chat_cross_chat_tool_call(test_client, db_session):
    pass

def test_chat_gemini_image_shortcut(test_client, db_session):
    with patch('backend.llm_gateway._call_gemini_image_generation_api', new_callable=AsyncMock) as mock_gemini_image_api:
        mock_gemini_image_api.return_value = {"image_url": "/user_images/gemini_test.png", "usage": {}, "cost": {"total_cost": 0.02}}
        
        response = test_client.post("/api/chat", json=    {
            "prompt": "zeichne ein bild von einem frosch",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "chat_id": None # KORRIGIERT
        })

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Bild wurde erfolgreich mit Gemini generiert."
        assert data["image_url"] == "/user_images/gemini_test.png"

@pytest.mark.skip(reason="Budget test needs more specific mocking, skipping for now")
def test_chat_budget_exceeded(test_client, db_session):
    pass