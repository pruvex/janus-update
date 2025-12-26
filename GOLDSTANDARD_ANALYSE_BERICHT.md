# Goldstandard-Analyse des Janus-Projekts

## Zusammenfassung

Diese Analyse bewertet den aktuellen Zustand des Janus-Projekts im Hinblick auf den intern definierten "Goldstandard", der auf Best Practices und projektspezifischen Direktiven (insbesondere aus `GEMINI.md`) basiert. Während in einigen Bereichen solide Ansätze erkennbar sind, offenbart die Codebasis kritische Mängel in zentralen Aspekten wie Sicherheit, Testbarkeit und Wartbarkeit.

**Gesamtbewertung: ca. 32%**

## Detaillierte Bewertung

### 1. Code-Qualität & Stil (Backend)
*   **Bewertung:** 40%
*   **Stärken:** `ruff` ist als Linter integriert und es wird versucht, ihn zu nutzen.
*   **Schwächen:** Zahlreiche `ruff`-Fehler, insbesondere `E701` und `E702` (mehrere Anweisungen pro Zeile), verstoßen gegen PEP8 und beeinträchtigen die Lesbarkeit erheblich. Dies deutet auf mangelnde Konsequenz bei der Durchsetzung von Code-Stil-Regeln hin.

### 2. Code-Qualität & Stil (Frontend)
*   **Bewertung:** 20%
*   **Stärken:** Verwendung von ES-Modulen (`import`/`export`).
*   **Schwächen:** Keine Linter-Infrastruktur (`eslint` nicht installiert oder konfiguriert), viele globale Variablen, prozeduraler Code ohne klare Modul- oder Komponentenstruktur. Starke Kopplung an das DOM macht den Code fragil und schwer wartbar.

### 3. Testing (Backend: Unit/Integration)
*   **Bewertung:** 30%
*   **Stärken:** Eine beachtliche Anzahl von 114+ Tests existiert, die auf durchdachte Szenarien und Fehlerfälle hindeuten. Es gibt Anzeichen für Integrationstests (z.B. LLM-Integration).
*   **Schwächen:** Die Testsuite ist defekt und nicht lauffähig (zwei `ImportError`s verhindern die Test-Sammlung). Dadurch können Regressionen nicht zuverlässig erkannt werden. `pytest-cov` für die Abdeckung ist nicht installiert. Viele veraltete Abhängigkeiten (`PydanticDeprecatedSince20`).

### 4. Testing (Frontend: E2E)
*   **Bewertung:** 0%
*   **Stärken:** -
*   **Schwächen:** Nicht existent. Die `playwright.config.js` ist konfiguriert, verweist aber auf ein nicht existierendes Testverzeichnis (`waechter/tests/e2e`).

### 5. Architektur & Struktur
*   **Bewertung:** 50%
*   **Stärken:** Backend zeigt eine service-orientierte Architektur mit Dependency Injection (FastAPI `Depends`), die gute Ansätze zur Entkopplung bietet.
*   **Schwächen:** Das in `GEMINI.md` definierte `waechter`-Verzeichnis fehlt. `backend/main.py` und `ChatOrchestrator` sind "Gott-Objekte" mit zu vielen Verantwortlichkeiten. Wichtige Logik (z.B. Prompt-Erstellung, Tool-Auswahl) ist hart im Code verankert und nicht flexibel. API-Endpunkte in `main.py` sind unübersichtlich.

### 6. Fehlerbehandlung & Logging
*   **Bewertung:** 65%
*   **Stärken:** Systematisches Logging mit `logger.error` und `exc_info=True` ist weit verbreitet, was das Debugging erleichtert. Es gibt eine zentrale `logger_config.py`.
*   **Schwächen:** Exzessive Nutzung von zu allgemeinen `except Exception as e:`-Blöcken verhindert eine differenzierte Reaktion auf spezifische Fehlertypen und kann die Fehlerbehebung erschweren, selbst wenn geloggt wird.

### 7. Secret-Management
*   **Bewertung:** 10%
*   **Stärken:** Die Infrastruktur für sicheres Secret-Management (`keyring`, Umgebungsvariablen, `.gitignore` für `.env`-Dateien) ist grundsätzlich vorhanden und an vielen Stellen korrekt implementiert.
*   **Schwächen (KRITISCH):** Ein hartkodierter API-Schlüssel wurde in `tools/gemini-auth/use-api.ps1` gefunden. Dies stellt ein **schwerwiegendes Sicherheitsrisiko** dar und kompromittiert sofort das gesamte System.

### 8. Workflow & Automatisierung
*   **Bewertung:** 40%
*   **Stärken:** Das `AGENT_WORK_LOG.md` wird vorbildlich und detailliert geführt.
*   **Schwächen:** Das `health_check.py`-Skript ist veraltet und nicht funktionsfähig. Im Frontend fehlen jegliche Skripte (`npm test`, `npm run lint`, `npm run build`) in der `package.json`, was grundlegende Automatisierung vermissen lässt. Git-Historie konnte nicht analysiert werden.

---

## Empfohlener Maßnahmenplan (Priorisiert)

Die folgenden Punkte sollten priorisiert werden, um das Projekt näher an den Goldstandard heranzuführen.

### Prio 1: Kritische Sicherheitslücken und Stabilität beheben
1.  **Hartkodierten API-Schlüssel entfernen:**
    *   **Maßnahme:** Den hartkodierten `GEMINI_API_KEY` aus `tools/gemini-auth/use-api.ps1` entfernen und sicherstellen, dass alle API-Schlüssel ausschließlich über `keyring` oder Umgebungsvariablen geladen werden.
    *   **Begründung:** Dies ist ein unmittelbares Sicherheitsrisiko.

2.  **Testsuite reparieren:**
    *   **Maßnahme:** Die `ImportError`s in `backend/tests/llm_providers/test_gemini_service.py` und `backend/tests/test_tool_registry.py` beheben, um die Backend-Testsuite wieder lauffähig zu machen.
    *   **Begründung:** Eine funktionierende Testsuite ist entscheidend, um Regressionen zu verhindern und die Codequalität zu sichern.

### Prio 2: Code-Qualität und grundlegende Automatisierung verbessern
3.  **Backend-Code-Stil aufräumen:**
    *   **Maßnahme:** Alle `ruff`-Fehler im Backend beheben, insbesondere die `E701`/`E702`-Verstöße. `ruff format` könnte hier helfen.
    *   **Begründung:** Verbessert die Lesbarkeit, Wartbarkeit und Einhaltung von PEP8.

4.  **Frontend-Build- und Linting-Pipeline einrichten:**
    *   **Maßnahme:** `eslint` und notwendige Plugins als `devDependencies` in `frontend/package.json` installieren. `npm scripts` für `lint` und `build` hinzufügen.
    *   **Begründung:** Ermöglicht die Durchsetzung von Code-Stil-Regeln und einen standardisierten Build-Prozess.

5.  **`health_check.py` aktualisieren:**
    *   **Maßnahme:** Das `health_check.py`-Skript an die aktuelle Projektstruktur anpassen und erweitern, um alle relevanten Komponenten zu validieren.
    *   **Begründung:** Ein funktionsfähiger Health Check ist essenziell für die schnelle Diagnose von Problemen im Projekt.

### Prio 3: Architektonische Verbesserungen und fortgeschrittene Praktiken
6.  **`waechter`-Verzeichnis integrieren:**
    *   **Maßnahme:** Klären, welche Funktionalität das `waechter`-Verzeichnis haben sollte, und es gemäß der Architekturdokumentation implementieren.
    *   **Begründung:** Stellt die Einhaltung der definierten Architektur sicher.

7.  **`ChatOrchestrator` refaktorieren:**
    *   **Maßnahme:** Die `handle_chat_request`-Methode in kleinere, fokussierte Funktionen aufteilen und Verantwortlichkeiten besser delegieren, um das "God-Object"-Problem zu beheben.
    *   **Begründung:** Verbessert Modularität, Testbarkeit und Wartbarkeit.

8.  **Differenzierte Fehlerbehandlung implementieren:**
    *   **Maßnahme:** Allgemeine `except Exception as e:`-Blöcke durch spezifischere Exception-Typen ersetzen und jeweils eine angemessene Reaktion (z.B. Retry, spezifische Fehlermeldung) implementieren.
    *   **Begründung:** Erhöht die Robustheit und ermöglicht präzisere Fehlerreaktionen.

9.  **Frontend-Architektur verbessern:**
    *   **Maßnahme:** Eine klarere Strukturierung des Vanilla JS-Codes in Komponenten oder kleinere, gekapselte Module. Einsatz eines einfachen State-Management-Musters zur Reduzierung globaler Variablen.
    *   **Begründung:** Verbessert die Skalierbarkeit und Wartbarkeit des Frontends.

10. **E2E-Tests für das Frontend implementieren:**
    *   **Maßnahme:** E2E-Tests mit Playwright für kritische Benutzerflows implementieren. Das Testverzeichnis in der `playwright.config.js` korrigieren.
    *   **Begründung:** Sichert die Funktionalität der Benutzeroberfläche und verhindert Regressionen bei UI-Änderungen.

Dieser Bericht bietet einen klaren Fahrplan, um die Codebasis des Janus-Projekts schrittweise auf den Goldstandard zu heben.
