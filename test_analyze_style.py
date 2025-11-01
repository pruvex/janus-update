import requests
import json

collection_name = "StephenKing"
url = f"http://localhost:8001/api/rag/collections/{collection_name}/analyze-style"

try:
    response = requests.post(url)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
