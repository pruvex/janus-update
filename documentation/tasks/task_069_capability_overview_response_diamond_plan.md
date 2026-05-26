# 💎 DIAMOND TASK: Capability Overview Response

---
task_id: TASK-069
status: SEALED
assigned_to: KIMI-FIRST
confidence_level: HIGH
created_at: 2026-05-04 21:22
updated_at: 2026-05-05 01:08
source_spec: documentation/Planned Features/Capability Overview Response.md
completion_gate:
  tests: true
  audit_trail: true
  lessons_learned: true
---

# 1️⃣ Task Description

Janus soll auf explizite Nutzerfragen nach seinen Fähigkeiten, z. B. `Was kannst du?`, eine vollständige, strukturierte, deterministische und nutzerverständliche Capability-Übersicht ausgeben.

Die Antwort muss ausschließlich aus der validierten Capability Registry erzeugt werden. Der bestehende Help Fast-Path wird erweitert/gehärtet. Es darf kein LLM für die Capability-Overview-Antwort verwendet werden.

# 2️⃣ Impact-Analyse

- **Basiert auf:** FEAT-HELP-001 bestehendes Help-System / Capability Registry; `documentation/Planned Features/Capability Overview Response.md`
- **Beeinflusst:** `backend/services/capability_registry.py`, `backend/services/help_skill.py`, `backend/services/orchestrator/intent_engine.py`, `backend/services/chat_orchestrator.py`, `backend/data/capability_registry.json`, Tests für Unit/Integration/E2E
- **Risiko-Einschätzung:** MEDIUM

# 2.1 Resolved Product Decisions

- **Renderer-Architektur:** Deterministischer Backend-Renderer ohne LLM.
- **Sortierung:** Feste Kategorie-Reihenfolge im Renderer, Capabilities alphabetisch nach Anzeigename.
- **Kategorie-Reihenfolge:**
  1. Kommunikation & Chat
  2. Wissen & Recherche
  3. Aufgaben & Produktivität
  4. Kalender & Termine
  5. Dateien & Dokumente
  6. Bilder & Medien
  7. Analyse & Auswertung
  8. Entwicklung & Automatisierung
  9. Einstellungen & System
  10. Updates & Installation
  11. Sonstiges
- **Unknown Categories:** Immer unter `Sonstiges` einsortieren.
- **Intent-Erkennung:** Exakte Phrase-Liste mit Normalisierung.
- **Trigger:** `was kannst du`, `was kannst du?`, `welche fähigkeiten hast du`, `welche fähigkeiten hast du?`, `zeig mir deine fähigkeiten`, `zeige mir deine fähigkeiten`.
- **Normalisierung:** `lowercase + trim + collapse_whitespace`; nur terminales `?` wird ignoriert.
- **Fallback:** Nutzer sieht exakt: `Ich kann meine Fähigkeiten aktuell nicht zuverlässig anzeigen. Bitte versuche es später erneut.`
- **Fallback Logging:** Internes `warning` mit Fehlerklasse; keine technischen Details im UX-Output.
- **Antwortformat:**
  - Header: `## Das kann ich aktuell`
  - Intro: `Ich kann dir aktuell in diesen Bereichen helfen:`
  - Category: `### {category}`
  - Capability: `- **{name}:** {description}`
  - Leere Kategorien auslassen.
  - Kein Outro.
- **Required Capability Fields:** `id`, `name`, `description`, `category`, `status`, `confidence`.
- **Skip Rule:** Capabilities mit fehlendem Pflichtfeld werden übersprungen.
- **Dedupe Key:** `id`.
- **Trust Layer:** Lokale Registry-Filter only: `status == verified` und `confidence >= 0.7`; externer Trust-Service ist `OUT_OF_SCOPE`.

# 3️⃣ Relevant Prior Learnings

- **#RealModuleE2E:** E2E-Tests müssen echte Produktionspfade prüfen und dürfen keine UI-/Routing-Logik testlokal nachbauen.
- **#DeterministicSkillTesting:** Validierung muss deterministisch sein; keine KI-basierte Bewertung von Output-Korrektheit.
- **Capability UX Rule:** Capability-Texte müssen produktsprachlich bleiben und dürfen keine Task-IDs, Dateien, Module, IPC oder Implementierungsdetails enthalten.

# 4️⃣ Spec Validation Result

## Mandatory Sections

- **Feature Name:** vorhanden.
- **Core Idea:** vorhanden.
- **Functional Core:** vorhanden, durch Entscheidungen konkretisiert.
- **System Behavior:** vorhanden, durch Entscheidungen konkretisiert.
- **Edge Cases:** vorhanden, Fallback exakt definiert.
- **Constraints:** vorhanden.
- **Integration Context:** vorhanden.
- **Test Strategy:** vorhanden.
- **Definition of Done:** vorhanden.

## Determinism Status

- **Output generation:** deterministisch, kein LLM.
- **Intent trigger:** deterministische Triggerliste.
- **Filtering:** deterministische lokale Trust-Regeln.
- **Sorting:** feste Kategorie-Reihenfolge + alphabetische Capability-Sortierung.
- **Fallback:** exakt definierter Nutzertext.

# 5️⃣ Codebase Alignment

## Existing Modules To Extend

- `backend/services/capability_registry.py`
  - Lädt `backend/data/capability_registry.json`.
  - Enthält bereits `get_overview()` und i18n-Helfer.
  - Aktuell liefert Overview nach bestehender Registry-Struktur, aber ohne `status/confidence`-Filter und ohne das neue Output-Schema.

- `backend/services/help_skill.py`
  - Bereits deterministischer HelpSkill ohne LLM.
  - `_handle_capability_overview()` ist der primäre Erweiterungspunkt.
  - Aktueller Output enthält Intro mit Produkt-/Provider-/Memory-Text und listet Kategorien anders als die neue Spec.

- `backend/services/orchestrator/intent_engine.py`
  - Enthält `HELP_CAPABILITY_OVERVIEW_PATTERNS` und `detect_capability_overview()`.
  - Aktuell regex-/substring-artiger als die neue exakte Triggerregel.

- `backend/services/chat_orchestrator.py`
  - Hat bestehenden Help Fast-Path.
  - `_resolve_help_intent()` priorisiert `model_query > capability_overview > how_to > navigation`.
  - Bei Help-Intent wird `self.help_skill.handle(...)` aufgerufen und LLM übersprungen.

- `backend/data/capability_registry.json`
  - Bestehendes Schema nutzt Kategorien mit `display_name`, `description`, `abilities`, Ability-Felder wie `id`, `label`, `how_to`, `skill_refs`.
  - Das Feature verlangt ein flaches Anzeigeschema (`id`, `name`, `description`, `category`, `status`, `confidence`) oder eine eindeutige Adapterlogik.

## Architecture Conflict

Es gibt einen Schema-Konflikt zwischen Feature-Spec und aktueller Registry:

- **Spec erwartet Capability-Felder:** `name`, `description`, `category`, `status`, `confidence`.
- **Aktuelle Registry enthält primär:** Kategorien + `abilities[].label`, `abilities[].how_to`, ohne sichtbare `status/confidence` in gelesenen Ausschnitten.

## Required Resolution

Die Umsetzung darf die Registry nicht großflächig migrieren. Stattdessen wird ein **Adapter in `CapabilityRegistry`** geplant:

- Kategorie-Daten liefern `category` aus lokalisiertem `display_name`.
- Ability `name` kommt aus lokalisiertem `label`.
- Ability `description` kommt aus lokalisiertem `how_to`, solange kein separates `description`-Feld vorhanden ist.
- `status` defaultet nicht automatisch auf `verified`, außer die Capability erfüllt eine explizite bestehende oder neu ergänzte Registry-Regel.
- Für Plan-Determinismus muss jede angezeigte Capability tatsächlich `status` und `confidence` besitzen oder durch eine explizite, getestete Registry-Normalisierung ergänzt werden.

# 6️⃣ Target Architecture

```text
User Input
  → IntentEngine.detect_capability_overview()
  → ChatOrchestrator._resolve_help_intent()
  → Help Fast-Path
  → HelpSkill._handle_capability_overview()
  → CapabilityRegistry.get_verified_capability_overview()
  → Deterministic Markdown Renderer
  → Chat response without LLM
```

## Module Boundaries

- **IntentEngine:** Nur Trigger-Erkennung, keine Registry-Logik.
- **CapabilityRegistry:** Laden, defensive Validierung, Filterung, Dedupe, Gruppierung, Sortierdaten bereitstellen.
- **HelpSkill:** Antwortformat und Fallback-Handling.
- **ChatOrchestrator:** Bestehenden Help Fast-Path unverändert nutzen, nur Tests absichern.

# 7️⃣ Implementation Plan

## Task 069.1 — Intent Detection deterministisch machen

- **EXECUTION TARGET:** `Kimi k2.5`
- **Target Decision Reason:** Deterministische String-Normalisierung in einer klar abgegrenzten Datei mit geringem Architektur-Risiko.
- **Goal:** `Capability Overview` wird nur durch die definierte Triggerliste erkannt.
- **Files:** `backend/services/orchestrator/intent_engine.py`
- **Actions:**
  - Bestehende `HELP_CAPABILITY_OVERVIEW_PATTERNS` für dieses Feature durch eine normalisierte exakte Triggerliste ersetzen oder ergänzen.
  - Normalisierung implementieren: lowercase/casefold, trim, whitespace collapse, terminales `?` entfernen.
  - `detect_capability_overview()` darf nur `True` liefern, wenn normalisierter Text exakt in der Triggerliste liegt.
- **Expected Result:** Keine False Positives durch freie Regex-Matches wie `deine features` oder `show capabilities`, sofern nicht explizit in Triggerliste.

## Task 069.2 — Capability Registry Adapter/Validator ergänzen

- **EXECUTION TARGET:** `Kimi k2.5`
- **Target Decision Reason:** Isolierte Datenstruktur- und Filterlogik in einer bestehenden Serviceklasse ohne neue Architekturentscheidung.
- **Goal:** Registry liefert eine deterministische, gefilterte, deduplizierte Capability-Liste für die Overview-Antwort.
- **Files:** `backend/services/capability_registry.py`
- **Actions:**
  - Neue Methode planen/implementieren: `get_verified_capabilities_for_overview(language="de")`.
  - Defensive Validierung für erforderliche Felder nach normalisiertem Adapter-Schema: `id`, `name`, `description`, `category`, `status`, `confidence`.
  - Filter: `status == "verified"`, `confidence >= 0.7`.
  - Dedupe: erster gültiger Eintrag pro `id` gewinnt.
  - Fehlende/ungültige Einträge überspringen und intern mit `warning` loggen.
  - Unbekannte/leer gemappte Kategorie auf `Sonstiges` setzen.
- **Expected Result:** HelpSkill bekommt nur gültige, anzeigbare Produkt-Capabilities.

## Task 069.3 — Registry-Daten für Anzeige vervollständigen

- **EXECUTION TARGET:** `Kimi k2.5`
- **Target Decision Reason:** Reines JSON-Content-Editing mit klaren Pflichtfeldern und validierbarem Output.
- **Goal:** Die aktuelle `capability_registry.json` enthält alle Pflichtdaten für anzeigbare Capabilities.
- **Files:** `backend/data/capability_registry.json`
- **Actions:**
  - Für alle Capabilities, die angezeigt werden sollen, `status` und `confidence` ergänzen.
  - Falls ein Ability-spezifisches `description`-Feld fehlt, entweder hinzufügen oder Adapter nutzt deterministisch `how_to` als Beschreibung.
  - Kategorie-Mapping auf die beschlossene UX-Kategorie-Reihenfolge sicherstellen.
  - Keine technischen Details in UX-Feldern eintragen.
- **Expected Result:** Mindestens eine gültige Capability je relevanter Produktkategorie ist anzeigbar; ungültige/unsichere Capabilities bleiben ausgeblendet.

## Task 069.4 — Deterministischen Markdown Renderer im HelpSkill umsetzen

- **EXECUTION TARGET:** `Kimi k2.5`
- **Target Decision Reason:** Deterministisches Template-Rendering in einer einzelnen bestehenden Datei mit klar definiertem Markdown-Output.
- **Goal:** `_handle_capability_overview()` gibt exakt das beschlossene Markdown-Format aus.
- **Files:** `backend/services/help_skill.py`
- **Actions:**
  - `FALLBACK_MESSAGE` oder capability-spezifischen Fallback auf exakt `Ich kann meine Fähigkeiten aktuell nicht zuverlässig anzeigen. Bitte versuche es später erneut.` setzen.
  - `_handle_capability_overview()` auf neue Registry-Methode umstellen.
  - Feste Kategorie-Reihenfolge verwenden.
  - Capabilities innerhalb der Kategorie alphabetisch nach `name` sortieren.
  - Leere Kategorien auslassen.
  - Output exakt rendern:
    - `## Das kann ich aktuell`
    - Leerzeile
    - `Ich kann dir aktuell in diesen Bereichen helfen:`
    - Leerzeile
    - `### {category}`
    - `- **{name}:** {description}`
  - Suggestions für diese Antwort entweder leer lassen oder nur explizit testbare bestehende UX-Regeln beibehalten; bevorzugt leer, damit Output rein deterministisch bleibt.
- **Expected Result:** Antwort ist snapshot-stabil und enthält nur Registry-basierte Produkttexte.

## Task 069.5 — Help Fast-Path Regression absichern

- **EXECUTION TARGET:** `SWE 1.6`
- **Target Decision Reason:** Integrationstest und Fast-Path-Wiring betreffen Orchestrator-Verhalten und benötigen breiteres Codebase-Reasoning.
- **Goal:** Sicherstellen, dass `Was kannst du?` den LLM-Pfad nicht nutzt.
- **Files:** `backend/services/chat_orchestrator.py`, Tests
- **Actions:**
  - Keine Architekturänderung am Fast-Path, sofern bestehendes Wiring funktioniert.
  - Regressionstest ergänzen, der `help_intent_type == "capability_overview"`, `skip_llm_generation == True` und `final_text_to_generate` mit Markdown-Header prüft.
- **Expected Result:** Capability Overview bleibt lokaler Fast-Path ohne Modellkosten und ohne Halluzinationsrisiko.

# 8️⃣ Test Strategy

## Unit Tests

### `IntentEngine.detect_capability_overview()`

- **Positive:**
  - `Was kannst du?`
  - `was kannst du`
  - `Welche Fähigkeiten hast du?`
  - `Zeig mir deine Fähigkeiten`
  - `Zeige mir deine Fähigkeiten`
- **Negative:**
  - `Was kannst du über München sagen?`
  - `Welche Features hat Python?`
  - `Erklär mir deine Meinung`
  - leerer String

### `CapabilityRegistry.get_verified_capabilities_for_overview()`

- Zeigt nur `status == verified`.
- Zeigt nur `confidence >= 0.7`.
- Überspringt fehlende `description`.
- Überspringt fehlende `id`.
- Dedupliziert nach `id`.
- Mappt unbekannte Kategorie auf `Sonstiges`.
- Gibt Fallback-leere Liste bei ungültiger Registry-Struktur zurück.

### `HelpSkill._handle_capability_overview()`

- Rendert exakt Header/Intro/Kategorie/Capability-Zeilen.
- Lässt leere Kategorien aus.
- Sortiert Kategorien nach fester Liste.
- Sortiert Capabilities alphabetisch.
- Gibt exakt den Fallback-Text bei leerem Ergebnis zurück.

## Integration Tests

- `CapabilityRegistry` lädt echte `backend/data/capability_registry.json`.
- `HelpSkill.handle(intent_type="capability_overview")` erzeugt mit echter Registry eine nicht-leere Antwort.
- Antwort enthält keine technischen Begriffe wie `task_`, `IPC`, `.py`, `.js`, `backend/`, `frontend/`, sofern diese nicht Teil eines legitimen Produktnamens wären.

## E2E Tests (Mandatory)

- **File:** `tests/e2e/capability-overview.spec.js`
- **Flow:**
  1. App öffnen.
  2. Neuen Chat starten.
  3. `Was kannst du?` senden.
  4. Letzte Assistant-Nachricht prüfen.
- **Assertions:**
  - Antwort enthält `## Das kann ich aktuell`.
  - Antwort enthält `Ich kann dir aktuell in diesen Bereichen helfen:`.
  - Antwort enthält mindestens eine Kategorieüberschrift `### ...`.
  - Antwort enthält mindestens eine Capability-Zeile im Format `- **...:** ...`.
  - Antwort enthält keine technischen Interna: `backend/`, `frontend/`, `IPC`, `task_`, `.py`, `.js`.
  - Antwort erscheint ohne erkennbare LLM-Wartezeit/Tool-Ausführung; falls testbar, Backend-Log oder Response-Metadaten bestätigt Help Fast-Path.

## State / Consistency Tests

- Änderung einer Test-Registry-Kopie von `status=verified` auf `status=draft` entfernt die Capability aus der Ausgabe.
- Änderung `confidence=0.69` entfernt die Capability.
- Änderung `confidence=0.7` zeigt die Capability.

# 9️⃣ Acceptance Criteria

- [x] `Was kannst du?` wird über Help Fast-Path beantwortet und löst keinen LLM-Call aus.
- [x] Antwort basiert ausschließlich auf `backend/data/capability_registry.json`.
- [x] Nur Capabilities mit `status == verified` und `confidence >= 0.7` werden angezeigt.
- [x] Capabilities mit fehlenden Pflichtfeldern werden übersprungen.
- [x] Doppelte Capabilities werden nach `id` dedupliziert.
- [x] Kategorien folgen exakt der beschlossenen Reihenfolge.
- [x] Unbekannte Kategorien werden unter `Sonstiges` einsortiert.
- [x] Capabilities innerhalb einer Kategorie sind alphabetisch nach Anzeigename sortiert.
- [x] Fallback-Text ist exakt: `Ich kann meine Fähigkeiten aktuell nicht zuverlässig anzeigen. Bitte versuche es später erneut.`
- [x] UX-Output enthält keine technischen Implementierungsdetails.
- [x] Mindestens ein echter Playwright-E2E-Flow besteht.

# 🔟 Out of Scope

- Externe Capability Trust Service Integration.
- LLM-basierte Formulierung oder Umformulierung der Capability Overview.
- UI-Komponenten für eine separate Capability-Seite.
- Neue Capability-Erfassung oder Auto-Discovery über die bestehende Registry-Pflege hinaus.
- Mehrsprachige Ausgabe außerhalb bestehender `language="de"`-Pfadabsicherung.
- Änderung der allgemeinen How-To- oder Navigation-Help-Features, außer Regressionen entstehen durch gemeinsame Helper.

# 1️⃣1️⃣ Risk Register

| Risiko | Impact | Mitigation |
| :--- | :--- | :--- |
| Registry-Schema passt nicht zur Spec | Hoch | Adapter-Methode statt große Migration; Pflichtfelder gezielt ergänzen |
| Bestehende Help-Features brechen | Mittel | Tests für `how_to`, `navigation`, `model_query` nicht verändern oder ergänzen |
| E2E testet Mock statt Produktpfad | Hoch | RealModuleE2E: echte App und echter Chat-Flow verwenden |
| UX enthält technische Details aus Registry | Mittel | Integrationstest auf verbotene Tokens |
| Trigger wird zu breit | Mittel | Exakte Normalisierung + Triggerliste |

# 1️⃣2️⃣ Phase 6.5 Task Coverage Validation

| Spec Requirement | Covered By | Test Mapping |
| :--- | :--- | :--- |
| Explizite Anfrage erkennen | Task 069.1 | Unit Intent + E2E |
| Registry als Single Source | Task 069.2/069.3 | Integration echte Registry |
| Verified + confidence Filter | Task 069.2 | Unit + State Tests |
| Gruppierung nach Kategorie | Task 069.2/069.4 | Unit Renderer |
| Deterministische Sortierung | Task 069.4 | Unit Snapshot |
| Strukturierte Markdown-Antwort | Task 069.4 | Unit + E2E |
| Fallback bei leer/fehlerhaft | Task 069.2/069.4 | Unit |
| Dedupe nach ID | Task 069.2 | Unit |
| Keine technischen Details | Task 069.3/069.4 | Integration + E2E |
| Kein LLM | Task 069.5 | Integration/Fast-Path Test |

Coverage Status: **PASS** — alle Anforderungen sind Tasks und Tests zugeordnet oder explizit OUT OF SCOPE.

# 1️⃣3️⃣ Phase 6.6 Final Plan Lock

- **Duplicate Tasks:** Keine erkannt.
- **Contradictions:** Keine nach Entscheidungen.
- **Atomicity:** Tasks sind sequenziell und pro Ziel getrennt.
- **Execution Target:** Pro Task explizit festgelegt; keine Zielmodell-Entscheidung durch Orchestrator oder Downstream-Agent.
- **READY FOR TASK EXECUTION:** Ja.

# 1️⃣4️⃣ Audit Trail

| Datum | Status | Änderung | Verantwortlich | Bemerkung |
| :--- | :--- | :--- | :--- | :--- |
| 2026-05-04 | OPEN | Task initialisiert | Cascade | `/1_Feature-erstellen` auf Capability Overview Response ausgeführt |
| 2026-05-04 | DONE | Implementierung + Final Audit PASS WITH FIXES; Dokumentationsupdate (`4_Dokumentationsupdate`) | SWE | E2E-Fixes in `capability-overview.spec.js` |

# 1️⃣5️⃣ Lessons Learned

- Siehe `WHAT_I_LEARNED.md` → Pattern **#BrowserE2EInternalApiKey** (Vite-E2E ohne Electron benötigt `X-Janus-Internal-Key` für `/api/*`).

# 1️⃣6️⃣ Completion Gate Checklist

- [x] Implementierung abgeschlossen.
- [x] Unit Tests grün.
- [x] Integration Tests grün.
- [x] Playwright E2E grün.
- [x] `/2_final-audit` PASS oder PASS WITH FIXES.
- [x] Audit Trail aktualisiert.
- [x] Lessons Learned geprüft.

---

## POST-IMPLEMENTATION AUDIT TRAIL

### Implementation Scope
- **Implemented tasks:** T069.1–T069.5 (Intent-Normalisierung, Registry-Adapter `get_verified_capabilities_for_overview`, Registry-Pflichtfelder, HelpSkill-Markdown-Renderer, Tests + E2E)
- **Feature status:** DONE
- **Final audit status:** PASS WITH FIXES

### Files Changed
- **`backend/services/orchestrator/intent_engine.py`:** Exakte Triggerliste + Textnormalisierung für Capability-Overview-Intent.
- **`backend/services/capability_registry.py`:** `get_verified_capabilities_for_overview()`, Filter/Dedupe/Validierung, Kategorie-Mapping inkl. „Sonstiges“.
- **`backend/services/help_skill.py`:** Deterministisches Markdown laut Spec; Fallback-Text fix.
- **`backend/data/capability_registry.json`:** `status`/`confidence` für angezeigte Fähigkeiten (verified ≥0.7).
- **`backend/tests/unit/test_capability_registry_logic.py`:** Filter-/Dedupe-/Pflichtfeld-Tests.
- **`backend/tests/integration/test_help_end_to_end.py`**, **`test_help_integration_real.py`:** Fast-Path ohne LLM.
- **`tests/e2e/capability-overview.spec.js`:** End-to-End „Was kannst du?“ (JWT + interner API-Key, siehe Fixes).

### What Was Done
Deterministische Capability-Übersicht aus der Registry über den Help Fast-Path ohne LLM; Trigger strikt per normalisierter Phrasenliste; E2E gegenecht mit realem Chat-Pfad.

### Validation Evidence
- **`python -m pytest backend/tests/unit/test_capability_registry_logic.py backend/tests/integration/test_help_end_to_end.py backend/tests/integration/test_help_integration_real.py -q`:** PASS — 21 passed (Stand Final Audit).
- **`python -m json.tool backend/data/capability_registry.json`:** PASS.
- **`npx playwright test tests/e2e/capability-overview.spec.js`:** PASS — 2 passed (describe serial).

### Final Audit Fixes
- **`tests/e2e/capability-overview.spec.js`:** Playwright `page.route` setzt `X-Janus-Internal-Key` aus AppData-`config.json` (Vite ohne Electron); Klick auf Chat-Fenster A vor „Neuer Chat“; Warten auf erfolgreiches `POST /api/chats`; Senden via `import('/js/chat.js').sendMessage('A')`; `test.describe.configure({ mode: 'serial' })` gegen SQLite-Konkurrenz.

### Version Bump
- **Old version:** 0.4.17-beta.3
- **New version:** 0.4.17-beta.4
- **Files changed:** package.json, PROJECT_STATE.md

### Remaining Risks
- Registry-Warnungen zu verwaisten `skill_refs` und Einträgen ohne Pflichtfelder bleiben im Log sichtbar; betrifft nicht den Overview-Fast-Path.

## DEBUGGING LOG

- **Keine Assistant-Nachricht im E2E:** Ursache fehlender `X-Janus-Internal-Key` bei Browser-Fetch (nur Electron injiziert); Fix `page.route` + Key aus Config.
- **`#dock-bar` blockiert Senden-Klick:** Umstellung auf programmatisches `sendMessage('A')`.
- **Parallele Playwright-Worker + eine E2E-DB:** Timeouts; Fix `serial` im Describe.
- **„Neuer Chat“ ohne aktives Fenster A / ohne verifiziertes POST:** Warten auf `POST /api/chats` ok + Region A fokussieren.
