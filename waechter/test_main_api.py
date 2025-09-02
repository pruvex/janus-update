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

def test_chat_cross_chat_tool_call(test_client, db_session):
    # Wir mocken wieder die Kette
    with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason, 
         patch('backend.tool_registry.cross_chat_memory_tool') as mock_memory_tool:
        # 1. Simuliere, dass das LLM das Memory-Tool aufrufen will
        mock_reason.return_value = {
            "type": "tool_code",
            "tool_name": "cross_chat_memory_tool",
            "tool_args": {"query": "past topics"}
        }
                # 2. Simuliere das Ergebnis der Tool-Ausführung
        mock_memory_tool.return_value = {
            "output": "--- ZUSAMMENFASSUNGEN ---\nThema: Elektroautos",
            "usage": {}, "cost": {}
        }
        response = test_client.post("/api/chat", json={
            "prompt": "was haben wir besprochen?", "provider": "openai", "model": "gpt-4o-mini"
        })
        # 3. Überprüfe die generische Antwort
        assert response.status_code == 200
        data = response.json()
        assert "Ergebnis von Tool 'cross_chat_memory_tool'" in data["text"]
        assert "Thema: Elektroautos" in data["text"]
                # Überprüfe, ob das Tool mit den korrekten Argumenten aufgerufen wurde
        # (beachte, dass 'db' vom Dispatcher hinzugefügt wird, was wir hier nicht direkt testen)
        mock_memory_tool.assert_called_once()
        args, kwargs = mock_memory_tool.call_args
        assert kwargs['query'] == 'past topics'


def test_chat_gemini_image_shortcut(test_client, db_session):
    """
    Tests the keyword-based shortcut for Gemini image generation.
    """
    with patch('backend.llm_gateway._call_gemini_image_generation_api', new_callable=AsyncMock) as mock_gemini_image_api, 
         patch('backend.main.load_model_catalog') as mock_load_catalog: # Wir mocken den Katalog, um Abhängigkeiten zu reduzieren
                # 1. Simuliere den Modell-Katalog
        mock_load_catalog.return_value = {
            "gemini-2.5-flash": {"image_generation_model_id": "gemini-2.5-flash-image-preview"}
        }
        # 2. Simuliere eine erfolgreiche Bild-API-Antwort
        mock_gemini_image_api.return_value = {
            "image_url": "/user_images/gemini_test.png",
            "usage": {}, "cost": {"total_cost": 0.02}
        }
                response = test_client.post("/api/chat", json={
            "prompt": "zeichne ein bild von einem frosch",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "chat_id": 1 # Annahme: Chat 1 existiert
        })
        # 3. Überprüfe das Ergebnis
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Bild wurde erfolgreich mit Gemini generiert."
        assert data["image_url"] == "/user_images/gemini_test.png"
                # Stelle sicher, dass die teure reason_and_respond NICHT aufgerufen wurde
        # (Dies erfordert einen weiteren Mock, kann aber vorerst weggelassen werden,
        # die Log-Ausgabe würde es im echten Lauf bestätigen)

def test_chat_budget_exceeded(test_client, db_session):
    """
    Tests that a 402 Payment Required error is raised when budget is exceeded.
    """
    # Wir mocken die Funktion, die die Kosten berechnet
    with patch('backend.database.get_costs_for_month') as mock_get_costs:
        # 1. Simuliere, dass die Kosten das Budget übersteigen
        mock_get_costs.return_value = 999.0 # (Budget ist standardmäßig 10.0)
        response = test_client.post("/api/chat", json={
            "prompt": "irgendeine frage",
            "provider": "openai",
            "model": "gpt-4o-mini"
        })
        # 2. Überprüfe den Fehlercode und die Nachricht
        assert response.status_code == 402
        data = response.json()
        assert "Monthly budget" in data["detail"]