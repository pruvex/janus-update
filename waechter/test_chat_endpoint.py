
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
import sys
import os

# Füge das übergeordnete Verzeichnis zum Python-Pfad hinzu, um das Backend-Modul zu finden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app

class TestChatEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch('backend.llm_gateway.call_llm')
    def test_chat_endpoint(self, mock_call_llm):
        # Richte den Mock für die llm_gateway.call_llm-Funktion ein
        mock_call_llm.return_value = {"response": "mocked LLM answer"}

        # Rufe den zu testenden Endpunkt auf
        response = self.client.post("/api/chat", json={"prompt": "Test prompt", "provider": "test-provider"})

        # Überprüfe, ob der Endpunkt den richtigen Statuscode zurückgibt
        self.assertEqual(response.status_code, 200)

        # Überprüfe, ob der Response-Body der vom Mock definierten Antwort entspricht
        self.assertEqual(response.json(), {"response": "mocked LLM answer"})

        # Überprüfe, ob die llm_gateway.call_llm-Funktion mit den richtigen Argumenten aufgerufen wurde
        mock_call_llm.assert_called_once_with("test-provider", "Test prompt", "dummy_key_for_now")

    def test_chat_endpoint_with_invalid_payload(self):
        # Rufe den Endpunkt mit einem ungültigen Payload auf (fehlender "prompt")
        response = self.client.post("/api/chat", json={"provider": "test-provider"})

        # Überprüfe, ob der Statuscode 422 (Unprocessable Entity) ist
        self.assertEqual(response.status_code, 422)

if __name__ == '__main__':
    unittest.main()
