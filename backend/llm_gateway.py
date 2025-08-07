
import requests

def call_llm(provider: str, prompt: str, api_key: str):
    """
    Ruft eine LLM-API mit dem gegebenen Provider, Prompt und API-Key auf.
    """
    url = f"https://api.mockllm.dev/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": provider,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # Löst eine Ausnahme für HTTP-Fehler aus
    return response.json()
