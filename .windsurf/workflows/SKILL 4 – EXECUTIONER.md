---
description: Janus V3 — Skill 4 Execution. Ein Target-Task aus gebundenen Artefakten; Command-First Mini-TestPlan; Playwright-Verifikation; kein Scope jenseits Task/Contract.
---

This skill follows the global rules in `documentation/pipeline/PIPELINE_CONTRACT.md`.

## Rolle

- Genau **ein** Target-Task pro Lauf (bei mehreren Tasks in einer Datei: nur die genannte ID; Rest per Handoff).
- **Execution only:** Implementierung, Tests, Validierung — keine Planung, keine Spec-Erweiterung aus Chat.
- Gebundene Artefakte (Task, Spec, optional Pre-Check) sind maßgeblich; Modell muss dem Task entsprechen.

## Modell

- Standard: **SWE 1.6**
- Abweichung nur wenn im Task explizit: Kimi k2.5; Eskalation: GPT-5.5 wie von Skill 2/3 vorgegeben.

## Eingabe (Minimalaufruf)

```text
@[/SKILL 4 – EXECUTIONER]
Target Task: TASK-XXX.Y
Assigned Model: <SWE 1.6 | Kimi k2.5>
Spec: documentation/Planned Features/<FEATURE>.md
Task: documentation/tasks/<TASK_FILE>.md
Pre-Check: <optional>
```

Bei fehlenden/widersprüchlichen Artefakten oder Modell-Mismatch: **BLOCKED** mit klarer Ursache und Re-Run-Hinweis (keine Implementation).

---

## Skill-3-Handover Gate

Wenn der Aufruf aus Skill 3 kommt oder `Pre-Check`/`PRE-CHECK PASSED` behauptet, muss Skill 4 vor jeder Implementierung den Handover validieren.

Ein Skill-3-PASS-Handover ist nur gueltig, wenn diese Literal-Zeilen im Copy Prompt vorhanden sind:

```text
BEGIN COPY FOR SKILL 4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
Scope-Regel:
Automated Evidence Gate:
npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
Oracle-/TestPlan-Regel:
END COPY FOR SKILL 4
```

Diese Formen sind ungueltig:

```text
PRE-CHECK RESULT: PASSED
PRE-CHECK ERGEBNIS
Pre-Check Decision:
Pre-Check Decision: PRE-CHECK PASSED
PRE-CHECK RESULT
PASSED
PRE-CHECK PASSED
Skill 4 Handover
BEGIN COPY FOR @[/SKILL 4
Manual Janus Validation Gate
Stop at Manual Janus Validation Gate
Regeln:
Aufgaben:
Hard Rules:
Task Scope:
Risiko:
Execution Model:
Führe alle im Task spezifizierten Validierungen
Fuehre alle im Task spezifizierten Validierungen
alternativ JSON-Schema
sofern Generator/Validator
sofern Generator
Generator/Validator/Playwright-Run nur wenn
nur wenn Task nicht
nur wenn der Task nicht
außer wenn Analyse echten Bug zeigt
ausser wenn Analyse echten Bug zeigt
Produktcode fixen
Produktcode-Fix
Scope erweitern
Scope-Erweiterung
Wenn ungültig:
Wenn ungueltig:
```

Wenn der Handover unvollstaendig ist:

```text
BLOCKED: INVALID_SKILL3_HANDOVER
Reason: Skill-3-Handover enthaelt keinen vollstaendigen V3.2 Copyblock.
Required Fix: Skill 3 erneut ausfuehren und einen Handover mit BEGIN COPY FOR SKILL 4 / END COPY FOR SKILL 4 erzeugen lassen.
```

Skill 4 darf in diesem Zustand nicht implementieren.

---

## Golden Path (Execution Flow)

1. **Artefakte laden** — Task (Target isoliert), Spec, Pre-Check; Scope und Acceptance Criteria festhalten.
2. **Command-First** — Vollständigen Mini-TestPlan-JSON **im Chat ausgeben** (siehe unten); bei zulässigem Playwright-**N/A** stattdessen N/A-Planblock (Begründung, Pfade, Bestätigung „kein Chat-/Provider-/Stream-Pfad“). **Erst danach** Edits am Produkt-/Task-Scope.
3. **Implementieren** — nur laut Task benannte Dateien/Logik; Fixes bei Verifikationsfehlern nur im **Task-Scope** (sonst STOP → Handoff Skill 5).
4. **Tests** — gemäß Task (Unit/Integration/E2E); wenn nicht spezifiziert: minimaler Unit-Test für Kernlogik.
5. **Automatische Validierung** — Build/Unit/Integration/E2E wie Task es verlangt; ohne Shell-Fakes.
6. **Playwright Auto-Verification** — Mini-TestPlan-Datei schreiben, Generator + Validator + Runner ausführen (siehe nächster Abschnitt), außer begründetes **N/A** wie unten.
7. **Abschlusszustand** — genau ein Final-State laut Contract (`PASS` | `BLOCKED` | `NEEDS_INFO` | `FAILED` | `HANDOFF`); bei PASS: Pipeline-Fortsetzung (nächster Task vs. User Sign-off) und `/save` nur nach PASS.
8. **Letzter Task / Spec komplett / Backlog abgeschlossen** — Gesamt-Smoke/Regression wie Spec oder Backlog-Finding erfordert; danach muss ein konkreter naechster P2-Handover ausgegeben werden. Skill 4 darf nicht mit "wenn gewuenscht Skill 6" oder ohne Copy-Handover enden.

---

## Command-First (Mini-TestPlan)

- **Schema / SSOT:** `tests/e2e/generator/test-plan.schema.json`, Strategien nur aus `tests/e2e/generator/strategy-registry.json`.
- **Datei:** `documentation/test-runs/<task_id>_verify.json` (reines JSON, spiegelt den vorab im Chat ausgegebenen Plan).
- Pflichtfelder u. a.: `testRunId` im Generator-SSOT-Format `TEST-RUN-YYYY-MM-DD-NNN`, `executionMode: LIVE_VISUAL`, `target: JANUS_CHAT`, `chatWindow`, `tests` mit Prompt + `expected`/`mustNotContain`. Der Task-Bezug steht im Dateinamen (`<task_id>_verify.json`) und im `title`, nicht im `testRunId`.
- **N/A (Playwright entfällt):** nur bei reinen `.css` / `.md` / `.yml` ohne Logik-Pfade; **nicht** bei `.py`/`.js`/`.ts` oder Chat/Backend/Stream. Generator-/Playwright-Fehler **nie** durch N/A umgehen.

---

## Playwright-Verifikation (Pflichtpfad)

Nach funktionalen Änderungen an Chat-/Janus-sichtbaren Pfaden (und vor finalem Sign-off), sofern nicht **N/A**:

```text
node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/<task_id>_verify.json --out tests/e2e/generated/<task_id>_verify.live.spec.js
node tests/e2e/generator/validate-runner.mjs --plan documentation/test-runs/<task_id>_verify.json --runner tests/e2e/generated/<task_id>_verify.live.spec.js
npx playwright test tests/e2e/generated/<task_id>_verify.live.spec.js --headed --workers=1 --reporter=list
```

- Befehle im Workspace **tatsächlich** ausführen; Ergebnis als `Auto-Verification: PASS | FAIL | N/A` mit Kurzbegründung und Pfaden (`playwright-report/`, `test-results/`, optional `documentation/test-results/<testRunId>/`).
- Playwright darf in Skills keinen blockierenden HTML-Report-Server offen halten. Wenn im Output `Serving HTML report at http://localhost:9323. Press Ctrl+C to quit.` erscheint, ist der Testlauf bereits beendet; Prozess beenden, Exit-Code/Failures auswerten und künftig `--reporter=list` bzw. `open: 'never'` verwenden.
- **Chat-Fixes:** Evidence aus diesem Lauf — kein `TASK NEEDS EVIDENCE` als Ersatz für fehlende Playwright-Evidence auf Chat-Pfaden.
- **Provider:** Kein „nicht automatisierbar“-Mantra, wenn `config.json` einen nutzbaren Key zeigt. Bei jedem Automations-/Config-Blocker muss der V3.1-Block `Credential Check` aus `documentation/pipeline/PIPELINE_CONTRACT.md` ausgegeben werden (Secrets niemals drucken). Benchmark-nachweislich automatisierbare Provider nicht auf „nur manuell“ ausweichen (siehe Contract: Invalid Examples).

### Provider-Bug Isolation Gate (HARD)

Wenn der Task einen provider-spezifischen Fehler betrifft (z. B. `Gemini Provider Error`,
`GPT-5.4-nano`, `Provider: gemini`, `Provider: GPT`, `provider parity`, `llm_gateway` oder
`Provider Integration`), gelten zusaetzlich:

- Skill 4 darf den Fehler nicht durch Provider-Fallback kaschieren.
- Skill 4 darf Gemini-Fehler nicht durch GPT-Aufruf, Modellwechsel oder generische Fallback-Antwort als behoben markieren.
- Skill 4 darf GPT-Fehler nicht durch Gemini-Aufruf oder Providerwechsel als behoben markieren.
- Provider-Isolation ist Teil der Akzeptanzkriterien.
- Wenn der betroffene Provider nicht konfiguriert oder nicht testbar ist, muss Skill 4 `TASK EXECUTION BLOCKED - PROVIDER_NOT_TESTABLE` mit Credential-Check ohne Secrets ausgeben.
- Bei einem Provider-Fix muss Validation Evidence den betroffenen Provider und die betroffene TestCase-ID nennen.
- Ein PASS ohne fokussierten Retest des urspruenglich fehlgeschlagenen Provider-TestCase ist ungueltig.
- Wenn die Ursache ohne Logs/Evidence nicht identifiziert werden kann, ist ein bloßes `Bitte Backend-Logs bereitstellen` verboten. Skill 4 muss `TASK EXECUTION BLOCKED - PROVIDER_RUNTIME_EVIDENCE_REQUIRED` ausgeben und einen P2-Handover zu `SKILL 5 – FEATURE DEBUG` liefern.

Verbotene Abschlussformulierungen bei Provider-Bugs:

```text
Fallback auf GPT
Fallback auf Gemini
mit anderem Provider erfolgreich
Modell gewechselt und damit behoben
Quality fallback genutzt
```

es sei denn, der Task verlangt explizit einen Modell-Routing-Fix und der urspruengliche Provider-TestCase
wird anschliessend separat als PASS oder BLOCKED dokumentiert.

### Provider/Runtime Blocked Handoff to Skill 5 (HARD)

Wenn Skill 4 bei einem Provider-, Backend-, Runtime-, LLM-Gateway-, Stream- oder Tool-Routing-Finding blockiert,
muss der Output mit einem konkreten Debug-Handover enden.

Verboten:

```text
Bitte Backend-Logs bereitstellen
Bitte Logs bereitstellen
Backend-Logs pruefen
Fokussierten Debug-Run autorisieren
Naechster Schritt: Logs pruefen
```

ohne direkt folgenden Copy-Handover zu `SKILL 5 – FEATURE DEBUG`.

Pflichtformat:

```text
TASK EXECUTION BLOCKED - PROVIDER_RUNTIME_EVIDENCE_REQUIRED

Reason:
- <konkreter Blocker, z. B. Gemini Exception im Backend nicht sichtbar>

Observed Analysis:
- <Dateien/Funktionen, die untersucht wurden>

NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 – FEATURE DEBUG
Canonical State: BLOCKED
Required Artifacts: Backlog Item, Task, Source TestRun, Failed TestCase, Evidence, untersuchte Dateien, Debug-Ziel
Evidence Paths: <evidence path>, <relevante code paths>
Failure Code: PROVIDER_RUNTIME_EVIDENCE_REQUIRED
Changed Files: NONE | <files>
Decision: HANDOFF
Reason: Provider-/Runtime-Ursache kann in Skill 4 ohne fokussierte Logs/Evidence nicht sicher identifiziert werden.
Copy Prompt: @[/SKILL 5 – FEATURE DEBUG] Mode=PROVIDER_RUNTIME_DEBUG; ExecutionModel=SWE_1_6; BacklogItem=<BACKLOG-XXX>; Task=<task path>; TargetTask=<task id>; SourceTestRun=<TEST-RUN-ID>; FailedTestCase=<case id>; Evidence=<evidence path>; Failure=<failure summary>; DebugGoal=REPRODUCE_CAPTURE_LOGS_IDENTIFY_ROOT_CAUSE_NO_SECRETS_NO_PROVIDER_FALLBACK; Rules=NO_SECRETS_NO_SCOPE_EXPANSION_PRESERVE_PROVIDER_ISOLATION; ExpectedOutput=FIXED_WITH_RETEST_HANDOFF_OR_BLOCKED_WITH_EVIDENCE
```

Wenn ein Provider-Credential-Problem moeglich ist, muss der Handover zusaetzlich enthalten:

```text
CredentialCheck=REQUIRED_NO_SECRETS
```

Skill 4 darf in diesem Zustand nicht mit `TASK COMPLETE`, `TASK EXECUTION COMPLETE`, `Backlog-Status: DONE`,
`SKILL 7`, oder einer offenen Rueckfrage an den User enden.

**Manual-Gate-Verbot bei Chat-/Backend-Fixes:** Bei Änderungen an Chat-, Backend-,
Provider-, Intent-, Memory-, Context-, Stream- oder Tool-Routing-Pfaden ist ein Abschluss mit
`Manual Janus Validation Gate`, `Please run a manual test`, `Automated validation passed
(Python compilation)` oder sinngleicher Prosa ungültig, solange Generator, Validator und
Playwright nicht gelaufen sind.

Python-Compile, Typecheck oder Unit-Tests sind nur Vorvalidierung. Sie ersetzen nie die
Auto-Verification für Chat-/Backend-Verhalten.

## Backlog Completion Gate (HARD)

Backlog-Items sind kein Audit-Bypass. Fuer Backlog-Tasks gelten dieselben Abschlussregeln wie
fuer Spec-Tasks, plus eine zusaetzliche Evidence-Pflicht bei TestRun-Findings.

Ein Backlog-Item darf nur auf `DONE` gesetzt werden, wenn alle Bedingungen erfuellt sind:

1. Die Implementierung ist abgeschlossen.
2. `Auto-Verification` steht unmittelbar vorher mit `- Status: PASS`.
3. Bei Backlog-Items aus einem TestRun (`Quelle: TestRun`) existiert Retest-Evidence fuer die urspruenglich fehlgeschlagenen TestCase-IDs oder ein neu erzeugter TestResult-JSON mit verbesserter/erfolgreicher PassRate.
4. `Final audit` ist nicht `PENDING`, wenn der Output `TASK EXECUTION COMPLETE`, `TASK COMPLETE` oder `ALL TASKS COMPLETE` behauptet.
5. Der Backlog-Block steht physisch unter der passenden kanonischen Sektion: `Status: DONE` nur unter `## DONE`, nie unter `## READY`.

Ungültige Abschluss-Evidence:

```text
sollte nun PASS zeigen
Manual Janus Test Evidence: Ausstehend
Python compilation passed
System-Prompt-Optimierung implementiert
Dashboard synchronisiert
```

Diese Aussagen duerfen Implementation-Fortschritt belegen, aber niemals Completion.

Wenn Implementierung fertig ist, aber Retest-/Auto-Verification-Evidence fehlt:

```text
IMPLEMENTATION COMPLETE - VALIDATION REQUIRED

NEXT_SKILL_HANDOFF
Target Skill: TEST SKILL 1 – TESTSPEC TO TEST PLAN
Canonical State: HANDOFF
Required Artifacts: Original TestSpec, baseline TestRun, changed files, fixed Backlog IDs
Evidence Paths: <baseline TestResultJson>, <changed files>
Failure Code: VALIDATION_REQUIRED
Changed Files: <files>
Decision: HANDOFF
Reason: Implementation changed Chat/Prompt behavior, but the original failing TestRun has not been retested.
Copy Prompt: @[/TEST SKILL 1 – TESTSPEC TO TEST PLAN] ...
```

### TestRun-Finding Retest Handoff (HARD)

Bei Backlog-Items aus TestRun-Findings (`Quelle: TestRun`) darf Skill 4 nach einem Produkt-/Provider-/Routing-Fix
nicht direkt final abschliessen. Nach der Implementierung muss ein Retest-Handover ausgegeben werden.

Pflicht:

- Zuerst lokale/Unit-/Provider-Tests im Task-Scope ausfuehren.
- Wenn die Aenderung Chat-, Provider-, Intent-, Calendar-, Memory-, Tool- oder Backend-Verhalten betrifft,
  muss danach die Test-Pipeline retesten.
- Der Handover muss den urspruenglichen `Source TestRun`, die fehlgeschlagenen TestCase-IDs und die Evidence-Pfade nennen.
- Fuer provider-spezifische Bugs muss der fokussierte Retest zuerst den urspruenglich fehlgeschlagenen Provider-TestCase nennen.
- Danach muss ein kompletter TestRun der betroffenen TestSpec folgen oder als naechster Schritt angefordert werden.

Gueltiger Abschluss nach Implementierung ohne vollstaendigen Retest:

```text
IMPLEMENTATION COMPLETE - VALIDATION REQUIRED

NEXT_SKILL_HANDOFF
Target Skill: TEST SKILL 1 - TESTSPEC TO TEST PLAN
Canonical State: HANDOFF
Required Artifacts: Updated source files, Source TestSpec, baseline TestRun, failed TestCase IDs, Evidence paths
Evidence Paths: <baseline evidence>, <changed files>
Failure Code: VALIDATION_REQUIRED
Changed Files: <files>
Decision: HANDOFF
Reason: Produkt-/Provider-Fix wurde implementiert; betroffene TestSpec muss mit neuem TestPlan und Live-TestRun retestet werden.
Copy Prompt: @[/TEST SKILL 1 - TESTSPEC TO TEST PLAN] TestSpec: <source TestSpec>; Mode=TESTSPEC_TO_TEST_PLAN; SourceBacklog=<BACKLOG-XXX>; SourceTestRun=<TEST-RUN-ID>; FocusedRetest=<TestCase IDs>; Rules=GENERATE_FRESH_PLAN_FOR_RETEST_NO_MANUAL_PLAN_PATCH; ExpectedOutput=TEST_PLAN_CREATED_PLUS_SKILL2_HANDOVER
```

Wenn bereits ein frischer valider TestPlan fuer den Retest existiert, darf direkt zu TEST SKILL 3 geroutet werden:

```text
@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION] Mode=LIVE_VISUAL; ExecutionModel=SWE_1_6; TestSpec=<source TestSpec>; TestPlan=<fresh retest plan>; TargetTestRun=<fresh TEST-RUN-ID>; SourceBacklog=<BACKLOG-XXX>; SourceTestRun=<baseline TEST-RUN-ID>; FocusedRetest=<TestCase IDs>; ConnectivityMode=PLAYWRIGHT_WEBSERVER_AUTOSTART; ManualJanusStartRequired=NO; Rules=USE_ARTIFACTS_ONLY_EXECUTE_LIVE_TESTS_COLLECT_EVIDENCE_NO_IMPLEMENTATION; ExpectedOutput=TEST_RESULT_PLUS_SINGLE_LINE_HANDOFF_TO_TEST_SKILL_4_WITH_METRICS
```

Test-Skill-Zielnamen sind strikt:

```text
LIVE_RETEST / LIVE_VISUAL -> @[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]
DIAMOND RETEST AUDIT -> @[/TEST SKILL 5 – DIAMOND RETEST AUDIT]
```

Verboten:

```text
@[/TEST SKILL 3 – DIAMOND RETEST AUDIT]
@[/TEST SKILL 5 – LIVE JANUS TEST EXECUTION]
```

Wenn Skill 4 einen Produkt-/Prompt-/Provider-Fix implementiert und `LIVE_RETEST` verlangt, muss der
Copy-Prompt `@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]` enthalten, mit `TestSpec`, `TestPlan`,
`TargetTestRun`, `SourceBacklog`, `ChangedFiles`, `FocusTestCase`, `Rules` und `ExpectedOutput`.

Verboten bei TestRun-Finding-Fixes:

```text
TASK EXECUTION COMPLETE
Backlog-Status: DONE
SKILL 7 Handover
Final Audit nicht erforderlich
```

solange kein frischer TestResultJson den urspruenglichen Finding-Scope validiert.

### TestSpec-/Oracle-Execution Boundary (HARD)

Wenn der Target Task als TestSpec-, TestPlan-, Test-Oracle-, Assertion-, `containsAny`-, `mustNotContain`- oder Response-Format-Aufgabe klassifiziert ist, gilt:

- Skill 4 muss zuerst die dauerhafte Source-of-Truth-TestSpec/Oracle-Datei bestimmen. Fuer Janus-Testpipeline-Oracle-Fixes ist das normalerweise `documentation/TEST_SPEC/*.md`.
- Skill 4 darf nur die konkrete Source-of-Truth-TestSpec/Oracle-Datei aendern.
- Skill 4 darf keine bestehenden `documentation/test-runs/*_plan.json` manuell patchen.
- Alte `documentation/test-runs/*_plan.json` Dateien duerfen nur als Evidence, Baseline oder Reference Plan verwendet werden.
- Wenn der Skill-3-Handover als Files/Scope nur einen alten TestPlan nennt, muss Skill 4 BLOCKED melden oder die eindeutige Source-of-Truth-TestSpec aus Spec/Backlog/TestPlan ableiten und dokumentieren. Ein Plan-only-Patch ist verboten.
- Skill 4 darf keine `documentation/test-results/*` manuell erzeugen oder als PASS-Evidence behaupten.
- Skill 4 darf das Backlog-Item nicht auf `DONE` setzen, bevor ein neuer TestRun aus der aktualisierten TestSpec gelaufen ist und TEST SKILL 4/5 die Resultate bewertet haben.
- Nach der TestSpec-Aenderung muss Skill 4 mit `IMPLEMENTATION COMPLETE - VALIDATION REQUIRED` enden und einen Copy-Handover zu `TEST SKILL 1 - TESTSPEC TO TEST PLAN` ausgeben.
- Skill 4 darf bei solchen Tasks nicht direkt zu `TEST SKILL 3`, `TEST SKILL 5`, `SKILL 6` oder `SKILL 7` routen.

Pflicht-Handover nach TestSpec-/Oracle-Aenderung:

```text
IMPLEMENTATION COMPLETE - VALIDATION REQUIRED

NEXT_SKILL_HANDOFF
Target Skill: TEST SKILL 1 - TESTSPEC TO TEST PLAN
Canonical State: HANDOFF
Required Artifacts: Updated TestSpec, changed files, source Backlog ID
Evidence Paths: <updated TestSpec path>, <changed files>
Failure Code: TESTSPEC_VALIDATION_REQUIRED
Changed Files: <updated TestSpec path>
Decision: HANDOFF
Reason: TestSpec/Oracle wurde angepasst; ein neuer TestPlan und Live-TestRun muessen deterministisch durch die Test-Pipeline erzeugt werden.
Copy Prompt: siehe grauen Copyblock direkt darunter.
```

Der direkt folgende graue Copyblock MUSS exakt `TestSpec:` verwenden, nicht `Spec:`.
`Expected Output` MUSS zu TEST SKILL 2 routen, nicht direkt zu TEST SKILL 3.
Skill 4 darf keinen konkreten naechsten `TEST-RUN-...` vorgeben; TEST SKILL 1 bestimmt den
naechsten freien TestRun deterministisch.

Pflicht-Copyblock:

```text
@[/TEST SKILL 1 - TESTSPEC TO TEST PLAN]
TestSpec: <updated TestSpec path>
Backlog Item: <BACKLOG-XXX>
Source Task: <task id>
Old Reference Plan: <old plan path | N/A>
Mode: TESTSPEC_TO_TEST_PLAN
Execution Model: SWE 1.6

Context:
- Skill-4 Ergebnis: IMPLEMENTATION COMPLETE - VALIDATION REQUIRED
- TestSpec/Oracle aktualisiert: <kurze Zusammenfassung>
- Alter TestPlan dient nur als Baseline/Reference.
- Ziel: Frischen TestPlan aus aktualisierter TestSpec generieren.

Rules:
- Nutze die aktualisierte TestSpec als Source of Truth.
- Generiere einen frischen TestPlan.
- Der alte TestPlan darf nicht gepatcht werden.
- Der alte TestPlan darf nur als Baseline/Reference verwendet werden.
- Bestimme den naechsten freien TestRun deterministisch.
- Fuehre Generator-Validation aus, bevor TEST PLAN CREATED gemeldet wird.

Expected Output:
- TEST PLAN CREATED
- TESTPLAN VALID
- Copy-Handover zu TEST SKILL 2 - TEST RUN PRECHECK
```

Verboten fuer TestSpec-/Oracle-Tasks:

```text
TASK EXECUTION COMPLETE
Backlog-Status: DONE
BEGIN COPY FOR TEST SKILL 5
BEGIN COPY FOR SKILL 6
TestRun wurde ausgefuehrt
TestResult erstellt
Changed Files: documentation/test-runs/<old_test_run>_plan.json
Files Modified: documentation/test-runs/<old_test_run>_plan.json
Scope: alter TestPlan direkt patchen
Spec: documentation/TEST_SPEC/<...>.md
Expected Output: Handoff zu TEST SKILL 3
Expected Output: TEST_RESULT_PLUS_HANDOFF_TO_TEST_SKILL_4
Ziel ist TEST-RUN-<konkrete Nummer>
Ziel: TEST-RUN-<konkrete Nummer>
```

Wenn ein frischer TestPlan bereits existiert und nur Live-Ausfuehrung fehlt, darf statt TEST SKILL 1
direkt zu `TEST SKILL 3 – LIVE JANUS TEST EXECUTION` geroutet werden. Der Handover muss dann den
frischen TestPlan, Baseline-PassRate und zu verifizierende TestCase-IDs enthalten.

Verboten bei fehlender Retest-Evidence:

```text
TASK EXECUTION COMPLETE
Backlog-Status: DONE
SKILL 6 Audit optional
Für Backlog-Items ist SKILL 6 nicht erforderlich
```

Wenn Playwright durch einen bestehenden Infra-/Frontend-Fehler blockiert ist (z. B.
`win is not defined`), muss Skill 4 STOPPEN und einen P2-Handoff zu Skill 5 erzeugen:

```text
TASK EXECUTION BLOCKED - E2E INFRA BLOCKER

NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 – FEATURE DEBUG
Canonical State: BLOCKED
Required Artifacts: Task, Target Task ID, Mini-TestPlan, generated runner, validation logs, frontend/backend error evidence, changed files
Evidence Paths: <paths>
Failure Code: FRONTEND_NOT_READY | RUNNER_PRECLICK_DOM_BROKEN | RUNNER_SELECTOR_FAILURE | <exakter Code>
Changed Files: <files>
Decision: HANDOFF
Reason: Chat/backend fix cannot be accepted without Playwright evidence; E2E is blocked by unrelated infra/frontend error.
Copy Prompt: @[/SKILL 5 – FEATURE DEBUG] ...
```

Verboten in diesem Zustand:

```text
Implementation Complete
Manual Janus Validation Gate
Please run a manual test
Automated validation passed (Python compilation)
Full E2E validation is blocked ... please test manually
```

---

## Failure Management

**Quelle der Failure-Codes:** `tests/e2e/generator/generate-live-runner.mjs` (Taxonomie im Header). Bei `FAIL` exakt diesen Code und den suggested Bucket nutzen — keine Umbenennung.

| Code | Kurz |
|------|------|
| `RUNNER_PRECLICK_EMPTY` / `RUNNER_PRECLICK_DOM_BROKEN` | Eingabe/DOM vor Klick |
| `RUNNER_SELECTOR_FAILURE` / `RUNNER_WAIT_FAILURE` | Selector / Wait |
| `RUNNER_STREAM_TIMEOUT` (A: kein POST stream / B: Bubble leer/`...`) | Sendepfad vs. SSE/Content |
| `FRONTEND_NOT_READY` / `BACKEND_HEALTH_FAIL` | Infra / Dev-Server |
| `PROVIDER_TIMEOUT` | Provider / Kosten |
| `TOOL_ROUTING_FAILURE` / `ASSERTION_MISMATCH` | Routing / Spec |

**Timeout / Stream:** Symptom-Hinweise (z. B. `[SSE-REANCHOR]`, fehlender `POST /api/chat/stream`) nur zur Einordnung — Code bleibt der Taxonomie treu.

**Bei FAIL — verbindliches Kurzprotokoll:**

```text
FAILURE LOG (BINDEND)
TestRunId: <…>
Failure Code: <exakt ein Code>
Suggested Triage: <Bucket>
Evidence Paths: …
Excerpt: <erste relevante Zeilen>
```

**Fix-Loop:** Max. **zwei** zielgerichtete Versuche **innerhalb** Task-Scope + ohne Protokoll-/Produktverfälschung nur für Tests. Danach **FIX LOOP LIMIT REACHED** oder bei strukturellen/timeouts außerhalb Scope **sofort** Eskalation (kein „wegdoktern“).

**Eskalation:** Strukturelle Ursachen, wiederholte Timeouts ohne Scope-Fix, Scope-Bedarf außerhalb Task → Handoff **Skill 5** mit Evidence (Code, Logs, Plan-Pfad).

**Debug-vs-Audit Routing (HARD):** Wenn Auto-Verification `FAIL`, `BLOCKED`,
`FIX LOOP LIMIT REACHED`, `TASK EXECUTION BLOCKED`, Provider-spezifische Abweichungen,
Assertion-Mismatch, Context-Leakage, Tool-Routing-Failure, Timeout oder irgendein anderes
unbehobenes Problem zeigt, ist der naechste Skill **immer SKILL 5 – FEATURE DEBUG** oder
BACKLOG SKILL 3 bei Task-Reclassification. Skill 6 ist nur fuer Final Audit nach vollstaendigem
PASS erlaubt.

Verboten bei FAIL/BLOCKED:

```text
@[/SKILL 6 – FEATURE DEBUG]
@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]
Target Skill: SKILL 6
```

Gueltig bei fehlgeschlagener Auto-Verification:

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 – FEATURE DEBUG
Canonical State: HANDOFF
Required Artifacts: Task, Target Task ID, Mini-TestPlan, generated runner, FAILURE LOG, changed files
Evidence Paths: <paths>
Failure Code: <exakter Failure Code>
Changed Files: <files>
Decision: HANDOFF
Reason: Auto-Verification failed; debug/fix required before any audit.
Copy Prompt: @[/SKILL 5 – FEATURE DEBUG] ...
```

Skill 6 darf nur ausgegeben werden, wenn unmittelbar vorher `Auto-Verification` mit
`- Status: PASS` steht und kein bekannter Failure offen ist.

**Backlog-/Task-Identitaetswechsel:** Wenn Skill 4 waehrend eines Backlog-Tasks feststellt,
dass die Task-Klassifikation falsch ist (z. B. Test-Oracle-Task entpuppt sich als Produktbug,
Produktbug entpuppt sich als Test-Oracle, Scope muss neu klassifiziert werden), darf Skill 4
nicht direkt zu Skill 2 routen. Skill 2 zerlegt bereits definierte Requirements; er ist nicht
zustaendig fuer Backlog-Reclassification.

Wenn Skill 4 in einem Folgeaufruf merkt, dass er bereits zuvor einen falschen Handoff
ausgegeben hat (z. B. `P2 handover to Skill 2` bei Reclassification), muss er diesen Handoff
als STALE/INVALID markieren und sofort einen korrigierten Handoff zu BACKLOG SKILL 3 ausgeben.
Er darf in diesem Fall nicht fragen, ob der User mit dem alten falschen Skill-2-Handoff
fortfahren will.

Verbotene Folgefrage bei Reclassification:

```text
Proceed with the P2 handover to Skill 2
Which would you like me to do?
```

Stattdessen:

```text
PREVIOUS HANDOFF INVALIDATED
Reason: Reclassification must route to BACKLOG SKILL 3, not Skill 2.
```

In diesem Fall ist der naechste Skill:

```text
@[/BACKLOG SKILL 3 – EXECUTION HANDOFF]
Mode: DASHBOARD_PREP
Backlog Items:
<BACKLOG-XXX>
```

Der Handoff muss verlangen:

- Backlog Item neu klassifizieren.
- Routing reason/routing confidence aktualisieren.
- Neues oder aktualisiertes Task-Artefakt erzeugen.
- Entry Point und Recommended next skill neu setzen.
- Evidence-Pfade aus Skill 4 uebernehmen.
- Geaenderte Dateien und moegliche Out-of-Scope-Diffs benennen.

Verboten bei Task-Identitaetswechsel:

- `BEGIN COPY FOR SKILL 2 – TASK BREAKDOWN ENGINE`
- `@[/SKILL 2 – TASK BREAKDOWN ENGINE]`
- direktes Produktcode-Fixing im falschen Task-Scope

Gueltiger Final-State:

```text
TASK EXECUTION BLOCKED - RECLASSIFICATION REQUIRED

NEXT_SKILL_HANDOFF
Target Skill: BACKLOG SKILL 3 – EXECUTION HANDOFF
Canonical State: BLOCKED
Required Artifacts: Backlog Item, current Task, Skill-4 Evidence, changed files, failed test output
Evidence Paths: <paths>
Failure Code: RECLASSIFICATION_REQUIRED | PRODUCTBUG_DETECTED | ORACLE_MISCLASSIFIED
Changed Files: <files changed before block, or NONE>
Decision: HANDOFF
Reason: Task classification/scope is incorrect; Backlog routing must be repaired before execution.
Copy Prompt: @[/BACKLOG SKILL 3 – EXECUTION HANDOFF] ...
```

---

## Completion & User Sign-off

- **`TASK COMPLETE` / `ALL TASKS COMPLETE`:** nur **direkt nach** einem Block `Auto-Verification:` mit Zeile **`- Status: PASS`**. Kein Text dazwischen. **`N/A` → kein `TASK COMPLETE`**; stattdessen `N/A-SCOPE CLOSURE` (mit N/A-Begründung).
- **`TASK COMPLETE` mit `FAIL`:** verboten.
- Abschlüsse ohne gültigen State / ohne nächste Aktion: verboten (siehe Contract **One Final State**).

**User Sign-off** (nach PASS, letzter Task + Gesamtvalidierung): kurzer **MANUELLER UX-CHECK** (1 Test-Prompt, erwartete Reaktion, Erfolgskriterium in Produktsprache), dann **zwei Optionen**: (1) `Manueller Test erfolgreich.` → danach separater Skill-6-Handover; (2) Fehlerbeschreibung → Skill-5-Handover. Kein Skill-6-Block im selben Posting wie `ALL TASKS COMPLETE`.

**`/save`:** nur nach erfolgreicher Validierung und vor nächstem Skill.

---

## Handover (P2)

### Subtask Follow-up Handoff to Skill 3 (HARD)

Wenn Skill 4 einen einzelnen Subtask abschliesst und weitere Subtasks offen sind, darf der naechste
Skill-3-Handoff nicht als Kurzblock ausgegeben werden.

Pflichtfelder im naechsten Skill-3-Handoff:

```text
Spec:
Task:
Backlog Item:
Target Task:
Target Subtask:
Previous Subtask:
Remaining Subtasks:
Mode: PRE_IMPLEMENTATION_VERIFICATION
Execution Model:
Context:
Rules:
Expected Output:
```

Verboten:

```text
SKILL 3 Handoff for Next Subtask
text
@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]
Spec: <path>
Task: <path>
Execution Model: SWE 1.6
Target Subtask: <id>
Previous Subtask: <id>
Remaining Subtasks: <ids>
```

ohne `Backlog Item`, `Target Task`, `Mode`, `Context`, `Rules` und `Expected Output`.

Auch verboten:

```text
Status: SUBTASK_COMPLETED
...
SKILL 3 Handoff for Next Subtask
@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]
Spec:
Task:
Execution Model:
Target Subtask:
Previous Subtask:
Remaining Subtasks:
```

Wenn ein Subtask abgeschlossen ist und weitere Subtasks offen sind, ist `SUBTASK_COMPLETED` nur gueltig,
wenn im selben Output der vollstaendige Pflichtformat-Copyblock fuer den naechsten Skill-3-Lauf steht.
Andernfalls muss Skill 4 den Output selbst korrigieren, bevor er antwortet.

Output Self-Check (P0):

Vor dem finalen Antworten muss Skill 4 den eigenen Text pruefen. Wenn alle drei Muster vorkommen:

```text
Status: SUBTASK_COMPLETED
SKILL 3 Handoff for Next Subtask
@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]
```

dann MUSS derselbe Output auch alle folgenden Literale enthalten:

```text
Backlog Item:
Target Task:
Target Subtask:
Previous Subtask:
Remaining Subtasks:
Mode: PRE_IMPLEMENTATION_VERIFICATION
Context:
Rules:
Expected Output:
```

Fehlt eines dieser Literale, ist der Output ungueltig. Skill 4 darf ihn nicht senden und muss ihn
ersetzen durch:

```text
SUBTASK HANDOFF BLOCKED: NEXT_SKILL3_HANDOFF_INCOMPLETE

Reason:
- Subtask completed, but next Skill-3 handoff is missing mandatory fields.

Required Fix:
- Re-emit the complete Skill-3 handoff with Backlog Item, Target Task, Target Subtask, Mode, Context, Rules and Expected Output.
```

Wenn `Remaining Subtasks: None`, `Remaining Subtasks: NONE` oder "final subtask" genannt wird, darf
Skill 4 nicht zu Skill 3 fuer einen weiteren Subtask routen. Dann muss der Handoff zum passenden
Validierungs-/Audit-Pfad gehen:

- bei ausstehender TestRun-Validierung: `TEST SKILL 3 – LIVE JANUS TEST EXECUTION`
- bei vollstaendig validiertem Backlog-Fix: `SKILL 6 – DIAMANTSTANDARD FINAL AUDIT`
- bei Blocker: `SKILL 5 – FEATURE DEBUG` oder Backlog-Handoff mit Evidence

Pflichtformat:

```text
@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]
Spec: <spec path>
Task: <task path>
Backlog Item: <BACKLOG-XXX | N/A>
Target Task: <task id>
Target Subtask: <next subtask id>
Previous Subtask: <completed subtask id> (COMPLETED)
Remaining Subtasks: <remaining ids or NONE>
Mode: PRE_IMPLEMENTATION_VERIFICATION
Execution Model: <SWE 1.6 | Kimi k2.5 | GPT-5.5>
Context: <one-line context including why this subtask is next>
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_SKILL_4_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_SKILL_4_HANDOFF_OR_PRE_CHECK_BLOCKED
```

### Portable Path Cleanup Evidence Gate (HARD)

Wenn der Target Task/Subtask harte Pfade, Portable Startup, Python Path, `site-packages`,
`Startup log`, `webServer`-Startup oder machine-specific path assumptions betrifft, darf Skill 4
`SUBTASK_COMPLETED` nur ausgeben, wenn ein Residual-Check dokumentiert ist.

Pflicht-Residual-Checks vor Abschluss:

```powershell
rg -n "C:\\\\python311|C:\\\\KI\\\\Janus-Projekt|VENV_SITE_PACKAGES|Startup log" backend/main.py package.json playwright.config.js
```

Regeln:

- Wenn der Check noch harte Pfade in der erlaubten Write-Scope-Datei findet, ist der Subtask nicht abgeschlossen.
- Wenn harte Pfade absichtlich bleiben, muss Skill 4 fuer jede Fundstelle begruenden, warum sie nicht im Scope ist und nicht den aktuellen Blocker betrifft.
- Behauptungen wie "backend startup no longer depends on C:\\KI\\Janus-Projekt" sind verboten, solange `rg` noch solche Pfade in Startup-Code findet.
- Bei nicht erledigtem Residual-Check muss Skill 4 `SUBTASK BLOCKED: RESIDUAL_HARDCODED_PATHS` oder einen Handoff zur Fortsetzung desselben Subtasks ausgeben, nicht zum naechsten Subtask.

---

Jeder Übergang zu einem anderen Skill nutzt:

Zusatzpflicht: Der eigentliche Copy Prompt MUSS immer als eigener grauer `text` Copy-Kasten
ausgegeben werden. `NEXT_SKILL_HANDOFF` ist Diagnose/Metadaten, aber nie der einzige
kopierbare Handover. Skill 4 darf nicht mit `Copy Prompt: @[/...]` im Fliesstext enden.

Pflicht:

- Nach jedem `NEXT_SKILL_HANDOFF` folgt ein einzelner fenced Codeblock mit Info-String `text`.
- Dieser Block beginnt direkt mit dem Ziel-Skill-Trigger, z. B. `@[/SKILL 5 ...]`.
- Der Block enthaelt alle Artefakte, Rules und Expected Output fuer den naechsten Lauf.
- Wenn Skill 4 keinen grauen Copyblock erzeugen kann, muss er `TASK EXECUTION BLOCKED - COPY_HANDOVER_MISSING` ausgeben.

```text
NEXT_SKILL_HANDOFF
Target Skill:
Canonical State:
Required Artifacts:
Evidence Paths:
Failure Code:
Changed Files:
Decision:
Reason:
Copy Prompt:
```

**Beispiel → Skill 5 (Debug):**

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 – FEATURE DEBUG
Canonical State: HANDOFF
Required Artifacts: Spec, Task, Target Task ID, Mini-TestPlan-Pfad, FAILURE LOG, geänderte Dateien, Terminalauszug
Evidence Paths: <Mini-TestPlan, generated runner, playwright-report/test-results, relevante Logs>
Failure Code: <exakter Generator-/Runner-Code>
Changed Files: <geänderte Dateien oder NONE>
Decision: HANDOFF
Reason: Struktureller Fehler / Fix-Loop erschöpft / außerhalb Task-Scope
Copy Prompt: @[/SKILL 5 – FEATURE DEBUG] … (kompaktes Debug-Paket einfügen)
```

**Beispiel → BACKLOG SKILL 3 (Reclassification nach falscher Task-Identitaet):**

```text
NEXT_SKILL_HANDOFF
Target Skill: BACKLOG SKILL 3 – EXECUTION HANDOFF
Canonical State: BLOCKED
Required Artifacts: BACKLOG-XXX, aktuelles Task-Artefakt, Skill-4 Test-Evidence, geaenderte Dateien, Failure Summary
Evidence Paths: <test-results/...>, <playwright-report/...>, <generated runner>, <Mini-TestPlan>
Failure Code: PRODUCTBUG_DETECTED
Changed Files: <Dateien oder NONE>
Decision: HANDOFF
Reason: Der laufende Task war als Test-Oracle/Config/Scope-X klassifiziert, Evidence zeigt aber echten Produktbug oder andere Task-Identitaet. Backlog-Routing muss vor neuer Ausfuehrung korrigiert werden.
Copy Prompt:
@[/BACKLOG SKILL 3 – EXECUTION HANDOFF]

Mode: DASHBOARD_PREP
Backlog Items:
BACKLOG-XXX

Neue Diagnose:
- <kurze Diagnose aus Skill 4>

Evidence:
- <konkrete Evidence-Pfade>

Ziel:
- Backlog Item neu klassifizieren.
- Routing reason/routing confidence aktualisieren.
- Neues oder aktualisiertes Task-Artefakt erzeugen.
- Entry Point und Recommended next skill neu setzen.
- Geaenderte Dateien und Out-of-Scope-Diffs pruefen.
```

**Beispiel → Skill 4 (nächster Task):**

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 4 – EXECUTIONER
Canonical State: HANDOFF
Required Artifacts: Spec, Task-Datei, nächste Target Task ID, Assigned Model
Evidence Paths: <Auto-Verification PASS Pfade des abgeschlossenen Tasks>
Failure Code: N/A
Changed Files: <geänderte Dateien>
Decision: HANDOFF
Reason: Weitere Tasks in derselben Task-Datei offen
Copy Prompt: @[/SKILL 4 – EXECUTIONER] mit neuem Target Task …
```

**Beispiel → Skill 6 (nach User „Manueller Test erfolgreich.“** — nur in **folgender** Nachricht):

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 6 – DIAMANTSTANDARD FINAL AUDIT
Canonical State: HANDOFF
Required Artifacts: Compact Audit Package (Spec, Task, Pre-Check, Diff, Tests, Auto-Verification PASS, User-Sign-off)
Evidence Paths: <Auto-Verification PASS, Gesamtvalidierung, User-Sign-off Evidence>
Failure Code: N/A
Changed Files: <geänderte Dateien>
Decision: HANDOFF
Reason: Spec-Umsetzung vollständig validiert; User hat UX-Sign-off gegeben
Copy Prompt: @[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT] …
```

**Beispiel → Skill 6 (Backlog-Item nach vollstaendiger Auto-Verification PASS):**

Backlog-Tasks muessen bei Erfolg ebenfalls einen Skill-6-Handover erzeugen. Nicht erlaubt ist
die Aussage, Skill 6 sei fuer Backlog-Items nicht erforderlich.

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 6 – DIAMANTSTANDARD FINAL AUDIT
Canonical State: HANDOFF
Required Artifacts: Backlog Item, Task, Diff, Tests, Auto-Verification PASS, Retest Evidence, Dashboard-Sync
Evidence Paths: <Auto-Verification PASS>, <TestResultJson oder Retest Evidence>, <changed files>
Failure Code: N/A
Changed Files: <geänderte Dateien>
Decision: HANDOFF
Reason: Backlog-Task vollständig implementiert und durch Auto-Verification/Retest Evidence validiert.
Copy Prompt:
@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT] mit folgenden Artefakten:
Backlog Item: <BACKLOG-XXX>
Target Task: <task id>
Task: <task file>
Changed Files:
- <files>
Auto-Verification: PASS
Retest Evidence: <paths>
Dashboard Sync: PASS
```

**Beispiel → Skill 3 (Pre-Check erneut):**

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 3 – PRE-IMPLEMENTATION VERIFICATION
Canonical State: NEEDS_INFO | BLOCKED
Required Artifacts: korrigierte Task-Datei / Spec
Evidence Paths: N/A WITH REASON: Artefakte sind vor Ausführung ungültig
Failure Code: N/A
Changed Files: NONE
Decision: NEEDS_INFO | BLOCKED
Reason: Artefakte/Task-Struktur ungültig für Ausführung
Copy Prompt: @[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION] …
```

---

## GPT-5.5 Eskalation

Bei Mehrdeutigkeit, Scope-Konflikt oder nicht-deterministischer Umsetzbarkeit: **STOP**, `MODEL SWITCH REQUIRED: SWE 1.6 → GPT-5.5` mit kurzer Begründung und P2-Handover in neuen Chat mit GPT-5.5.
