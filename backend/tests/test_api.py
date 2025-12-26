import requests

try:
    response = requests.get("http://localhost:8001/api/rag/collections")
    response.raise_for_status()
    print(response.json())
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
