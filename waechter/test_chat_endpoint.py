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

    @patch('keyring.get_password')
    @patch('backend.llm_gateway.call_llm')
    @patch('backend.main.load_config')
    @patch('backend.main.save_config')
    def test_chat_endpoint(self, mock_save_config, mock_load_config, mock_call_llm, mock_get_password):
        # Richte den Mock für die llm_gateway.call_llm-Funktion ein
        mock_call_llm.return_value = {"text": "mocked LLM answer", "usage": {"input_tokens": 10, "output_tokens": 20}, "cost": {"total_cost": 0.001}}
        mock_get_password.return_value = "mocked-api-key"

        # Richte den Mock für load_config ein, um einen API-Key bereitzustellen
        mock_load_config.return_value = {"api_keys": {"test-provider": "test-api-key-123"}}

        # Rufe den zu testenden Endpunkt auf
        response = self.client.post("/api/chat", json={"prompt": "Test prompt", "provider": "test-provider", "model": "test-model"})

        # Überprüfe, ob der Endpunkt den richtigen Statuscode zurückgibt
        self.assertEqual(response.status_code, 200)

        # Überprüfe, ob der Response-Body der vom Mock definierten Antwort entspricht
        self.assertEqual(response.json(), {"sender": "model", "text": "mocked LLM answer", "image_url": None})

        # Überprüfe, ob die llm_gateway.call_llm-Funktion mit den richtigen Argumenten aufgerufen wurde
        mock_call_llm.assert_called_once_with("test-provider", "test-model", "Test prompt", "mocked-api-key")

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
        self.assertEqual(response.json(), {"api_keys": {"openai": "********", "gemini": "********"}})

    @patch('keyring.set_password')
    @patch('backend.main.load_config')
    def test_post_api_keys(self, mock_load_config, mock_set_password):
        mock_load_config.return_value = {"api_keys": {}}
        response = self.client.post("/api/keys", json={"provider": "new-provider", "api_key": "new-api-key"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "API Key saved successfully"})
        mock_set_password.assert_called_once_with("Janus-Projekt", "new-provider", "new-api-key")

if __name__ == '__main__':
    unittest.main()
