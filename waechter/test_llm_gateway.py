
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Füge das übergeordnete Verzeichnis zum Python-Pfad hinzu, um das Backend-Modul zu finden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import llm_gateway

class TestLlmGateway(unittest.TestCase):

    @patch('requests.post')
    def test_call_llm(self, mock_post):
        # Richte den Mock für die requests.post-Methode ein
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_response

        # Rufe die zu testende Funktion auf
        provider = "test-provider"
        prompt = "Test prompt"
        api_key = "test-api-key"
        response = llm_gateway.call_llm(provider, prompt, api_key)

        # Überprüfe, ob requests.post mit den richtigen Argumenten aufgerufen wurde
        mock_post.assert_called_once_with(
            f"https://api.mockllm.dev/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": provider,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )

        # Überprüfe, ob die Antwort korrekt ist
        self.assertEqual(response, {"choices": [{"message": {"content": "Test response"}}]})

if __name__ == '__main__':
    unittest.main()
