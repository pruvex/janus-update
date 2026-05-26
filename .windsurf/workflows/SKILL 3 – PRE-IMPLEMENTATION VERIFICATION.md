---
description: Janus V3.2 - Skill 3 Pre-Implementation Verification. Validiert genau einen Task vor Skill 4 und erzeugt einen strikt formatierten Skill-4-Handover.
---

This skill follows the global rules in `documentation/pipeline/PIPELINE_CONTRACT.md`.

# SKILL 3 - PRE-IMPLEMENTATION VERIFICATION

## Critical Output Contract

Ein PASS ist nur gueltig, wenn der Output diese literal pruefbaren Zeilen enthaelt.
Fehlt eine Zeile, darf `PRE-CHECK PASSED` nicht ausgegeben werden.

Pflicht-Literale fuer jeden PASS:

```text
PRE-CHECK RESULT
PRE-CHECK PASSED
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

Verbotene PASS-Literale:

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
Stoppe nach Abschluss der Task
warte auf manuelle Janus-Validierung
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

Vor dem Antworten muss Skill 3 einen internen Self-Check machen:

- Sind alle Pflicht-Literale vorhanden?
- Ist keines der verbotenen PASS-Literale vorhanden?
- Beginnt der Copyblock exakt mit `BEGIN COPY FOR SKILL 4`?
- Endet der Copyblock exakt mit `END COPY FOR SKILL 4`?
- Ist `Automated Evidence Gate` vorhanden und nicht durch manuelle Pruefung ersetzt?
- Folgt auf `PRE-CHECK RESULT` direkt `PRE-CHECK PASSED`, ohne Zwischenzeile `PASSED`?
- Steht `PRE-CHECK PASSED` als eigene Literal-Zeile direkt unter `PRE-CHECK RESULT` und nicht in Prosa wie `Pre-Check Decision:`?
- Enthält `Automated Evidence Gate` Generator, Validator und Playwright als Pflichtkette ohne `alternativ`/`sofern`?
- Enthält `Automated Evidence Gate` keine Bedingung, die Generator/Validator/Playwright nur optional macht?
- Enthält der Skill-4-Copyblock keine Produktcode- oder Scope-Erweiterungs-Klausel fuer Test-Oracle-Tasks?
- Wenn die Oracle-vs-Produktanalyse einen echten Produktbug zeigt, muss Skill 4 BLOCKED/HANDOFF ausgeben, nicht den Scope erweitern.
- Steht der komplette Skill-4-Copyblock in einem einzigen fenced `text` Codeblock?
- Gibt es keine frei erfundene Kurzfassung wie `Regeln:`, `Hard Rules:` oder `Task Scope:` statt der Pflichtsektionen?
- Heisst das Modellfeld im Copyblock exakt `Assigned Model:` und nicht `Execution Model:`?
- Enthaelt der Output keine `Changed Files:` oder `Geaenderte Dateien:` Liste?
- Enthaelt der Output keine neu erzeugten TestPlan/TestResult-Artefakte als Precheck-Fakt?
- Bei TestSpec-/Oracle-Tasks: routet der Skill-4-Handover nach der TestSpec-Aenderung zu TEST SKILL 1 und behauptet keine TestRun-Artefakte im selben Skill-4-Lauf?

Wenn irgendein Punkt fehlschlaegt, muss Skill 3 den PASS verwerfen und stattdessen ausgeben:

```text
PRE-CHECK BLOCKED: SKILL-4-HANDOVER-INCOMPLETE
```

---

## Rolle

Skill 3 ist ein reines Pre-Implementation-Gate.

Er entscheidet nur:

```text
PRE-CHECK PASSED
PRE-CHECK FAILED
PRE-CHECK BLOCKED
MODEL SWITCH REQUIRED
```

Keine Implementierung. Keine Codeaenderung. Keine Architekturentscheidung. Kein neuer Scope.

### Precheck Artifact-Mutation Guard (HARD)

Skill 3 darf im PASS-Output niemals behaupten, dass Implementierungs-, TestPlan- oder TestResult-Dateien bereits geaendert oder neu erzeugt wurden.

Verboten im Skill-3-Output:

```text
Changed Files:
Geaenderte Dateien:
documentation/test-runs/<...>_plan.json (neu)
documentation/test-results/<...>_results.json (neu)
TestRun ausgefuehrt
TestPlan neu generiert
Implementation Complete
```

Erlaubt ist nur:

```text
Expected Files:
- <Dateien, die Skill 4 voraussichtlich aendern darf>
Evidence To Produce:
- <Artefakte, die nach Skill 4 oder in der Test-Pipeline entstehen muessen>
```

Wenn Skill 3 erkennt, dass ein Task mehrere Pipeline-Phasen enthaelt, muss er den Skill-4-Handover auf die erste tatsaechlich ausfuehrbare Aenderung begrenzen. Nachgelagerte Phasen wie TestPlan-Generierung, Live-TestRun, Finding-Triage oder Audit muessen als Post-Execution-Handover benannt werden, nicht als Skill-4-Ausfuehrungsscope.

Wenn der Skill-4-Handover TestRun-/TestResult-Artefakte als bereits geaendert oder im selben Skill-4-Lauf zu erzeugen beschreibt, ist der PASS ungueltig:

```text
PRE-CHECK BLOCKED: PHASE_BOUNDARY_VIOLATION
```

---

## Input

Minimaler Aufruf:

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]

Target Task: <task id>
Task: documentation/tasks/<task_file>.md
Spec: <spec path | N/A WITH REASON>
Backlog Item: <optional BACKLOG-XXX>
Mode: SINGLE_TASK_PRECHECK
Execution Model: <SWE 1.6 | Kimi k2.5 | GPT-5.5>
```

Wenn eine Task-Datei mehrere Tasks enthaelt, ist `Target Task` Pflicht.

---

## Validation Gates

Skill 3 muss pruefen:

- Task-Datei existiert und ist lesbar.
- Target Task ist eindeutig.
- Spec existiert oder `Spec: N/A WITH REASON` ist plausibel.
- Backlog-Referenz ist konsistent, falls vorhanden.
- Bei `Backlog Item: BACKLOG-XXX` muss die Task-Datei exakt denselben ID-Token enthalten. `BACKLOG_XXX`
  statt `BACKLOG-XXX` ist ein Artefakt-Identitaetsfehler.
- Wenn `documentation/backlog/BACKLOG.md` fuer das Backlog-Item ein `Handoff`-Feld enthaelt, muss
  der Input-`Task:` exakt diesem Pfad entsprechen.
- Wenn die Task-Datei nicht existiert, darf Skill 3 keinen PASS ausgeben und keine Precheck-Findings
  aus einem erfundenen oder aehnlich benannten Pfad ableiten.
- Assigned Model ist im Task oder Input eindeutig.
- Scope ist atomar.
- IN SCOPE und OUT OF SCOPE sind klar.
- Acceptance Criteria sind messbar.
- Risiko ist LOW, MEDIUM oder HIGH.
- Betroffene Dateien / Artefakte sind benannt oder aus dem Task deterministisch ableitbar.
- Keine offenen Produkt- oder Architekturentscheidungen.
- Keine Provider-Fallbacks oder Scope-Erweiterungen.

Pflicht-Blocker bei Pfad-/ID-Mismatch:

```text
PRE-CHECK BLOCKED: ARTIFACT_IDENTITY_MISMATCH

Reason:
- Backlog Item, Target Task, Task path or BACKLOG.md Handoff path do not match.

Required Fix:
- Use the exact Handoff path from documentation/backlog/BACKLOG.md.
```

Bei Test-Oracle-, Assertion-, `containsAny`-, `mustNotContain`- oder Response-Format-Aufgaben muss Skill 3 zusaetzlich pruefen:

- Ist das beobachtete Produktverhalten fachlich valide?
- Ist der Test-Oracle moeglicherweise zu eng?
- Ist `ASSERTION_ORACLE_TOO_NARROW` plausibel?
- Ist der erste Implementierungsschritt Oracle-vs-Produktverhalten, bevor Produktcode geaendert wird?

### TestSpec-/Oracle-Task Boundary (HARD)

Wenn der Target Task eine TestSpec-, TestPlan-, Test-Oracle-, Assertion-, `containsAny`-, `mustNotContain`- oder Response-Format-Anpassung ist, gelten zusaetzlich:

- Skill 3 MUSS die dauerhafte Source-of-Truth-TestSpec bestimmen. Fuer Janus-Testpipeline-Oracle-Fixes ist das normalerweise `documentation/TEST_SPEC/*.md`.
- Skill 4 darf nur die konkrete Source-of-Truth-TestSpec/Oracle-Datei aendern.
- Skill 4 darf keine bestehenden `documentation/test-runs/*_plan.json` manuell patchen.
- Alte `documentation/test-runs/*_plan.json` Dateien duerfen nur als Evidence, Baseline oder Reference Plan im Handover genannt werden.
- Skill 4 darf keine `documentation/test-results/*` manuell erzeugen oder als PASS-Evidence behaupten.
- Nach der TestSpec-Aenderung muss Skill 4 einen Handover zu `TEST SKILL 1 - TESTSPEC TO TEST PLAN` ausgeben.
- Der neue TestPlan muss durch TEST SKILL 1 aus der aktualisierten TestSpec entstehen.
- Live-TestRun und Ergebnisvalidierung muessen danach durch TEST SKILL 2/3/4 der Test-Pipeline laufen.

Ein Skill-4-Handover fuer solche Tasks ist ungueltig, wenn er `TestPlan neu generieren`, `TestRun ausfuehren`, `Ergebnisse validieren` oder aehnliche spaetere Pipeline-Schritte als Skill-4-Scope ausgibt.

Wenn der Task als Primary File nur einen alten `documentation/test-runs/*_plan.json` nennt,
muss Skill 3 `PRE-CHECK BLOCKED: TESTSPEC_SOURCE_OF_TRUTH_MISSING` ausgeben, ausser er kann
aus Spec/Backlog/TestPlan eindeutig eine `documentation/TEST_SPEC/*.md` Source-of-Truth ableiten
und den Skill-4-Handover entsprechend korrigieren.

---

### TestRun-Finding Handover Gate (HARD)

Wenn der Target Task aus einem TestRun-Finding stammt (`Backlog Item: BACKLOG-XXX` mit `Quelle: TestRun`,
`TestRun: TEST-RUN-...`, Evidence-Pfad oder fehlgeschlagenem TestCase), muss der Skill-4-Copyblock
die TestRun-Identitaet und Evidence explizit enthalten.

Pflichtfelder im Skill-4-Copyblock:

```text
Failed TestCase:
Evidence:
Failure:
Source TestRun:
Provider Isolation:
Focused Retest:
```

Regeln:

- `Failed TestCase` muss die konkrete TestCase-ID oder eine kommagetrennte Liste enthalten.
- `Evidence` muss auf vorhandene Evidence-Dateien zeigen, z. B. `documentation/test-results/<run>/<case>_evidence.json`.
- `Failure` muss den beobachteten Fehler kurz beschreiben, nicht nur den Backlog-Titel wiederholen.
- `Provider Isolation` muss bei Provider-spezifischen Findings ausdruecklich `NO_PROVIDER_FALLBACK` enthalten.
- `Focused Retest` muss den minimalen Retest nennen, der nach Skill 4 erwartet wird, z. B. `TC-002-GEMINI`.
- Bei Gemini/GPT-Providerfehlern muss der Skill-4-Handover ausdruecklich verbieten, den Fehler durch einen anderen Provider oder ein anderes Modell zu kaschieren.
- Wenn diese Felder nicht sicher aus Task/Backlog/Evidence ableitbar sind, darf Skill 3 keinen PASS ausgeben und muss `PRE-CHECK BLOCKED: TESTRUN_FINDING_HANDOVER_INCOMPLETE` melden.

Verbotene TestRun-Finding-Handover:

```text
Implementiere Fix gemäß Akzeptanzkriterien.
Führe erforderliche Tests durch.
Keine Scope-Erweiterung.
```

ohne `Failed TestCase`, `Evidence`, `Failure`, `Provider Isolation` und `Focused Retest`.

---

### Analysis-/Documentation Subtask Handover Gate (HARD)

Wenn `Target Subtask` oder Task-Ziel eine Analyse-, Dokumentations-, Read-only- oder Discovery-Arbeit ist,
darf Skill 3 keinen Kurz-Handover zu Skill 4 ausgeben.

Der Skill-4-Copyblock muss zusaetzlich enthalten:

```text
Target Subtask:
Subtask Type: ANALYSIS_ONLY | DOCUMENTATION_ONLY | READ_ONLY
Allowed Write Scope:
Required Deliverable:
Remaining Subtasks:
Completion Rule:
```

Regeln:

- Wenn der Subtask Findings dokumentieren soll, ist `Files to Modify: None` falsch. Dann muss
  `Allowed Write Scope` mindestens die Task-/Analyse-Artefaktdatei nennen, z. B.
  `documentation/tasks/<task>.md`.
- Wenn wirklich kein Schreibzugriff erlaubt ist, muss `Required Deliverable` `NO_FILE_CHANGES` nennen
  und Skill 4 darf nicht behaupten, Findings in einer Datei zu dokumentieren.
- `Remaining Subtasks` muss alle noch offenen Subtasks nennen oder `NONE`.
- `Completion Rule` muss sagen, wann Skill 4 nach der Analyse stoppen und welchen naechsten Handoff
  erzeugen soll.

Verboten fuer Analysis-/Documentation-Subtasks:

```text
@[/SKILL 4 – EXECUTIONER]
Spec: <path>
Task: <path>
Execution Model: SWE 1.6
Target Subtask: <id>
Remaining Subtasks: <ids>
```

ohne `Allowed Write Scope`, `Required Deliverable`, `Rules` und `Expected Output`.

---

### Live E2E Validation Subtask Gate (HARD)

Wenn ein Target Task/Subtask als Ziel `Live E2E`, `Playwright`, `TestRun`, `TEST-RUN-...`,
`INFRASTRUCTURE_OFFLINE`-Validierung, `BACKLOG-047`-Retest oder `TestResult artifacts` nennt,
darf Skill 3 keinen kurzen Skill-4-Handoff ausgeben.

Solche Subtasks sind keine Produktimplementation. Sie muessen ueber die Testpipeline validiert werden.

Zulaessige Ausgaenge:

1. Direkter Copy-Handoff zu `TEST SKILL 3 – LIVE JANUS TEST EXECUTION`, wenn ein valider TestPlan
   vorhanden ist und keine Codeaenderung mehr erforderlich ist.
2. Vollstaendiger `BEGIN COPY FOR SKILL 4`-Block, wenn Skill 4 zuerst ein Handoff-Artefakt oder eine
   Dokumentation erzeugen muss. Dann muss `Completion Rule` ausdruecklich zu `TEST SKILL 3` routen.

Verboten:

```text
SKILL 4 Handoff
@[/SKILL 4 – EXECUTIONER]
Spec: <path>
Task: <path>
Execution Model: SWE 1.6
Target Subtask: <id>
Previous Subtask: <id>
Remaining Subtasks: None (final subtask)
```

Wenn `Remaining Subtasks: None`, `final subtask` und `TestRun`/`Playwright` im Precheck vorkommen,
muss Skill 3 bevorzugt diesen direkten Testpipeline-Handoff ausgeben:

```text
@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION] Mode=LIVE_RETEST; ExecutionModel=SWE_1_6; TestSpec=<testspec path>; TestPlan=<plan path>; TargetTestRun=<TEST-RUN-ID>; SourceBacklog=<BACKLOG-XXX>; SourceTask=<task id>; SourceSubtask=<subtask id>; RetestReason=<reason>; ChangedFiles=<changed files>; FocusTestCase=<case id or N_A>; ConnectivityMode=PLAYWRIGHT_WEBSERVER_AUTOSTART; ManualJanusStartRequired=NO; Rules=USE_EXISTING_TESTPLAN_EXECUTE_LIVE_RETEST_COLLECT_EVIDENCE_NO_IMPLEMENTATION_NO_CURL_DASH_S_NO_FINDING_TRIAGE_ON_INFRA_BLOCKER; ExpectedOutput=TEST_RESULT_PLUS_SINGLE_LINE_HANDOFF_TO_TEST_SKILL_4_WITH_METRICS_OR_SKILL5_INFRA_BLOCKER
```

Wenn kein TestPlan vorhanden ist, muss Skill 3 zu `TEST SKILL 1 – TESTSPEC TO TEST PLAN` routen
oder blocken mit `PRE-CHECK BLOCKED: LIVE_E2E_TESTPLAN_MISSING`.

---

## Pass/Block Rules

`PRE-CHECK PASSED` ist nur erlaubt, wenn:

- alle Validation Gates bestanden sind,
- genau ein Target Task freigegeben wird,
- der Skill-4-Copyblock vollstaendig nach dem Template unten ausgegeben wird.
- der Skill-4-Copyblock exakt mit `BEGIN COPY FOR SKILL 4` beginnt und exakt mit `END COPY FOR SKILL 4` endet.
- der Skill-4-Copyblock `Target Task`, `Target Subtask`, `Task`, `Spec`, `Backlog Item`, `Assigned Model`, `Mode`, `Pre-Check Context`, `Scope-Regel`, `Automated Evidence Gate`, `Artifact Identity Check`, `Completion Rule` und `Expected Output` enthaelt.

Wenn der Skill-4-Copyblock nicht vollstaendig ausgegeben werden kann:

```text
PRE-CHECK BLOCKED: SKILL-4-HANDOVER-INCOMPLETE
```

Verboten nach `PRE-CHECK PASSED`:

```text
SKILL 4 Handoff
@[/SKILL 4 – EXECUTIONER]
Spec: <path>
Task: <path>
Execution Model: SWE 1.6
Target Subtask: <id>
Previous Subtask: <id>
Remaining Subtasks: <ids>
```

```text
@[/SKILL 4 – EXECUTIONER]
Spec:
Task:
Execution Model:
Target Subtask:
```

Solche Kurz-Handoffs muessen als `PRE-CHECK BLOCKED: SKILL-4-HANDOVER-INCOMPLETE`
behandelt oder durch den vollstaendigen `BEGIN COPY FOR SKILL 4`-Block ersetzt werden.

Wenn der Task nicht deterministisch validierbar ist:

```text
MODEL SWITCH REQUIRED: SWE 1.6 -> GPT-5.5
```

---

## Verbotene Skill-4-Handover

Ein Skill-4-Handover ist ungueltig, wenn er eines davon enthaelt:

- `Stoppe ... und warte auf manuelle Janus-Validierung`
- `Manual Janus Validation Gate`
- `Stop at Manual Janus Validation Gate`
- `PRE-CHECK RESULT: PASSED`
- `PRE-CHECK ERGEBNIS`
- `Pre-Check Decision:`
- `Pre-Check Decision: PRE-CHECK PASSED`
- eine alleinstehende `PASSED` Zeile zwischen `PRE-CHECK RESULT` und `PRE-CHECK PASSED`
- `Skill 4 Handover`
- `BEGIN COPY FOR @[/SKILL 4`
- `Regeln:` als Ersatz fuer `Scope-Regel:`
- `Aufgaben:` als Ersatz fuer `Pre-Check Context:`
- `Hard Rules:` als Ersatz fuer `Scope-Regel:`
- `Task Scope:` als Ersatz fuer `Pre-Check Context:`
- `Risiko:` als Ersatz fuer `Risk:` im `Pre-Check Context`
- `Execution Model:` als Ersatz fuer `Assigned Model:`
- `Changed Files:`
- `Geaenderte Dateien:`
- `TestPlan neu generieren`
- `TestRun ausfuehren`
- `Ergebnisse validieren`
- `documentation/test-runs/`
- `documentation/test-results/`
- `Führe alle im Task spezifizierten Validierungen`
- `Fuehre alle im Task spezifizierten Validierungen`
- `alternativ JSON-Schema`
- `sofern Generator/Validator`
- `sofern Generator`
- `Generator/Validator/Playwright-Run nur wenn`
- `nur wenn Task nicht`
- `nur wenn der Task nicht`
- `außer wenn Analyse echten Bug zeigt`
- `ausser wenn Analyse echten Bug zeigt`
- `Produktcode fixen`
- `Produktcode-Fix`
- `Scope erweitern`
- `Scope-Erweiterung`
- `Wenn ungültig:`
- `Wenn ungueltig:`
- ein manuelles Gate als Ersatz fuer automatisierte Evidence
- keinen exakten `Pre-Check: PRE-CHECK PASSED` Eintrag
- keinen `Pre-Check Context`
- keinen `Automated Evidence Gate`
- keinen exakten Playwright-Befehl mit `--reporter=list`
- keinen `Artifact Identity Check`
- bei Oracle-/Assertion-Problemen keine Oracle-/TestPlan-Regel

Optionaler Produkt-Smoke ist nur nach automatischer Evidence erlaubt. Er ist nie das Abschlussgate.

---

## Output Bei PASS

Der Output bei PASS muss exakt diese Hauptstruktur verwenden:

```text
SKILL 3 - PRE-IMPLEMENTATION VERIFICATION

Artifact Validation
Task File: <task path>
Target Task: <target task id>
Mode: SINGLE_TASK_PRECHECK
Execution Model: <model>

Verification Results
- ARTIFACT VALIDITY: PASS
- SCOPE CLARITY: PASS
- FILE ACCESSIBILITY: PASS
- RISK ASSESSMENT: PASS
- ACCEPTANCE CRITERIA: PASS
- DEPENDENCIES: PASS
- ORACLE CHECK: PASS | N/A

PRE-CHECK RESULT
PRE-CHECK PASSED

<one short summary>

BEGIN COPY FOR SKILL 4
@[/SKILL 4 - EXECUTIONER] mit folgenden Artefakten:

Target Task: <target task id>
Target Subtask: <subtask id | N/A>
Task: <task file path>
Spec: <spec path | N/A WITH REASON - Backlog-Task ohne Spec>
Assigned Model: <SWE 1.6 | Kimi k2.5 | GPT-5.5>
Mode: SINGLE_TASK_EXECUTION

Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Target Task: <target task id>
- Target Subtask: <subtask id | N/A>
- Ziel: <kurz>
- Subtask Type: <IMPLEMENTATION | ANALYSIS_ONLY | DOCUMENTATION_ONLY | READ_ONLY>
- Risk: LOW | MEDIUM | HIGH
- Scope: <kurzer Scope>
- Files: <validierte Dateien/Artefakte>
- Allowed Write Scope: <konkrete Dateien oder NO_FILE_CHANGES>
- Required Deliverable: <konkretes Ergebnisartefakt>
- Remaining Subtasks: <ids oder NONE>
- Assigned Model: <SWE 1.6 | Kimi k2.5 | GPT-5.5>

Scope-Regel:
- Nutze die Task-Datei als Single Source of Truth.
- Implementiere ausschliesslich den angegebenen Target Task.
- Wenn `Subtask Type` ANALYSIS_ONLY/DOCUMENTATION_ONLY/READ_ONLY ist: Keine Produktcode-Aenderungen; schreibe nur in `Allowed Write Scope`.
- Keine Scope-Erweiterung.
- Keine spaeteren Tasks im selben Lauf.
- Bei Test-Oracle-Tasks: Keine Produktcode-Changes. Wenn die Analyse einen echten Produktbug statt Oracle-Problem zeigt, STOP mit BLOCKED/HANDOFF, nicht im selben Lauf fixen.

Automated Evidence Gate:
- Nach Implementierung: JSON-/Schema-Validierung, Generator, Validator und Playwright ausfuehren.
- Generator-Pflicht: `node tests/e2e/generator/generate-live-runner.mjs --plan <plan> --out <runner>`
- Validator-Pflicht: `node tests/e2e/generator/validate-runner.mjs --plan <plan> --runner <runner>`
- Playwright-Befehl muss exakt `npx playwright test <runner> --headed --workers=1 --reporter=list` enthalten.
- Schema-/Generator-/Validator-Fehler sind BLOCKED/FAIL mit Evidence, aber kein Grund, Playwright als optionalen Ersatzpfad zu formulieren.
- Optionaler Produkt-Smoke ist nur nach Auto-Verification PASS erlaubt und kein Ersatz fuer automatisierte Evidence.
- Kein TASK COMPLETE ohne Auto-Verification PASS oder explizites BLOCKED/NEEDS_INFO mit Evidence.
- Bei TestSpec-/Oracle-Tasks: Skill 4 fuehrt nur die TestSpec-Aenderung aus und darf keinen bestehenden TestPlan manuell patchen. Danach muss Skill 4 einen Copy-Handover zu TEST SKILL 1 ausgeben, damit Generator, Validator und Playwright in der Test-Pipeline aus dem neuen TestPlan laufen.
- Bei TestSpec-/Oracle-Tasks darf Skill 4 keinen TestRun, keine TestResult-Datei und keinen PASS aus Live-Evidence behaupten.
- Bei TestSpec-/Oracle-Tasks ist ein alter `documentation/test-runs/*_plan.json` nur Reference/Baseline. Wenn keine `documentation/TEST_SPEC/*.md` Source-of-Truth im Handover steht, ist PASS verboten.
- Bei TestSpec-/Oracle-Tasks muss der Skill-4-Handover fuer TEST SKILL 1 exakt `TestSpec:` verwenden, nicht `Spec:`.
- Bei TestSpec-/Oracle-Tasks muss der Skill-4-Handover nach TEST SKILL 1 als Expected Output `Copy-Handover zu TEST SKILL 2 - TEST RUN PRECHECK` verlangen. Ein direkter Expected Output zu TEST SKILL 3 ist ungueltig.
- Skill 3 darf in einem TestSpec-/Oracle-Skill-4-Handover keinen konkreten naechsten `TEST-RUN-...` als Ziel vorgeben; TEST SKILL 1 bestimmt die naechste freie Nummer.
- Bei Analysis-/Documentation-Subtasks: Kein Playwright-/Generator-Zwang, wenn `Required Deliverable` reine Analyse-Dokumentation ist; stattdessen muss Skill 4 das Deliverable schreiben und danach mit naechstem Subtask-Handoff stoppen.

Artifact Identity Check:
- Plan Path:
- Plan testRunId:
- Runner Path:
- Runner internal testRunId / describe title:
- Executed Playwright Path:
- Identity Result: PASS | FAIL

Oracle-/TestPlan-Regel:
- Wenn der Task ein Test-Oracle-, Assertion-, containsAny-, mustNotContain- oder Response-Format-Problem betrifft, muss Skill 4 zuerst Oracle-vs-Produktverhalten bestaetigen.
- Wenn das Produktverhalten fachlich gueltig ist: Source-of-Truth-TestSpec/Oracle anpassen, nicht Produktcode und nicht nur einen alten TestPlan.
- Wenn das Produktverhalten fachlich nicht gueltig ist: BLOCKED/HANDOFF mit Evidence und neuem Scope, nicht Produktcode im Oracle-Task aendern.
- Wenn eine TestSpec geaendert wurde: Handover zu `@[/TEST SKILL 1 - TESTSPEC TO TEST PLAN]` mit der aktualisierten TestSpec ausgeben. Kein direkter Handover zu TEST SKILL 3 oder TEST SKILL 5.
- Der Handover zu `@[/TEST SKILL 1 - TESTSPEC TO TEST PLAN]` muss `TestSpec:` enthalten und als `Expected Output` TEST PLAN CREATED, TESTPLAN VALID und Copy-Handover zu TEST SKILL 2 verlangen.

Completion Rule:
- <wann Skill 4 stoppen muss und welcher naechste Handoff erwartet wird>

END COPY FOR SKILL 4
```

Der Copyblock darf nicht frei umformuliert werden. Nur Platzhalter duerfen ersetzt werden.

Der Skill-4-Copyblock muss als ein einziger grauer Copy-Kasten ausgegeben werden:

````text
```text
BEGIN COPY FOR SKILL 4
@[/SKILL 4 - EXECUTIONER] mit folgenden Artefakten:
...
END COPY FOR SKILL 4
```
````

Ungueltige Kurzform, die bei PASS verboten ist:

```text
BEGIN COPY FOR SKILL 4
@[/SKILL 4 – EXECUTIONER] mit folgenden Artefakten:

Spec: N/A (Backlog-Task ohne Spec)
Task: documentation/tasks/...
Target Task: ...
Mode: SINGLE_TASK_EXECUTION
Execution Model: SWE 1.6

Regeln:
- Nutze Task und Spec als einzige Quelle
- Implementiere exakt den definierten Scope
- Führe alle im Task spezifizierten Validierungen aus
```

Warum verboten: Diese Kurzform verliert `Pre-Check Context`, `Automated Evidence Gate`,
`Artifact Identity Check`, Oracle-Regel und das Abschlussliteral `END COPY FOR SKILL 4`.

Ebenfalls verboten ist diese scheinbar bessere, aber weiterhin unvollstaendige Form:

```text
BEGIN COPY FOR SKILL 4
@[/SKILL 4 – EXECUTIONER] mit folgenden Artefakten:

Spec: N/A (Backlog-Task ohne Spec)
Task: documentation/tasks/...
Target Task: ...
Mode: SINGLE_TASK_EXECUTION
Execution Model: SWE 1.6

Hard Rules:
- ...

Task Scope:
IN SCOPE: ...
OUT OF SCOPE: ...

Risiko: LOW
```

Warum verboten: `Hard Rules`, `Task Scope`, `Risiko` und `Execution Model` sind freie
Umformulierungen. Gueltig sind nur `Assigned Model`, `Pre-Check Context`, `Scope-Regel`,
`Automated Evidence Gate`, `Artifact Identity Check` und `Oracle-/TestPlan-Regel`.

Unmittelbar vor dem Senden muss Skill 3 die Pflicht-Literale aus `Critical Output Contract`
gegen den eigenen Output pruefen. Wenn der Skill die Vorlage kuerzt, umbenennt oder frei
umformuliert, ist das Ergebnis automatisch `PRE-CHECK BLOCKED: SKILL-4-HANDOVER-INCOMPLETE`.

---

## Output Bei Blocked/Failed

Auch bei `PRE-CHECK BLOCKED`, `PRE-CHECK FAILED`, `NEEDS_INFO` oder `MODEL SWITCH REQUIRED`
muss Skill 3 immer einen einzelnen grauen `text` Copy-Kasten ausgeben. Freier Fliesstext mit
`Copy Prompt:` ist ungueltig, wenn der Copy Prompt nicht zusaetzlich als kopierbarer fenced
`text` Block wiederholt wird.

Pflichtregeln fuer Blocked/Failed-Handoffs:

- Der letzte relevante Handover der Antwort MUSS in genau einem fenced Codeblock mit Info-String
  `text` stehen.
- Der graue Block MUSS direkt mit dem Ziel-Skill-Trigger beginnen, z. B. `@[/SKILL 2 ...]`,
  `@[/BACKLOG SKILL 3 ...]`, `@[/SKILL 5 ...]` oder `@[/SPEC SKILL 1 ...]`.
- `NEXT_SKILL_HANDOFF` darf oberhalb als Diagnose erscheinen, ersetzt aber niemals den grauen
  Copyblock.
- Wenn der Ziel-Skill nicht sicher bestimmbar ist, muss der graue Block ein `@[/SKILL 3 ...]`
  Re-Run-Handover mit Required Fix enthalten.
- Skill 3 darf nicht mit einer nackten Zeile `Copy Prompt: @[/...]` enden.
- Wenn kein grauer Copyblock erzeugt werden kann, muss die Antwort lauten:
  `PRE-CHECK BLOCKED: COPY_HANDOVER_MISSING`.

```text
PRE-CHECK BLOCKED | PRE-CHECK FAILED

Reason:
- <konkreter Grund>

Required Fix:
- <konkreter naechster Schritt>

NEXT_SKILL_HANDOFF
Target Skill:
Canonical State: BLOCKED | NEEDS_INFO | ESCALATED
Required Artifacts:
Evidence Paths:
Failure Code:
Changed Files: NONE
Decision:
Reason:
Copy Prompt:
```

Direkt danach MUSS der kopierbare Block folgen:

```text
@[/<TARGET SKILL>]
<vollstaendige Artefakte und Regeln fuer den naechsten Lauf>
```

---

## Output Guarantee

Skill 3 ist:

- deterministic
- validation-only
- single-task-only
- artifact-bound
- non-implementing
- no-manual-bypass
- Skill-4-handover-template-strict
