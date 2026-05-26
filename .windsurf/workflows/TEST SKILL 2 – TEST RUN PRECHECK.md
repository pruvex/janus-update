---
description: SWE 1.6 Test Pipeline Phase 2 â€“ Test Run Precheck Gate. Prueft, ob ein TestRun sicher und vollstaendig live in Janus ausgefuehrt werden darf. Keine Implementation.
---

# TEST SKILL 2 â€“ TEST RUN PRECHECK

## ðŸŽ¯ PURPOSE

Dieser Skill ist ein **harte Sicherheits- und Vollstaendigkeits-Gate** vor der Live-Test-Ausfuehrung.

Er entscheidet ausschliesslich:

â†’ DARF DER TESTRUN LIVE IN JANUS STARTEN?

KEINE IMPLEMENTATION. KEIN CODE. KEINE PLANUNG.

---

## ðŸ¤– DEFAULT MODEL

SWE 1.6

Ausnahme:
- GPT-5.5 nur bei unklarem Security-Scope oder nicht deterministisch bewertbarem Risiko

---

## ðŸ“¥ INPUT

- TestSpec aus `documentation/TEST_SPEC/`
- TestPlan aus `documentation/test-runs/`

---

## ðŸ“Œ AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer eine TestSpec-Datei und eine TestPlan-Datei nennt, sind diese Artefakte automatisch die verbindlichen Pruefquellen.

Der Skill MUSS dann:

- die genannte TestSpec-Datei vollstaendig lesen
- die genannte TestPlan-Datei vollstaendig lesen
- die Ausfuehrbarkeit ausschliesslich gegen diese Artefakte validieren
- Chatverlauf, fruehere Diskussionen und zusaetzliche muendliche Nebeninformationen ignorieren, sofern sie den Artefakten widersprechen oder ueber sie hinausgehen
- keine Requirements, Produktentscheidungen oder Architekturentscheidungen aus dem Chatkontext ergaenzen
- stoppen, wenn TestSpec und TestPlan nicht konsistent sind

Minimaler gueltiger User-Aufruf:

```text
/TEST SKILL 2 â€“ TEST RUN PRECHECK mit folgenden Artefakten:
TestSpec: documentation/TEST_SPEC/<TESTSPEC>.md
TestPlan: documentation/test-runs/<TEST_RUN_ID>_plan.json
```

Canonical Single-Line Handover von TEST SKILL 1 ist ebenfalls gueltig und bevorzugt,
weil mehrzeilige Chat-Bloecke in manchen UIs Zeilenumbrueche verlieren koennen:

```text
@[/TEST SKILL 2 â€“ TEST RUN PRECHECK] Mode=TEST_RUN_PRECHECK; ExecutionModel=SWE_1_6; TestSpec=documentation/TEST_SPEC/<TESTSPEC>.md; TestPlan=documentation/test-runs/<TEST_RUN_ID>_plan.json; TargetTestRun=<TEST-RUN-ID>; Capability=<Name>; Skill1Result=TEST_PLAN_CREATED; StrictValidator=TESTPLAN_VALID; GeneratorPlanTests=<tests.length>; Rules=USE_ARTIFACTS_ONLY_VALIDATE_PRECHECK_NO_IMPLEMENTATION_NO_LIVE_TESTS; ExpectedOutput=READY_FOR_LIVE_TEST_OR_TEST_RUN_BLOCKED
```

Wenn dieser Single-Line-Handover verwendet wird, MUSS Skill 2 die Semikolon-Felder parsen und
genau dieselben Artefakt-Validierungen ausfuehren wie bei der mehrzeiligen Form. `StrictValidator=TESTPLAN_VALID`
ist nur ein Handover-Hinweis; Skill 2 MUSS trotzdem `validate-test-plan.mjs` selbst ausfuehren.

Ungueltig:

- `TestPlan: documentation/test-runs/<TEST_RUN_ID>_plan.md`
- TestPlans ohne Generator-Pflichtfelder
- TestPlans mit Meta-JSON-Struktur statt `tests[]`

Wenn eine Datei nicht lesbar ist oder die Artefakte widerspruechlich sind:

```text
TEST RUN PRECHECK ARTIFACTS INVALID

Issue:
- <konkretes Problem>

Action:
â†’ korrekte Artefakte angeben oder TEST SKILL 1 erneut ausfuehren
```

---

## âš™ï¸ EXECUTION FLOW

---

### 1. LOAD ARTIFACTS

- TestSpec vollstaendig laden
- TestPlan vollstaendig laden
- TestPlan als JSON parsen; Markdown-TestPlans sind ungueltig
- Alle Sections extrahieren

### 1a. TESTPLAN GENERATOR COMPATIBILITY GATE (HARD REQUIREMENT)

Vor jeder Safety- oder Provider-Bewertung MUSS Skill 2 pruefen:

- TestPlan-Pfad endet auf `.json`: JA | NEIN
- JSON-Syntax valide: JA | NEIN
- Top-Level-Pflichtfelder vorhanden: `testRunId`, `title`, `executionMode`, `target`, `chatWindow`, `baseUrl`, `backendHealthUrl`, `timeouts`, `strategies`, `tests`: JA | NEIN
- `tests` ist ein nicht-leeres Array: JA | NEIN
- Jeder `tests[]`-Eintrag enthaelt `id`, `name`, `type`, `provider`, `model`, `prompt`, `expected`: JA | NEIN
- Strikter TestPlan-Validator meldet `TESTPLAN VALID`: JA | NEIN
- Generator akzeptiert den Plan ohne `TESTPLAN INVALID`: JA | NEIN

Verbindliche Checks:

```text
node tests/e2e/generator/validate-test-plan.mjs --plan <TestPlan>
node tests/e2e/generator/generate-live-runner.mjs --plan <TestPlan> --out documentation/test-runs/<test_run_id>_generated.spec.js
```

Wenn der Generator-Check fehlschlaegt:

```text
TEST RUN BLOCKED

Reason:
- TestPlan ist nicht generator-kompatibel: <konkrete Missing/Invalid Fields aus Generator-Ausgabe>

Action:
â†’ TEST SKILL 1 erneut ausfuehren. TEST SKILL 2 darf keinen LIVE-Handover fuer diesen Plan ausgeben.
```

---

### 2. RUNTIME SAFETY GATE (HARD REQUIREMENT)

Section 2 MUSS pruefen:

- **Test data isolated**: JA | NEIN | UNKLAR
  - Keine echten User-Dateien betroffen?
  - Sandbox oder Testaccount verwendet?
- **No real user files affected**: JA | NEIN | UNKLAR
  - Keine destruktiven Aktionen auf Produktivdaten?
- **Destructive steps require confirmation**: JA | NEIN | N/A
  - Falls destruktive Schritte im TestPlan: Bestaetigungsmechanismus vorhanden?
- **Logs avoid sensitive data**: JA | NEIN | UNKLAR
  - Keine Passwoerter, API-Keys, PII in Logs?
- **Prompt injection test cases isolated**: JA | NEIN | UNKLAR
  - Prompt-Injection-Tests laufen sicher abgekapselt?
- **Rollback/recovery available**: JA | NEIN | N/A
  - Kann der Testzustand zurueckgesetzt werden?

Wenn ein Gate NEIN oder UNKLAR ist und nicht deterministisch als sicher begruendet werden kann:

```text
TEST RUN BLOCKED

Reason:
- <konkretes Safety-Gate-Problem>

Action:
â†’ TestPlan anpassen oder Security-Scope mit GPT-5.5 klaeren
```

---

### 3. PROVIDER-/MODEL-MATRIX VOLLSTAENDIGKEIT

Pruefe:

- smallest viable GPT definiert? JA | NEIN
- smallest viable Gemini definiert? JA | NEIN
- Default/Quality-Model nur bei Bedarf definiert? JA | NEIN
- GPT-5.5 Eskalation klar abgegrenzt? JA | NEIN
- GPT smallest viable ist exakt `gpt-5.4-nano`? JA | NEIN
- GPT Default/Quality ist nur `gpt-5.4-mini` oder `gpt-5.4`? JA | NEIN | N/A
- Gemini smallest viable ist exakt `gemini-3-flash-preview`? JA | NEIN
- Gemini Default/Quality ist nur `gemini-3.1-pro-preview`? JA | NEIN | N/A
- Verbotene Textmodelle kommen nicht vor? JA | NEIN

Verbotene Textmodelle:
- `gpt-4o-mini`
- `gpt-4o`
- `GPT-4o`
- `gemini-1.5-flash`
- `Gemini Pro`
- `Pro model`

Wenn Matrix unvollstaendig:

```text
TEST RUN BLOCKED

Reason:
- Provider-/Model-Matrix unvollstaendig.

Action:
â†’ TEST SKILL 1 erneut mit vollstaendiger Matrix
```

Wenn verbotene Textmodelle vorkommen oder der Model-Katalog nicht passt:

```text
TEST RUN BLOCKED

Reason:
- Provider-/Model-Matrix verwendet veraltete oder falsche Textmodelle.

Required model catalog:
- GPT smallest viable: gpt-5.4-nano
- GPT quality/default: gpt-5.4-mini oder gpt-5.4
- Gemini smallest viable: gemini-3-flash-preview
- Gemini quality/default: gemini-3.1-pro-preview
- GPT-5.5 nur Eskalation/Audit

Action:
â†’ TEST SKILL 1 erneut ausfuehren oder TestSpec/TestPlan mit aktuellem Model-Katalog normalisieren.
```

---

### 4. TESTDATEN-VERFUEGBARKEIT

Pruefe:

- Testdaten vorhanden oder klar definiert, wie sie erstellt werden? JA | NEIN
- Testdaten sind isoliert von Produktivdaten? JA | NEIN

---

### 5. LOGS/EVIDENCE KLARHEIT

Pruefe:

- Logging-Evidence im TestPlan definiert? JA | NEIN
- Frontend-Debug-Log-Plan vorhanden (falls UI betroffen)? JA | NEIN | N/A
- Backend-Log-Pfade definiert? JA | NEIN

---

### 6. AUTOMATION READINESS GATE

Pruefe:

- Functional/Intent/UX Tests sind grundsaetzlich Playwright-automatisierbar? JA | NEIN
- TestPlan enthaelt genug Prompt-, Erwartungs- und Evidence-Daten fuer einen Playwright Runner? JA | NEIN
- Normale Chat-Prompts werden nicht als manuelle Pflichtschritte markiert? JA | NEIN
- Externe API-Aufrufe werden nicht als Grund fuer manuelle Prompt-Ausfuehrung verwendet? JA | NEIN
- Provider-/Model-Switching ist automatisierbar oder als isoliertes Manual Gate markiert? JA | NEIN | N/A

Harte Regeln:

- `Requires live Janus chat interaction` ist kein gueltiger Grund fuer manuelle Ausfuehrung.
- Externe API-Aufrufe wie Wetter, Wikipedia, Geo oder RSS sind kein gueltiger Grund fuer manuelle Prompt-Ausfuehrung.
- Wenn Provider-/Model-Switching manuell ist, darf nur der Switch manuell sein; Prompt-Ausfuehrung bleibt Playwright-pflichtig.
- Wenn Functional/Intent/UX pauschal manuell geplant sind, ist der TestRun nicht automation-ready.

Wenn Automation Readiness fehlschlaegt:

```text
TEST RUN BLOCKED

Reason:
- TestPlan ist nicht automation-ready fuer TEST SKILL 3.

Action:
â†’ TEST SKILL 1 erneut ausfuehren oder TestPlan so ergaenzen, dass TEST SKILL 3 einen ausfuehrbaren Playwright Live-Runner generieren kann.
```

---

## ðŸŒ OUTPUT LANGUAGE

Alle user-facing Zusammenfassungen, Bewertungen, Titel, Zielbeschreibungen, Next Steps und Fehlermeldungen MUeSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Klassennamen, Funktionsnamen und Modellnamen bleiben unveraendert.

---

## ðŸ“¤ OUTPUT STATES

### âœ… READY FOR LIVE TEST

```text
READY FOR LIVE TEST

TestRun: <TEST-RUN-ID>

Runtime Safety Gate:
- Test data isolated: JA
- No real user files affected: JA
- Destructive steps require confirmation: JA | N/A
- Logs avoid sensitive data: JA
- Prompt injection test cases isolated: JA
- Rollback/recovery available: JA | N/A

Provider-/Model-Matrix:
- smallest viable GPT: gpt-5.4-nano â€“ definiert
- smallest viable Gemini: gemini-3-flash-preview â€“ definiert
- Default/Quality: gpt-5.4-mini | gpt-5.4 | gemini-3.1-pro-preview | N/A
- GPT-5.5 escalation: <Bedingung> â€“ definiert | N/A

Automation Readiness Gate:
- Functional/Intent/UX Playwright automation-ready: JA
- Normal chat prompts require manual copy/paste: NEIN
- Provider/model switching manual gate only if required: JA | N/A

Testdaten:
- Status: vorhanden | klar definiert

Logs/Evidence:
- Backend-Log: <Pfad/Plan>
- Frontend-Debug-Log: <Pfad/Plan | N/A>

Naechster Schritt:
â†’ Starte TEST SKILL 3 mit TestSpec, TestPlan und diesem Precheck-Ergebnis.
```

Nach `READY FOR LIVE TEST` MUSS Skill 2 den Skill-3-Handover deterministisch erzeugen:

```text
node tests/e2e/generator/create-test-skill3-handover.mjs --spec <TestSpec> --plan <TestPlan> --run <TEST_RUN_ID> --capability "<Capability Name>"
```

Wenn das Script `HANDOVER INVALID` ausgibt, darf Skill 2 keinen Skill-3-Handover ausgeben.
Stattdessen muss `TEST RUN BLOCKED` mit dem konkreten Handover-Fehler ausgegeben werden.

### Skill-3-Handover Mode Gate (HARD)

Der Skill-3-Handover darf ausschliesslich die kanonische Generator-Ausgabe verwenden.

Pflicht:

- Genau ein einzelner grauer `text` Copy-Block.
- Inhalt ist exakt die Single-Line-Ausgabe von `node tests/e2e/generator/create-test-skill3-handover.mjs`.
- `Mode=LIVE_VISUAL` ist Pflicht.
- `ConnectivityMode=PLAYWRIGHT_WEBSERVER_AUTOSTART` ist Pflicht.
- `ManualJanusStartRequired=NO` ist Pflicht.
- `ExpectedOutput=TEST_RESULT_PLUS_SINGLE_LINE_HANDOFF_TO_TEST_SKILL_4_WITH_METRICS` ist Pflicht.

Verboten:

```text
Mode: LIVE_TEST_EXECUTION
Mode=LIVE_TEST_EXECUTION
Mode: LIVE_TEST_RUN
Mode=LIVE_TEST_RUN
Mode: LIVE_RETEST
BEGIN COPY FOR TEST SKILL 3
END COPY FOR TEST SKILL 3
@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION] mit folgenden Artefakten:
freie mehrzeilige Handover-Felder
ExpectedOutput: TEST_RESULT_PLUS_HANDOFF_TO_TEST_SKILL_4
```

Wenn der Output eines dieser verbotenen Muster enthaelt, darf `READY FOR LIVE TEST` nicht finalisiert werden. Stattdessen:

```text
TEST RUN BLOCKED
Reason:
- SKILL3_HANDOVER_MODE_INVALID

Required Fix:
- create-test-skill3-handover.mjs ausfuehren und exakt dessen Single-Line-Handover ausgeben.
```

### âŒ TEST RUN BLOCKED

```text
TEST RUN BLOCKED

Reason:
- <konkreter Grund>

Action:
â†’ TestSpec/TestPlan anpassen oder mit GPT-5.5 klaeren
```

---

## ðŸ“‹ COPY-PASTE HANDOVER FUER TEST SKILL 3 (PFLICHT)

Am Ende bei READY FOR LIVE TEST MUSS ein einzelner grauer Copy-Block mit exakt der
Single-Line-Ausgabe aus `create-test-skill3-handover.mjs` ausgegeben werden.
Mehrzeilige Skill-3-Handover sind ungueltig, weil sie in Chat-UIs zerfallen und wichtige
Felder verlieren koennen.

```text

@[/TEST SKILL 3 â€“ LIVE JANUS TEST EXECUTION] Mode=LIVE_VISUAL; ExecutionModel=SWE_1_6; TestSpec=<path>; TestPlan=<path>; TargetTestRun=<TEST-RUN-ID>; Capability=<name>; PrecheckResult=READY_FOR_LIVE_TEST; StrictValidator=TESTPLAN_VALID; GeneratorPlanTests=<n>; ConnectivityMode=PLAYWRIGHT_WEBSERVER_AUTOSTART; ManualJanusStartRequired=NO; Rules=USE_ARTIFACTS_ONLY_EXECUTE_LIVE_TESTS_COLLECT_EVIDENCE_NO_IMPLEMENTATION; ExpectedOutput=TEST_RESULT_PLUS_SINGLE_LINE_HANDOFF_TO_TEST_SKILL_4_WITH_METRICS
```

Pflichtfelder:

- `ConnectivityMode=PLAYWRIGHT_WEBSERVER_AUTOSTART`
- `ManualJanusStartRequired=NO`
- `TargetTestRun` muss exakt `testRunId` aus dem TestPlan sein.
- `GeneratorPlanTests` muss exakt `tests.length` aus dem TestPlan sein.
- `ExpectedOutput` muss den metrischen Skill-4-Handover verlangen:
  `TEST_RESULT_PLUS_SINGLE_LINE_HANDOFF_TO_TEST_SKILL_4_WITH_METRICS`

Verboten im Skill-3-Handover:

- freie mehrzeilige Prosa
- `Mode: LIVE_TEST_EXECUTION`
- `Mode=LIVE_TEST_EXECUTION`
- `BEGIN COPY FOR TEST SKILL 3`
- `END COPY FOR TEST SKILL 3`
- `Fuehre den User durch konkrete Live-Testschritte im offenen Janus`
- `Manual Janus Start`
- `npm run start-dev` als User-Pflicht
- Skill-4-Handover ohne `PassRatePct`, `FailRatePct`, `ProviderPassRatePct`, `TypePassRatePct`


---

## GPT-5.5 ESCALATION HANDOVER (COST-SAFE)

Wenn GPT-5.5 erforderlich ist, darf der Skill nicht mit voller Chat-Historie weiterarbeiten.

Stattdessen MUSS der Skill stoppen und genau einen kompakten Copy-Block fuer einen frischen GPT-5.5-Chat ausgeben.

```text
MODEL SWITCH REQUIRED: SWE 1.6 -> GPT-5.5

Reason:
- <konkreter Eskalationsgrund>

BEGIN COPY FOR NEW GPT-5.5 CHAT

@[/TEST SKILL 2 â€“ TEST RUN PRECHECK]

Mode: ESCALATION_REVIEW
Execution Model: GPT-5.5

Binding Artifacts:
- TestSpec: <path>
- TestPlan: <path>
- Precheck Draft/Issue: <kompakte Beschreibung oder N/A>

Escalation Question:
- Darf dieser TestRun unter den gegebenen Runtime-Safety-Bedingungen live in Janus gestartet werden?

Relevant Evidence:
- <nur relevante Safety-Gate-Werte, Sandbox-/Rollback-Unklarheiten, keine volle Chat-Historie>

Hard Rules:
- Use only listed artifacts and evidence as source of truth.
- Ignore previous chat history.
- Do not add product requirements.
- Do not implement code.
- Do not request full logs unless absolutely required.
- Decide only the escalation question.

Expected Output:
- Decision: PASS_TO_CONTINUE | BLOCKED | REQUIRED_TESTPLAN_FIX
- Reason:
- Required next skill:
- Recommended model:
- Copy handover back to SWE 1.6 if continuation is possible.

END COPY
```

---

## ï¿½ RESTRICTIONS

KEINE Codeausfuehrung ausser deterministischer Artefakt-Validierung gegen JSON-Schema/Generator
KEINE Implementation
KEINE Architekturentscheidungen
KEINE Scope-Erweiterung
KEINE Task-Neuerfindung

---

## ðŸ§  ERROR HANDLING

Wenn TestSpec oder TestPlan nicht lesbar:

```text
TEST RUN PRECHECK FAILED: Artefakt nicht lesbar
```

---

## ðŸ§  OUTPUT GUARANTEE

Output ist immer:

deterministisch
validation-only
non-executing
safe-before-run gate
