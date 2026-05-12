---
description: SWE 1.6 Test Pipeline Phase 2 – Test Run Precheck Gate. Prueft, ob ein TestRun sicher und vollstaendig live in Janus ausgefuehrt werden darf. Keine Implementation.
---

# TEST SKILL 2 – TEST RUN PRECHECK

## 🎯 PURPOSE

Dieser Skill ist ein **harte Sicherheits- und Vollstaendigkeits-Gate** vor der Live-Test-Ausfuehrung.

Er entscheidet ausschliesslich:

→ DARF DER TESTRUN LIVE IN JANUS STARTEN?

KEINE IMPLEMENTATION. KEIN CODE. KEINE PLANUNG.

---

## 🤖 DEFAULT MODEL

SWE 1.6

Ausnahme:
- GPT-5.5 nur bei unklarem Security-Scope oder nicht deterministisch bewertbarem Risiko

---

## 📥 INPUT

- TestSpec aus `documentation/TEST_SPEC/`
- TestPlan aus `documentation/test-runs/`

---

## 📌 AUTOMATIC ARTIFACT INPUT MODE

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
/TEST SKILL 2 – TEST RUN PRECHECK mit folgenden Artefakten:
TestSpec: documentation/TEST_SPEC/<TESTSPEC>.md
TestPlan: documentation/test-runs/<TEST_RUN_ID>_plan.md
```

Wenn eine Datei nicht lesbar ist oder die Artefakte widerspruechlich sind:

```text
TEST RUN PRECHECK ARTIFACTS INVALID

Issue:
- <konkretes Problem>

Action:
→ korrekte Artefakte angeben oder TEST SKILL 1 erneut ausfuehren
```

---

## ⚙️ EXECUTION FLOW

---

### 1. LOAD ARTIFACTS

- TestSpec vollstaendig laden
- TestPlan vollstaendig laden
- Struktur parsen
- Alle Sections extrahieren

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
→ TestPlan anpassen oder Security-Scope mit GPT-5.5 klaeren
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
→ TEST SKILL 1 erneut mit vollstaendiger Matrix
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
→ TEST SKILL 1 erneut ausfuehren oder TestSpec/TestPlan mit aktuellem Model-Katalog normalisieren.
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
→ TEST SKILL 1 erneut ausfuehren oder TestPlan so ergaenzen, dass TEST SKILL 3 einen ausfuehrbaren Playwright Live-Runner generieren kann.
```

---

## 🌐 OUTPUT LANGUAGE

Alle user-facing Zusammenfassungen, Bewertungen, Titel, Zielbeschreibungen, Next Steps und Fehlermeldungen MUeSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Klassennamen, Funktionsnamen und Modellnamen bleiben unveraendert.

---

## 📤 OUTPUT STATES

### ✅ READY FOR LIVE TEST

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
- smallest viable GPT: gpt-5.4-nano – definiert
- smallest viable Gemini: gemini-3-flash-preview – definiert
- Default/Quality: gpt-5.4-mini | gpt-5.4 | gemini-3.1-pro-preview | N/A
- GPT-5.5 escalation: <Bedingung> – definiert | N/A

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
→ Starte TEST SKILL 3 mit TestSpec, TestPlan und diesem Precheck-Ergebnis.
```

### ❌ TEST RUN BLOCKED

```text
TEST RUN BLOCKED

Reason:
- <konkreter Grund>

Action:
→ TestSpec/TestPlan anpassen oder mit GPT-5.5 klaeren
```

---

## 📋 COPY-PASTE HANDOVER FUER TEST SKILL 3 (PFLICHT)

Am Ende bei READY FOR LIVE TEST MUSS ein einzelner grauer Copy-Block ausgegeben werden.

```text
@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]

Mode: LIVE_TEST_RUN
Execution Model: SWE 1.6
TestSpec: <source test spec file>
TestPlan: <source test plan file>
TestResult: N/A
Target TestRun: <TEST-RUN-ID>

Context:
- Capability: <Name>
- TEST SKILL 2 Ergebnis: READY FOR LIVE TEST
- Runtime Safety Gate: PASS

Arbeitsregel:
- Nutze die genannte TestSpec-Datei und TestPlan-Datei als verbindliche Artefakte.
- Ignoriere widerspruechliche oder zusaetzliche Chat-Kontexte.
- Erzeuge keine Implementation.
- Fuehre den User durch konkrete Live-Testschritte im offenen Janus.
- Sammle Evidence aus User-Beobachtung, Logs und Token-Anzeigen.
- Schreibe Ergebnisse nach documentation/test-results/<test_run_id>_results.md.
- Preserve security/privacy/prompt-injection gates.
- Preserve provider/model matrix (smallest viable first).

Naechster erwarteter Output:
- TestResult-Artefakt: documentation/test-results/<test_run_id>_results.md
- Copy-Handover zu TEST SKILL 4 – FINDING TRIAGE AND ROUTING
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

@[/TEST SKILL 2 – TEST RUN PRECHECK]

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

## � RESTRICTIONS

KEINE Codeausfuehrung
KEINE Implementation
KEINE Architekturentscheidungen
KEINE Scope-Erweiterung
KEINE Task-Neuerfindung

---

## 🧠 ERROR HANDLING

Wenn TestSpec oder TestPlan nicht lesbar:

```text
TEST RUN PRECHECK FAILED: Artefakt nicht lesbar
```

---

## 🧠 OUTPUT GUARANTEE

Output ist immer:

deterministisch
validation-only
non-executing
safe-before-run gate
