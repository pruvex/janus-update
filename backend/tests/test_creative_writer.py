import json

import requests

url = "http://localhost:8001/api/chat"
headers = {"Content-Type": "application/json"}
body = {
    "prompt": "Schreibe eine kurze Horrorgeschichte im Stil von Stephen King über ein altes Auto, das verlassen an einer Landstraße in Maine steht.",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "chat_id": 1,
}

try:
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
