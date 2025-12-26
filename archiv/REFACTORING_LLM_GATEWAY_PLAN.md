## Refactoring-Plan: Modularisierung des LLM-Gateways nach Providern

**Ziel:** Entkopplung der LLM-Provider-spezifischen Logik und Tool-Implementierungen, um die Wartbarkeit, Skalierbarkeit und Testbarkeit des Systems zu verbessern und das Risiko von Regressionen zu minimieren.

**Betroffene Dateien (Übersicht):**

*   `backend/llm_gateway.py` (wird zum zentralen Router)
*   `backend/tool_registry.py`
*   `backend/schemas.py`
*   `backend/main.py` (API-Endpunkte)
*   `backend/memory_manager.py` (enthält `cross_chat_memory_tool`)
*   Neue Dateien:
    *   `backend/llm_providers/openai_service.py`
    *   `backend/llm_providers/gemini_service.py`
    *   `backend/llm_providers/__init__.py` (für Paketstruktur)
*   Testdateien:
    *   `backend/test_llm_integration_filesystem.py`
    *   `backend/test_llm_gateway.py` (falls vorhanden, anpassen)
    *   Neue Testdateien für die Provider-Services

**Detaillierter Plan und Schritte:**

### Phase 1: Vorbereitung und Strukturierung

1.  **Verzeichnis `backend/llm_providers` erstellen:**
    *   `backend/llm_providers/__init__.py` (leer)
2.  **`backend/llm_providers/openai_service.py` erstellen:**
    *   Initialer Inhalt: Importe für `openai`, `logging`, `List`, `Dict`, `Optional`, `retry`, `stop_after_attempt`, `wait_exponential`, `calculate_cost`, `MODEL_PRICES`, `get_all_tool_definitions`.
    *   Kopieren von `_call_openai_api` aus `backend/llm_gateway.py` hierher.
    *   Kopieren von `generate_image_tool` aus `backend/llm_gateway.py` hierher.
    *   Anpassung der Importe innerhalb dieser Datei.
3.  **`backend/llm_providers/gemini_service.py` erstellen:**
    *   Initialer Inhalt: Importe für `google.generativeai`, `logging`, `List`, `Dict`, `Optional`, `retry`, `stop_after_attempt`, `wait_exponential`, `calculate_cost`, `MODEL_PRICES`, `image_manager`, `uuid`.
    *   Kopieren von `_call_gemini_api` aus `backend/llm_gateway.py` hierher.
    *   Kopieren von `_call_gemini_image_generation_api` aus `backend/llm_gateway.py` hierher.
    *   Anpassung der Importe innerhalb dieser Datei.

### Phase 2: Refactoring des LLM-Gateways und der Tool-Registrierung

1.  **`backend/llm_gateway.py` anpassen (wird zum Router):**
    *   Entfernen von `_call_openai_api`, `_call_gemini_api`, `_call_gemini_image_generation_api`, `generate_image_tool`.
    *   Entfernen des Imports `from backend.tool_registry import get_all_tool_definitions`.
    *   Importieren der neuen Provider-Services: `from backend.llm_providers import openai_service, gemini_service`.
    *   Die Funktion `call_llm` anpassen, um den Provider zu identifizieren und den Aufruf an den entsprechenden Provider-Service zu delegieren. `tools` sollte weiterhin als Argument übergeben werden.
    *   Die Funktion `reason_and_respond` anpassen, um `call_llm` mit den korrekten Argumenten aufzurufen.
2.  **`backend/tool_registry.py` anpassen:**
    *   Entfernen der Imports `from backend.llm_gateway import generate_image_tool` und `from backend.memory_manager import cross_chat_memory_tool`.
    *   Importieren der Tool-Funktionen von ihren neuen Speicherorten:
        *   `from backend.llm_providers.openai_service import generate_image_tool`
        *   `from backend.memory_manager import cross_chat_memory_tool`
    *   Sicherstellen, dass alle Tools korrekt registriert sind.

### Phase 3: Anpassung der Aufrufe und Tests

1.  **`backend/main.py` anpassen:**
    *   Überprüfen, ob `llm_gateway.py` korrekt aufgerufen wird und ob die `tools`-Argumente korrekt übergeben werden.
    *   Anpassung der Bildgenerierungs-Endpunkte, falls diese direkt `llm_gateway.py` aufrufen.
2.  **`backend/test_llm_integration_filesystem.py` anpassen:**
    *   Die Mocks für `backend.llm_gateway.reason_and_respond` bleiben bestehen.
    *   Die Tests sollten weiterhin funktionieren, da sie die Schnittstelle von `reason_and_respond` mocken und die Tool-Aufrufe über `TOOL_REGISTRY` ausführen.
3.  **Neue Testdateien erstellen:**
    *   `backend/llm_providers/test_openai_service.py`: Unit-Tests für `openai_service.py`.
    *   `backend/llm_providers/test_gemini_service.py`: Unit-Tests für `gemini_service.py`.
    *   Diese Tests sollten die Funktionalität der Provider-spezifischen APIs und der dort implementierten Tools abdecken.

### Phase 4: Bereinigung und Verifizierung

1.  **Alte Imports entfernen:** Sicherstellen, dass keine alten, nicht mehr benötigten Imports in den Dateien verbleiben.
2.  **Alle Tests ausführen:** Sicherstellen, dass alle Unit- und Integrationstests grün sind.
3.  **Dokumentation aktualisieren:** Den Refactoring-Plan in der Hauptdokumentation (`REFAKTORING_PLANalt.md`, `blocks.md`) vermerken.

**Geschätzter Aufwand und Nutzen:**

*   **Aufwand:**
    *   **Initial:** Mittel bis Hoch. Es erfordert ein gutes Verständnis der bestehenden Codebasis und sorgfältiges Verschieben und Anpassen von Funktionen und Imports. Schätzungsweise 1-2 Tage konzentrierter Arbeit, abhängig von der Komplexität der LLM-spezifischen Logik.
    *   **Laufend:** Gering. Das Hinzufügen neuer Provider oder das Ändern der Logik für einen bestehenden Provider wird deutlich einfacher und schneller.
*   **Nutzen:**
    *   **Modularität:** Starke Reduzierung der Kopplung zwischen Providern.
    *   **Wartbarkeit:** Leichtere Fehlerbehebung und Code-Verständnis.
    *   **Skalierbarkeit:** Einfaches Hinzufügen neuer LLM-Provider.
    *   **Testbarkeit:** Bessere Isolation für Unit-Tests der Provider-spezifischen Logik.
    *   **Fehlerreduzierung:** Geringeres Risiko von Regressionen bei Änderungen.