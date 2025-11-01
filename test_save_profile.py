import requests
import json

GENERATED_PROFILE = {
  "genre": "Psychologischer Thriller",
  "author_style": "Stephen King",
  "key_elements": [
    "Dichten, psychologischen Spannungsaufbau",
    "Alltagsnahe Charaktere mit inneren Dämonen",
    "Humorvolle Dialoge, die die Spannung konterkarieren",
    "Der Einsatz von alltäglichen Gegenständen als Symbole"
  ],
  "complexity": "komplex"
}

url = "http://localhost:8001/api/styles/profiles"
headers = {"Content-Type": "application/json"}
body = {
  "profile_key": "StephenKing",
  "profile_data": GENERATED_PROFILE
}

try:
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
