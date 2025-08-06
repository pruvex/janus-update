AGENTIC HANDLUNGSPLAN:
Dein Ziel: Implementiere die grundlegende Backend-Logik für das Key-Management, indem du eine config.json-Datei erstellst und eine Funktion zum Auslesen der API-Keys schreibst.
Relevante PHASE_X.md: C:\KI\Janus-Projekt\PHASE_2_KERNFUNKTIONALITAET.md
Der Plan:
Stufe 1: Validierung des Ausgangszustands
Führe python health_check.py aus, um die Integrität des Projekts zu bestätigen.
Stufe 3: Implementierung & Arbeits-Logbuch
Implementierung (Platzhalter-Konfigurationsdatei): Erstelle eine neue Datei C:\KI\Janus-Projekt\backend\config.json mit einer beispielhaften Struktur.
code
Code
'''
{
  "api_keys": {
    "openai": "DEIN_OPENAI_KEY_HIER",
    "gemini": "DEIN_GEMINI_KEY_HIER"
  }
}
'''
Implementierung (Key-Management-Modul): Erstelle eine neue Python-Datei C:\KI\Janus-Projekt\backend\key_manager.py, die die Logik zum Laden der Keys enthält.
code
Code
'''
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

def get_api_key(provider: str) -> str | None:
    """Lädt den API-Key für einen gegebenen Anbieter aus der config.json."""
    if not CONFIG_PATH.exists():
        return None
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    
    return config.get("api_keys", {}).get(provider)
'''
Stufe 4: Dynamische Verifizierung (Funktionstest)
Erstelle ein temporäres Test-Skript C:\KI\Janus-Projekt\waechter\tests\test_key_manager.py.
Dieses Skript muss die get_api_key-Funktion importieren und zwei Fälle testen:
Erfolgsfall: Rufe get_api_key("openai") auf und überprüfe, ob das Ergebnis der Platzhalter-String DEIN_OPENAI_KEY_HIER ist.
Fehlerfall: Rufe get_api_key("non_existent_provider") auf und überprüfe, ob das Ergebnis None ist.
Führe dieses Test-Skript aus.
Stufe 5: Aufräumen & Finale Validierung
Lösche das temporäre Test-Skript.
Führe python health_check.py erneut aus.
Erfolgs-Kriterien:
Die config.json und key_manager.py müssen erstellt werden.
Das Test-Skript muss beide Fälle (Erfolg und Fehler) korrekt validieren.
Finale Erfolgsmeldung:
Gib die folgende Meldung aus: Aufgabe erfolgreich abgeschlossen: Die grundlegende Logik für das Key-Management wurde im Backend implementiert und durch Tests verifiziert.