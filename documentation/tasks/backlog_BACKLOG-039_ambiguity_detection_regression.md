# TASK: BACKLOG-039 – Ambiguity-Detection Regression Fix

## TASK IDENTITY

- Task ID: backlog_BACKLOG-039_ambiguity_detection_regression
- Backlog Item: BACKLOG-039
- Titel: Ambiguity-Detection Regression: Keine Klärungsfragen bei ambigen Anfragen
- Typ: BUG
- Status: READY
- Erstellt: 2026-05-14
- Assigned Model: SWE 1.6

## TASK CONTEXT

Follow-up zu BACKLOG-037 (DONE). TASK-037-02 implementierte Context-Isolation für Gemini bei ambigen Anfragen (confidence>=0.6) in execution_dispatcher.py. BACKLOG-039 wurde ursprünglich als Test-Oracle-Problem klassifiziert, aber Skill 4 Test-Oracle-Fix zeigte einen Produktbug: Sowohl GPT als auch Gemini stellen bei ambigen Prompts keine Klärungsfragen mehr, sondern greifen direkt auf Memory/Context zu.

## PROBLEM ANALYSIS

**Diagnose:** PRODUCTBUG_DETECTED in Ambiguity-Detection / Context-Isolation

**Aktuelle Antworten (Playwright TestRun 2026-05-14):**
- TC-005 (GPT, Prompt "Ich brauche Infos dazu"): "Die Infos dazu sind:" (direkte Informationsbereitstellung aus Memory/Context)
- LTC-002 (Gemini, Prompt "Ich brauche Infos"): "Basierend auf den vorliegenden Daten aus deinem Speicher kann ich dir folgende Informationen geben:" (direkte Informationsbereitstellung aus Memory/Context)

**Erwartetes Verhalten (laut TASK-037-02 Fix):**
- Bei ambigen Anfragen mit confidence>=0.6 sollte eine Klärungsfrage gestellt werden
- Context-Isolation sollte aktiviert sein (Memory/Context deaktiviert)
- Keine Tool-Ausführung bei Ambiguity-Detection

**Analyse:**
- TASK-037-02 Fix scheint nicht korrekt zu funktionieren oder Regression aufgetreten
- Context-Isolation Logik in execution_dispatcher.py wird nicht korrekt angewendet
- Memory/Context wird nicht deaktiviert bei Ambiguity-Detection
- Sowohl GPT als auch Gemini sind betroffen (Provider Parity Problem)

## TASK SCOPE

**IN SCOPE:**
1. Ursachenanalyse in execution_dispatcher.py (TASK-037-02 Fix Regression?)
2. Prüfung ob Context-Isolation bei Ambiguity-Detection korrekt aktiviert wird
3. Prüfung ob Memory/Context bei Ambiguity korrekt deaktiviert wird
4. Fix der Context-Isolation Logik für beide Provider (GPT und Gemini)
5. Validation mit TC-005 und LTC-002 nach Fix

**OUT OF SCOPE:**
1. Test-Oracle Änderungen (bereits als vorbereitende TestPlan-Anpassung durchgeführt)
2. Änderungen an anderen TestCases
3. Änderungen an Ambiguity-Detection Logic außerhalb execution_dispatcher.py

## ACCEPTANCE CRITERIA

- [ ] Ambiguity-Detection stellt Klärungsfragen bei ambigen Prompts (confidence>=0.6)
- [ ] Context-Isolation wird korrekt aktiviert bei Ambiguity-Detection
- [ ] Memory/Context wird korrekt deaktiviert bei Ambiguity-Detection
- [ ] Sowohl GPT als auch Gemini zeigen gleiches Verhalten (Provider Parity)
- [ ] TC-005 und LTC-002 bestehen mit Klärungsfragen
- [ ] Fix in TASK-037-02 bleibt stabil (keine Regression)

## IMPLEMENTATION STEPS

### Step 1: Ursachenanalyse execution_dispatcher.py
- TASK-037-02 Fix Code prüfen (Context-Isolation Logik)
- Prüfen ob `requires_clarification=True` korrekt persistiert wird
- Prüfen ob `context_isolation_mode='gemini_ambiguity_clarification'` korrekt gesetzt wird
- Prüfen ob `disable_tools=True` korrekt angewendet wird
- Prüfen ob Memory/Context (`memory_context_string`, fact coupons, active directives) korrekt deaktiviert wird

### Step 2: GPT Provider prüfen
- Prüfen ob Context-Isolation auch für GPT aktiviert werden muss
- Prüfen ob GPT bei ambigen Prompts gleiche Logik wie Gemini verwenden sollte
- Provider Parity sicherstellen

### Step 3: Fix implementieren
- Context-Isolation Logik korrigieren falls Bug gefunden
- Memory/Context Deaktivierung korrigieren falls Bug gefunden
- Fix für beide Provider (GPT und Gemini) implementieren

### Step 4: Validation
- TC-005 Test mit GPT ausführen
- LTC-002 Test mit Gemini ausführen
- Prüfen ob Klärungsfragen gestellt werden
- Prüfen ob Memory/Context nicht verwendet wird

## FILES TO CHECK

- backend/services/orchestrator/execution_dispatcher.py (TASK-037-02 Fix)
- backend/services/chat_orchestrator.py (Context-Handling)
- backend/services/memory/retrieval_service.py (Memory Context)
- documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json (TestPlan mit erweiterten Keywords - bereits angepasst)

## RISK ASSESSMENT

- **Risk:** MEDIUM - Core Ambiguity-Detection Logic betroffen
- **Impact:** HIGH - Beeinträchtigt User Experience bei ambigen Anfragen
- **Regression Risk:** MEDIUM - TASK-037-02 Fix könnte Regression haben

## DEPENDENCIES

- BACKLOG-037 (DONE) - TASK-037-02 Fix muss analysiert werden
- TC-005 Test-Evidence verfügbar
- LTC-002 Test-Evidence verfügbar

## NOTES

Test-Oracle-Erweiterung (semantisch valide Keywords in TEST-RUN-2026-05-12-001_plan.json) kann als vorbereitende TestPlan-Anpassung behalten werden, aber der eigentliche Fix muss im Produktcode erfolgen. Die TestPlan-Anpassung ist hilfreich für zukünftige Tests, aber löst nicht das aktuelle Produktproblem.

## EXECUTION MODEL

**Assigned Model:** SWE 1.6
**Reason:** Produktbug-Fix in execution_dispatcher.py erfordert Codebase-Verständnis und Backend-Integration, aber keine hochriskanten Security-Changes oder Electron/IPC-Änderungen.

## NEXT STEP

Run @[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION] mit folgenden Artefakten:

```text
@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]
Target Task: backlog_BACKLOG-039_ambiguity_detection_regression
Task: documentation/tasks/backlog_BACKLOG-039_ambiguity_detection_regression.md
Backlog Item: BACKLOG-039
Mode: SINGLE_TASK_PRECHECK
Execution Model: SWE 1.6
```

Nach erfolgreichem Precheck erzeugt Skill 3 den V3.2-Copyblock fuer Skill 4.
