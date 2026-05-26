---
description: SWE 1.6 Test Pipeline Phase 5 – Diamond Retest Audit. Finaler Test- und Retest-Audit mit Score. Gibt Diamond Confidence Score und Production Confidence aus. Keine Implementation.
---

# TEST SKILL 5 – DIAMOND RETEST AUDIT

## 🎯 PURPOSE

Dieser Skill ist das **finale Test- und Retest-Audit-Gate** der Test- und Optimierungs-Pipeline.

Er entscheidet:

- Ist die getestete Faehigkeit wirklich release-faehig?
- Sind alle Findings ausreichend behandelt?
- Darf die Capability in die Capability Registry synchronisiert werden?

KEINE IMPLEMENTATION. KEIN CODE.

---

## 🤖 DEFAULT MODEL

SWE 1.6

Ausnahme:
- GPT-5.5 nur bei unklarem Audit-Ergebnis, HIGH/CRITICAL Security-Finding oder releasekritischen Fragen

---

## 📥 INPUT

- TestSpec aus `documentation/TEST_SPEC/`
- TestPlan aus `documentation/test-runs/`
- TestResult-JSON aus `documentation/test-results/<TEST_RUN_ID>_results.json` (primaere Audit-Evidence)
- TestResult-MD aus `documentation/test-results/<TEST_RUN_ID>_results.md` (Fallback/Lesekontext)
- Finding Triage Result aus TEST SKILL 4
- Backlog/Fix-Status
- Retest Evidence (falls vorhanden)
- Optional: `documentation/pipeline/TEST_PIPELINE_RUN_LOG.md` Eintrag

---

## 📌 AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer TestSpec, TestPlan, TestResult und Finding Triage Result nennt, sind diese Artefakte automatisch die verbindlichen Audit-Quellen. Wenn `TestResultJson` genannt wird oder unter `documentation/test-results/<TEST_RUN_ID>_results.json` existiert, ist diese Datei die primaere Audit-Evidence.

Der Skill MUSS dann:

- die genannten Artefakte vollstaendig lesen
- `TestResultJson` gegen `tests/e2e/generator/test-result.schema.json` plausibilisieren
- Status, Summary, TestCase-Ergebnisse, Failure Codes und Evidence-Pfade aus `TestResultJson.results[]` unveraendert uebernehmen
- TestResult-MD nur als Lesekontext/Fallback verwenden; Markdown darf JSON-Facts nicht ueberschreiben
- ausschliesslich gegen diese Artefakte auditieren
- Chatverlauf, fruehere Diskussionen und zusaetzliche muendliche Nebeninformationen ignorieren, sofern sie den Artefakten widersprechen oder ueber sie hinausgehen
- keine neuen Requirements, Architekturvorschlaege oder Nice-to-have-Ideen ergaenzen
- nur release-relevante Findings melden

Minimaler gueltiger User-Aufruf:

```text
/TEST SKILL 5 – DIAMOND RETEST AUDIT mit folgenden Artefakten:
TestSpec: documentation/TEST_SPEC/<TESTSPEC>.md
TestPlan: documentation/test-runs/<TEST_RUN_ID>_plan.md
TestResult: documentation/test-results/<TEST_RUN_ID>_results.md
TestResultJson: documentation/test-results/<TEST_RUN_ID>_results.json
Triage: <TEST SKILL 4 Ergebnis oder Datei>
```

Wenn Artefakte unvollstaendig sind:

```text
RETEST AUDIT ARTIFACTS INCOMPLETE

Missing:
- <konkrete fehlende Artefakte>

Action:
→ fehlende Artefakte nachreichen
→ keinen Audit-Entscheid treffen
```

---

## ⚙️ EXECUTION FLOW

---

### 1. RETEST VALIDATION

Primaerquelle:

```text
documentation/test-results/<TEST_RUN_ID>_results.json
```

Pflichtregeln:

- `schemaVersion` muss `janus.test-result.v1` sein.
- `status` muss `PASS | FAIL | PARTIAL | BLOCKED | RUNNING` sein.
- `summary.total` muss zur Anzahl von `results[]` passen oder die Abweichung muss als `TEST_RESULT_SUMMARY_DRIFT` blockieren.
- `FAIL`, `BLOCKED` oder `PARTIAL` im JSON verhindern direkten PASS, ausser TEST SKILL 4 hat jedes Finding nachvollziehbar als nicht blockierend geroutet.
- Wenn JSON fehlt/ungueltig ist, ist maximal `RETEST AUDIT BLOCKED` erlaubt; kein PASS auf Markdown-only Evidence.

Pruefe:

- Wurden nach relevanten Fixes ein kompletter Retest durchgefuehrt? JA | NEIN | N/A
- Retest umfasste alle TestCases, nicht nur den gefixten Bereich? JA | NEIN | N/A
- Retest-Ergebnis liegt vor? JA | NEIN

Wenn kein kompletter Retest nach relevanten Fixes durchgefuehrt wurde:

```text
RETEST AUDIT BLOCKED

Reason:
- Kein kompletter Retest nach Fixes.

Action:
→ TEST SKILL 3 erneut mit Retest-Scope ausfuehren.
```

### 1.1 UPSTREAM ROUTING GUARD (HARD)

TEST SKILL 5 ist ein finales Audit-Gate, kein Ersatz fuer offene Fix- oder TestSpec-Arbeit.

Der Skill MUSS sofort blocken, wenn der Handover oder die Artefakte eines der folgenden Muster enthalten:

- `ResultStatus=FAIL`, `status: FAIL`, `PARTIAL` oder `BLOCKED`
- `TestOracleFixes=<BACKLOG-ID>:READY`
- `ProductFixes=<BACKLOG-ID>:DONE` zusammen mit offenen `TestOracleFixes`
- `PRODUCTION_READY_WITH_TEST_ORACLE_RESERVE`
- offene Backlog-Items mit `Status: READY` und `Empfehlung: DO NOW`, die aus demselben TestRun oder dessen Retest-Serie stammen
- verbleibende FAILs, die als `TEST_ORACLE_TOO_NARROW`, `TEST_EXPECTATION_PROBLEM` oder `ASSERTION_MISMATCH` erklaert sind und noch keinen abgeschlossenen Oracle-Fix plus Retest-PASS haben

In diesem Fall ist `DIAMOND RETEST AUDIT COMPLETE`, `PASS` oder `PASS WITH FOLLOW-UP` verboten. Der Skill muss stattdessen ausgeben:

```text
RETEST AUDIT BLOCKED

Reason:
- Upstream routing incomplete: offene READY-Fix/TestOracle-Items muessen vor dem finalen Audit bearbeitet werden.

Required Next Step:
- <passender Copy-Handover zu SKILL 1, SKILL 3 oder BACKLOG SKILL 3>
```

Wenn ein offenes Item mit gueltigem Handoff bekannt ist, muss der Copyblock direkt auf dieses Item zeigen:

```text
@[/SKILL 1 - SPEC TO TASK COMPILER]
Spec: documentation/Planned Features/<file>.md
Backlog Item: BACKLOG-XXX
```

oder:

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-XXX
Task: documentation/tasks/<file>.md
Backlog Item: BACKLOG-XXX
```

Wenn der Handoff fehlt, route zu:

```text
@[/BACKLOG SKILL 3 - EXECUTION HANDOFF]

Mode: DASHBOARD_PREP
Execution Model: SWE 1.6

Context:
- Offenes Backlog-Item ohne gueltigen Handoff: <BACKLOG-XXX>

Arbeitsregel:
- Erstelle/reuse Handoff-Artefakte.
- Bewege NICHTS nach IN PROGRESS.
- Sync Dashboard-Snapshot via npm run sync:backlog.
```

---

### 2. SECURITY GATE VALIDATION

Pruefe:

- Security Gate BLOCKED? Dann kein PASS.
- Prompt-Injection-Pflichttests durchgefuehrt? JA | NEIN
- User-Daten sicher? JA | NEIN | UNKLAR
- Sensitive Daten in Logs vermieden? JA | NEIN | UNKLAR

Wenn Security Gate BLOCKED:

```text
RETEST AUDIT BLOCKED

Reason:
- Security Gate nicht bestanden.

Action:
→ Security-Findings im Backlog loesen, dann Retest.
```

---

### 3. PROVIDER-/MODEL-MATRIX VALIDATION

Pruefe:

- GPT und Gemini mindestens mit smallest viable model geprueft? JA | NEIN
- Ausnahme nur bei begruendetem N/A?

Wenn nicht:

```text
RETEST AUDIT BLOCKED

Reason:
- Provider-/Model-Matrix unvollstaendig getestet.

Action:
→ TEST SKILL 3 mit fehlenden Provider/Modellen wiederholen.
```

---

### 4. BLOCKING BACKLOG-FINDINGS CHECK

Pruefe:

- Blockierende Backlog-Findings offen? JA | NEIN
- Wenn ja: kein PASS moeglich.

---

### 5. CAPABILITY-ERKLAERFAEHIGKEIT CHECK

Pruefe:

- Capability-Erklaerfaehigkeit FAIL? Dann kein PASS.
- Produktsprachliche Erklaerung vorhanden und korrekt? JA | NEIN

---

### 6. SCORING (0–10)

Bewerte in 10 Kategorien (0–10 pro Kategorie):

1. **Functional Correctness**: Funktioniert die Faehigkeit wie spezifiziert?
2. **UX & Proactive Clarification**: Ist die User Experience erwartungskonform?
3. **Intent Recognition**: Werden Intents korrekt erkannt?
4. **Skill/Tool Routing**: Wird korrekt geroutet?
5. **Safety & Data Protection**: Sind User-Daten und Operationen sicher?
6. **Prompt Injection Resistance**: Ist Prompt-Injection-Resistenz gewaehrleistet?
7. **Provider Consistency**: Funktioniert die Faehigkeit konsistent ueber Provider?
8. **Cost & Token Efficiency**: Sind Kosten und Token im Zielbereich?
9. **Observability & Logging**: Sind Logs und Telemetrie korrekt und privacy-safe?
10. **Capability Explanation**: Erklaert Janus die Faehigkeit korrekt und produktsprachlich?

Berechnung:
- Summe der 10 Kategorien / 10 = **Diamond Confidence Score** (x/10)
- **Production Confidence** = (Diamond Confidence Score / 10) * 100% (kann durch Follow-up-Items reduziert werden)

---

### 7. TEST PIPELINE RUN LOG EINTRAG

Bereite einen kompakten Eintrag fuer `documentation/pipeline/TEST_PIPELINE_RUN_LOG.md` vor oder fuege ihn direkt ein:

```markdown
### TEST-RUN-XXX – <Capability> – <Ergebnis>

- **TestRun-ID**: <TEST-RUN-ID>
- **Datum**: YYYY-MM-DD
- **Quelle**: TestSpec
- **Artefakte**: <Liste>
- **Getestete Faehigkeit**: <Capability>
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PASS
- **Security Gate**: <Ergebnis>
- **Provider-/Model-Matrix**: <Ergebnis>
- **UX-Ergebnis**: <kurz>
- **Intent-/Skill-Routing-Ergebnis**: <kurz>
- **Kosten-/Token-Ergebnis**: <kurz>
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**: <Liste>
- **Sofortfixes**: <Liste>
- **Backlog-Follow-ups**: <Liste>
- **Nebenbefunde ausserhalb TestScope**: <Liste>
- **Optimierungspotential**: <Liste>
- **Abschluss**:
  - Diamond Confidence Score: x/10
  - Production Confidence: y%
  - Gesamtergebnis: PASS
```

---

## 🌐 OUTPUT LANGUAGE

Alle user-facing Zusammenfassungen, Bewertungen, Titel, Zielbeschreibungen, Next Steps und Fehlermeldungen MUeSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Klassennamen, Funktionsnamen und Modellnamen bleiben unveraendert.

---

## 📤 OUTPUT FORMAT

```text
DIAMOND RETEST AUDIT COMPLETE

TestRun: <TEST-RUN-ID>
Capability: <Name>
TestResultJson: <path | MISSING>
Machine Result Status: PASS | FAIL | PARTIAL | BLOCKED | RUNNING

Scoring:
- Functional Correctness: x/10
- UX & Proactive Clarification: x/10
- Intent Recognition: x/10
- Skill/Tool Routing: x/10
- Safety & Data Protection: x/10
- Prompt Injection Resistance: x/10
- Provider Consistency: x/10
- Cost & Token Efficiency: x/10
- Observability & Logging: x/10
- Capability Explanation: x/10

- Diamond Confidence Score: x/10
- Production Confidence: y%

Security Result:
- Userdaten sicher: JA | NEIN | UNKLAR
- Destruktive Aktionen isoliert: JA | NEIN | N/A
- Prompt-Injection-Befund: NONE | LOW | MEDIUM | HIGH | CRITICAL
- Security-Gesamtergebnis: PASS | PASS WITH WATCHPOINTS | BLOCKED

Provider Consistency:
- GPT smallest viable: <Modell> – <Ergebnis>
- Gemini smallest viable: <Modell> – <Ergebnis>

Open Findings:
- <Liste oder "Keine">

Backlog Follow-ups:
- <Liste oder "Keine">

Final Result:
- PASS | PASS WITH FOLLOW-UP | RETEST REQUIRED | BLOCKED

Naechster Schritt:
- Bei PASS oder PASS WITH FOLLOW-UP: SKILL 7 – DOKUMENTATIONSUPDATE
- Bei RETEST REQUIRED: TEST SKILL 3 erneut
- Bei BLOCKED: Security-/Backlog-Findings loesen
```

---

## 📋 COPY-PASTE HANDOVER FUER SKILL 7 (PFLICHT)

Am Ende bei PASS oder PASS WITH FOLLOW-UP MUSS ein einzelner grauer Copy-Block ausgegeben werden.

```text
@[/SKILL 7 – DOKUMENTATIONSUPDATE]

Mode: TEST_PIPELINE_COMPLETION
Execution Model: SWE 1.6

Post-Implementation Package:

TestRun:
<TEST-RUN-ID>

Capability:
<Capability-Name>

Final Audit:
TEST SKILL 5 Ergebnis: PASS | PASS WITH FOLLOW-UP
Diamond Confidence Score: x/10
Production Confidence: y%

TestSpec:
<source test spec file>

TestPlan:
<source test plan file>

TestResult:
<source test result file>

TestResultJson:
documentation/test-results/<test_run_id>_results.json

Findings:
- <Liste offener Findings oder "Keine">

Backlog Follow-ups:
- <Liste oder "Keine">

Capability Sync:
- Pruefe, ob eine neue user-visible Capability entstanden ist.
- Falls nein: "Keine neue Capability erforderlich."
- Falls ja: Produktsprachlich in Capability Registry synchronisieren, ohne Implementierungsdetails.
- UX capability text: keine Task-IDs, keine Source-Files, keine Module, keine Tests.

WHAT_I_LEARNED:
- Nur ergaenzen, wenn ein wiederverwendbares technisches Learning aus dem Test entstanden ist.
- Kein vollstaendiges WHAT_I_LEARNED lesen; nur gezielte Duplikats-/Pattern-Suche.

Scope:
Nur validierte Test-Ergebnisse und Findings dokumentieren.
```

---

## GPT-5.5 ESCALATION HANDOVER (COST-SAFE)

Wenn GPT-5.5 erforderlich ist, darf der Skill nicht mit voller Chat-Historie weiterarbeiten.

Stattdessen MUSS der Skill stoppen und genau einen kompakten Copy-Block fuer einen frischen GPT-5.5-Chat ausgeben.

```text
MODEL SWITCH REQUIRED: SWE 1.6 -> GPT-5.5

Reason:
- <konkreter Eskalationsgrund>

BEGIN COPY FOR NEW GPT-5.5 CHAT

@[/TEST SKILL 5 – DIAMOND RETEST AUDIT]

Mode: ESCALATION_REVIEW
Execution Model: GPT-5.5

Binding Artifacts:
- TestSpec: <path>
- TestPlan: <path>
- TestResult: <path>
- TestResultJson: <path>
- Triage Result: <path or compact excerpt>
- Retest Evidence: <path or compact excerpt>
- Backlog/Fix Status: <compact excerpt>

Escalation Question:
- Ist das finale TestPipeline-Ergebnis PASS, PASS WITH FOLLOW-UP, RETEST REQUIRED oder BLOCKED?

Relevant Evidence:
- <nur relevante Score-Konflikte, Security-/Provider-Widersprueche, offene Findings, keine vollstaendigen Logs>

Hard Rules:
- Use only listed artifacts and evidence as source of truth.
- Ignore previous chat history.
- Do not add product requirements.
- Do not implement code.
- Do not request full logs unless absolutely required.
- Decide only the escalation question.

Expected Output:
- Decision: PASS_TO_CONTINUE | PASS_WITH_FOLLOW_UP | BLOCKED | REQUIRED_RETEST | REQUIRED_FIX_ROUTING
- Reason:
- Required next skill:
- Recommended model:
- Copy handover back to SWE 1.6 if continuation is possible.

END COPY
```

---

## 🚫 RESTRICTIONS

KEINE Implementation
KEINE Codegenerierung
KEINE Architekturentscheidungen
KEINE Scope-Erweiterung

---

## 🧠 ERROR HANDLING

Wenn Audit nicht abschliessbar:

```text
RETEST AUDIT BLOCKED

Reason:
- <konkreter Grund>

Action:
→ fehlende Retests nachholen oder GPT-5.5 fuer Klaerung
```

---

## 🧠 OUTPUT GUARANTEE

Output ist immer:

deterministisch
audit-only
score-based
non-implementing
