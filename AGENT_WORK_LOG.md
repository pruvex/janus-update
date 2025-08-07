**Zyklus: Implementierung des Chat-API-Endpunkts**

*   **Stufe 1: Validierung**
    *   `python health_check.py` erfolgreich ausgeführt.
    *   Existenz von `backend/main.py` und `backend/llm_gateway.py` validiert.
*   **Stufe 2: Planung & Recherche**
    *   Analyse von `backend/main.py` zur Definition von FastAPI-Routen.
    *   Planung des `ChatRequest` Pydantic-Modells.
*   **Stufe 3: Implementierung**
    *   `backend/main.py` um den `/api/chat`-Endpunkt und das `ChatRequest`-Modell erweitert.