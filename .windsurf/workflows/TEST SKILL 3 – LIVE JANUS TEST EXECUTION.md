---
description: Janus V3 — TEST SKILL 3. Live-Janus-Test: Preflight (Generator/Validator/Connectivity), User-Gate OK START LIVE TEST, Playwright-Lauf, Evidence/TestResult, Handoff TEST SKILL 4. Keine Produktimplementation.
---

This skill follows the global rules in `documentation/pipeline/PIPELINE_CONTRACT.md`.

## Rolle

Orchestrierung der **versionierten** Generator-/Validator-/Runner-Pipeline für **einen** gebundenen Testlauf. Kein freier Playwright-Code aus dem Chat; keine Produkt-Features.

## Critical Preflight Contract

### PowerShell Command Safety (P0)

TEST SKILL 3 laeuft im Windows-/PowerShell-Kontext niemals mit Unix-`curl`-Kurzformen.

Verboten waehrend des gesamten Skill-3-Laufs:

```powershell
curl -s <url>
curl --silent <url>
curl <url>
Invoke-WebRequest <url>
Invoke-RestMethod <url>
```

Grund: In PowerShell ist `curl` oft ein Alias fuer `Invoke-WebRequest`. `curl -s <url>` kann
dadurch in eine interaktive `Uri:`-Abfrage laufen und den Skill blockieren.

Erlaubt sind nur nicht-interaktive Formen mit vollstaendigen Parametern:

```powershell
curl.exe -s http://localhost:8001/api/health
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/health" -TimeoutSec 5
```

```powershell
Invoke-WebRequest -Uri "http://localhost:8001/api/health" -UseBasicParsing -TimeoutSec 5
```

Wenn im Terminal `Uri:` erscheint, MUSS Skill 3 sofort abbrechen/unterbrechen (`Ctrl+C`) und den
Lauf mit dem deterministischen Preflight-Script neu starten. Ein Skill-3-Output nach interaktiver
`Uri:`-Abfrage ist ungueltig, bis der haengende Befehl beendet wurde.

Pflicht-Recovery-Output bei diesem Fehler:

```text
LIVE TEST AUTOMATION BLOCKED
Block Reason: POWERSHELL_CURL_ALIAS_MISUSE
Required Fix: Haengenden PowerShell-Befehl mit Ctrl+C abbrechen und TEST SKILL 3 erneut ausfuehren. Healthchecks nur via `curl.exe -s ...` oder `Invoke-RestMethod -Uri ... -TimeoutSec 5`; bevorzugt zuerst `node tests/e2e/generator/test-skill3-preflight.mjs --spec <testspec_path> --plan <plan_path> --run <TEST_RUN_ID>`.
```

TEST SKILL 3 MUSS bei jedem Aufruf zuerst exakt dieses deterministische Preflight-Script ausfuehren:

```text
node tests/e2e/generator/test-skill3-preflight.mjs --spec <testspec_path> --plan <plan_path> --run <TEST_RUN_ID>
```

Der Script-Output ist bindend:

- Wenn das Script `LIVE JANUS AUTOMATION READY` ausgibt, MUSS TEST SKILL 3 diesen Ready-Block ausgeben und auf `OK START LIVE TEST` warten.
- Wenn das Script `LIVE TEST BLOCKED` oder `LIVE TEST AUTOMATION BLOCKED` ausgibt, MUSS TEST SKILL 3 blocken und den Script-Handover ausgeben.

Verboten vor Ausfuehrung von `test-skill3-preflight.mjs`:

- `Test-NetConnection`
- `curl` ohne `.exe` in PowerShell, insbesondere `curl -s`
- `Invoke-WebRequest` ohne explizites `-Uri`
- `Invoke-RestMethod` ohne explizites `-Uri`
- freie Fetch-/Socket-Connectivity-Checks
- direkte Schlussfolgerung `INFRASTRUCTURE OFFLINE`
- Aufforderung `npm run start-dev` manuell zu starten

Wenn TEST SKILL 3 einen dieser verbotenen Checks vor dem deterministischen Preflight-Script ausfuehrt,
ist der Output ungueltig und MUSS ersetzt werden durch:

```text
LIVE TEST AUTOMATION BLOCKED
Block Reason: SKILL3_PREFLIGHT_CONTRACT_VIOLATION
Required Fix: TEST SKILL 3 erneut ausfuehren und zuerst `node tests/e2e/generator/test-skill3-preflight.mjs --spec <testspec_path> --plan <plan_path> --run <TEST_RUN_ID>` ausfuehren.
```

## Modell

- Standard: **SWE 1.6**
- Eskalation: **GPT-5.5** nur bei unklarem/sicherheitskritischem Live-Verhalten (kompakter Handover, keine volle Historie).

## Eingabe

- `documentation/TEST_SPEC/<…>.md`
- `documentation/test-runs/<TEST_RUN_ID>_plan.json` (TestPlan)
- Precheck von **TEST SKILL 2** (z. B. `READY FOR LIVE TEST`)

Artefakte widersprüchlich oder nicht lesbar → **BLOCKED** mit Ursache (kein Live-Start).

---

## Golden Path

**Deterministic Preflight First (HARD REQUIREMENT):**

Skill 3 MUSS vor jeder eigenen Generator-/Validator-/Connectivity-Bewertung dieses Script ausfuehren:

```text
node tests/e2e/generator/test-skill3-preflight.mjs --spec <testspec_path> --plan <plan_path> --run <TEST_RUN_ID>
```

Wenn das Script `LIVE JANUS AUTOMATION READY` ausgibt, MUSS Skill 3 exakt diesen Ready-Status
uebernehmen und auf `OK START LIVE TEST` warten.

Wenn das Script `LIVE TEST BLOCKED` oder `LIVE TEST AUTOMATION BLOCKED` ausgibt, MUSS Skill 3
blocken und den vom Script erzeugten Handover ausgeben.

Freie Generator-/Validator-/Connectivity-Interpretation ist nur erlaubt, wenn das Script technisch
fehlt oder nicht gestartet werden kann.

1. Artefakte laden (TestSpec + TestPlan + Precheck).
2. **Preflight:** Generator → Validator → **Connectivity-Guard** (ohne User-Fragen).
3. Bei Preflight-PASS: **User Gate** — genau ein Ready-Block, Warten auf `OK START LIVE TEST`.
4. Playwright-Live-Run (`--headed --workers=1 --reporter=list` Standard, sofern User nicht explizit anderes verlangt).
5. Evidence aggregieren, `documentation/test-results/<test_run_id>_results.md` und maschinenlesbar `documentation/test-results/<test_run_id>_results.json` schreiben.
6. **P2-Handoff** an TEST SKILL 4 (oder BLOCKED-Template mit Re-Test-Handoff).

### Infrastructure/Auth Blocker Gate (HARD)

TEST SKILL 3 darf Infrastruktur-, Auth- oder Test-Harness-Blocker nicht als fachliche Test-Fails an TEST SKILL 4 routen.

Wenn waehrend Preflight oder Playwright-Lauf eines der folgenden Muster auftritt, ist das Ergebnis `LIVE TEST AUTOMATION BLOCKED` und nicht `FINDING TRIAGE`:

- `INFRASTRUCTURE_OFFLINE`
- `ERR_CONNECTION_REFUSED` gegen `baseUrl` oder `backendHealthUrl`
- Frontend/Backend nicht erreichbar, bevor eine fachliche Assistant-Antwort entstanden ist
- Playwright `webServer` startet nicht oder erreicht die Health URL nicht innerhalb des Timeouts
- `JWT-Token nicht im localStorage gefunden`
- `localStorage` enthaelt keinen erwarteten E2E-/Janus-Token
- `JANUS_CONFIG_OR_AUTH_MISSING`
- Backend Health URL nicht erreichbar, obwohl webServer-Start fehlgeschlagen ist
- Frontend nicht erreichbar, obwohl webServer-Start fehlgeschlagen ist
- `page.waitForFunction: Timeout` vor erster authentifizierter Chat-Interaktion
- Alle oder fast alle Tests scheitern vor fachlicher Assistant-Antwort wegen Auth/Setup/Healthcheck/Runner-Setup

In diesem Fall MUSS Skill 3:

- Kein `BEGIN COPY FOR TEST SKILL 4` ausgeben.
- Keinen `@[/TEST SKILL 4 – FINDING TRIAGE AND ROUTING]` Single-Line-Handover ausgeben.
- Keine fachliche PassRate/FailRate als Produktqualitaet interpretieren.
- Keine `Total Tests: <n>`, `Passed: 0`, `Failed: <n>`, `Pass Rate: 0%` Summary fuer Infrastruktur-/Auth-Blocker ausgeben.
- Keine 21 Auth-/Setup-Fails als TestFindings triagieren.
- Einen Single-Line-Retest-Handover zu TEST SKILL 3 ausgeben.
- `TestResult=N/A` verwenden, wenn kein valides fachliches TestResult entstanden ist.
- `PreviousStatus=LIVE_TEST_BLOCKED_AUTH_OR_INFRASTRUCTURE` oder konkreter `LIVE_TEST_BLOCKED_JANUS_CONFIG_OR_AUTH_MISSING` verwenden.
- `RequiredAction=RECHECK_WITH_PLAYWRIGHT_WEBSERVER_AUTOSTART_AND_E2E_AUTH_CONFIG` verwenden, wenn Playwright webServer die Server starten soll, aber Auth/Config fehlt.

Wenn der Aufruf bereits `Mode=LIVE_RETEST` und `PreviousStatus=LIVE_TEST_BLOCKED_JANUS_CONFIG_OR_AUTH_MISSING` enthaelt und derselbe JWT/localStorage/Auth-Blocker erneut auftritt, darf Skill 3 keinen weiteren Retest-Handover und keinen TEST-SKILL-4-Handover ausgeben. Dann ist die Ursache ein wiederholter E2E-Auth-/Harness-Blocker und muss zu Skill 5 geroutet werden.

Pflicht-Handover bei wiederholtem Auth-/JWT-Blocker:

```text
LIVE TEST AUTOMATION BLOCKED

Block Reason: REPEATED_E2E_AUTH_SETUP_BLOCKER

NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 - FEATURE DEBUG
Canonical State: BLOCKED
Required Artifacts: TestSpec, TestPlan, generated runner, Playwright output, auth/localStorage failure evidence
Evidence Paths: <runner path>, <test-results path or N/A>, <playwright output/log excerpt>
Failure Code: E2E_AUTH_TOKEN_MISSING
Changed Files: NONE
Decision: HANDOFF
Reason: Playwright webServer starts Frontend/Backend, but E2E auth setup does not seed a JWT/localStorage token; no valid fachliches TestResult exists.
Copy Prompt: @[/SKILL 5 - FEATURE DEBUG] Mode=E2E_INFRA_DEBUG; ExecutionModel=SWE_1_6; FailureCode=E2E_AUTH_TOKEN_MISSING; TestSpec=<testspec_path>; TestPlan=<plan_path>; TargetTestRun=<TEST_RUN_ID>; Context=PLAYWRIGHT_WEBSERVER_READY_BUT_JWT_LOCALSTORAGE_MISSING; Rules=FIX_TEST_HARNESS_OR_E2E_AUTH_ONLY_NO_PRODUCT_ORACLE_CHANGES; ExpectedOutput=FIXED_OR_BLOCKED_WITH_RETEST_HANDOFF
```

Pflicht-Handover bei Auth-/JWT-Blocker:

```text
node tests/e2e/generator/create-test-skill3-retest-handover.mjs --spec <testspec_path> --plan <plan_path> --run <TEST_RUN_ID> --reason LIVE_TEST_BLOCKED_JANUS_CONFIG_OR_AUTH_MISSING --action RECHECK_WITH_PLAYWRIGHT_WEBSERVER_AUTOSTART_AND_E2E_AUTH_CONFIG
```

Verboten bei Auth-/JWT-/Healthcheck-Blocker:

```text
BEGIN COPY FOR TEST SKILL 4
@[/TEST SKILL 4 – FINDING TRIAGE AND ROUTING]
Action=REQUIRED_START_DEV_SERVERS
Status: BLOCKED
Status: BLOCKED (INFRASTRUCTURE_OFFLINE)
Status: BLOCKED (Janus-App nicht erreichbar)
Total Tests: 18
Passed: 1
Failed: 21
Passed: 0
Failed: 22
Pass Rate: 0%
Baseline Pass Rate:
Delta:
All 18 test cases were blocked
TestResult: BLOCKED (21/21 fehlgeschlagen wegen Infrastructure-Problem)
TestResult: BLOCKED (22/22 fehlgeschlagen wegen Runtime-Auth-Problem)
ExpectedOutput: FINDING_TRIAGE_ROUTING_RESULT
```

Pflicht-Handover bei Infrastruktur-/WebServer-Blocker ohne fachliches TestResult:

```text
LIVE TEST AUTOMATION BLOCKED

Block Reason: INFRASTRUCTURE_OR_WEBSERVER_START_FAILED

NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 - FEATURE DEBUG
Canonical State: BLOCKED
Required Artifacts: TestSpec, TestPlan, generated runner, Playwright webServer output, backend/frontend startup logs
Evidence Paths: <runner path>, <playwright output/log excerpt>, <backend/frontend startup logs or N/A>
Failure Code: INFRASTRUCTURE_OFFLINE
Changed Files: <changed files or NONE>
Decision: HANDOFF
Reason: Playwright webServer should own Frontend/Backend startup, but the runner cannot reach baseUrl/backendHealthUrl; no valid fachliches TestResult exists.
Copy Prompt: @[/SKILL 5 - FEATURE DEBUG] Mode=E2E_INFRA_DEBUG; ExecutionModel=SWE_1_6; FailureCode=INFRASTRUCTURE_OFFLINE; TestSpec=<testspec_path>; TestPlan=<plan_path>; TargetTestRun=<TEST_RUN_ID>; Context=PLAYWRIGHT_WEBSERVER_FAILED_TO_START_OR_CONNECT; ChangedFiles=<changed files or NONE>; Rules=FIX_TEST_HARNESS_OR_WEBSERVER_STARTUP_ONLY_NO_PRODUCT_ORACLE_CHANGES_NO_FINDING_TRIAGE; ExpectedOutput=FIXED_OR_BLOCKED_WITH_RETEST_HANDOFF
```

---

## Preflight

### Generator (Phase 3A)

```text
node tests/e2e/generator/generate-live-runner.mjs --plan <plan_path> --out <spec_path>
```

Beispiel:

```text
node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/<TEST_RUN_ID>_plan.json --out tests/e2e/generated/<TEST_RUN_ID>.live.spec.js
```

### Validator (Phase 3B)

```text
node tests/e2e/generator/validate-runner.mjs --plan <plan_path> --runner <spec_path>
```

### Referenzen (SSOT)

- `tests/e2e/generator/test-plan.schema.json`
- `tests/e2e/generator/strategy-registry.json`
- Generiertes Artefakt: `tests/e2e/generated/<TEST_RUN_ID>.live.spec.js` (nicht manuell patchen — Plan/Registry/Generator fixen und neu erzeugen).

### Connectivity-Guard (Phase 3C, vor User-Gate)

PowerShell-Kompatibilitaet (HARD):

- Unter PowerShell ist `curl` oft ein Alias fuer `Invoke-WebRequest`; deshalb ist `curl -s <url>` verboten, weil es in eine interaktive `Uri:`-Abfrage laufen kann.
- Wenn ein Befehl interaktiv nach `Uri:` fragt, ist der Befehl sofort als `POWERSHELL_CURL_ALIAS_MISUSE` zu werten und durch eine der erlaubten Formen zu ersetzen.
- Erlaubte Healthcheck-Formen unter PowerShell:

```powershell
curl.exe -s http://localhost:8001/api/health
```

```powershell
Invoke-WebRequest -Uri "http://localhost:8001/api/health" -UseBasicParsing -TimeoutSec 5
```

```powershell
try { (Invoke-WebRequest -Uri "http://localhost:8001/api/health" -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 } catch { $false }
```

- `baseUrl` und optional `backendHealthUrl` **aus dem TestPlan** lesen; **eine** kurze, nicht-interaktive Erreichbarkeitsprüfung mit Timeout. Unter PowerShell nur `curl.exe -s`, `Invoke-RestMethod -Uri ... -TimeoutSec 5` oder `Invoke-WebRequest -Uri ... -UseBasicParsing -TimeoutSec 5` verwenden.
- Bei Refused/Timeout: **kein** `OK START LIVE TEST`; stattdessen:

```text
LIVE TEST BLOCKED — INFRASTRUCTURE OFFLINE
Blocker: Keine Verbindung zu <baseUrl> (aus TestPlan).
Vorgeschlagen: vom Repo-Root `npm run start-dev` (oder laut Projekt-Doku).
Connectivity-Guard fehlgeschlagen — kein OK START LIVE TEST.
```

Danach MUSS TEST SKILL 3 immer einen direkt kopierbaren Single-Line-Retest-Handover fuer denselben Skill ausgeben.
Der Handover MUSS deterministisch durch dieses Script erzeugt werden:

```text
node tests/e2e/generator/create-test-skill3-retest-handover.mjs --spec <testspec_path> --plan <plan_path> --run <TEST_RUN_ID> --reason LIVE_TEST_BLOCKED_INFRASTRUCTURE_OFFLINE --action START_JANUS_DEV_SERVER_WITH_NPM_RUN_START_DEV
```

Der Output ist eine einzelne Zeile und MUSS unveraendert ausgegeben werden, z. B.:

```text
@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION] Mode=LIVE_RETEST; ExecutionModel=SWE_1_6; TestSpec=<path>; TestPlan=<path>; TestResult=N/A; TargetTestRun=<TEST-RUN-ID>; PreviousStatus=LIVE_TEST_BLOCKED_INFRASTRUCTURE_OFFLINE; RequiredAction=START_JANUS_DEV_SERVER_WITH_NPM_RUN_START_DEV; Rules=USE_SAME_ARTIFACTS_VALIDATE_PREFLIGHT_NO_IMPLEMENTATION; ExpectedOutput=OK_START_LIVE_TEST_OR_LIVE_TEST_BLOCKED
```

- Keine Port-Ratespiele: nur URLs aus Plan/Spec; Default-Erwartung nur Hinweis, nicht override ohne Artefakt.
- Der `START_JANUS_DEV_SERVER_WITH_NPM_RUN_START_DEV`-Retest-Handover ist nur erlaubt, wenn `playwright.config.js` keinen passenden `webServer` fuer die Plan-URLs enthaelt. Wenn `webServer` vorhanden ist, gehoert Startup-/Timeout-Failure zu `SKILL 5 - FEATURE DEBUG`, nicht zum User und nicht zu TEST SKILL 4.

### Playwright WebServer Ownership Rule (Pflicht)

Vor einem `LIVE TEST BLOCKED — INFRASTRUCTURE OFFLINE` MUSS Skill 3 `playwright.config.js` pruefen.

Wenn `playwright.config.js` eine `webServer`-Konfiguration fuer die Plan-URLs enthaelt
(hier typisch Backend `http://localhost:8001/api/health` und Frontend `http://localhost:5173`),
ist ein aktuell offline wirkender Port **kein Blocker**. Dann ist der Status:

```text
Connectivity-Guard: PLAYWRIGHT_WEBSERVER_AUTOSTART_READY
Reason: Frontend/Backend sind offline, aber Playwright webServer startet sie beim Runner-Lauf selbst.
```

In diesem Fall MUSS Skill 3 zum User Gate weitergehen und darf NICHT
`LIVE TEST BLOCKED — INFRASTRUCTURE OFFLINE` ausgeben.

Der User muss Janus nicht manuell oeffnen. Playwright startet Server und Browser automatisch
beim Runner-Lauf.

Wenn Playwright `webServer` vorhanden ist, ist `npm run start-dev` als manuelle User-Aktion kein gueltiger
naechster Schritt. Bei Startup-/Timeout-Fehlern muss Skill 3 zu `SKILL 5 - FEATURE DEBUG` mit
`FailureCode=INFRASTRUCTURE_OFFLINE` routen, nicht zu TEST SKILL 4 und nicht zur manuellen Server-Start-Aufforderung.

### Preflight-FAIL (ohne User-Gate)

- Generator/Validator-Fehler → `LIVE TEST AUTOMATION BLOCKED` mit `Block Reason: GENERATOR_NOT_READY | GENERATOR_VALIDATION_FAILED | TESTPLAN_STRATEGY_INVALID` und exaktem Tool-Output.
- Veraltete Modelle im Plan (falls eure Policy das blockt) → `LIVE TEST BLOCKED: Provider-/Model-Matrix …` wie im TestPlan definiert.
- Fehlende lokale E2E-Auth/Config → `JANUS_CONFIG_OR_AUTH_MISSING` mit konkreter nächster Aktion (ohne Secrets im Chat).

**Failure-Codes nach dem Lauf:** Taxonomie wie im Generator (`generate-live-runner.mjs`); bei Übergabe an TEST SKILL 4 **unverändert** durchreichen.

---

## User Gate (OK START LIVE TEST)

Nur wenn Generator **SUCCESS**, Validator **PASSED**, Connectivity-Guard **PASS**.

Auch gueltig ist:

```text
Connectivity-Guard: PLAYWRIGHT_WEBSERVER_AUTOSTART_READY
```

Dann gehoert in den Ready-Block:

```text
Connectivity-Guard: PLAYWRIGHT_WEBSERVER_AUTOSTART_READY
Server Lifecycle: Playwright webServer starts backend/frontend automatically
Manual Janus Start Required: NEIN
```

**Genau ein** Ready-Block; letzte Zeile muss lauten: `Antworte mit: OK START LIVE TEST`. Keine Zwischenfragen zu Janus-Läuft-schon, Visual-Mode, Watch-Target etc. (Guard hat entschieden).

```text
LIVE JANUS AUTOMATION READY

TestRun: <TEST-RUN-ID>
Generator: SUCCESS | Validator: PASSED
Connectivity-Guard: PASS

Scope:
| TestCase-ID | Type | Provider/Model | Status |
|-------------|------|----------------|--------|
| … | … | … | AUTOMATED | … |

Alle <N> Tests validiert. Bereit für LIVE_VISUAL Dauerlauf.

Antworte mit: OK START LIVE TEST
```

**Nach** `OK START LIVE TEST`: Runner starten, Evidence sammeln, TestResult schreiben — keine weiteren Gate-Stopps außer explizit im TestPlan markierte `MANUAL_GATE_REQUIRED`-Schritte.

Skill 3 DARF den User nicht auffordern, Janus manuell zu oeffnen oder `npm run start-dev`
manuell auszufuehren, wenn `playwright.config.js` passende `webServer`-Eintraege besitzt.
In diesem Fall startet der Playwright-Runner Backend und Frontend selbst.

**Runner (Standard):**

```text
npx playwright test tests/e2e/generated/<TEST_RUN_ID>.live.spec.js --headed --workers=1 --reporter=list
```

Der Live-Run darf keinen blockierenden HTML-Report-Server offen halten. Wenn Playwright `Serving HTML report at http://localhost:9323. Press Ctrl+C to quit.` ausgibt, ist das kein laufender Test, sondern der HTML-Reporter; Prozess beenden, Ergebnis auswerten und den nächsten Lauf mit `--reporter=list` starten.

---

## Blockers (Anti-Patterns, kompakt)

- Keine freie Playwright-Spec aus Chat; kein Patch an `tests/e2e/generated/*.live.spec.js`.
- Keine **zusätzlichen** Health-/Port-Loops nach bestandenem Guard (kein Raten von 8000 vs. 8001 — Plan-URLs nutzen).
- Kein Live-Start ohne `OK START LIVE TEST`.
- Kein „manuell testen statt Playwright“ ohne dokumentierten Automations-Blocker (Contract).
- Keine Umetikettierung von Generator-**Failure Codes** gegenüber TEST SKILL 4.
- Keine Produkt-Source-Änderungen außer ausdrücklich separatem Auftrag.
- Evidence: kein Backend/SSE-Root-Cause-Label ohne passende Request-/Console-Evidence (siehe ehemalige Evidence-Gate-Logik — knapp: **nicht raten**).

---

## Output

- Artefakte unter `documentation/test-results/<test_run_id>/`, Reports/Traces/Logs wie bisher üblich; zusammenfassend **`documentation/test-results/<test_run_id>_results.md`** und maschinenlesbar **`documentation/test-results/<test_run_id>_results.json`** nach `tests/e2e/generator/test-result.schema.json`.
- User-facing Text **Deutsch**; Pfade/IDs technisch unverändert.

Wenn der Runner nur `documentation/test-results/<test_run_id>_results.json` erzeugt und
`documentation/test-results/<test_run_id>_results.md` fehlt, MUSS Skill 3 vor dem Handover
diesen deterministischen Fallback ausfuehren:

```text
node tests/e2e/generator/create-test-result-md.mjs --result-json documentation/test-results/<TEST_RUN_ID>_results.json --out documentation/test-results/<TEST_RUN_ID>_results.md
```

Ein Skill-4-Handover ohne vorhandenes `TestResult`-MD ist ungueltig.

---

## Handoff (P2) → TEST SKILL 4

Nach erfolgreichem Lauf oder kontrolliertem fachlichem PARTIAL/BLOCKED mit TestResult.
Infrastruktur-, Auth-, webServer-, Healthcheck-, localStorage- und Runner-Setup-Blocker sind davon ausgeschlossen
und duerfen niemals zu TEST SKILL 4 geroutet werden.

Der Copy-Handover zu TEST SKILL 4 MUSS als robuste Single-Line-Handover-Zeile erzeugt werden.
Der Handover MUSS deterministisch durch dieses Script erzeugt werden:

```text
node tests/e2e/generator/create-test-skill4-handover.mjs --spec <testspec_path> --plan <plan_path> --run <TEST_RUN_ID> --result documentation/test-results/<TEST_RUN_ID>_results.md --result-json documentation/test-results/<TEST_RUN_ID>_results.json --failure-code <FailureCodeOrNONE>
```

Wenn das Script `HANDOVER INVALID` ausgibt, darf TEST SKILL 3 keinen Skill-4-Handover ausgeben;
stattdessen muss der fehlende Ergebnis-Artefaktpfad konkret als Blocker genannt werden.

Failure-Code-Regel (HARD):

- Wenn `ResultStatus=PASS`, `Failed=0`, `Blocked=0` und `ManualGate=0`, MUSS der Skill-4-Handover `FailureCode=NONE` enthalten.
- `FailureCode=N/A`, `FailureCode=N_A`, leere FailureCodes oder Prosawerte sind bei PASS verboten.
- Bei FAIL/PARTIAL/BLOCKED muss der exakte Runner-/Generator-Code erhalten bleiben, z. B. `ASSERTION_MISMATCH`, `TOOL_ROUTING_FAILURE`, `E2E_AUTH_TOKEN_MISSING`.
- Wenn nur ein fehlender Code bekannt ist und das Ergebnis nicht PASS ist, verwende `FailureCode=N_A`, aber niemals bei PASS.
- Wenn ein einzelner FocusTestCase PASS ist, darf seine Evidence-Klassifikation nicht `ASSERTION_MISMATCH` lauten. PASS-Evidence muss eine PASS-Klassifikation wie `ASSERTION_PASS`, `TOOL_ROUTING_PASS`, `RESPONSE_TIME_PASS`, `CONFIRMATION_PASS` oder `RESPONSE_PRESENT_PASS` verwenden.
- Evidence-Pfade muessen den vollstaendigen `TargetTestRun` enthalten. Verkuerzte Pfade wie `TEST-RUN-2026-05-011` statt `TEST-RUN-2026-05-15-011` sind ungueltig.
- Ein Focus-Retest darf keinen Minimal-Handover mit `TestRun=...; TestCase=...; Result=PASS` ausgeben, wenn TestSpec/TestPlan/TestResult/TestResultJson vorhanden sind. Dann muss der Standard-Skill4-Handover mit Artefaktpfaden ausgegeben werden.

Verboten:

```text
Classification: ASSERTION_MISMATCH (default, but actual result is PASS)
EvidencePath=documentation/test-results/TEST-RUN-2026-05-011/...
@[/TEST SKILL 4 – FINDING TRIAGE AND ROUTING] TestRun=<id>; TestCase=<case>; Result=PASS
```

Gueltige finale Single-Line-Form:

```text
@[/TEST SKILL 4 – FINDING TRIAGE AND ROUTING] Mode=FINDING_TRIAGE; ExecutionModel=SWE_1_6; TestSpec=<path>; TestPlan=<path>; TestResult=<results.md>; TestResultJson=<results.json>; TargetTestRun=<TEST-RUN-ID>; ResultStatus=<PASS|FAIL|PARTIAL|BLOCKED>; TotalTests=<n>; Passed=<n>; Failed=<n>; Blocked=<n>; ManualGate=<n>; PassRatePct=<0.00>; FailRatePct=<0.00>; BlockedRatePct=<0.00>; ProviderPassRatePct=<Provider:0.00,...>; TypePassRatePct=<type:0.00,...>; FailureCode=<code>; ChangedFiles=NONE; Rules=USE_RESULT_ARTIFACTS_ONLY_PRESERVE_FAILURE_CODES_NO_IMPLEMENTATION; ExpectedOutput=FINDINGS_TRIAGED_OR_NO_FINDINGS
```

Vergleichsmetriken sind Pflicht. `PassRatePct`, `FailRatePct`, `BlockedRatePct`,
`ProviderPassRatePct` und `TypePassRatePct` muessen aus TestResult-JSON und TestPlan
berechnet werden; keine gerundeten Prosawerte und keine Schaetzung aus Markdown.

### Human-Readable Metrics Summary (PFLICHT)

Vor dem finalen Single-Line-Handover MUSS Skill 3 immer eine kurze deutschsprachige Prozent-Summary ausgeben. Diese Summary ist fuer Menschen, der Single-Line-Handover bleibt fuer Maschinen.

Pflichtformat:

```text
Metrik-Summary:
- Overall Green: <PassRatePct>%
- Overall Red: <FailRatePct>%
- Blocked: <BlockedRatePct>%
- Provider Green: <ProviderPassRatePct als lesbare Liste>
- Type Green: <TypePassRatePct als lesbare Liste>
```

Wenn die lokalen Generator-Skripte verfuegbar sind, MUSS Skill 3 die Summary deterministisch erzeugen:

```text
node tests/e2e/generator/create-test-metrics-summary.mjs --plan <plan_path> --result-json documentation/test-results/<TEST_RUN_ID>_results.json
```

Beispiel:

```text
Metrik-Summary:
- Overall Green: 66.67%
- Overall Red: 33.33%
- Blocked: 0.00%
- Provider Green: Gemini 77.78%, GPT 55.56%
- Type Green: functional 66.67%, intent_routing 100.00%, prompt_injection 100.00%, security 33.33%
```

Regeln:

- Die Werte muessen identisch zu den Feldern im Single-Line-Handover sein.
- `PassRatePct` darf nicht nur im Handover versteckt sein.
- Bei PASS muss `Overall Green: 100.00%` sichtbar sein.
- Bei FAIL muss die Fail-Rate sichtbar sein.
- Diese Summary ersetzt nicht den Single-Line-Handover.

Verboten ist ein mehrzeiliger oder abgeschnittener `Copy Prompt` fuer TEST SKILL 4, z. B. mit
`Failure Codes:`-Listen, die am Ende abgeschnitten werden koennen. Wenn Ergebnisartefakte existieren,
MUSS Skill 3 stattdessen den Single-Line-Handover aus `create-test-skill4-handover.mjs` ausgeben.

```text
NEXT_SKILL_HANDOFF
Target Skill: TEST SKILL 4 – FINDING TRIAGE AND ROUTING
Canonical State: HANDOFF
Required Artifacts: TestSpec, TestPlan, TestResult-MD, TestResult-JSON, ggf. Playwright-Report/Traces
Evidence Paths: documentation/test-results/<test_run_id>_results.md, documentation/test-results/<test_run_id>_results.json, documentation/test-results/<test_run_id>/, playwright-report/test-results falls vorhanden
Failure Code: <exakter Runner-Code oder N/A>
Changed Files: NONE
Decision: HANDOFF | FAILED (mit Grund)
Reason: <kurz>
Copy Prompt:

@[/TEST SKILL 4 – FINDING TRIAGE AND ROUTING]
Mode: FINDING_TRIAGE
Execution Model: SWE 1.6
TestSpec: <path>
TestPlan: <path>
TestResult: documentation/test-results/<test_run_id>_results.md
TestResultJson: documentation/test-results/<test_run_id>_results.json
Target TestRun: <TEST-RUN-ID>
… (Failure Codes 1:1 aus Runner, keine Umbenennung)
```

**Re-Test nach BLOCKED (gleicher Skill):**

```text
NEXT_SKILL_HANDOFF
Target Skill: TEST SKILL 3 – LIVE JANUS TEST EXECUTION
Canonical State: HANDOFF
Required Artifacts: korrigierter TestPlan / Registry / Umgebung
Evidence Paths: <Generator-/Validator-/Connectivity-Output oder N/A WITH REASON>
Failure Code: <Block Reason oder exakter Failure Code>
Changed Files: NONE
Decision: HANDOFF
Reason: LIVE TEST AUTOMATION BLOCKED — <Block Reason>
Copy Prompt: @[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION] Mode: LIVE_RETEST …
```

---

## GPT-5.5 Eskalation

Bei harter Unklarheit / Security-Review-Bedarf: **STOP**, kompakter `MODEL SWITCH REQUIRED`-Block + P2 mit `Execution Model: GPT-5.5` und **nur** gebundenen Artefakten/Evidence-Auszug — keine volle Chat-Historie.
