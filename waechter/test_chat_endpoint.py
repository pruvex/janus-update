import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os
import json

# Füge das übergeordnete Verzeichnis zum Python-Pfad hinzu, um das Backend-Modul zu finden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app

class TestChatEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch('backend.llm_gateway.call_llm')
    @patch('backend.main.load_config')
    @patch('backend.main.save_config')
    def test_chat_endpoint(self, mock_save_config, mock_load_config, mock_call_llm):
        # Richte den Mock für die llm_gateway.call_llm-Funktion ein
        mock_call_llm.return_value = {"choices": [{"message": {"content": "mocked LLM answer"}}]}

        # Richte den Mock für load_config ein, um einen API-Key bereitzustellen
        mock_load_config.return_value = {"api_keys": {"test-provider": "test-api-key-123"}}

        # Rufe den zu testenden Endpunkt auf
        response = self.client.post("/api/chat", json={"prompt": "Test prompt", "provider": "test-provider"})

        # Überprüfe, ob der Endpunkt den richtigen Statuscode zurückgibt
        self.assertEqual(response.status_code, 200)

        # Überprüfe, ob der Response-Body der vom Mock definierten Antwort entspricht
        self.assertEqual(response.json(), {"choices": [{"message": {"content": "mocked LLM answer"}}]})

        # Überprüfe, ob die llm_gateway.call_llm-Funktion mit den richtigen Argumenten aufgerufen wurde
        mock_call_llm.assert_called_once_with("test-provider", "Test prompt", "test-api-key-123")

    def test_chat_endpoint_with_invalid_payload(self):
        # Rufe den Endpunkt mit einem ungültigen Payload auf (fehlender "prompt")
        response = self.client.post("/api/chat", json={"provider": "test-provider"})

        # Überprüfe, ob der Statuscode 422 (Unprocessable Entity) ist
        self.assertEqual(response.status_code, 422)

    @patch('backend.main.load_config')
    @patch('backend.main.save_config')
    def test_get_api_keys(self, mock_save_config, mock_load_config):
        mock_load_config.return_value = {"api_keys": {"test-provider-1": "key1", "test-provider-2": "key2"}}
        response = self.client.get("/api/keys")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"api_keys": {"test-provider-1": "key1", "test-provider-2": "key2"}})

    @patch('backend.main.load_config')
    @patch('backend.main.save_config')
    def test_post_api_keys(self, mock_save_config, mock_load_config):
        mock_load_config.return_value = {"api_keys": {}}
        response = self.client.post("/api/keys", json={"provider": "new-provider", "api_key": "new-api-key"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "API Key saved successfully"})
        mock_save_config.assert_called_once()
        # Überprüfe, ob save_config mit den aktualisierten Daten aufgerufen wurde
        saved_config = mock_save_config.call_args[0][0]
        self.assertEqual(saved_config["api_keys"]["new-provider"], "new-api-key")

if __name__ == '__main__':
    unittest.main()