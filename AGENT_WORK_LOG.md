## Zyklus: Reparatur der Feedback-Schleife

**Stufe 3: Implementierung & Arbeits-Logbuch**

*   **WAS:** `is_confirmation`-Funktion in `backend/main.py` aktualisiert.
*   **WARUM:** Um die Erkennung von Bestätigungen durch den Benutzer robuster zu machen und falsche positive Ergebnisse zu vermeiden.

## Zyklus: Behebung des Datenbank-Schema-Fehlers

**Stufe 3: Implementierung & Arbeits-Logbuch**

*   **WAS:** `init_db()`-Funktion in `backend/database.py` modifiziert, um `sqlite3.OperationalError` (Schema-Mismatch) zu behandeln.
*   **WARUM:** Um sicherzustellen, dass die Anwendung auch bei einer älteren Datenbankversion startet, indem die alte Datenbank gelöscht und eine neue mit dem korrekten Schema erstellt wird. Dies ist eine temporäre Lösung für die Entwicklungsphase.
*   **WAS:** Vollständiger Installer (`Janus Projekt Setup 1.1.0.exe`) neu gebaut, um die Änderungen zu integrieren.
*   **WARUM:** Um die aktualisierte Funktionalität auf Testsystemen bereitzustellen.

## Zyklus: Korrektur des OpenAI Bildgenerierungsmodells

**Stufe 3: Implementierung & Arbeits-Logbuch**

*   **WAS:** `id` des DALL-E 3 (Standard) Bildmodells in `backend/model_catalog.json` von `"dall-e-3-standard"` zu `"dall-e-3"` geändert.
*   **WARUM:** Um den `400 Bad Request` Fehler bei der OpenAI Bildgenerierung auf dem Testsystem zu beheben, da die OpenAI API den Modellnamen `"dall-e-3-standard"` nicht erkennt, aber `"dall-e-3"` unterstützt.
*   **WAS:** Vollständiger Installer (`Janus Projekt Setup 1.1.0.exe`) neu gebaut, um die Änderungen zu integrieren.
*   **WARUM:** Um die aktualisierte Funktionalität auf Testsystemen bereitzustellen.
