---
description: Janus V3 — Skill 5 Feature Debug. Iterativer Fix mit Evidence; eine Verifikationskette (Mini-Playwright + optionale Sichtprüfung + Final Suite); max. 5 Iterationen; Stagnations-Stopp; Handoffs Skill 6 / Skill 7 / GPT-5.5.
---

This skill follows the global rules in `documentation/pipeline/PIPELINE_CONTRACT.md`.

## Rolle

Iteratives Debug nach Abweichung (Skill 4 `TASK EXECUTION FAILED` / `FIX LOOP LIMIT REACHED`, Skill 6 `BLOCKED` / `PASS WITH FIXES`, Playwright-/Audit-Evidence, reproduzierbarer User-Ist/Soll-Konflikt). **Keine** neuen Features, **kein** Scope über gebundene Task/Spec hinaus (Details: Contract).

## Modell

- Standard: **SWE 1.6**
- **GPT-5.5:** wenn Root Cause nicht deterministisch, mehrere gleich plausible Ursachen, **nach Iteration 5** ohne §-Exit, oder bei **Stagnations-Stopp** (unten).

## Debug-Paket (pro Iteration)

Kompakt: Feature, Task(+Pfad), Spec, Pre-Check, Skill-6-/Audit-Kontext, Ist/Soll (Playwright-Evidence bevorzugt), Logs (Backend; Frontend nur **nach** erschöpfter Auto-Verification, kompakt), geänderte Dateien, Testergebnisse, Known Risks.

Bei fehlenden Pflichtteilen: **BLOCKED** `DEBUG PACKAGE INCOMPLETE` — keine Fixes ohne reproduzierbaren Konflikt.

---

## Iterations- und Stagnations-Regeln (hart)

- **Höchstens 5** SWE-1.6-Iterationen **pro gleicher Fehlerkette** (gleiches Feature, gleicher Task/Konflikt).
- **Progress-Validierung** ab Iteration 2: Failure-Code (Taxonomie aus `generate-live-runner.mjs` oder `N/A`) **und** Fehlerbild/Evidence vs. Iteration **N−1** dokumentieren (`JA`/`NEIN` geändert).
- **Stagnations-Guard (P0/P1):** Vor Start der **5.** Iteration **abbrechen** und **`SKILL 5 ESCALATION REQUIRED`**, wenn es **3 unveränderte Übergänge** bzw. **4 gleiche Failure-Snapshots in Folge** gibt: Failure-Code und Evidence/Fehlerbild haben sich gegenüber der jeweils vorherigen Iteration nicht geändert. Reason: `STAGNATION_NO_PROGRESS_ON_FAILURE_CODE_OR_EVIDENCE` (analog Contract: kein blindes Weiterdrehen ohne Evidence-Fortschritt).
- Nach **Iteration 5** ohne erreichbare technische Freigabe (unten): ebenfalls **`SKILL 5 ESCALATION REQUIRED`** + temporäre Datei + GPT-5.5-Handover.
- Jede Iteration braucht **neue oder aktualisierte** Evidence (kein reines Prosa-Repeat).

---

## Verifikation nach Fix (eine zusammenhängende Kette)

Nach jedem Code-Fix, der Chat/FE/BE/Tool/Stream berührt:

1. **Mini Auto-Verification** (wie Skill 4), sofern nicht zulässiges **N/A** (nur reine `.css`/`.md`/`.yml` ohne Logik — sonst **kein** N/A):
   - `documentation/test-runs/<id>_verify.json` (Schema `tests/e2e/generator/test-plan.schema.json`, Strategien nur `strategy-registry.json`)
   - `node tests/e2e/generator/generate-live-runner.mjs --plan … --out tests/e2e/generated/…_verify.live.spec.js`
   - `node tests/e2e/generator/validate-runner.mjs --plan … --runner …`
   - `npx playwright test … --headed --workers=1 --reporter=list`
   - Output: `Auto-Verification:` mit `- Status: PASS | FAIL | N/A`; bei **FAIL** → `FAILURE LOG (BINDEND)` mit exaktem **Failure Code** und Bucket (Tabelle = Quelle `generate-live-runner.mjs` — keine Umbenennung).
2. **Optionale Janus-Sichtprüfung** — nur ergänzend, **ersetzt** keine `PASS`-Evidence aus (1).
3. **Finale Feature-Suite** (gesamtes Feature-E2E laut Task/Spec/`package.json`) — **Pflicht vor `FIXED`**. Ohne definierbare Suite: `FINAL SUITE: N/A WITH REASON` → **kein** `FIXED`, kein Skill-6-Handover, bis geklärt/eskaliert.

### Generator-/Runner-Gate (P0/P1, kein Manual Bypass)

Vor jedem Playwright-Lauf MUSS Skill 5 einen **Artifact Identity Check** durchführen. Diese vier Werte müssen zusammenpassen:

```text
Plan Path:
Plan testRunId:
Runner Path:
Runner internal testRunId / describe title:
Executed Playwright Path:
Identity Result: PASS | FAIL
```

Wenn ein anderer Runner läuft als der gerade generierte Runner, ist der Test **ungültig**. Beispiel: Plan/Runner `BACKLOG-023...`, aber Playwright führt `TEST-RUN-2026-05-11-005...` aus. Ergebnis:

```text
Auto-Verification: FAIL
Failure Code: RUNNER_ARTIFACT_MISMATCH
Bucket: Generator/Runner Invocation
Canonical State: FAILED oder BLOCKED
```

Wenn `generate-live-runner.mjs` oder `validate-runner.mjs` scheitert, ist das ein **Generator-Layer-Debug**, kein Freibrief für handgeschriebene Runner. Skill 5 MUSS zuerst klassifizieren:

```text
GENERATOR_PLAN_INVALID        Plan verletzt Schema/Strategy-Registry.
GENERATOR_RUNNER_FAILED       Generator wirft Fehler oder erzeugt keinen Runner.
RUNNER_VALIDATION_FAILED      validate-runner lehnt den Runner ab.
RUNNER_ARTIFACT_MISMATCH      Plan, Runner und ausgeführter Playwright-Pfad passen nicht zusammen.
ASSERTION_ORACLE_TOO_NARROW   Janus-Verhalten ist korrekt, aber containsAny/mustNotContain ist zu eng.
STALE_RUNNER_EXECUTED         Ein alter Runner oder altes TestResult wurde statt des Ziel-Runners ausgeführt.
```

Regeln:

- **Kein handgeschriebener Playwright-Runner als Ersatz** für Generator/Validator/Runner-PASS.
- Ein temporärer manueller Playwright-Test ist nur als **Diagnose-Artefakt** erlaubt, wenn der Generator-Layer selbst das Debug-Ziel ist. Er darf **niemals** finale `PASS`-Evidence für `FIXED` ersetzen.
- Bei Generator-/Runner-Gate-FAIL muss Skill 5 zuerst Plan, Schema, Strategy, Runner-Identity, Invocation oder Assertion-Oracle fixen. Produktcode-Fixes sind verboten, solange unklar ist, ob überhaupt der richtige Test lief.
- Bei `ASSERTION_ORACLE_TOO_NARROW` ist der Fix der TestPlan/Oracle, nicht Janus-Produktcode.
- Bei `STALE_RUNNER_EXECUTED` oder `RUNNER_ARTIFACT_MISMATCH` muss der nächste Schritt der exakte Playwright-Befehl mit dem Ziel-Runner sein; keine Root-Cause-Behauptung über Janus-Verhalten.
- Wenn Playwright `Serving HTML report at http://localhost:9323. Press Ctrl+C to quit.` ausgibt, ist der Testlauf beendet und nur der HTML-Reporter blockiert. Nicht warten/loopen: Prozess beenden, Failures/Exit-Code auswerten und künftig `--reporter=list` bzw. Playwright `open: 'never'` verwenden.
- Wenn Skill 4 mit `TASK EXECUTION BLOCKED - E2E INFRA BLOCKER` oder einem Frontend-Fehler wie `win is not defined` übergibt, ist das Debug-Ziel zuerst die E2E-/Frontend-Blockade. Skill 5 darf diesen Blocker nicht durch manuelle Janus-Validierung ersetzen. Ergebnis muss entweder E2E-Blocker behoben + Original-Runner erneut ausgeführt oder sauberer Handoff mit Evidence sein.

**Manuelle Logs** (`frontend_log.md` / Ctrl+Shift+L): **nur** wenn (1) nicht anwendbar oder Evidence trotz Diagnostics nicht ausreicht — dann gezielt, kein Voll-Console-Dump.

---

## Ablauf (kurz)

1. **Repro / Scope** — Konflikt bestätigen; Out-of-Scope → `DEBUG OUT OF SCOPE` + Routing (Skill 1/2), nicht „heimlich“ erweitern.
2. **Root Cause** — eine primäre Hypothese; bei Auto-Verif-FAIL Code aus Taxonomie nennen; mehrdeutig → `MODEL SWITCH REQUIRED` / GPT-5.5.
3. **Minimaler Fixplan** — Dateien, Änderung, Tests + Verifikationskette; Risiko LOW/MEDIUM und eindeutig → **sofort implementieren** (kein Plan-only ohne `BLOCKED`/`ESCALATION REQUIRED`).
4. **Implementieren** — nur mit Tool-Nachweis; kein `FIXED` ohne echte Edits.
5. **Verifikationskette** (Abschnitt oben) + Progress-Validierung.
6. **`FIXED`** nur bei: Auto-Verification **`- Status: PASS`**, Final Suite **PASS** (oder begründetes N/A laut Regel), **und** im **selben** finalen Output P2-Handoff **Skill 6 Re-Audit** (siehe unten).

---

## Eskalation (Iteration 5 oder Stagnation)

- Datei: `.windsurf/tmp/skill5_escalation_<feature-or-task>_<YYYYMMDD-HHMM>.md` — kompakt, **keine** vollen Rohlogs; Verweis dass Skill 7 die Datei nach Doku-Gate löscht.
- User: Block `SKILL 5 ESCALATION REQUIRED` + `BEGIN COPY FOR NEW GPT-5.5 CHAT` mit Pfad zur tmp-Datei und `/SKILL 5 – FEATURE DEBUG` Modell GPT-5.5.

---

## Audit-Modell vor Re-Audit (kompakt)

- `Audit Risk: LOW | MEDIUM | HIGH | CRITICAL`
- **`Audit Model To Use`:** nur `SWE 1.6` oder `GPT-5.5` (Re-Audit: **kein** Kimi).
- **Pflicht GPT-5.5:** HIGH/CRITICAL, Security-relevant, Iteration **>3**, instabile Schnittstelle/mehrere Subsysteme ohne klare Isolation, oder Risiko nicht eindeutig niedrig/mittel.
- Sonst LOW/MEDIUM → `SWE 1.6`, sofern keine Pflichtregel greift.

---

## Handover (P2)

### TestRun-Finding Retest Handoff nach Debug-Fix (HARD)

Diese Regel gilt fuer jedes Debug-Paket mit `SourceTestRun`, `FailedTestCase`, `TestPlan`,
`TestResultJson`, `TargetTestRun`, `FailureCode`, `Mode=E2E_INFRA_DEBUG`, `Mode=PROVIDER_RUNTIME_DEBUG`
oder Retest-Kontext aus TEST SKILL 3/4. Skill 5 darf dann niemals mit einem losen Einzelkommando,
einer freien Retest-Anweisung oder einer Markdown-Retest-Box enden.

Ein `FIXED`- oder `NEEDS RETEST`-Output ist nur gueltig, wenn ein pipeline-kompatibler Retest-Handoff
enthalten ist. Der Retest muss ueber die Testpipeline laufen, damit ein neues oder aktualisiertes
TestResult-Artefakt entsteht.

Nach `Status: FIXED` oder `SKILL 5 DEBUG RESULT: FIXED` ist ein `NEXT_SKILL_HANDOFF` Pflicht.
Fehlt `NEXT_SKILL_HANDOFF`, ist der Output ungueltig und muss ersetzt werden durch
`SKILL 5 DEBUG RESULT: BLOCKED` mit `Reason: PIPELINE_RETEST_HANDOFF_INCOMPLETE`.

Zulaessige Retest-Ziele:

1. `TEST SKILL 3 – LIVE JANUS TEST EXECUTION`, wenn ein valider TestPlan bereits vorliegt.
2. `TEST SKILL 1 – TESTSPEC TO TEST PLAN`, wenn der TestPlan nach einer TestSpec-/Oracle-Aenderung neu erzeugt werden muss.
3. `SKILL 5 – FEATURE DEBUG`, wenn der Fix nur eine technische Debug-Iteration war und noch kein pipeline-faehiger Retest moeglich ist.

Bei Provider-/Runtime-Findings mit bestehendem TestPlan ist der bevorzugte Handoff:

```text
NEXT_SKILL_HANDOFF
Target Skill: TEST SKILL 3 – LIVE JANUS TEST EXECUTION
Canonical State: RETEST_REQUIRED
Required Artifacts: TestSpec, TestPlan, changed files, focused failed TestCase, baseline metrics
Evidence Paths: <original evidence>, <changed files>, <debug evidence>
Failure Code: <original failure code or N/A>
Changed Files: <files>
Decision: HANDOFF
Reason: Debug-Fix implementiert; Original-TestRun-Finding muss durch pipeline-kompatiblen Live-Retest validiert werden.
Copy Prompt: @[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION] Mode=LIVE_RETEST; ExecutionModel=SWE_1_6; TestSpec=<path>; TestPlan=<path>; TargetTestRun=<TEST-RUN-ID>; RetestReason=<BACKLOG-ID>_FIXED; ChangedFiles=<files>; FocusTestCase=<failed-testcase>; Rules=USE_EXISTING_TESTPLAN_EXECUTE_LIVE_RETEST_COLLECT_EVIDENCE_NO_IMPLEMENTATION_FULL_RUN_PREFERRED_PROVIDER_ISOLATION_NO_PROVIDER_FALLBACK; ExpectedOutput=TEST_RESULT_PLUS_SINGLE_LINE_HANDOFF_TO_TEST_SKILL_4_WITH_METRICS
```

Verboten als finaler Retest-Handoff fuer TestRun-Findings:

```text
BEGIN COPY FOR RETEST
END COPY FOR RETEST
PLAYWRIGHT WEBSERVER FIX RETEST HANDOVER
Retest Handover
Retest Required:
Command:
Command: cd tests/e2e; npx playwright test
pytest tests/e2e/calendar-mutation-intent.spec.js
pytest <single test file>
npx playwright test generated/
npx playwright test <handgeschriebener oder nicht validierter Runner>
Validation Command:
Retest Required:
Next Step: Retest TC-002-GEMINI
Next Step: Retest TEST-RUN
Run Playwright test for TEST-RUN
Bitte Backend-Logs bereitstellen
```

Ein einzelnes `pytest`-, `npx playwright`- oder Debug-Script-Kommando ist nur Diagnose-Evidence.
Es darf niemals das pipeline-kompatible RetestResult ersetzen und darf nicht der einzige
"Next Step" bleiben.

Wenn Skill 5 eines der verbotenen Muster ausgegeben haette, muss er den Output sofort selbst korrigieren
und stattdessen den `NEXT_SKILL_HANDOFF` zu TEST SKILL 3 oder TEST SKILL 1 ausgeben. Kein "spaeter
haerten", kein separater Hinweis ohne Patch.

Wenn Skill 5 wegen fehlendem TestPlan/TestSpec keinen gueltigen Retest-Handoff erzeugen kann, muss er blocken:

```text
SKILL 5 DEBUG RESULT: BLOCKED
Reason: PIPELINE_RETEST_HANDOFF_INCOMPLETE
Required Fix: TestSpec/TestPlan/TargetTestRun im Debug-Paket nachreichen oder zu TEST SKILL 1 routen.
```

### Partial-Progress / E2E-Infra Blocker Routing (HARD)

`PARTIAL PROGRESS` ist kein Abschlusszustand.

Wenn Skill 5 einen E2E-Infra-, Auth-, JWT-, localStorage-, API-Key-, Healthcheck- oder Runner-Harness-Blocker nur teilweise verbessert, aber der Original-TestRun weiterhin `BLOCKED`, `FAIL`, `PARTIAL` oder ohne valides fachliches TestResult bleibt, gelten diese Regeln:

- Kein Handover zu `TEST SKILL 4 – FINDING TRIAGE AND ROUTING`.
- Kein Handover zu `TEST SKILL 5 – DIAMOND RETEST AUDIT`.
- Kein Handover zu `SKILL 6 – DIAMANTSTANDARD FINAL AUDIT`.
- Keine Aussage, dass eine TestSpec-/Oracle-Aenderung ohne Live-Test als abgeschlossen betrachtet werden kann.
- Kein Backlog-Item auf `DONE` setzen.
- Keine fachlichen Pass-/Fail-Raten aus Auth-/Harness-Fails ableiten.

Verbotene Aussagen:

```text
kann die TestSpec-Änderung ohne Live-Tests als abgeschlossen betrachtet werden
kann die TestSpec-Aenderung ohne Live-Tests als abgeschlossen betrachtet werden
Live-Tests BLOCKED, aber Oracle-Update abgeschlossen
BEGIN COPY FOR TEST SKILL 4
TestResult: TESTSPEC_UPDATE_COMPLETE_LIVE_TESTS_BLOCKED
ExpectedOutput: FINDING_TRIAGE_ROUTING_RESULT
BEGIN COPY FOR RETEST
END COPY FOR RETEST
PLAYWRIGHT WEBSERVER BLOCKED HANDOVER
Required Action:
Either relax NO_MANUAL_SERVER_START
relax NO_MANUAL_SERVER_START
relax NO_PRODUCT_ORACLE_CHANGES
manual server startup
manual startup
constraints relaxation
constraint relaxation
infrastructure redesign
Next Step
BLOCKED - Requires constraint relaxation
```

Bei verbleibendem E2E-Auth-/JWT-/localStorage-/Healthcheck-/webServer-/Infrastructure-Blocker muss Skill 5 genau einen dieser Wege waehlen:

1. **Weiterer Skill-5-Debug**, wenn Iterationsbudget vorhanden ist und es Progress oder eine neue Hypothese gibt.
2. **GPT-5.5-Eskalation**, wenn die 5 SWE-1.6-Iterationen ausgeschoepft sind, Root Cause nicht deterministisch ist, mehrere Secrets/Keys/Backend-Auth-Pfade konkurrieren oder Stagnationsregeln greifen.
3. **Backlog-/Infra-Handoff**, wenn der Blocker ein neues separates, groesseres Infra-Thema ist, das nicht im aktuellen Debug-Scope geloest werden darf. Dieser Weg ist Pflicht, wenn Skill 5 zu dem Schluss kommt, dass die Loesung Backend-Startup-/Pfad-/Dependency-Anpassungen, neue Test-Infrastruktur oder Aenderungen ausserhalb des aktuellen Test-Harness-Scopes braucht.

Verboten bei BLOCKED:

- Den User um Constraint-Relaxation bitten.
- `NO_MANUAL_SERVER_START` oder `NO_PRODUCT_ORACLE_CHANGES` als Bitte an den User ausgeben.
- Einen Retest-Handover erzeugen, obwohl der Blocker weiterhin nicht testbar ist.
- `BEGIN COPY FOR RETEST` verwenden.
- Einen manuellen Serverstart als Alternative vorschlagen.

Stattdessen muss der Output entweder einen `NEXT_SKILL_HANDOFF` zu `SKILL 5 - FEATURE DEBUG` fuer die naechste Iteration, eine GPT-5.5-Eskalation oder einen Backlog-/Infra-Handoff enthalten.

Iterationspflicht fuer E2E-Infra-Debug:

- Iteration 1 bis 5 duerfen bei nachweisbarem Progress nicht zu TEST SKILL 4, TEST SKILL 5 Audit, SKILL 6 oder Backlog-Triage ausweichen.
- Bei Progress (`Evidence geaendert: JA`, z. B. Passed steigt 0 -> 1 -> 2) muss der naechste Handover wieder zu `SKILL 5 - FEATURE DEBUG` gehen, solange Iteration < 5.
- Eine Regression (`Passed` sinkt, z. B. 2 -> 0) ist ebenfalls Evidence-Aenderung, aber kein automatischer Eskalationsgrund vor Iteration 5. Bei Iteration < 5 muss Skill 5 den Regressionskontext im naechsten Skill-5-Handover weitergeben.
- Vor Start der 6. Debug-Runde oder nach 5 ausgeschoepften SWE-1.6-Iterationen muss ein GPT-5.5-Eskalationshandover erzeugt werden.
- Skill 5 darf BACKLOG-042 nicht als `BLOCKED`, `DONE` oder `COMPLETE` markieren, solange der Live-Retest durch E2E-Auth blockiert ist. BACKLOG-042 bleibt wartend auf valides TestResult.

Eskalation vor Iteration 5 ist nur erlaubt, wenn mindestens eine harte Bedingung erfuellt ist:

- `MODEL SWITCH REQUIRED` wegen nicht deterministisch entscheidbarem Root Cause mit mindestens zwei gleich plausiblen Ursachen, die nicht weiter isoliert werden koennen.
- Stagnations-Guard ist tatsaechlich ausgeloest: 3 unveraenderte Uebergaenge oder 4 gleiche Failure-Snapshots in Folge.
- Safety/Security-Risiko HIGH/CRITICAL im Debug selbst.

Verboten:

```text
SKILL 5 ESCALATION REQUIRED
Iteration: 3 of 5
Reason: E2E_AUTH_INFRASTRUCTURE_CANNOT_BE_FIXED_WITHIN_SKILL_5_ITERATIONS
Recommendation: Escalate to GPT-5.5
```

Wenn Iteration < 5 und keine harte Eskalationsbedingung greift, muss der Output stattdessen einen `SKILL 5 - FEATURE DEBUG` Handover fuer die naechste Iteration enthalten.

Verboten bei Iteration 1 bis 5 mit Progress:

```text
BEGIN COPY FOR TEST SKILL 4
TestResult: TESTSPEC_UPDATE_COMPLETE_LIVE_TESTS_BLOCKED_AUTH_ISSUE
BACKLOG-042 als BLOCKED markieren
separates Backlog-Item erstellen und BACKLOG-042 als BLOCKED markieren
```

Pflicht-Handover bei weiterem Skill-5-Debug:

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 – FEATURE DEBUG
Canonical State: HANDOFF
Required Artifacts: TestSpec, TestPlan, changed files, Playwright output, backend/auth evidence
Evidence Paths: <runner path>, <test-results path or N/A>, <backend logs or N/A>, <changed files>
Failure Code: E2E_AUTH_BACKEND_TOKEN_MISMATCH | E2E_AUTH_TOKEN_MISSING | <exakter Code>
Changed Files: <files>
Decision: HANDOFF
Reason: E2E-Auth/Harness ist verbessert, aber weiterhin nicht validiert; kein fachliches TestResult vorhanden.
Copy Prompt: @[/SKILL 5 - FEATURE DEBUG] Mode=E2E_INFRA_DEBUG_CONTINUE; ExecutionModel=SWE_1_6; FailureCode=<code>; TestSpec=<path>; TestPlan=<path>; TargetTestRun=<TEST-RUN-ID>; Context=<kompakter Stand>; ChangedFiles=<files>; Rules=CONTINUE_FIX_TEST_HARNESS_OR_E2E_AUTH_ONLY_NO_PRODUCT_ORACLE_CHANGES; ExpectedOutput=FIXED_OR_BLOCKED_WITH_RETEST_HANDOFF
```

Wenn Skill 5 den Blocker als separates Backlog-Thema routet, muss er zuerst `documentation/backlog/BACKLOG.md` aktualisieren und danach zu `BACKLOG SKILL 3 – EXECUTION HANDOFF` routen. Reine Prosa "separates Backlog-Item empfohlen" ist ungueltig.

Pflicht-Handover bei neuem separatem Infra-Backlog:

```text
NEXT_SKILL_HANDOFF
Target Skill: BACKLOG SKILL 3 – EXECUTION HANDOFF
Canonical State: HANDOFF
Required Artifacts: Backlog item, Source TestRun, TestSpec, TestPlan, failed runner evidence, changed files
Evidence Paths: <playwright output/log excerpt>, <runner path>, <changed files>
Failure Code: INFRASTRUCTURE_OFFLINE | BACKEND_HEALTH_FAIL | <exakter Code>
Changed Files: <files>
Decision: HANDOFF
Reason: E2E/webServer infrastructure cannot be solved inside current debug scope; routing metadata and handoff artefact are required.
Copy Prompt: @[/BACKLOG SKILL 3 – EXECUTION HANDOFF] Mode=DASHBOARD_PREP; ExecutionModel=SWE_1_6; SourceTestRun=<TEST_RUN_ID>; NewBacklogItem=<BACKLOG-ID>; Context=E2E_WEBSERVER_INFRA_BLOCKER; Rules=FILL_ROUTING_METADATA_CREATE_HANDOFF_SYNC_DASHBOARD_DO_NOT_MOVE_IN_PROGRESS; ExpectedOutput=BACKLOG_HANDOFF_READY_AND_DASHBOARD_SYNCED
```

### Skill-Nummer-Routing (HARD)

Skill 5 muss Skill-Nummern strikt korrekt verwenden:

```text
FEATURE DEBUG -> SKILL 5
DIAMANTSTANDARD FINAL AUDIT -> SKILL 6
DOKUMENTATIONSUPDATE -> SKILL 7
```

Bei `FIXED`, Auto-Verification PASS und Final Suite PASS ist der naechste Skill immer:

```text
@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]
```

Verboten bei `FIXED`:

```text
@[/SKILL 5 – DIAMANTSTANDARD FINAL AUDIT]
Skill 6 Debug
Skill 6 Debug Iteration
Target Skill: SKILL 5 – DIAMANTSTANDARD FINAL AUDIT
```

Wenn Skill 5 im Output "DIAMANTSTANDARD FINAL AUDIT" schreibt, muss die Slash-Zeile zwingend
`@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]` lauten.

### Bei `FIXED` (§ Auto-Verification PASS + Final Suite PASS)

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 6 – DIAMANTSTANDARD FINAL AUDIT
Canonical State: HANDOFF
Required Artifacts: Spec, Task, Original-Skill-6-Finding, Diff, geänderte Dateien, Auto-Verification PASS, Final Suite PASS, Evidence-Pfade (`*_evidence.json`, Reports), Audit Model To Use
Evidence Paths: <Mini-Verification, Final Suite, Reports/Traces, *_evidence.json>
Failure Code: N/A
Changed Files: <geänderte Dateien>
Decision: HANDOFF
Reason: Debug abgeschlossen; Re-Audit erforderlich
Copy Prompt:

@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]
(neuer Chat mit Audit Model To Use: SWE 1.6 | GPT-5.5)
Re-Audit Package: Feature, Spec, Task, Finding, Fix-Summary, Changed Files, Diff-Auszug, Test Results, Evidence-Pfade, Known Risks …
```

### Nach Skill-6 Re-Audit `PASS` / `PASS WITH FIXES` (vom User ausgeführt; Skill 5 dokumentiert nur die Weiterleitung)

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 7 – DOKUMENTATIONSUPDATE
Canonical State: HANDOFF
Required Artifacts: Spec (Pfad nach Spec-Done falls schon verschoben), Task, Final Audit Result, Changed Files, Tests
Evidence Paths: <Final Audit Result, Tests, Auto-Verification/Final Suite>
Failure Code: N/A
Changed Files: <geänderte Dateien>
Decision: HANDOFF
Reason: Audit grün — Dokumentation/Version
Copy Prompt: @[/SKILL 7 – DOKUMENTATIONSUPDATE] … Post-Implementation Package …
```

### Zurück zu Skill 5 (Re-Test) oder Skill 4

Bei `NEEDS RETEST` / fehlender Evidence: P2 mit `Target Skill: SKILL 5` oder `SKILL 4` je nach Ursache; `Decision: NEEDS_INFO` | `HANDOFF`; konkrete `Copy Prompt`-Zeile.

### GPT-5.5 (Eskalation)

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 – FEATURE DEBUG
Canonical State: ESCALATED
Required Artifacts: .windsurf/tmp/skill5_escalation_….md
Evidence Paths: <Eskalationsdatei + letzte Playwright-/Suite-Evidence>
Failure Code: <letzter exakter Generator-/Runner-Code oder N/A>
Changed Files: <geänderte Dateien oder NONE>
Decision: ESCALATION
Reason: Iteration 5 erschöpft oder STAGNATION_NO_PROGRESS_ON_FAILURE_CODE_OR_EVIDENCE
Copy Prompt: BEGIN COPY FOR NEW GPT-5.5 CHAT … /SKILL 5 – FEATURE DEBUG Modell GPT-5.5 …
```

### Secret Redaction Gate fuer Eskalationen (HARD)

Skill 5 darf in keinem Output, Handover, Eskalationspaket oder Logauszug geheime Werte ausgeben.

Verboten:

- `jwt_secret_key: <wert>`
- `JWT_SECRET_KEY=<wert>`
- `api_key: <wert>`
- `JANUS_INTERNAL_API_KEY=<wert>`
- Bearer Tokens, JWTs, Session Tokens, Cookies, API Keys, Internal Keys
- Werte aus `%APPDATA%\Janus Projekt\config.json`
- komplette Authorization Header

Erlaubt:

- Pfade und Schluesselnamen ohne Werte, z. B. `%APPDATA%\Janus Projekt\config.json` enthaelt `jwt_secret_key` und `api_key`.
- Fingerprints nur wenn noetig und nicht rekonstruierbar, z. B. `jwt_secret_key: present (redacted, length verified)`.
- Evidence, dass Werte geladen wurden, ohne den Wert selbst zu drucken.

Wenn ein Secret versehentlich im Output erscheinen wuerde, muss Skill 5 den Output verwerfen und ersetzen durch:

```text
SKILL 5 OUTPUT BLOCKED: SECRET_REDaction_REQUIRED

Reason:
- Escalation package would expose secret material.

Required Fix:
- Redact all secret values and output only paths, key names, presence/length checks, and non-sensitive evidence.
```

Wenn ein Secret bereits in einen Chat oder ein Artefakt gelangt ist, muss Skill 5 melden:

```text
SECURITY NOTE:
- Secret material may have been exposed in previous output.
- Rotate affected local E2E/API/JWT secrets before relying on them for further testing.
```

---

## Output-Skelett

```text
SKILL 5 DEBUG RESULT: FIXED | NEEDS RETEST | ESCALATION REQUIRED | BLOCKED | OUT OF SCOPE

Iteration: 1–5
Progress-Validierung: Failure Code … | Evidence geändert ggü. N-1: JA/NEIN | Stagnationszähler | Stopp-Regel ausgelöst: JA/NEIN
Auto-Verification: PASS | FAIL | N/A (+ Mini-Plan-Pfad; bei FAIL FAILURE LOG)
Artifact Identity Check: PASS | FAIL (Plan testRunId | Runner Path | Runner internal testRunId | Executed Playwright Path)
Final Feature Suite: PASS | FAIL | N/A WITH REASON
Geänderte Dateien / Implementierungsnachweis: …
Nächster Schritt: /save bei FIXED mit Codeänderung; dann P2 Skill 6 …
```

Atomic **`/save`:** nach erfolgreichem `FIXED` mit Codeänderung vor Skill-6-Re-Audit.
