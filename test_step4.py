# test_step4.py

import requests
import json

# Die URL unseres API-Endpunkts
url = "http://localhost:8001/api/styles/profiles"

# Die Daten, die wir senden wollen (als Python Dictionary)
payload = {
  "profile_key": "StephenKing",
  "profile_data": {
    "genre": "Horror / Thriller",
    "author_style": "Stephen King",
    "key_elements": [
      "Klarer und direkter Schreibstil",
      "Integration von übernatürlichen Elementen in alltägliche Situationen",
      "Entwicklung komplexer Charaktere mit inneren Konflikten",
      "Langsam aufbauende Spannung, die auf psychologischem Horror basiert"
    ],
    "complexity": "komplex"
  }
}

# Sende den Request
try:
    print("Sende POST-Request an API...")
    # requests wandelt das Dictionary automatisch in perfektes JSON um
    response = requests.post(url, json=payload)

    # Überprüfe die Antwort
    response.raise_for_status()  # Löst einen Fehler aus, wenn der Status-Code nicht 2xx ist

    print("--- TEST ERFOLGREICH ---")
    print(f"Status-Code: {response.status_code}")
    print("Antwort vom Server:")
    print(response.json())

except requests.exceptions.RequestException as e:
    print("--- TEST FEHLGESCHLAGEN ---")
    print(f"Ein Fehler ist aufgetreten: {e}")
    if e.response:
        print("Fehlerdetails vom Server:")
        print(e.response.text)