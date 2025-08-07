
import requests

def call_llm(provider: str, prompt: str, api_key: str):
    """
    Ruft eine LLM-API mit dem gegebenen Provider, Prompt und API-Key auf.
    """
    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        model = "gpt-3.5-turbo"
    elif provider == "gemini":
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        model = "gemini-1.5-flash"
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    headers = {
        "Content-Type": "application/json"
    }
    if provider == "openai":
        headers["Authorization"] = f"Bearer {api_key}"
    elif provider == "gemini":
        url += f"?key={api_key}"

    if provider == "openai":
        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    elif provider == "gemini":
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # Löst eine Ausnahme für HTTP-Fehler aus
    json_response = response.json()

    if provider == "gemini":
        # Gemini-Antwort in OpenAI-ähnliches Format umwandeln
        if "candidates" in json_response and len(json_response["candidates"]) > 0:
            first_candidate = json_response["candidates"][0]
            if "content" in first_candidate and "parts" in first_candidate["content"] and len(first_candidate["content"]["parts"]) > 0:
                return {"choices": [{"message": {"content": first_candidate["content"]["parts"][0]["text"]}}]}
        return {"choices": [{"message": {"content": "No valid response from Gemini."}}]}
    return json_response
