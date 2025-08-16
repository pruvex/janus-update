📑 Roadmap & Architekturplan für Chat- und Memory-System
1️⃣ Chats speichern (Persistenzschicht)

Problem: Chats gehen verloren nach Session-Ende.

Lösung: Aufbau einer Datenbank.

Technik:

DB: lokal SQLite (Single-User) oder Postgres/MySQL (Multi-User).

Tabellenstruktur:

chats: id, titel, erstellt_am

messages: id, chat_id, sender, timestamp, inhalt

2️⃣ Mehrere Chats verwalten

UI:

„Neuen Chat starten“

„Chatliste anzeigen“

Chat-Switcher (Seitenleiste o. Dropdown)

Backend:

API: /chat/{id} → Laden eines Chats

Jeder Chat = eindeutige ID → klare Trennung

3️⃣ Context Memory (pro Chat)

Ziel: Innerhalb eines Chats den Kontext halten.

Ansätze:

Kompletter Verlauf → für kleine Chats.

Rolling Summary → bei langen Chats: ältere Teile zusammenfassen, neue Nachrichten anhängen.

Funktionen:

Vorschläge: „Soll ich diese Info global merken?“

Kontextbezogene Nachfragen

Stabile Kohärenz trotz langer Verläufe

4️⃣ Übergreifendes Chat-Memory (Global Memory)

Ziel: Infos aus mehreren Chats verknüpfen.

Mechanik:

Relevante Ausschnitte aus allen Chats in Knowledgebase speichern.

Zugriff via Vektor-Suche (Embedding-Index).

Fähigkeiten:

Chatübergreifende Fragen: „Was haben wir Montag besprochen?“

Themenprojekte durchsuchbar & abrufbar

⚙️ Context-Window-Anpassung für verschiedene Modelle
Problem

Provider nutzen Modelle mit unterschiedlichem Tokenlimit (z. B. 4k, 16k, 32k, 200k).

Ohne Anpassung → Gefahr von Truncation / unvollständigem Kontext.

Lösung: Adaptive Context Manager

Tokenbudget ermitteln

Abhängig vom Modell (Provider API liefert Limit).

Beispiel: GPT-4o → 128k, Gemini 2.5 → 1M, LLaMA lokal → evtl. 4k–8k.

Budget-Verteilung definieren

z. B.:

70 % Verlauf/Memory

20 % aktuelle User-Query

10 % System-Prompts/Anweisungen

Context-Skalierung

Kleine Limits (4k–8k): Rolling Summary nutzen.

Mittlere Limits (16k–32k): Teilweise vollständiger Verlauf.

Große Limits (100k+): Voller Verlauf + Global Memory-Injektionen.

Fallback-Strategie

Bei Überschreitung → Priorisierung:

Neueste Nachrichten

Verdichtete Summary älterer Nachrichten

Relevante Memory-Snippets

✅ Vorteile der Reihenfolge

Jeder Schritt bringt sofort funktionale Erweiterung.

Context Memory (3) fühlt sich schon wie „intelligente KI“ an, auch ohne Global Memory (4).

Durch adaptive Context-Strategie bleiben alle Provider kompatibel.

---

## 🚀 Optimierungsvorschläge für den Goldstandard

Basierend auf der Analyse des Projekts und den Kriterien aus `GEMINI.md` werden hier Vorschläge zur Erreichung des Goldstandards präsentiert.

### A. Allgemeine Code-Qualität & Wartbarkeit

1.  **Zentralisiertes Frontend-Logging:**
    *   **Problem:** Aktuell werden `console.log` und `console.error` direkt in vielen Frontend-Dateien (`app.js`, `chat.js`, `cost-visualizer.js`, `settings.js`) verwendet. Dies erschwert die Kontrolle der Log-Ausgaben in verschiedenen Umgebungen (Entwicklung vs. Produktion) und kann sensible Informationen preisgeben.
    *   **Vorschlag:** Implementierung eines zentralen Logging-Utilitys im Frontend. Dieses Utility sollte konfigurierbare Log-Level (z.B. DEBUG, INFO, WARN, ERROR) unterstützen und die Möglichkeit bieten, Log-Ausgaben in Produktionsumgebungen zu unterdrücken oder an einen externen Dienst zu senden.
    *   **Umsetzung:** Eine neue Datei `frontend/js/logger.js` erstellen, die eine einfache Wrapper-Funktion um `console` bereitstellt. Alle direkten `console.log`/`console.error`-Aufrufe durch Aufrufe des neuen Logging-Utilitys ersetzen.

2.  **Automatisches Python-Linting und -Formatierung:**
    *   **Problem:** Es gibt keine explizite Konfiguration für Python-Code-Formatierung und -Linting (z.B. Black, Flake8). Dies kann zu inkonsistentem Code-Stil und potenziellen Fehlern führen.
    *   **Vorschlag:** Integration von Black für die automatische Code-Formatierung und Flake8 für das Linting in den Python-Entwicklungsworkflow. Dies kann über Pre-Commit-Hooks oder in der CI/CD-Pipeline erfolgen.
    *   **Umsetzung:** `black` und `flake8` in `backend/requirements.txt` hinzufügen. Konfigurationsdateien (`pyproject.toml` für Black, `.flake8` für Flake8) erstellen. Pre-Commit-Hooks einrichten.

3.  **Verbesserte Frontend-Fehlerbehandlung:**
    *   **Problem:** Fehlermeldungen im Frontend werden teilweise über `alert()` angezeigt oder in `catch`-Blöcken stillschweigend ignoriert. Dies führt zu einer schlechten Benutzererfahrung und erschwert die Fehlerdiagnose.
    *   **Vorschlag:** `alert()`-Aufrufe durch ein nicht-invasives UI-Benachrichtigungssystem (z.B. Toast-Nachrichten, temporäre Statusleisten) ersetzen. Sicherstellen, dass alle `catch`-Blöcke Fehler angemessen protokollieren (via neuem Logging-Utility) und dem Benutzer eine verständliche, nicht-technische Fehlermeldung präsentieren.
    *   **Umsetzung:** Eine zentrale Funktion für UI-Benachrichtigungen erstellen. Alle `alert()`-Aufrufe und leeren `catch`-Blöcke entsprechend anpassen.

4.  **Bereinigung von redundantem und ungenutztem Code:**
    *   **Problem:** Die Datei `backend/key_manager.py` ist ungenutzt und die Funktion `_call_dalle_api_old` in `backend/llm_gateway.py` ist veraltet. Ungenutzte Importe (`re`, `traceback`, `httpx` in `llm_gateway.py`) sind vorhanden.
    *   **Vorschlag:** Entfernen Sie diese ungenutzten Code-Bestandteile, um die Codebasis sauber und wartbar zu halten.
    *   **Umsetzung:** Löschen von `backend/key_manager.py`. Entfernen von `_call_dalle_api_old` und ungenutzten Importen in `backend/llm_gateway.py`.

5.  **Konsistente API-Basis-URL-Nutzung im Frontend:**
    *   **Problem:** `frontend/main.js` verwendet eine hartkodierte URL (`http://127.0.0.1:8000`) anstatt die zentrale `API_BASE_URL` aus `config.js`.
    *   **Vorschlag:** Alle API-Aufrufe im Frontend sollten die global definierte `API_BASE_URL` verwenden, um Konfigurationsänderungen zu vereinfachen und Fehler zu vermeiden.
    *   **Umsetzung:** `frontend/main.js` anpassen, um `window.API_BASE_URL` zu nutzen.

6.  **Standardisierung der Python-Pfadbehandlung in Tests:**
    *   **Problem:** Testdateien wie `waechter/test_chat_endpoint.py` und `waechter/test_llm_gateway.py` verwenden `sys.path.append` als Workaround für Importe. Dies ist eine unsaubere Lösung und kann zu Problemen führen.
    *   **Vorschlag:** Die Projektstruktur oder die Test-Runner-Konfiguration (z.B. `pytest.ini`) so anpassen, dass Python-Module korrekt importiert werden können, ohne den `sys.path` manuell zu manipulieren.
    *   **Umsetzung:** Eine `pytest.ini` im Root-Verzeichnis erstellen und den `pythonpath` entsprechend konfigurieren.

### B. Chat- & Memory-System Spezifisch (gemäß `Chat.md`)

1.  **Zentralisierung und Dynamisierung des Modellkatalogs:**
    *   **Problem:** Es existieren zwei separate Modellkataloge (`backend/model_catalog.json` und `frontend/js/model-catalog.js`), die inkonsistente Daten enthalten können. Der Frontend-Katalog ist statisch und enthält nicht-numerische Preisinformationen.
    *   **Vorschlag:** Der Backend-Katalog (`backend/model_catalog.json`) sollte die einzige Quelle der Wahrheit sein. Das Frontend sollte eine API-Route (`/api/models/catalog`) abfragen, um die aktuellen Modellinformationen (inkl. Preise für die Anzeige) dynamisch zu laden.
    *   **Umsetzung:** Backend-API-Endpunkt für den Modellkatalog erstellen. Frontend anpassen, um diesen Endpunkt zu nutzen und die `frontend/js/model-catalog.js` zu entfernen oder stark zu vereinfachen.

2.  **Implementierung des Context Memory (pro Chat):**
    *   **Problem:** `Chat.md` beschreibt detaillierte Strategien wie "Rolling Summary" und "Fallback-Strategie" für das Kontextmanagement, die in der aktuellen Implementierung noch fehlen. Der Chat speichert lediglich den kompletten Verlauf.
    *   **Vorschlag:** Implementierung der Kontextmanagement-Logik im Backend. Dies beinhaltet die Verwaltung des Token-Limits pro Modell und die Anwendung der beschriebenen Strategien (z.B. Zusammenfassung älterer Nachrichten, Priorisierung neuer Nachrichten) vor dem Aufruf der LLM-APIs.
    *   **Umsetzung:** Eine neue Komponente im Backend (z.B. `backend/context_manager.py`) erstellen, die vom `llm_gateway` genutzt wird.

3.  **Implementierung des Global Memory (Übergreifendes Chat-Memory):**
    *   **Problem:** Das Konzept des "Global Memory" mit Vektor-Suche und Embedding-Index ist in `Chat.md` beschrieben, aber noch nicht implementiert.
    *   **Vorschlag:** Design und Implementierung eines globalen Memory-Systems. Dies ist ein Kernbestandteil des "Goldstandards" für ein KI-System.
    *   **Umsetzung:**
        *   Mechanismus zur Extraktion relevanter Informationen aus Chat-Nachrichten (z.B. mittels Embeddings).
        *   Auswahl und Integration einer Vektor-Datenbank (lokal oder extern).
        *   Integration in den `llm_gateway`, um relevante Memory-Snippets in Prompts zu injizieren.
        *   Nutzung des `save_memory`-Tools (gemäß `GEMINI.md`) zur Dokumentation wichtiger Erkenntnisse.

4.  **Adaptive Context-Window-Anpassung:**
    *   **Problem:** Die detaillierte adaptive Kontextverwaltung basierend auf Modell-Token-Limits und Budgetverteilung ist in `Chat.md` beschrieben, aber noch nicht umgesetzt.
    *   **Vorschlag:** Implementierung dieser adaptiven Logik im Backend, um die Prompt-Konstruktion dynamisch an die Token-Limits des ausgewählten Modells und die definierte Budgetverteilung anzupassen.
    *   **Umsetzung:** Erweiterung des `backend/context_manager.py` (siehe Punkt B.2) um diese Logik.

### C. Teststrategie

1.  **Umfassende Frontend-Tests (Unit/Integration):**
    *   **Problem:** Es fehlen dedizierte Unit- und Integrationstests für die Frontend-Komponenten und -Logik. Der aktuelle E2E-Smoke-Test ist sehr grundlegend.
    *   **Vorschlag:** Einführung eines Test-Frameworks wie Jest für Unit-Tests von JavaScript-Funktionen und Komponenten. Dies stellt die Korrektheit der Frontend-Logik sicher und erleichtert Refactorings.
    *   **Umsetzung:** Jest installieren und Testdateien für `frontend/js/*.js` erstellen.

2.  **Erweiterung der E2E-Testabdeckung:**
    *   **Problem:** Der bestehende `smoke.spec.js` testet nur das Laden und die Sichtbarkeit grundlegender UI-Elemente.
    *   **Vorschlag:** Erweiterung der E2E-Tests (Playwright) um kritische Benutzerabläufe, wie z.B. das Senden von Chat-Nachrichten, das Speichern von API-Keys, die Überprüfung der Kostenanzeige und die Interaktion mit der Modellauswahl.
    *   **Umsetzung:** Neue `*.spec.js`-Dateien in `waechter/tests/e2e/` erstellen, die diese Szenarien abdecken.

3.  **Vervollständigung der Backend-Testabdeckung:**
    *   **Problem:** Die Testabdeckung für `backend/llm_gateway.py` ist unvollständig (z.B. Gemini-API-Aufrufe, direkte DALL-E-Aufrufe, Fehlerbehandlungspfade sind nicht abgedeckt).
    *   **Vorschlag:** Ergänzung der Tests in `waechter/test_llm_gateway.py` um alle Pfade und Fehlerfälle.
    *   **Umsetzung:** Neue Testfälle in `waechter/test_llm_gateway.py` hinzufügen.

### D. Architektur & Deployment

1.  **Produktions-Deployment-Strategie für das Backend:**
    *   **Problem:** Derzeit wird das Backend mit `uvicorn` im Entwicklungsmodus gestartet. Für eine Produktionsumgebung ist dies nicht robust oder skalierbar.
    *   **Vorschlag:** Definition und Implementierung einer Produktions-Deployment-Strategie für das FastAPI-Backend.
    *   **Umsetzung:** Verwendung eines robusten ASGI-Servers wie Gunicorn mit Uvicorn-Workern. Optional: Containerisierung der Anwendung mittels Docker für konsistente Umgebungen.

2.  **Korrekte Verwaltung der Python-Virtual-Environment:**
    *   **Problem:** Das Verzeichnis `backend/venv/` (die virtuelle Python-Umgebung) wird derzeit von Git verfolgt, was zu großen, unnötigen Commits und potenziellen Problemen bei der Reproduzierbarkeit auf verschiedenen Systemen führt.
    *   **Vorschlag:** Die virtuelle Umgebung sollte nicht im Repository versioniert werden.
    *   **Umsetzung:** `backend/venv/` zur `.gitignore`-Datei hinzufügen. Das Verzeichnis `backend/venv/` lokal löschen und neu erstellen, um sicherzustellen, dass es nicht mehr verfolgt wird. **Dies ist ein kritischer Fix für einen Goldstandard.**