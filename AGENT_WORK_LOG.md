

**Zyklus: Implementierung des API-Key-Managements**

*   **Stufe 1: Validierung**
    *   `python health_check.py` erfolgreich ausgeführt.
    *   Existenz von `backend/main.py` und `backend/config.json` validiert.
*   **Stufe 2: Planung & Recherche**
    *   Planung der Backend-Endpunkte (`GET /api/keys`, `POST /api/keys`) und der Key-Lade-Logik im Chat-Endpunkt.
    *   Planung der Frontend-Anpassungen (`index.html` für Provider-Dropdown, `settings.js` für API-Aufrufe).
*   **Stufe 3: Implementierung**
    *   **Backend:** `backend/main.py` um Key-Management-Endpunkte und Key-Lade-Logik erweitert.
    *   **Frontend:** `frontend/index.html` angepasst, um Provider-Input durch Select zu ersetzen.
    *   **Frontend:** `frontend/js/settings.js` mit Logik zum Laden und Speichern von API-Keys aktualisiert.
