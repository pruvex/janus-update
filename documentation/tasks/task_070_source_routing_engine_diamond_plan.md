# 💎 DIAMOND TASK: Source Routing Engine

---
task_id: TASK-070
status: PLANNED
assigned_to: KIMI-FIRST
confidence_level: MEDIUM_HIGH
created_at: 2026-05-06 02:02
updated_at: 2026-05-06 02:02
source_spec: documentation/Planned Features/Source Routing Engine.md
completion_gate:
  tests: true
  audit_trail: true
  lessons_learned: true
---

# 1️⃣ Task Description

Janus soll für faktenbasierte, aktuelle oder quellenpflichtige Nutzeranfragen eine deterministische Source Routing Engine erhalten. Die Engine klassifiziert solche Anfragen regelbasiert, wählt eine definierte Primärquelle, führt kontrollierte Fallbacks aus und macht die verwendeten Quellen in der Antwort transparent.

Die Umsetzung erfolgt risikoarm und schrittweise. Version 1 gilt nicht global für jede Janus-Anfrage, sondern nur für eindeutig source-required Anfragen. Bestehende Chat-, Kalender-, Memory-, Datei- und Kreativ-Flows dürfen nicht global umgeleitet werden.

# 2️⃣ Impact-Analyse

- **Basiert auf:** `documentation/Planned Features/Source Routing Engine.md`
- **Beeinflusst:** `backend/services/orchestrator/intent_engine.py`, `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/orchestrator/response_finalizer.py`, `backend/services/tool_manager.py`, `backend/skills/system/*.json`, neue Source-Routing-Services, Unit-/Integration-/E2E-Tests
- **Risiko-Einschätzung:** HIGH
- **MVP-Rest-Risiko:** MEDIUM mit MVP-Scope und Shadow-Mode-Gate
- **Primäres Risiko:** Routing-Änderungen können bestehende Tool-Auswahl, Forced-Tool-Logik und normale Chat-Flows brechen.
- **Risikoreduktion:** Additive Architektur, Shadow Mode vor Enforced Mode, begrenzter MVP-Scope, harte Tests gegen reale Produktionspfade.

# 2.1 Resolved Product Decisions

- **Scope v1:** Source Routing gilt nur für `source_required` Anfragen.
- **Included v1 Datentypen:** `weather`, `country_info`, `routing`, `news_rss`, `web_fact`, `wiki_fact`, `local_business`.
- **Enforced MVP Phase:** Zuerst nur `weather`, `country_info`, `routing` erzwingen.
- **Shadow Mode:** Jede neue Routing-Entscheidung wird zuerst ohne Verhaltensänderung geloggt und getestet.
- **Global Pipeline:** `jede Anfrage MUSS durch Pipeline laufen` aus der Source-Spec wird für v1 konkretisiert zu: jede Anfrage läuft durch einen leichten Source-Routing-Eligibility-Check; nur `source_required=True` wird durch Policy/Source-Auswahl geführt.
- **Out of Scope v1:** Kreatives Schreiben, Smalltalk, Kalender-Mutationen, Memory-Schreiboperationen, reine Texttransformation, interne Help-/Capability-Fragen, PDF-/Dateioperationen ohne externe Faktenabfrage.
- **Hard Fail:** Nur wenn eine eindeutig source-required Anfrage nach Policy keine zulässige Quelle oder keinen zulässigen Fallback hat. UX-Text: `Keine verlässlichen Daten verfügbar.`
- **Fallback Limits:** Maximal 1 Primärquelle + maximal 2 Fallback-Quellen pro Routing-Entscheidung.
- **Source Block:** Antworten für source-required Anfragen müssen einen separaten Abschnitt `### Quellen` enthalten.
- **Source Identity:** Quellen werden aus Tool-/Service-Ergebnissen oder deterministischen Skill-Metadaten abgeleitet, nicht vom LLM frei erfunden.
- **Persistence:** Keine neue DB-Persistenz in v1. Routing-Entscheidungen werden über bestehendes Logging/Telemetry erfasst.
- **Security:** Keine neuen API-Keys hardcoden. Externe Quellen bleiben über bestehende Skills/Services gekapselt.

# 3️⃣ Relevant Prior Learnings

- **#IntentEngineV2:** Intent-Erkennung muss wortgrenzen-/normalisierungsbasiert sein und über einen Single-Dispatch-Vertrag laufen; keine zusätzlichen verstreuten Substring-Checks.
- **#GuidedAssistantMutation / #ToolChoiceEnforcement:** Wenn ein Tool deterministisch erzwungen wird, müssen `forced_tool`, `force_tool_name` und Skill-IDs konsistent bleiben; Modelle dürfen keine eigenen IDs oder Quellen erfinden.
- **#GeminiNameSanitization:** Janus nutzt dot-Notation für Skill-IDs, Gemini benötigt teilweise underscore-kompatible Toolnamen. Source Routing darf kanonische Skill-IDs nicht mit provider-sanierten Toolnamen verwechseln.
- **#ContextBleed:** Source-/Suggestion-Blöcke dürfen nicht als Fakten in Memory oder spätere Antworten diffundieren. Quellen müssen klar getrennt vom Antwortinhalt bleiben.
- **#RealModuleE2E:** E2E-Tests müssen echte Produktionspfade prüfen, nicht testlokale Routing-Logik nachbauen.
- **#DeterministicSkillTesting:** Output-Validierung muss deterministisch sein; keine KI-basierte Bewertung von Routing-Korrektheit.

# 4️⃣ Spec Validation Result

## Mandatory Sections

- **Feature Name:** vorhanden.
- **Core Idea:** vorhanden.
- **Functional Core:** vorhanden, durch MVP-Scope konkretisiert.
- **System Behavior:** vorhanden, aber globaler Pipeline-Satz wurde für v1 eingegrenzt.
- **Edge Cases:** vorhanden, Hard-Fail und Fallback-Limits konkretisiert.
- **Constraints:** vorhanden, durch Out-of-Scope-Liste konkretisiert.
- **Integration Context:** vorhanden.
- **Test Strategy:** vorhanden.
- **Definition of Done:** vorhanden.

## Determinism Status

- **Eligibility:** deterministischer Check `source_required=True/False`.
- **Routing:** deterministische Policy `data_type → primary_skill_id → fallback_skill_ids`.
- **Fallback:** maximal 2 Fallbacks, feste Reihenfolge.
- **Output:** separater Quellenblock mit Tool-/Policy-basierten Quellen.
- **LLM-Freiheit:** LLM darf Antwort synthetisieren, aber Quelle und erlaubte Tools werden durch Policy begrenzt.

## Remaining Explicit Deferrals

- **Global Enforcement:** `OUT_OF_SCOPE v1`.
- **Neue externe Provider:** `OUT_OF_SCOPE v1`, außer bestehende Skills/Services nutzen sie bereits.
- **Neue UI-Komponente für Quellen:** `OUT_OF_SCOPE v1`; Quellenblock reicht.
- **DB-Persistenz für Source Decisions:** `OUT_OF_SCOPE v1`.

# 5️⃣ Codebase Alignment

## Existing Modules To Extend

- `backend/services/orchestrator/intent_engine.py`
  - Enthält bestehende Intent-Erkennung, Wortgrenzen-Pattern und `IntentDetectionResult`.
  - Source Eligibility darf hier oder über einen klar gekapselten Source-Routing-Classifier angeschlossen werden, aber nicht als verstreute Einzelchecks.

- `backend/services/chat_orchestrator.py`
  - Führt den Request-Workflow und ruft `execution_dispatcher.execute_generation(...)` auf.
  - Bestehende Provider-Coherence, Help-Fast-Path und Intent-Single-Dispatch dürfen nicht gebrochen werden.

- `backend/services/orchestrator/execution_dispatcher.py`
  - Baut Prompts, `relevant_skill_ids`, ToolExecutor und `gateway_kwargs`.
  - Bestehende Forced-Tool-Logik für Video/Kalender/Mutation ist High-Risk; Source Routing muss additiv und prioritätsbewusst eingebunden werden.

- `backend/services/orchestrator/response_finalizer.py`
  - Geeigneter Ort für deterministische finale Response-Erweiterung, falls der Quellenblock nach Tool-Ergebnissen ergänzt wird.

- `backend/services/tool_manager.py`
  - Verwaltet Skill-Metadaten, Skill-IDs, Tool-Definitionen und Gemini-kompatible Namen.
  - Source Routing muss kanonische Skill-IDs verwenden.

- `backend/skills/system/*.json`
  - Bestehende Skill-Metadaten für `system.weather`, `system.country_info`, `system.routing`, `system.rss_news`, `system.websearch`, `system.local_business`.
  - Können um source-relevante Metadaten ergänzt werden, ohne Tool-Code zu ändern.

## New Modules To Add

- `backend/services/source_routing/schemas.py`
- `backend/services/source_routing/policy.py`
- `backend/services/source_routing/classifier.py`
- `backend/services/source_routing/engine.py`
- `backend/services/source_routing/source_block.py`
- `backend/services/source_routing/__init__.py`
- optional: `config/source_routing_policy.json`

## Architecture Conflict

Die Spec fordert eine globale Pipeline für jede Anfrage. Der aktuelle Janus-Orchestrator enthält jedoch mehrere bewusst priorisierte Spezialpfade: Help Fast-Path, Smalltalk Guard, Kalender Live Truth, Calendar Mutation Hammer, Video Force, RAG/PDF Guards und Provider-Coherence.

## Required Resolution

Die Source Routing Engine wird in v1 als additiver Policy-Layer geplant:

- Eligibility-Check für alle Anfragen.
- Shadow-Mode-Logging ohne Verhaltensänderung.
- Enforced Mode nur für explizit freigegebene source-required Datentypen.
- Keine Überschreibung von Kalender-Mutationen, Help-Fast-Path, Smalltalk, PDF/Filesystem und Memory-Write.

# 6️⃣ Target Architecture

```text
User Input
  → ChatOrchestrator existing request workflow
  → IntentEngine.detect_all_intents()
  → SourceRoutingClassifier.classify(user_text, intent_result)
  → SourceRoutingEngine.evaluate(policy, classification)
  → Shadow Log OR Enforced Tool Restriction
  → ExecutionDispatcher gateway_kwargs / relevant_skill_ids
  → ToolExecutor executes selected source skill
  → ResponseFinalizer / SourceBlockRenderer
  → Final answer with ### Quellen
```

## Module Boundaries

- **IntentEngine:** Erkennt bestehende Intents und liefert Single-Dispatch-Kontext.
- **SourceRoutingClassifier:** Klassifiziert nur source eligibility und data type; führt keine Tools aus.
- **SourceRoutingPolicy:** Enthält deterministische Datentyp-zu-Quelle-Regeln.
- **SourceRoutingEngine:** Erzeugt eine `SourceRoutingDecision` mit Primär-/Fallback-Quellen und Modus.
- **ExecutionDispatcher:** Nutzt Decision nur zur Tool-Einschränkung/Force, wenn Enforced Mode aktiv ist.
- **SourceBlockRenderer:** Rendert Quellen aus Tool-Ergebnissen/Policy deterministisch.
- **ToolManager:** Bleibt kanonische Skill-ID-Autorität.

# 7️⃣ Implementation Plan

## Task 070.1 — Source Routing Schemas und Policy-Vertrag anlegen

- **EXECUTION TARGET:** `Kimi k2.5`
- **Target Decision Reason:** Isolierte neue Dateien mit deterministischen Dataclasses/Pydantic-Modellen und geringem Integrationsrisiko.
- **Goal:** Source Routing besitzt einen festen, testbaren Datenvertrag.
- **Files:**
  - `backend/services/source_routing/__init__.py`
  - `backend/services/source_routing/schemas.py`
  - `backend/services/source_routing/policy.py`
  - `tests/unit/test_source_routing_policy.py`
- **Actions:**
  - Modelle definieren: `SourceRoutingClassification`, `SourceRoutingDecision`, `SourceCandidate`, `SourceRecord`.
  - Erlaubte Datentypen als Enum/String-Literals definieren: `weather`, `country_info`, `routing`, `news_rss`, `web_fact`, `wiki_fact`, `local_business`.
  - Policy-Regeln für v1 festlegen:
    - `weather → primary system.weather, fallback system.websearch`
    - `country_info → primary system.country_info, fallback system.websearch`
    - `routing → primary system.routing, fallback system.websearch`
    - `news_rss → primary system.rss_news, fallback system.websearch`
    - `web_fact → primary system.websearch, fallback none`
    - `wiki_fact → primary wikipedia skill if existing else system.websearch`
    - `local_business → primary system.local_business, fallback system.websearch`
  - `mode` unterstützen: `shadow`, `enforced`.
  - Maximal 2 Fallbacks validieren.
- **Expected Result:** Policy kann ohne Orchestrator importiert und deterministisch getestet werden.
- **Acceptance Criteria:**
  - Unit-Test bestätigt jede v1-Datentyp-Regel.
  - Unit-Test bestätigt: unbekannter Datentyp erzeugt Hard-Fail-Decision.
  - Unit-Test bestätigt: mehr als 2 Fallbacks wird abgelehnt.

## Task 070.2 — Deterministischen Source Classifier bauen

- **EXECUTION TARGET:** `Kimi k2.5`
- **Target Decision Reason:** Regelbasierte Klassifikation in isoliertem Modul; kein Orchestrator-Wiring.
- **Goal:** Nutzertext wird deterministisch in source-required Datentypen oder `not_applicable` klassifiziert.
- **Files:**
  - `backend/services/source_routing/classifier.py`
  - `tests/unit/test_source_routing_classifier.py`
- **Actions:**
  - Normalisierung aus IntentEngine-Pattern übernehmen: casefold, whitespace collapse, Wortgrenzen.
  - Positivmarker für MVP definieren:
    - Wetter: `wetter`, `temperatur`, `regen`, `vorhersage` + Orts-/Zeitbezug optional.
    - Länderinfo: `hauptstadt`, `einwohner`, `fläche`, `land`, `währung`, `sprache`.
    - Routing: bestehende Routing-Marker konzeptionell spiegeln, keine Kalender-Zeit-False-Positives.
    - News/RSS: `nachrichten`, `news`, `aktuell`, `heute` mit Ereignis-/Themenbezug.
    - Web fact: `recherchiere`, `suche im web`, `aktuelle informationen`.
    - Wiki fact: enzyklopädische Fragen ohne Aktualitätsmarker.
    - Local business: `restaurant`, `geschäft`, `in der nähe`, `adresse`, `öffnungszeiten`.
  - Negativmarker für v1 hard ausschließen: Smalltalk, kreative Schreibaufgaben, Kalender-Mutation, Memory-Write, Dateioperation, Help-/Capability-Fragen.
  - Ergebnis enthält `source_required`, `data_type`, `confidence_label` (`high|medium|low`), `reason_code`.
  - Nur `high` darf später enforced werden.
- **Expected Result:** Classifier kann false-positive-arm entscheiden, ohne Tools oder LLM zu nutzen.
- **Acceptance Criteria:**
  - `Wie ist das Wetter morgen in Berlin?` → `weather/high`.
  - `Was ist die Hauptstadt von Frankreich?` → `country_info/high` oder `wiki_fact/high` gemäß finaler Policy-Regel.
  - `Wie weit ist es von München nach Hamburg?` → `routing/high`.
  - `Schreib mir ein Gedicht über Berlin` → `not_applicable`.
  - `Verschiebe meinen Termin morgen` → `not_applicable`.
  - `Was kannst du?` → `not_applicable`.

## Task 070.3 — Source Routing Engine ohne Orchestrator-Wiring implementieren

- **EXECUTION TARGET:** `Kimi k2.5`
- **Target Decision Reason:** Pure Decision-Logik mit klaren Inputs/Outputs; keine High-Risk Integration.
- **Goal:** Classification + Policy werden zu einer finalen Routing-Entscheidung kombiniert.
- **Files:**
  - `backend/services/source_routing/engine.py`
  - `tests/unit/test_source_routing_engine.py`
- **Actions:**
  - `evaluate(user_text, intent_result=None, mode="shadow")` implementieren.
  - Wenn `source_required=False`: Decision `applies=False`, keine Quellen.
  - Wenn `source_required=True` und Policy vorhanden: Decision mit Primärquelle, Fallbacks, Hard-Fail-Text und Quellenpflicht.
  - Enforced Mode nur erlauben bei `confidence_label=high` und Datentyp in `weather|country_info|routing`.
  - Für alle anderen Datentypen in v1: `shadow` oder `advisory`, keine Tool-Force.
  - Keine Exceptions in normalen Fehlfällen; invalid policy wird intern geloggt und erzeugt Hard-Fail-Decision.
- **Expected Result:** SourceRoutingEngine ist eigenständig testbar und kann sicher in Shadow Mode eingebunden werden.
- **Acceptance Criteria:**
  - `weather/high` + `shadow` verändert keine Tools.
  - `weather/high` + `enforced` liefert `system.weather` als Primärquelle.
  - `news_rss/high` + `enforced` bleibt v1 nicht-forcing/advisory.
  - Invalid Policy erzeugt Decision mit `hard_fail=True` und UX-Text.

## Task 070.4 — Shadow Mode in Orchestrator integrieren

- **EXECUTION TARGET:** `SWE 1.6`
- **Target Decision Reason:** Multi-file Integration im Request-Workflow mit Risiko für bestehende Routing-Pfade.
- **Goal:** Jede Anfrage erhält optional eine SourceRoutingDecision, aber ohne Verhaltensänderung.
- **Files:**
  - `backend/services/chat_orchestrator.py`
  - `backend/services/orchestrator/execution_dispatcher.py`
  - `backend/services/source_routing/engine.py`
  - `tests/integration/test_source_routing_shadow_mode.py`
- **Actions:**
  - SourceRoutingEngine nach bestehender Intent-Erkennung aufrufen.
  - Decision am Workflow/Context speichern, z. B. `wf.source_routing_decision`.
  - Bestehende `relevant_skill_ids`, `forced_tool`, `force_tool_name`, `tool_choice` unverändert lassen.
  - Telemetry/Logging Event `source_routing_decision` mit Feldern: `applies`, `data_type`, `mode`, `primary_skill_id`, `fallback_skill_ids`, `reason_code`.
  - Fehler im Source Routing dürfen Chat nicht abbrechen; loggen mit `exc_info=True` und Decision `applies=False` setzen.
- **Expected Result:** Source Routing ist beobachtbar, aber risikofrei für Produktverhalten.
- **Acceptance Criteria:**
  - Integrationstest beweist: Smalltalk-Antwort läuft unverändert ohne Tool-Force.
  - Integrationstest beweist: Kalender-Mutation behält bestehende Mutation-/Forced-Tool-Logik.
  - Integrationstest beweist: Wetterfrage erzeugt SourceRoutingDecision im Shadow Mode.

## Task 070.5 — Enforced MVP für Weather/Country/Routing aktivieren

- **EXECUTION TARGET:** `SWE 1.6`
- **Target Decision Reason:** High-Risk Orchestrator-Wiring mit Forced-Tool-Interaktion und Provider-Tool-Namen.
- **Goal:** Nur eindeutig klassifizierte `weather`, `country_info`, `routing` Anfragen werden auf die Policy-Primärquelle begrenzt.
- **Files:**
  - `backend/services/orchestrator/execution_dispatcher.py`
  - `backend/services/source_routing/engine.py`
  - `tests/integration/test_source_routing_enforced_mvp.py`
- **Actions:**
  - Feature Flag oder Konstante für Enforced MVP einführen, default im Task auf testbar/aktiv nach Shadow-Gate.
  - Enforced nur wenn Decision `applies=True`, `confidence_label=high`, Datentyp in MVP-Enforced-Liste.
  - `wf.relevant_skill_ids` auf Primärquelle + erlaubte Fallbacks begrenzen, ohne bestehende höher priorisierte Spezialpfade zu überschreiben.
  - `forced_tool` nur setzen, wenn genau eine Primärquelle eindeutig ist und keine Kalender-/Video-/Mutation-/Help-Priorität aktiv ist.
  - Kanonische Skill-ID in `forced_tool.skill_id` verwenden; provider-sanitized Namen nicht als interne IDs speichern.
  - Bei Tool-Fehler Fallback-Quelle gemäß Decision zulassen.
- **Expected Result:** Wetter/Land/Route nutzen deterministisch die definierte Quelle, ohne andere Janus-Flows zu brechen.
- **Acceptance Criteria:**
  - Wetterfrage erlaubt `system.weather` primär und maximal `system.websearch` als Fallback.
  - Routingfrage erlaubt `system.routing` primär und maximal `system.websearch` als Fallback.
  - Kalenderfrage mit Ort/Zeit wird nicht durch Source Routing überschrieben.
  - Provider Gemini erhält gültige Tool-Namen über bestehende ToolManager-Sanitization.

## Task 070.6 — Source Records aus Tool-Ergebnissen ableiten

- **EXECUTION TARGET:** `Kimi k2.5`
- **Target Decision Reason:** Adapter-/Renderer-nahe Logik mit deterministischen Inputs; keine Gateway-Änderung erforderlich.
- **Goal:** Janus kann verwendete Quellen aus Tool-Ergebnissen oder Skill-Policy deterministisch darstellen.
- **Files:**
  - `backend/services/source_routing/source_block.py`
  - optional: `backend/skills/system/weather.json`
  - optional: `backend/skills/system/country_info.json`
  - optional: `backend/skills/system/routing.json`
  - `tests/unit/test_source_block_renderer.py`
- **Actions:**
  - `extract_source_records(tool_results, decision)` implementieren.
  - Wenn Tool-Ergebnis explizite URLs/Provider enthält, diese verwenden.
  - Wenn Tool-Ergebnis keine Quelle enthält, deterministische Policy-Quelle verwenden, z. B. `Open-Meteo`, `REST Countries`, `OSRM`.
  - Keine Quellen aus LLM-Text extrahieren.
  - Dedupe nach `source_id` oder `(label,url)`.
  - Renderer für Markdown-Block:
    - `### Quellen`
    - `- {label}` oder `- [{label}]({url})`
- **Expected Result:** Quellenblock ist stabil, dedupliziert und nicht halluziniert.
- **Acceptance Criteria:**
  - Leere Tool-Ergebnisse + source-required Decision erzeugen Hard-Fail oder keine Quellen je Decision.
  - Wetter-Decision rendert `Open-Meteo`.
  - Routing-Decision rendert `OSRM`.
  - Country-Info-Decision rendert `REST Countries`.

## Task 070.7 — Quellenblock in finale Antwort integrieren

- **EXECUTION TARGET:** `SWE 1.6`
- **Target Decision Reason:** Response-Finalisierung betrifft Chat-Ausgabe, Tool-Ergebnisse und mögliche UI-/Streaming-Seiteneffekte.
- **Goal:** Source-required Antworten enthalten immer einen separaten Quellenblock oder einen definierten Hard-Fail.
- **Files:**
  - `backend/services/orchestrator/response_finalizer.py`
  - `backend/services/orchestrator/schemas.py`
  - `backend/services/source_routing/source_block.py`
  - `tests/integration/test_source_routing_response_sources.py`
- **Actions:**
  - Nach Tool-Ausführung `all_tool_results` mit SourceRoutingDecision auswerten.
  - Wenn source-required und mindestens eine erfolgreiche Quelle vorhanden: Quellenblock an finale Antwort anhängen, falls nicht bereits vorhanden.
  - Wenn source-required und keine zulässige Quelle verfügbar: finale Antwort exakt auf `Keine verlässlichen Daten verfügbar.` setzen oder bestehende Fehlerantwort ersetzen.
  - Quellenblock darf nicht in Memory-Fact-Extraction als Nutzerfakt gespeichert werden; falls bestehende Extraction später greift, Source-Block klar trennbar halten.
- **Expected Result:** Nutzer sieht verlässlich, welche Quelle verwendet wurde.
- **Acceptance Criteria:**
  - Wetterantwort enthält `### Quellen` und `Open-Meteo`.
  - Country-Info-Antwort enthält `### Quellen` und `REST Countries`.
  - Routingantwort enthält `### Quellen` und `OSRM`.
  - Bei fehlender Quelle erscheint exakt `Keine verlässlichen Daten verfügbar.`.

## Task 070.8 — News/Web/Wiki/Local als Advisory erweitern

- **EXECUTION TARGET:** `SWE 1.6`
- **Target Decision Reason:** Mehrere externe Quellen und Tool-Fallbacks erhöhen Integrations- und Testkomplexität.
- **Goal:** Nicht-MVP-Datentypen erhalten Source Routing zunächst als Advisory/Shadow mit Quellenblock, aber ohne harte globale Tool-Force.
- **Files:**
  - `backend/services/source_routing/policy.py`
  - `backend/services/source_routing/classifier.py`
  - `backend/services/orchestrator/execution_dispatcher.py`
  - `tests/integration/test_source_routing_advisory_sources.py`
- **Actions:**
  - `news_rss`, `web_fact`, `wiki_fact`, `local_business` in Advisory Mode aktivieren.
  - Tool-Einschränkung nur erlauben, wenn bestehende Intent-/Skill-Auswahl den Skill ohnehin enthält oder keine Spezialpriorität aktiv ist.
  - Keine neuen externen APIs einführen.
  - Für Websearch/RSS Quellen aus Tool-Ergebnissen bevorzugen.
- **Expected Result:** Erweiterte Quellenbereiche werden sichtbarer, ohne riskante globale Umleitung.
- **Acceptance Criteria:**
  - News-Frage erzeugt Decision `news_rss` und bevorzugt `system.rss_news`, falls verfügbar.
  - Web-Fact-Frage erzeugt Decision `web_fact`.
  - Local-Business-Frage überschreibt keine Kalender-/Routing-Priorität.

## Task 070.9 — Regression- und E2E-Testpaket

- **EXECUTION TARGET:** `SWE 1.6`
- **Target Decision Reason:** Breite systemische Absicherung über reale Produktionspfade; E2E darf keine Routing-Logik mocken.
- **Goal:** Source Routing ist gegen False Positives, Tool-Force-Konflikte und Quellenblock-Fehler abgesichert.
- **Files:**
  - `tests/e2e/source-routing.spec.js`
  - `tests/integration/test_source_routing_regression.py`
  - bestehende betroffene Tests nach Bedarf
- **Actions:**
  - E2E gegen echte Chat-/Backend-Pfade erstellen.
  - Externe Grenzen nur kontrolliert mocken, nicht die SourceRoutingEngine selbst.
  - Regressionsfälle prüfen:
    - Smalltalk bleibt plain chat.
    - Help/Capability bleibt Fast-Path ohne Source Routing.
    - Kalender-Mutation bleibt Calendar Mutation Flow.
    - Wetter/Land/Route enthalten Quellen.
    - Creative writing enthält keinen Quellenblock.
  - Testdaten deterministisch halten.
- **Expected Result:** Risikoarme Schritt-für-Schritt-Umsetzung mit belastbarem Sicherheitsnetz.
- **Acceptance Criteria:**
  - Unit-, Integration- und E2E-Tests laufen grün.
  - Kein E2E-Test dupliziert Produktions-Routing-Logik.
  - Mindestens ein Flow nutzt einen echten Produktionspfad ohne vollständige Mock-Kette.

## Task 070.10 — Dokumentation, Capability Sync und Lessons Learned

- **EXECUTION TARGET:** `Kimi k2.5`
- **Target Decision Reason:** Dokumentations- und Registry-Update mit klarer Produktformulierung; keine Architekturänderung.
- **Goal:** Implementierte Source-Routing-Fähigkeiten sind dokumentiert und produktsprachlich sichtbar.
- **Files:**
  - `documentation/02_SKILL_DEVELOPMENT.md` oder passende Architektur-/Feature-Doku
  - `backend/data/capability_registry.json`
  - `WHAT_I_LEARNED.md`
- **Actions:**
  - Nur tatsächlich implementierte und getestete Fähigkeiten dokumentieren.
  - Capability Registry produktsprachlich ergänzen, keine internen Task-IDs/Dateien/Module im UX-Text.
  - Reusable Learning nur ergänzen, wenn ein neues allgemeines Muster entstanden ist.
  - Dokumentieren, dass v1 nicht global für alle Anfragen gilt.
- **Expected Result:** Nutzer- und Entwicklerdokumentation ist synchron mit der validierten Umsetzung.
- **Acceptance Criteria:**
  - Capability-Eintrag beschreibt Quellen-/Faktenrouting produktsprachlich.
  - Doku nennt Scope und Out-of-Scope v1.
  - Keine nicht implementierten Fähigkeiten werden beworben.

# 8️⃣ Test Strategy

## Unit Tests

- `test_source_routing_policy.py`
  - Policy-Mapping für alle Datentypen.
  - Fallback-Limit.
  - Hard-Fail bei unbekanntem Datentyp.

- `test_source_routing_classifier.py`
  - Positive MVP-Klassifikationen.
  - Negative Out-of-Scope-Klassifikationen.
  - False-Positive-Schutz für Kalender, Smalltalk, Kreativtext, Help.

- `test_source_routing_engine.py`
  - Shadow vs Enforced.
  - Confidence-Gate.
  - MVP-Enforced-Liste.

- `test_source_block_renderer.py`
  - Quellenextraktion aus Tool-Ergebnissen.
  - Fallback auf Policy-Quelle.
  - Dedupe und Markdown-Format.

## Integration Tests

- `test_source_routing_shadow_mode.py`
  - Orchestrator-Decision ohne Verhaltensänderung.

- `test_source_routing_enforced_mvp.py`
  - Weather/Country/Routing Tool-Begrenzung.
  - Keine Überschreibung von Kalender-/Help-/Smalltalk-Pfaden.

- `test_source_routing_response_sources.py`
  - Quellenblock in finaler Antwort.
  - Hard-Fail bei fehlender zulässiger Quelle.

## E2E Tests

- `source-routing.spec.js`
  - User fragt Wetter → Antwort enthält Fakten + `### Quellen`.
  - User fragt Route → Antwort enthält Route/Distanz + `### Quellen`.
  - User sagt `Hallo` → kein Quellenblock.
  - User fragt `Was kannst du?` → Help/Capability-Fast-Path bleibt ohne Quellenrouting.

# 9️⃣ Risk Register

- **Risk 1: Tool-Force-Konflikt mit Kalender/Video/Mutation**
  - **Mitigation:** Source Enforced nur nach Spezialpfad-Prüfung; Kalender/Video/Mutation haben Vorrang.

- **Risk 2: False Positives bei kreativen oder persönlichen Fragen**
  - **Mitigation:** Negativmarker und `confidence_label=high` Gate für Enforced Mode.

- **Risk 3: Quellenblock wird vom LLM erfunden**
  - **Mitigation:** Quellenblock nach Tool-Ergebnis/Policy deterministisch rendern, nicht aus LLM-Text.

- **Risk 4: Gemini Toolnamen-Mismatch**
  - **Mitigation:** Intern nur kanonische Skill-IDs; Provider-Sanitization beim ToolManager belassen.

- **Risk 5: Externe API-Ausfälle machen E2E flaky**
  - **Mitigation:** E2E externe Grenzen kontrolliert mocken, aber Produktionsmodule real nutzen; mindestens ein realer Flow separat als optionaler Live-Smoke.

- **Risk 6: Memory Context Bleed durch Quellen/Suggestions**
  - **Mitigation:** Quellenblock klar separieren und keine Quellen aus Assistant-Text als Nutzerfakten behandeln.

# 🔟 Definition of Done

- Source Routing läuft zuerst im Shadow Mode ohne Regression.
- Enforced Mode ist nur für `weather`, `country_info`, `routing` aktiv.
- Source-required Antworten enthalten `### Quellen` oder den exakten Hard-Fail-Text.
- Smalltalk, Help, Kalender-Mutationen, Memory Writes, kreative Aufgaben und Dateioperationen bleiben unverändert.
- Alle Unit-, Integration- und E2E-Tests bestehen.
- Keine neuen API-Keys oder externen Provider werden hardcoded.
- Dokumentation und Capability Registry sind nur für implementierte Fähigkeiten aktualisiert.

# 11️⃣ Task Coverage Validation

## Requirements → Tasks

- **Intent-Klassifikation:** Task 070.2
- **Datentyp Mapping:** Task 070.1, 070.3
- **Source Policy:** Task 070.1, 070.3
- **Kontextbasierte Priorisierung:** Task 070.4, 070.5 mit Spezialpfad-Vorrang
- **Lineare Pipeline:** Task 070.4 bis 070.7 für source-required Pfade
- **Fallbacks:** Task 070.1, 070.3, 070.5
- **Quellenanzeige:** Task 070.6, 070.7
- **Hard Fail:** Task 070.3, 070.7
- **Tests:** Task 070.9
- **Dokumentation:** Task 070.10

## Edge Cases → Tasks

- **API failure:** Task 070.3, 070.5, 070.7
- **Websearch failure:** Task 070.3, 070.8
- **No source available:** Task 070.3, 070.7
- **Conflicting data:** Task 070.1 policy priority, Task 070.8 advisory expansion
- **Invalid request:** Task 070.2 not_applicable + existing chat behavior

## Constraints → Tasks

- **Keine freie LLM-Quellenwahl:** Task 070.3, 070.6, 070.7
- **Keine impliziten Entscheidungen:** Task 070.1 Policy-Vertrag
- **Keine Änderung bestehender Regeln, nur additive Erweiterung:** Task 070.4 Shadow Mode und Task 070.5 Priority Guard
- **Keine Best-Effort source-required Antwort:** Task 070.7 Hard-Fail

# 12️⃣ Final Plan Lock

- **Plan Status:** READY FOR TASK EXECUTION after `/2_pre-check` validates Impact-Analyse and scope.
- **Execution Order:** 070.1 → 070.2 → 070.3 → 070.4 → Shadow Gate → 070.5 → 070.6 → 070.7 → 070.8 → 070.9 → 070.10
- **Hard Stop Gate 1:** Nach 070.4 müssen Shadow-Mode-Tests beweisen, dass keine bestehenden Flows verändert wurden.
- **Hard Stop Gate 2:** Vor 070.5 muss entschieden sein, ob Enforced Mode per Feature Flag oder Konstante aktiviert wird.
- **Hard Stop Gate 3:** Vor 070.8 müssen MVP-Enforced-Flows stabil sein.
- **Invalid If:** Ein Task ohne `EXECUTION TARGET` existiert.
- **Invalid If:** Ein Task verlangt globale Source-Routing-Erzwingung für alle Janus-Anfragen.
- **Invalid If:** Quellen werden aus LLM-Fließtext statt Tool-/Policy-Daten erzeugt.
