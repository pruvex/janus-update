

**Zyklus: Implementierung des LLM-Gateway**

*   **Stufe 1: Validierung**
    *   `python health_check.py` erfolgreich ausgeführt.
    *   Existenz von `backend/config.json` validiert.
*   **Stufe 2: Planung & Recherche**
    *   Entscheidung für die `requests`-Bibliothek für HTTP-Anfragen.
*   **Stufe 3: Implementierung**
    *   `requests` zu `backend/requirements.txt` hinzugefügt und installiert.
    *   `backend/llm_gateway.py` mit der Funktion `call_llm` erstellt.
