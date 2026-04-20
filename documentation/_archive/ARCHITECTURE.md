# ARCHITECTURE.md - Janus Projekt

## Executive Summary
Janus ist ein hochmodularer, KI-gestuetzter persoenlicher Assistent (Personal Intelligence System). Im Diamond-Standard arbeitet das Backend entlang einer klaren Skill-Kette: Gateway -> Skill Router -> Policy Engine -> Tool Executor -> Skill Handler -> SkillResponse Contract. In V4 wurde die Agent Factory als Planungs-/Runtime-Layer eingefuehrt: AgentPlanner entwirft pro Anfrage einen AgentSpec, AgentRuntime fuehrt ihn in einer spezialisierten, skill-restriktiven Umgebung aus (inkl. Tracing, Guardrails, Dry-Run).

## Verzeichnisstruktur (Separation of Concerns)

### Backend (`/backend`)
*   **`api/routers/`**: REST-Endpunkte (FastAPI). Hier wird die HTTP-Schnittstelle nach außen definiert.
*   **`services/`**: Die "Business Logic". Jede Datei/Ordner hat eine klare Aufgabe:
    *   `chat_orchestrator.py`: Das "Gehirn", das Kontext, Tools und LLM-Antworten koordiniert.
    *   `memory_manager.py` / `vector_service.py`: Verwaltung des Langzeitgedächtnisses und der Einbettungen.
    *   `llm_gateway.py`: Abstraktionsschicht für verschiedene LLM-Provider.
    *   `agent_planner.py`: Entwirft AgentSpec (Ziel, Skills, Regeln, Iterationslimit) aus User-Intent + Capabilities.
    *   `agent_runtime.py`: Führt spezialisierte AgentSpecs in geschlossener Runtime aus (restricted skills, trace, policy).
    *   `skill_router.py`: Zentrale Aufloesung von Skill-IDs (`domain.action`) und Legacy-Namen auf konkrete Handler, inkl. rekursivem Catalog-Load und Dependency-Checks.
    *   `policy_engine.py`: Sicherheits-Firewall fuer Berechtigungsentscheidungen (`read_only`, `confirm_required`, `restricted`).
    *   `tool_manager.py`: Registry/Metadaten fuer Tools inkl. Skill-Catalog-Mapping, Versioning, Capabilities und Deprecation-Hinweisen bei Legacy-Aufrufen.
    *   `tool_executor.py`: Validierung, Policy-gekoppelte Ausfuehrung, Sandbox-Enforcement, Dry-Run-Simulation und Contract-Normalisierung zu `SkillResponse`.
    *   `vision_service.py`: Verarbeitung von Bilddaten und Gesichtserkennung.
    *   `tts_service.py`: Text-to-Speech Integration.
*   **`skills/`**: Modularer Skill-Catalog als JSON-Dateien je Domaene (`backend/skills/<domain>/<action>.json`).
*   **`data/`**: Persistenzschicht.
    *   `models.py`: SQLAlchemy-Datenbankmodelle (Schema).
    *   `database.py`: DB-Verbindung und Session-Handling.
    *   `crud.py`: Create, Read, Update, Delete Operationen.
*   **`llm_providers/`**: Spezifische Implementierungen für Provider wie OpenAI oder Gemini.

### Frontend (`/frontend`)
*   **`src/components/`**: Wiederverwendbare UI-Elemente (Chat-Interface, Sidebar, Einstellungen).
*   **`src/services/`**: API-Clients zur Kommunikation mit dem Backend.
*   **`src/types/`**: TypeScript-Typdefinitionen für konsistente Datenstrukturen.

## Feature-to-File Map

| Feature | Backend (Primaer) | Frontend (Primaer) | Contract-Standard |
| :--- | :--- | :--- | :--- |
| **Chat & Orchestrierung** | `services/chat_orchestrator.py` | `src/App.tsx`, `src/components/Chat/` | `SkillResponse`-Aggregation pro Toolturn |
| **Agent Factory** | `services/agent_planner.py`, `services/agent_runtime.py`, `data/schemas.py` (`AgentSpec`) | - | Geplanter AgentSpec + runtime trace |
| **LLM Gateway & Recovery** | `services/llm_gateway.py` | `src/services/api.ts` | Fehlercodes (`MALFORMED_REQUEST`, `INVALID_ARGUMENTS`) als Contract |
| **Skill Routing** | `services/skill_router.py`, `backend/skills/**/*.json` | - | Name-Resolution + Capability-Discovery + Dependency-Checks |
| **Policy/Security** | `services/policy_engine.py`, `services/tool_executor.py` | UI-Consent-Flow | `permission_required`, `RATE_LIMIT_EXCEEDED` |
| **Tool Registry & Execution** | `services/tool_manager.py`, `services/tool_executor.py`, `tool_registry.py` | - | Jeder Handler liefert `SkillResponse` inkl. `execution_time_ms` / `dry_run_success` |
| **Deep Tracing / Telemetry** | `data/models.py` (`SkillTelemetry`), `services/tool_executor.py` | (später Dashboard) | `trace_id`, `arguments_json`, `response_json`, `latency_ms` |
| **Memory & RAG** | `services/memory_manager.py`, `services/rag_manager.py`, `api/routers/rag.py` | `src/components/Memory/` | Treffer/Fehler im SkillResponse-Envelope |
| **Vision / Bilder** | `services/vision_service.py`, `api/routers/images.py` | `src/components/Vision/` | Strukturierte Ergebnisobjekte, gateway-kompatibel |
| **Kostenkontrolle** | `services/cost_service.py`, `data/models.py` (`Cost`) | `src/components/Settings/` | Kostenmetrik als separates Tracking-Contract |

Erweiterungsstandard fuer neue Skills: siehe `documentation/SKILL_DEVELOPMENT_GUIDE.md`.

## LLM-Provider-Interna: Ollama Adapter V2

Die lokale Provider-Schicht wurde in V6.2 weiter vereinheitlicht. Kernprinzipien:

### Zentraler Tool-Adapter (`backend/llm_providers/ollama_service.py`)
* **Non-Native Tool Calls** werden in `_resolve_tool_calls_from_non_native_response` zu OpenAI-kompatiblen `tool_calls` normalisiert.
* **Self-Healing** (`_attempt_tool_call_self_heal`) erzwingt bei JSON-Fehlern einen einmaligen Retry mit strengem System-Prompt und `format=json`.
* **Pflichtfeld-Validierung** (Name + JSON-Argumente) vermeidet Gatewayspezifische Sonderpfade (`strict_tool_calls` wurde entfernt).
* **Markdown-/Fence-Cleanup** und DTO-Normalisierung halten `raw_assistant_response`/`tool_calls` bei jeder Ollama-Antwort konsistent.

### Gateway-Bridges (`backend/services/llm_gateway.py`)
* **Toollisten-Limit**: `_limit_local_tool_definitions` priorisiert lokale Must-Have-Skills (`system.routing`, `system.local_business`, Memory/Filesystem). Das reduziert Promptgröße bei Gemma/Llama.
* **Forced-Tool-Sichtbarkeit**: `_ensure_forced_tool_visible` sorgt dafür, dass bei Limitierung erzwungene Tools (z. B. `system.local_business`) wieder eingefügt werden.
* **Phase-Zwei-Call**: Nach Toolrunde wird für Ollama explizit auf Synthese ohne Tools gewechselt (Second pass `call_type="synthesis"`).

### Lokale Business-Pipeline (`backend/tools/geo_service.py`)
* **DDG-Fallback** erkennt Bot-Captchas und springt deterministisch auf Overpass/OSM.
* **Website Discovery & Enrichment** (Async-Pipeline):
  - `_discover_missing_business_websites` ergänzt Domains/Menü/Reservierung, solange `max_discoveries` nicht erreicht ist.
  - `_selectively_enrich_businesses` erlaubt Ollama max. 1–2 Enrichment-Slots; Slots werden nur gezählt, wenn Felder tatsächlich besser werden (`_should_count_business_enrichment_attempt`).
  - Blockierte Domains (z. B. `expireddomains.com`) löschen nicht mehr das komplette Slot-Budget.
* **Final Ranking** (`_finalize_local_business_results`):
  - Starke Treffer (Website/Menü/Reservierung oder Öffnungszeiten+Telefon) landen vor schwachen OSM-Resten.
  - Schwache Kandidaten wie `Trattoria Da Pia` werden bei knappen Limits automatisch nach hinten geschoben.

### Regressionstests
* Provider: `backend/tests/llm_providers/test_ollama_service.py` deckt Markdown-JSON, Self-Healing, Tool-Fallback ab.
* Gateway: `backend/tests/test_policy_bypass_gateway.py` prüft Tool-Limit, Forced-Tool und Synthesewechsel.
* Geo-Service: `backend/tests/tools/test_geo_service.py` sichert DDG/OSM-Fallback, Slot-Recovery und Ranking (inkl. Prenzlauer-Berg-Case) ab.

## Datenbank-Modelle (SQLite)
Die Datenbank nutzt SQLAlchemy als ORM. Kern-Entitäten:
*   **Project**: Container für Chats und Einstellungen.
*   **Chat**: Eine Konversations-Sitzung.
*   **Message**: Einzelne Nachrichten innerhalb eines Chats (Rollen: user, assistant, system, tool).
*   **Memory**: Wissensfragmente mit Vektor-Embeddings für semantische Suche.
*   **Contact**: Adressbuch-Integration.
*   **GeneratedImage**: Historie der KI-generierten Bilder.
*   **Cost**: Token-Verbrauch und Kostenberechnung pro Provider/Modell.
*   **PersonProfile**: Bekannte Personen für die Gesichtserkennung (Vision).

### Datenbank-Migrationen & Updates
Das Projekt nutzt SQLAlchemy für die Modelle. Wenn Änderungen an `models.py` vorgenommen werden (z.B. neue Tabellen oder Spalten), gilt folgender Workflow:

*   **Produktion / Staging (falls Alembic genutzt wird):**
    1. Migration erstellen: `alembic revision --autogenerate -m "Beschreibung der Änderung"`
    2. Migration anwenden: `alembic upgrade head`
*   **Lokale Entwicklung (Dev-Modus ohne Alembic):**
    Da SQLite genutzt wird, kann bei strukturellen Änderungen an `models.py` (falls Datenverlust verschmerzbar ist) die lokale `janus.db` Datei gelöscht werden. FastAPI / SQLAlchemy baut die Tabellen beim nächsten Start via `Base.metadata.create_all(bind=engine)` automatisch neu und sauber auf.

## Architektur-Diagramm (Datenfluss, Diamond-Standard)

```mermaid
graph TD
    UI[Frontend UI] -->|User Message| Router[API Router]
    Router -->|Request| Orchestrator[Chat Orchestrator]
    Orchestrator -->|Complex Task| Planner[Agent Planner]
    Planner -->|AgentSpec| Runtime[Agent Runtime]
    Runtime -->|LLM + Tool Round| Gateway[LLM Gateway]
    Orchestrator -->|Standard Task| Gateway
    Gateway -->|Tool Name Check| SkillRouter[Skill Router]
    SkillRouter -->|Resolved Tool| Policy[Policy Engine]
    Policy -->|ALLOW / CONSENT| Executor[Tool Executor]
    Executor -->|Sandbox + Rate-Limit + Dry-Run Gate| Guardrails[Execution Guardrails]
    Guardrails -->|Invoke (oder Simulation)| Handler[Skill Handler]
    Handler -->|Composite macro| Composite[Composite Skill z. B. knowledge.hardened_edit]
    Composite -->|call_internal_skill(...), gleiche trace_id| SkillRouter
    Handler -->|status,data,error (+ execution_time_ms)| Contract[SkillResponse Contract]
    Contract -->|Tool Results| Runtime
    Runtime -->|Final Agent Answer| Orchestrator
    Contract -->|Flight Recorder| Telemetry[(SkillTelemetry: trace_id,args,response)]
    Orchestrator -->|Persist| DB[(SQLite)]
    Orchestrator -->|Final Response| UI
```

## Governance & Best Practices (warum das System stabil ist)

1. **Dekopplung durch Rollen**
   - Routing (`skill_router.py`), Security (`policy_engine.py`) und Ausfuehrung (`tool_executor.py`) sind klar getrennt.
   - Aenderungen in einem Bereich destabilisieren die anderen Schichten nicht direkt.

2. **Contract-First statt implizite Rueckgaben**
   - Tool-Ergebnisse laufen standardisiert ueber `SkillResponse`.
   - Fehler sind ueber Codes/Details maschinenlesbar und fuer Recovery nutzbar.

3. **Sicherheitsmodell vor Side-Effects**
   - Kritische Skills werden vor Handler-Ausfuehrung von der Policy bewertet.
   - Consent-Flow und One-Time-Bypass sind testbar und leak-sicher umgesetzt.

4. **Automatisierte Qualitaets-Gates**
   - Contract-, Integrations- und E2E-Diamond-Journey-Tests sichern die Gesamtstrecke.
   - Legacy-Aufrufe werden per Deprecation-Warning sichtbar gemacht und schrittweise migriert.

5. **Verbindliche Erweiterungsregeln**
   - Neue Skills folgen dem Guide `documentation/SKILL_DEVELOPMENT_GUIDE.md` (Schema, Mapping, Risiko, Tests).
   - Dadurch bleiben Naming, Security und Contracts konsistent ueber alle Teams hinweg.

6. **Implosions-Schutz (Agent-Grade)**
   - **#1 Capability-Routing:** Skills werden in Prompt/Metadaten nach Faehigkeiten gruppiert, nicht nur nach Namen.
   - **#2 Rate-Limiting:** `max_calls_per_turn` stoppt Endlos-/Kosten-Loops hart pro Skill.
   - **#3 Deep Tracing:** Alle Tool-Calls eines Requests teilen eine `trace_id` fuer reproduzierbare Analyse.

7. **Platform-Ready Skill-Catalog (V3.2)**
   - Skill-Definitionen sind modular in `backend/skills/` organisiert statt monolithischer Zentraldatei.
   - Versionierung (`version`) und Sandbox-Level (`sandbox_level`) sind Teil der Skill-Metadaten.
   - Dry-Run erlaubt sichere End-to-End Simulation ohne echte Side-Effects.

8. **Agent Factory (V4.0)**
   - Komplexe Requests werden in spezialisierte AgentSpecs zerlegt statt mit einem monolithischen "Alles-Agenten".
   - Runtime kann Tool-Zugriff auf `required_skills` eingrenzen und bleibt voll in Policy/Tracing eingebettet.
   - Architektur ist vorbereitet fuer spaetere Multi-Agent-Komposition.

9. **Hierarchical Discovery & Skill-RAG (V5.0) - "Bibliotheks-Logik"**
   - Janus exponiert dem LLM nicht mehr blind die komplette Toolmenge, sondern nutzt eine mehrstufige Vorauswahl.
   - Stufe 1 (semantisch): Skill-Descriptions werden als Embeddings im Chroma-Index `janus_skill_index` abgelegt und per Top-K Retrieval zum User-Prompt abgefragt.
   - Stufe 2 (Domain-Check): Klare Keywords (z. B. "Mail") priorisieren zusaetzlich passende Domaenen (z. B. `communication.*`).
   - Ergebnis: Planner/Orchestrator/Gateway reichen nur eine fokussierte Skill-Subset-Liste (typisch 5-15) an das LLM weiter.
   - Fallback-Sicherheit: Falls ein Filterlauf keine passenden Tool-Matches ergibt, wird automatisch auf die Vollmenge zurueckgefallen.

10. **Recursive Execution Path (V6.0 Composite Skills)**
   - Skills duerfen als Makro andere Skills intern aufrufen (`ToolExecutor.call_internal_skill`).
   - Interne Aufrufe behalten die urspruengliche `trace_id` und bleiben damit end-to-end nachvollziehbar.
   - Jeder interne Aufruf wird erneut durch die Policy geprueft (Nested Security, kein Blind-Bypass).
   - SkillTelemetry markiert interne Kaskaden ueber `__call_type=internal` in Arguments/Response.
   - Composite Skills (z. B. `knowledge.hardened_edit`) kapseln mehrstufige Workflows als atomare High-Level-Operation.

11. **UI-Test-Matrix (Playwright, Phase O)**
   - **Scenario A - Robot Scout:** Prompt "Kairo" -> Knowledge Center oeffnet -> PDF/Page Rendering validiert.
   - **Scenario B - Gatekeeper:** Riskanter Loesch-Intent -> Consent-Optionen (1/2/3) als klickbare DOM-Controls sichtbar.
   - **Scenario C - Master Flow:** Faktencheck-Ende-zu-Ende -> Audit-Status-Pills inkl. CSS-Klasse (`status-warning`, etc.) validiert.
   - Testlauf nutzt isolierte Backend-DB via `JANUS_TEST_DB_URL` fuer sichere E2E-Isolation.

---
*Zuletzt aktualisiert: 16.03.2026 (Ollama Adapter V2, Gateway Cleanup, Local-Business Flow).* 
