# TASK: BACKLOG-039 – TC-005 Test-Oracle Fix

## TASK IDENTITY

- Task ID: backlog_BACKLOG-039_tc005_test_oracle_fix
- Backlog Item: BACKLOG-039
- Titel: TC-005 Ambiguous Request Regression: Antwortformat stimmt nicht mit Test-Erwartung überein
- Typ: BUG
- Status: READY
- Erstellt: 2026-05-14
- Assigned Model: SWE 1.6

## TASK CONTEXT

Follow-up zu BACKLOG-037 (DONE). Der Fix in TASK-037-02 implementierte Context-Isolation für Gemini bei ambigen Anfragen (confidence>=0.6) in execution_dispatcher.py. TC-005-GEMINI-RETEST (2026-05-14) PASS mit Antwort "Zu welchem Thema benötigen Sie Informationen?" - dies ist eine semantisch valide Klärungsfrage, enthält aber nicht die exakten erwarteten Keywords im TestPlan.

## PROBLEM ANALYSIS

**Diagnose:** ASSERTION_ORACLE_TOO_NARROW

**Aktuelle Test-Erwartungen (TEST-RUN-2026-05-12-001_plan.json, TC-005):**
- Prompt: "Ich brauche Infos dazu"
- Expected containsAny: ["Was genau", "Welche", "meinst du"]
- Expected requiresConfirmation: true
- Expected mustNotContain: ["tool_call", "function_call"]

**Tatsächliche Antwort (TC-005-GEMINI-RETEST, 2026-05-14):**
- Response: "Zu welchem Thema benötigen Sie Informationen?"
- Result: PASS
- Die Antwort ist eine semantisch valide Klärungsfrage
- Sie enthält "benötigen" und "Thema" aber nicht die exakten erwarteten Keywords

**Analyse:**
- Die Antwort "Zu welchem Thema benötigen Sie Informationen?" erfüllt das funktionale Ziel (Klärungsfrage stellen)
- Der Test-Oracle prüft auf exakte Phrase-Matching statt semantischer Validität
- Dies ist ein Test-Oracle-Problem, kein Produkt-Code-Bug
- Die Backend-Logic (execution_dispatcher.py) funktioniert korrekt

## TASK SCOPE

**IN SCOPE:**
1. Test-Oracle Analyse: Prüfen ob die tatsächliche Antwort fachlich gültig ist
2. Wenn Antwort fachlich gültig: TestPlan/Oracle anpassen (nicht Produktcode)
3. Test-Erwartungen erweitern auf semantisch valide Klärungsfragen
4. Validation: Angepasster TestPlan muss mit semantisch korrekten Antworten bestehen

**OUT OF SCOPE:**
1. Produktcode-Changes in execution_dispatcher.py (außer wenn Analyse zeigt echten Bug)
2. Änderungen an TASK-037-02 Fix
3. Änderungen an Ambiguity-Detection-Logic
4. Änderungen an anderen TestCases

## ACCEPTANCE CRITERIA

- [ ] Test-Oracle prüft semantische Validität statt exakter Phrase-Matching
- [ ] Test-Erwartungen sind mit dem tatsächlichen Response-Format konsistent
- [ ] Fix in TASK-037-02 bleibt stabil (keine Regression)
- [ ] TC-005 testet Klärungsverhalten, nicht exakte Formulierung
- [ ] Angepasster TestPlan validiert erfolgreich mit "Zu welchem Thema benötigen Sie Informationen?"

## IMPLEMENTATION STEPS

### Step 1: Oracle-vs-Produktverhalten Analyse
- Prüfen: Ist "Zu welchem Thema benötigen Sie Informationen?" eine fachlich gültige Klärungsfrage?
- Prüfen: Erfüllt die Antwort das funktionale Ziel (Ambiguity-Detection)?
- Prüfen: Gibt es andere valide Klärungsfragen, die nicht die exakten Keywords enthalten?
- Entscheidung: Test-Oracle anpassen oder Produktcode fixen?

### Step 2: TestPlan Anpassung (wenn Oracle zu eng)
- Datei: documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json
- TC-005 containsAny erweitern: ["Was genau", "Welche", "meinst du", "benötigen", "Thema", "beziehst du dich"]
- Oder: containsAny durch flexiblere semantische Prüfung ersetzen
- LTC-002 (Gemini) ebenfalls prüfen und anpassen wenn nötig

### Step 3: Validation
- Angepassten TestPlan lokal validieren
- Prüfen ob JSON-Schema-Validierung besteht
- Prüfen ob Generator-Service akzeptiert
- Generator/Validator/Playwright-Run mit `--reporter=list` ausführen, sofern der Task nicht vorab durch Schema/Generator blockiert.
- Artifact Identity Check dokumentieren: Plan Path, Plan testRunId, Runner Path, Runner internal testRunId / describe title, Executed Playwright Path, Identity Result.
- Manuelle Janus-Validierung ist nur optional ergänzend und ersetzt keine automatisierte Evidence.

## FILES TO CHECK

- documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json (TC-005, LTC-002)
- documentation/test-results/TEST-RUN-2026-05-14-002/TC-005-GEMINI-RETEST_evidence.json
- documentation/TEST_SPEC/02_intent_routing_real_user_requests.md (TC-005 definition)

## RISK ASSESSMENT

- **Risk:** LOW - Test-Oracle Anpassung, kein Produktcode-Change
- **Impact:** LOW - Nur Test-Erwartungen, keine User-Facing Changes
- **Regression Risk:** LOW - Backend-Logic bleibt unverändert

## DEPENDENCIES

- BACKLOG-037 (DONE) - TASK-037-02 Fix muss stabil bleiben
- TC-005 Test-Evidence verfügbar

## NOTES

Bei PRE_IMPLEMENTATION_VERIFICATION muss zuerst Oracle-vs-Produktverhalten geprüft werden, bevor Produktcode geändert wird. Wenn die Antwort fachlich gültig ist: TestPlan/Oracle anpassen, nicht Produktcode.

## EXECUTION MODEL

**Assigned Model:** SWE 1.6
**Reason:** Test-Oracle-Analyse und TestPlan-Anpassung erfordert Codebase-Verständnis und deterministische JSON-Änderungen, aber keine hochriskanten Integrationen oder Security-Changes.

## NEXT STEP

Run @[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION] with:
- Spec: N/A (Backlog-Task ohne Spec)
- Task: documentation/tasks/backlog_BACKLOG-039_tc005_test_oracle_fix.md
- Target Task: backlog_BACKLOG-039_tc005_test_oracle_fix
- Mode: SINGLE_TASK_PRECHECK
- Execution Model: SWE 1.6
