# TASK: BACKLOG-073 - TestPlan Oracle mismatch für Core Routing Decision Quality (Spec 04)

## Ziel
TestPlan-Generator für Spec 04 Core Routing Decision Quality korrigieren, damit er korrekte Routing-Oracles statt generischer Source-Attribution-Patterns erzeugt.

## Beschreibung
Der TestPlan-Generator `tests/e2e/generator/compile-testspec-to-testplan.mjs` verwendet für Spec 04 (Core Routing Decision Quality) generische Source-Attribution-Patterns (Wetterdienst, Wikipedia, RSS/Feed, Geo-Service) statt der spezifischen Routing-Expectations (direct_response, capability_overview, weather/API route, filesystem route, memory recall, calendar read, web/current research, refusal, clarification). Dies führt zu 24/38 ASSERTION_MISMATCH-Failures in TEST-RUN-2026-05-18-020, obwohl die Evidence fachlich korrektes Produktverhalten zeigt.

## Files
- `tests/e2e/generator/compile-testspec-to-testplan.mjs` (Generator-Fix)
- `documentation/TEST_SPEC/01_core_system/04_core_routing_decision_quality.md` (Referenz-Spec)
- `documentation/test-runs/TEST-RUN-2026-05-18-020_plan.json` (Fehlerhafter aktueller Plan)
- `documentation/test-results/TEST-RUN-2026-05-18-020_results.json` (Evidence für korrektes Verhalten)

## Steps

### Step 1: Generator für Spec 04 Pattern-Logik erweitern
- Analysiere die Spec 04 Functional Test Matrix und Natural Language Intent Matrix
- Identifiziere die korrekten Routing-Expectations pro TestCase-Typ:
  - TC-001 (Plain chat): direct_response → akzeptiere Plain-Chat-Antworten, keine Wetter-Patterns
  - TC-002 (Capability help): capability_overview → akzeptiere Capability-Overview, keine Wikipedia-Patterns
  - TC-003 (Weather route): weather/API lookup → akzeptiere "Quelle:", Open-Meteo, Wetterdaten
  - TC-004 (Filesystem route): filesystem.create_directory/clarification → akzeptiere Ordner-erstellte/Clarification-Antworten, keine RSS/Feed-Patterns
  - TC-005 (Memory recall): memory/read → akzeptiere Memory-Recall oder "nicht gefunden", keine Web-Patterns
  - TC-006 (Calendar read): calendar.list_events → akzeptiere Calendar-Read oder "keine Termine", keine generischen Clarification-Patterns
  - TC-007 (Current research): web/current research → akzeptiere Web-Research oder honest blocker
  - TC-008 (Unsupported regulated): refusal → akzeptiere Refusal-Antworten, keine Capability-Patterns
  - TC-009 (Ambiguous target): clarification → akzeptiere Clarification-Fragen, keine Capability-Patterns
  - INT-001 (Smalltalk): direct_response → akzeptiere Smalltalk-Antworten, keine Clarification-Patterns
  - INT-002 (Help/capability): capability_overview → akzeptiere Capability-Overview, keine Wikipedia-Patterns
  - INT-003 (Weather lookup): weather/API lookup → akzeptiere "Quelle:", Open-Meteo
  - INT-004 (Filesystem mutation): filesystem.create_directory/clarification → akzeptiere Clarification oder Pfad-Anforderung, keine RSS/Feed-Patterns
  - INT-005 (Calendar read): calendar.list_events → akzeptiere Calendar-Read oder "keine Termine", keine Web-Patterns
  - INT-006 (Unsupported regulated): refusal → akzeptiere Clarification für Refusal-Kontext
- Erweitere `compile-testspec-to-testplan.mjs` mit Spec-04-spezifischer Pattern-Zuweisungslogik
- Füge eine Mapping-Function hinzu, die Spec-04-TestCase-IDs auf korrekte `containsAny`-Patterns mapped
- Stelle sicher, dass die Logik deterministisch ist und nur für Spec 04 greift

### Step 2: Neuen TestPlan generieren
- Führe `node tests/e2e/generator/compile-testspec-to-testplan.mjs` für Spec 04 aus
- Speichere den neuen TestPlan unter `documentation/test-runs/TEST-RUN-2026-05-18-021_plan.json` (neue TestRun-ID für Retest)
- Verifiziere, dass der generierte Plan die korrekten Patterns enthält

### Step 3: TestPlan validieren
- Führe `node tests/e2e/generator/validate-test-plan.mjs --plan documentation/test-runs/TEST-RUN-2026-05-18-021_plan.json --spec documentation/TEST_SPEC/01_core_system/04_core_routing_decision_quality.md` aus
- Stelle sicher, dass Validation PASS zurückgibt
- Wenn Validation FAIL: Generator-Fix in Step 1 korrigieren und Plan neu generieren

### Step 4: Live Runner generieren
- Führe `node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-18-021_plan.json` aus
- Verifiziere, dass `tests/e2e/generated/TEST-RUN-2026-05-18-021.live.spec.js` erstellt wurde

### Step 5: Retest ausführen
- Führe `npx playwright test tests/e2e/generated/TEST-RUN-2026-05-18-021.live.spec.js --workers=1 --reporter=list` aus
- Warte auf Test-Abschluss
- Generiere TestResult-JSON und Markdown mit `node tests/e2e/generator/compile-test-results.mjs --run TEST-RUN-2026-05-18-021`

### Step 6: Retest-Ergebnisse validieren
- Prüfe `documentation/test-results/TEST-RUN-2026-05-18-021_results.json`
- Wenn alle vorherigen ASSERTION_MISMATCH-Failures behoben sind: Task DONE
- Wenn neue FAILs auftreten, die echtes Produktfehlverhalten zeigen: STOP und Routing zu Product/Runtime Backlog (kein Oracle-Greenwashing)
- Wenn weiterhin ASSERTION_MISMATCH für andere Fälle: Generator-Fix in Step 1 verfeinern

## Acceptance Criteria
- TestPlan für Spec 04 enthält passende `expected.containsAny` Patterns für alle Core-Routing-Fälle (direct_response, capability_overview, weather/API, filesystem, memory, calendar, web/current research, refusal, clarification)
- Keine generischen Source-Attribution-Patterns (Wetterdienst, Wikipedia, RSS/Feed, Geo-Service) für Plain Chat, Capability Help, Filesystem, Memory, Calendar, Refusal oder Clarification
- `validate-test-plan.mjs` validiert den neu generierten Plan mit PASS
- Retest TEST-RUN-2026-05-18-021 zeigt keine ASSERTION_MISMATCH-Failures für die bisher betroffenen 24 TestCases
- Wenn Retest echtes Produktfehlverhalten zeigt, Task wird gestoppt und zu Product/Runtime Backlog geroutet (kein Oracle-Greenwashing)

## Tests
- TestPlan-Validation: `node tests/e2e/generator/validate-test-plan.mjs --plan documentation/test-runs/TEST-RUN-2026-05-18-021_plan.json --spec documentation/TEST_SPEC/01_core_system/04_core_routing_decision_quality.md` → PASS
- Live Retest: `npx playwright test tests/e2e/generated/TEST-RUN-2026-05-18-021.live.spec.js --workers=1 --reporter=list` → Mindestens 32/38 PASS (alle vorherigen 24 ASSERTION_MISMATCH behoben + bestehende 14 PASS)
- Result-Generation: `node tests/e2e/generator/compile-test-results.mjs --run TEST-RUN-2026-05-18-021` → Erfolgreiche JSON/MD-Generierung

## Model
SWE 1.6

## Reason
Deterministischer Generator-Fix mit klarer Code-Aenderung in einer Datei. Test-Validation und Retest sind integrierte Steps mit konkreten Output-Erwartungen. Keine Architekturentscheidungen erforderlich.

## Completion Audit Trail

- **Status:** DONE
- **Completed at:** 2026-05-18
- **Final Audit:** `documentation/test-runs/BACKLOG-073_final_audit.md`
- **Final TestRun:** `TEST-RUN-2026-05-18-023`
- **Final Result:** PASS 38/38; failed 0; blocked 0; manual gates 0.
- **Evidence:** `documentation/test-results/TEST-RUN-2026-05-18-023_results.json`, `documentation/test-results/TEST-RUN-2026-05-18-023_results.md`
- **Changed Files:** `tests/e2e/generator/compile-testspec-to-testplan.mjs`
- **Notes:** The intermediate retest `TEST-RUN-2026-05-18-021` was 31/38 because seven safe/correct responses were still rejected by overly narrow Spec-04 oracle patterns. The final generator calibration accepts safe refusal, safe clarification, memory recall and current-research follow-up variants while preserving unsafe-route and leak guards.

## Original Reason
Deterministischer Generator-Fix mit klarer Code-Änderung in einer Datei. Test-Validation und Retest sind integrierte Steps mit konkreten Output-Erwartungen. Keine Architekturentscheidungen erforderlich.
