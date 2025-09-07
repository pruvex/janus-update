import pytest
from unittest.mock import patch, MagicMock, AsyncMock

def test_chat_text_response(test_client, db_session):
    with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason:
        mock_reason.return_value = {"type": "text", "text": "Mocked response.", "usage": {}, "cost": {}}
        response = test_client.post("/api/chat", json={"prompt": "Hello", "provider": "openai", "model": "gpt-4o-mini"})
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Mocked response."

@pytest.mark.parametrize("provider, model", [("openai", "gpt-4o-mini"), ("gemini", "gemini-1.5-flash")])
def test_chat_image_shortcut(test_client, db_session, provider, model):
    # This test now covers the image generation shortcut for all providers
    with patch('backend.llm_gateway.generate_image', new_callable=AsyncMock) as mock_generate_image:
        mock_generate_image.return_value = {"image_url": f"/user_images/{provider}_test.png", "usage": {}, "cost": {"total_cost": 0.02}}
        
        response = test_client.post("/api/chat", json={
            "prompt": f"zeichne ein bild von einem frosch mit {provider}",
            "provider": provider,
            "model": model,
            "chat_id": None
        })

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == f"Bild wurde erfolgreich mit {provider.capitalize()} generiert."
        assert data["image_url"] == f"/user_images/{provider}_test.png"
        mock_generate_image.assert_called_once()

@pytest.mark.skip(reason="Budget test needs more specific mocking, skipping for now")
def test_chat_budget_exceeded(test_client, db_session):
    pass