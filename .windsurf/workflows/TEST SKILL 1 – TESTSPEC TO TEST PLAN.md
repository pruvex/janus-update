---
description: SWE 1.6 Test Pipeline Phase 1 – TestSpec zu TestPlan Compiler. Liest eine TestSpec und erzeugt einen deterministischen TestPlan unter documentation/test-runs/. Keine Code-Implementation.
---

# TEST SKILL 1 – TESTSPEC TO TEST PLAN

## 🎯 PURPOSE

Dieser Skill transformiert eine **TestSpec** in einen **deterministischen TestPlan**.

Er erzeugt:
→ eine ausfuehrbare TestPlan-Datei fuer TEST SKILL 2–3

KEINE CODE-IMPLEMENTATION. KEINE LIVE-TESTS. KEINE ARCHITEKTUR.

---

## 🤖 DEFAULT MODEL

SWE 1.6

Ausnahme:
- Kimi k2.5 nur fuer deterministische Markdown-/Single-File-/Daten-Strukturarbeit
- GPT-5.5 nur bei HIGH/CRITICAL Security-Scope oder nicht deterministisch loesbarer TestSpec

---

## 📥 INPUT

- TestSpec (MD-Datei)
- Zielsystem: Janus Codebase Kontext

Bevorzugter Input:

- normalisierte TestSpec aus `documentation/TEST_SPEC/`
- erzeugt mit `documentation/prompts/c_JANUS_FINAL_TESTSPEC_COPY_PROMPT_v1.0.md`
- Titel der Datei beginnt mit `# JANUS TESTSPEC – DIAMANTSTANDARD v1.0`

---

## 📌 AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer eine TestSpec-Datei nennt, ist diese Datei automatisch die **Single Source of Truth**.

Der Skill MUSS dann:

- die genannte TestSpec-Datei lesen
- den exakt genannten TestSpec-Pfad als `Input TestSpec Path` speichern
- bevorzugt normalisierte TestSpecs mit Titel `# JANUS TESTSPEC – DIAMANTSTANDARD v1.0` akzeptieren
- leicht fehlerhafte Normalizer-Ausgaben nicht sofort ablehnen, sondern zuerst durch das TestSpec Preflight Normalization Gate pruefen
- ausschliesslich die TestSpec in dieser Datei als Test-Grundlage verwenden
- Chatverlauf, fruehere Diskussionen und zusaetzliche muendliche Nebeninformationen ignorieren, sofern sie der TestSpec widersprechen oder ueber sie hinausgehen
- keine Produktentscheidungen aus dem Chatkontext ergaenzen
- keine alten Entwuerfe oder externe Notizen als Requirements verwenden
- in allen Folge-Handovers ausschliesslich den `Input TestSpec Path` verwenden
- keine absoluten Windows-Pfade in Handovers ausgeben
- keine abweichenden TestSpec-Pfade wie `documentation/test-specs/...` in Handovers verwenden

Minimaler gueltiger User-Aufruf:

```text
/TEST SKILL 1 – TESTSPEC TO TEST PLAN mit folgender TestSpec:
documentation/TEST_SPEC/<TESTSPEC>.md
```

Gueltige TestSpec-Artefaktpfade:

- `documentation/TEST_SPEC/<slug>.md`

Ungueltige TestSpec-Artefaktpfade:

- `documentation/test-specs/...`
- `documentation/prompts/...`
- absolute Windows-Pfade wie `C:\...`
- generierte Zwischenartefakte oder Review-Fragmente

Wenn der Input-Pfad nicht unter `documentation/TEST_SPEC/` liegt:

```text
TESTSPEC FILE INVALID

Issue:
- TestSpec path is not a normalized test artifact path.

Expected:
- documentation/TEST_SPEC/<slug>.md

Received:
- <input path>

Action:
→ Speichere die normalisierte TestSpec unter documentation/TEST_SPEC/<slug>.md und starte TEST SKILL 1 erneut.
```

Wenn die Datei nicht lesbar ist oder keine vollstaendige Janus TestSpec enthaelt:

```text
TESTSPEC FILE INVALID

Issue:
- <konkretes Problem>

Action:
→ korrekte TestSpec-Datei angeben oder finale TestSpec erneut speichern
```

---

## ⚙️ EXECUTION FLOW

---

### 1. TESTSPEC PARSING

Vor der fachlichen Auswertung MUSS Skill 1 ein deterministisches TestSpec Preflight Normalization Gate ausfuehren.

Ziel:
- haeufige Copy-/Markdown-Fehler selbst reparieren
- keine GPT-5.5-Pruefung fuer triviale Formatfehler benoetigen
- nur bei inhaltlicher Unklarheit, Security-Risiko oder nicht deterministisch reparierbaren Fehlern blocken/eskalieren

Skill 1 DARF deterministisch reparieren:

- fehlende Doppelpunkte in bekannten Routing-Feldern
- fehlende Doppelpunkte in bekannten strukturierten Bullet-Feldern
- kaputte Dokumentationspfade wie `documentationTEST_SPECfoo.md` zu `documentation/TEST_SPEC/foo.md`
- Space-Pseudotabellen zu echten Markdown-Pipe-Tabellen, wenn Spalten eindeutig erkennbar sind
- fehlende Leerzeile nach Ueberschriften
- Varianten von `SWE 1.6` zu `SWE_1_6` im Routing-Block
- Varianten von `GPT-5.5` zu `GPT_5_5` im Routing-Block
- verbotene alte Textmodell-Namen deterministisch auf den aktuellen Janus Model-Katalog mappen:
  - `gpt-4o-mini` -> `gpt-5.4-nano`
  - `GPT-4o` oder `gpt-4o` -> `gpt-5.4`
  - `gemini-1.5-flash` -> `gemini-3-flash-preview`
  - `Gemini Pro` oder `Pro model` -> `gemini-3.1-pro-preview`

Skill 1 DARF NICHT reparieren oder erfinden:

- fehlende Testziele
- fehlende Security-Werte
- unklare destructive-operation Entscheidung
- fehlende Provider-Zeilen fuer GPT oder Gemini
- leere Akzeptanzkriterien
- neue TestCases, die nicht aus der TestSpec ableitbar sind
- neue Produktanforderungen
- neue Tool-/API-Annahmen

Model-Katalog fuer Text-TestSpecs:

- GPT smallest viable: `gpt-5.4-nano`
- GPT quality/default fallback: `gpt-5.4-mini` oder `gpt-5.4`
- GPT escalation/audit only: `gpt-5.5`
- Gemini smallest viable: `gemini-3-flash-preview`
- Gemini quality/default fallback: `gemini-3.1-pro-preview`

Verboten in Text-TestSpecs und TestPlans:

- `gpt-4o-mini`
- `gpt-4o`
- `GPT-4o`
- `gemini-1.5-flash`
- `Gemini Pro`
- `Pro model`

Wenn nur deterministisch reparierbare Formatfehler gefunden werden:

```text
TESTSPEC PREFLIGHT NORMALIZED

Repairs:
- <Liste der Reparaturen>

Decision:
- Weiter mit TEST SKILL 1 unter SWE 1.6
```

Wenn keine Reparatur erforderlich ist:

```text
TESTSPEC PREFLIGHT PASSED

Repairs:
- none

Decision:
- Weiter mit TEST SKILL 1 unter SWE 1.6
```

Wenn nicht deterministisch reparierbare Fehler gefunden werden:

```text
TESTSPEC PREFLIGHT BLOCKED

Issue:
- <konkretes Problem>

Action:
→ TestSpec erneut mit `documentation/prompts/c_JANUS_FINAL_TESTSPEC_COPY_PROMPT_v1.0.md` normalisieren oder fehlende Entscheidung nachtragen
```

GPT-5.5 ist erst noetig, wenn die TestSpec formal reparierbar ist, aber Security-/Privacy-/Prompt-Injection-Scope fachlich HIGH/CRITICAL oder unklar bleibt.

Analysiere:

- Capability Name
- Test Objective
- Scope / Out of Scope
- Functional Test Matrix
- Natural Language Intent Matrix
- Provider and Model Test Matrix
- Security, Privacy & Prompt Injection Requirements
- Destructive Operation Safety
- User Data Safety
- Persistence Safety
- Logging & Telemetry Privacy
- Cost and Token Optimization Checks
- Skill/Tool Routing Checks
- Live Janus Test Cases
- Acceptance Criteria
- Blocking Conditions
- Retest Rules

Extrahiere nur explizite Informationen.

❌ Keine Interpretation
❌ Keine Ergaenzungen

---

### 2. SECURITY SCOPE GATE (HARD PROTOCOL)

Skill 1 MUSS vor der TestPlan-Erzeugung eine Security-Vorabpruefung durchfuehren.

Pruefe:

- **User data touched**: JA | NEIN | UNKLAR
- **Destructive operations possible**: JA | NEIN | UNKLAR
- **External content involved**: JA | NEIN | UNKLAR
- **Prompt injection surface**: JA | NEIN | UNKLAR
- **Persistence involved**: JA | NEIN | UNKLAR
- **Test sandbox required**: JA | NEIN | UNKLAR
- **Allowed to proceed**: JA | NEIN

Wenn Security HIGH/CRITICAL oder UNKLAR und nicht deterministisch loesbar:

```text
MODEL SWITCH REQUIRED: SWE 1.6 -> GPT-5.5

Reason:
- <konkrete Ursache: Security Scope unklar / destructive operations ohne Sandbox / prompt injection surface nicht abschaetzbar>

Action:
→ neuer Chat starten
→ TEST SKILL 1 erneut mit GPT-5.5 ausfuehren
```

---

### 3. TEST PLAN GENERATION

Skill 1 erzeugt den TestPlan ausschliesslich als **maschinenlesbare JSON-Datei** unter:

```text
documentation/test-runs/<test_run_id>_plan.json
```

Die Datei MUSS dem JSON-Schema des Generator Service entsprechen. Single Source of Truth ist:

```text
tests/e2e/generator/test-plan.schema.json
```

**Verbindliche Output-Regeln**:

- Skill 1 darf **keine** Markdown-Variante (`_plan.md`) mehr erzeugen.
- Die Datei MUSS rein maschinenlesbares JSON sein.
- Keine Markdown-Prosa, keine YAML-Front-Matter, keine Kommentare innerhalb der Datei (JSON kennt keine Kommentare).
- Erlaubt sind ausschliesslich Schluessel-Wert-Paare gemaess Schema.
- Strategy-IDs (`send`, `wait`, `evidence`, `evaluate`) MUeSSEN dem Schema-Enum entsprechen; freie Strings sind verboten.
- Provider-/Modellnamen MUeSSEN dem aktuellen Janus-Katalog folgen (siehe Section 1 Model-Katalog).
- Nach dem Schreiben MUSS Skill 1 deterministisch validieren:
  - JSON-Syntaxpruefung: `node -e "JSON.parse(require('fs').readFileSync('documentation/test-runs/<test_run_id>_plan.json', 'utf8'))"`
  - Bei Syntaxfehler MUSS Skill 1 den Plan neu erzeugen, bevor `TEST PLAN CREATED` ausgegeben wird.

**Verbindliches JSON-Schema (Pflicht-Form)**:

```json
{
  "testRunId": "TEST-RUN-YYYY-MM-DD-NNN",
  "title": "Capability Name",
  "executionMode": "LIVE_VISUAL",
  "target": "JANUS_CHAT",
  "chatWindow": "A",
  "baseUrl": "http://localhost:5173/",
  "backendHealthUrl": "http://localhost:8001/api/health",
  "timeouts": {
    "testCaseMs": 120000,
    "assistantResponseMs": 60000,
    "streamRequestMs": 15000
  },
  "strategies": {
    "send": "chat_button_click_send_v1",
    "wait": "assistant_text_present_v1",
    "evidence": "capture_network_v1",
    "evaluate": "contains_any_v1"
  },
  "tests": [
    {
      "id": "TC-001",
      "name": "Scenario Name",
      "type": "functional",
      "provider": "GPT",
      "model": "gpt-5.4-nano",
      "prompt": "User Prompt",
      "expected": {
        "containsAny": ["Term1"],
        "mustNotContain": ["ErrorTerm"]
      }
    }
  ]
}
```

**Feld-Constraints (aus Schema abgeleitet)**:

- `testRunId`: muss dem Pattern `^TEST-RUN-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}$` entsprechen.
- `executionMode`: einer von `LIVE_VISUAL` | `HEADLESS` | `LIVE_RETEST`.
- `target`: einer von `JANUS_CHAT` | `JANUS_DASHBOARD` | `JANUS_ELECTRON`.
- `chatWindow`: einer von `A` | `B` | `C` | `D`.
- `strategies.send`: `chat_window_scoped_send_v1` | `chat_button_click_send_v1`.
- `strategies.wait`: `assistant_stream_complete_v1` | `assistant_text_present_v1` | `error_toast_v1`.
- `strategies.evidence`: `capture_network_v1` | `capture_console_v1` | `capture_ui_state_v1`.
- `strategies.evaluate`: `contains_any_v1` | `must_not_contain_v1` | `tool_call_detected_v1`.
- `tests[].type`: `functional` | `intent_routing` | `ux` | `security` | `prompt_injection` | `cost_token` | `manual_gate`.
- `tests[].provider`: `GPT` | `Gemini` | `Any`.
- `tests[].model`: smallest-viable laut Janus-Katalog (siehe Section 1).
- `tests[].expected`: erlaubte Schluessel `containsAny`, `mustNotContain`, `responseTimeMsMax`, `requiresConfirmation`, `toolCallExpected`.

**Inhaltliche Mindestabdeckung aus der TestSpec (kein Markdown-Output, sondern als `tests[]`-Eintraege abgebildet)**:

- Testdaten/Sandbox MUSS in den `prompt`-Werten reflektiert sein, keine produktiven Userdaten.
- Provider-/Model-Matrix: pro Provider mindestens ein TestCase mit smallest-viable Modell.
- Model-Katalog-Hard-Gate: keine verbotenen alten Textmodelle in `tests[].model`.
- Security-/Prompt-Injection-/UX-/Intent-Routing-/Cost-Token-Faelle MUeSSEN als separate `tests[]`-Eintraege mit passendem `type` existieren, sofern die TestSpec sie fordert.
- Akzeptanzkriterien werden pro Test ueber `expected.containsAny`, `expected.mustNotContain`, `expected.toolCallExpected` etc. codiert; pauschale Prosa-Kriterien sind verboten.
- Stop/Block-Regeln, die nicht maschinenlesbar in `expected` ausdrueckbar sind, gehoeren NICHT in den TestPlan, sondern bleiben in der TestSpec und werden in Skill 2/3 zur Triage genutzt.

Verbotene Outputs von Skill 1:

- jegliche `.md`-TestPlan-Variante
- Markdown-Listen, Tabellen oder Prosa innerhalb der JSON-Datei
- Felder, die nicht im Schema definiert sind
- inline Strategy-Code oder Playwright-Snippets im Plan

---

## 🌐 OUTPUT LANGUAGE

Alle user-facing Zusammenfassungen, Bewertungen, Titel, Zielbeschreibungen, Next Steps und Fehlermeldungen MUeSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Klassennamen, Funktionsnamen und Modellnamen bleiben unveraendert.

---

## 📤 OUTPUT FORMAT

```text
TEST PLAN CREATED | TEST PLAN BLOCKED

TestRun-ID: TEST-RUN-YYYY-MM-DD-NNN
Capability: <Name>

Input TestSpec Path: <exact user-provided TestSpec path>
TestPlan Path: documentation/test-runs/<test_run_id>_plan.json

TestSpec Preflight:
- Status: PASSED | NORMALIZED | BLOCKED
- Repairs:
  - none | <deterministic repair list>

Security Gate:
- User data touched: JA | NEIN | UNKLAR
- Destructive operations possible: JA | NEIN | UNKLAR
- External content involved: JA | NEIN | UNKLAR
- Prompt injection surface: JA | NEIN | UNKLAR
- Persistence involved: JA | NEIN | UNKLAR
- Test sandbox required: JA | NEIN | UNKLAR
- Allowed to proceed: JA | NEIN

TestPlan:
- Path: documentation/test-runs/<test_run_id>_plan.json
- Format: JSON (machine-readable, schema-validated)
- Schema Source: tests/e2e/generator/test-plan.schema.json
- JSON Syntax Check: PASSED | FAILED
- Test Cases: <Anzahl>
- Provider/Model Tests: <Anzahl>
- Security Tests: <Anzahl>
- Prompt Injection Tests: <Anzahl>
- UX Tests: <Anzahl>
- Intent/Routing Tests: <Anzahl>

Akzeptanzkriterien:
- <Kriterium 1>
- <Kriterium 2>

Stop/Block-Regeln:
- <Regel 1>

Naechster Schritt:
→ TEST SKILL 2 mit TestSpec und TestPlan
```

---

## 📋 COPY-PASTE HANDOVER FUER TEST SKILL 2 (PFLICHT)

Am Ende bei TEST PLAN CREATED MUSS ein einzelner grauer Copy-Block ausgegeben werden.

Der Copy-Block MUSS ein echter fenced `text` Codeblock sein.

Der Copy-Block MUSS exakt mit einer Zeile beginnen, die nur aus drei Backticks und `text` besteht:

````markdown
```text
````

Der Copy-Block MUSS exakt mit einer Zeile enden, die nur aus drei Backticks besteht:

````markdown
```
````

Verboten im Copy-Block:
- absolute Windows-Pfade wie `C:\...`
- abweichende TestSpec-Pfade wie `documentation/test-specs/...`
- abgeleitete oder geratene TestSpec-Pfade
- fehlende Backticks vor oder nach dem Block
- loses Wort `text` ohne Backticks
- alternative Feldnamen wie `TestSpec Path:` oder `TestPlan Path:`

Der `TestSpec:` Wert MUSS exakt dem `Input TestSpec Path` entsprechen, den der User in Skill 1 angegeben hat.

Der Handover MUSS die folgenden Feldnamen exakt verwenden:

- `Mode: TEST_RUN_PRECHECK`
- `Execution Model: SWE 1.6`
- `TestSpec: <exact user-provided TestSpec path>`
- `TestPlan: documentation/test-runs/<test_run_id>_plan.json`
- `Target TestRun: <TEST-RUN-ID>`

Der `TestPlan:` Wert MUSS auf `.json` enden. Ein `.md`-Suffix ist im Copy-Block verboten und MUSS vor Ausgabe automatisch korrigiert oder die Antwort neu generiert werden.

Der Skill DARF NICHT stattdessen ausgeben:

- `TestSpec Path:`
- `TestPlan Path:`
- `TestRun-ID:`
- `Mode: PRECHECK`

Finaler Self-Check vor Antwort:

- Der letzte Handover-Block beginnt exakt mit einer eigenen Zeile, die nur ` ```text ` ohne Leerzeichen davor enthaelt.
- Direkt danach folgt `@[/TEST SKILL 2 – TEST RUN PRECHECK]`.
- Der letzte Handover-Block endet exakt mit einer eigenen Zeile, die nur ` ``` ` ohne Leerzeichen davor enthaelt.
- Es gibt kein loses Wort `text` vor dem Handover.
- Wenn einer dieser Punkte fehlschlaegt, MUSS der Skill die Antwort vor Ausgabe neu generieren.

```text
@[/TEST SKILL 2 – TEST RUN PRECHECK]

Mode: TEST_RUN_PRECHECK
Execution Model: SWE 1.6
TestSpec: <exact user-provided TestSpec path>
TestPlan: documentation/test-runs/<test_run_id>_plan.json
Target TestRun: <TEST-RUN-ID>

Context:
- Capability: <Name>
- TEST SKILL 1 Ergebnis: TEST PLAN CREATED
- Security Gate: <Ergebnis>

Arbeitsregel:
- Nutze die genannte TestSpec-Datei und TestPlan-Datei als verbindliche Artefakte.
- Ignoriere widerspruechliche oder zusaetzliche Chat-Kontexte.
- Erzeuge keine Implementation.
- Pruefe Runtime Safety, Provider-/Model-Matrix-Vollstaendigkeit und Testdatenverfuegbarkeit.
- Gib exakt READY FOR LIVE TEST oder TEST RUN BLOCKED aus.

Naechster erwarteter Output:
- READY FOR LIVE TEST oder TEST RUN BLOCKED
- Copy-Handover zu TEST SKILL 3 – LIVE JANUS TEST EXECUTION
```

Der Copy-Block ist PFLICHT, auch wenn davor bereits eine normale Zusammenfassung ausgegeben wurde.

---

## GPT-5.5 ESCALATION HANDOVER (COST-SAFE)

Wenn GPT-5.5 erforderlich ist, darf der Skill nicht mit voller Chat-Historie weiterarbeiten.

Stattdessen MUSS der Skill stoppen und genau einen kompakten Copy-Block fuer einen frischen GPT-5.5-Chat ausgeben.

```text
MODEL SWITCH REQUIRED: SWE 1.6 -> GPT-5.5

Reason:
- <konkreter Eskalationsgrund>

BEGIN COPY FOR NEW GPT-5.5 CHAT

@[/TEST SKILL 1 – TESTSPEC TO TEST PLAN]

Mode: ESCALATION_REVIEW
Execution Model: GPT-5.5

Binding Artifacts:
- TestSpec: <path>

Escalation Question:
- Kann diese TestSpec sicher und deterministisch in einen TestPlan uebersetzt werden, oder ist sie BLOCKED?

Relevant Evidence:
- <nur relevante TestSpec-Auszüge, Security-/Prompt-Injection-Unklarheiten, keine volle Chat-Historie>

Hard Rules:
- Use only listed artifacts and evidence as source of truth.
- Ignore previous chat history.
- Do not add product requirements.
- Do not implement code.
- Do not request full logs unless absolutely required.
- Decide only the escalation question.

Expected Output:
- Decision: PASS_TO_CONTINUE | BLOCKED | REQUIRED_TESTSPEC_FIX
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
KEINE Live-Tests
KEINE Architekturentscheidungen
KEINE Feature-Erweiterung
KEINE freien Interpretationen

VERBOTEN: Markdown-TestPlans unter `documentation/test-runs/<test_run_id>_plan.md`
VERBOTEN: Markdown-Prosa, Tabellen, Listen oder Kommentare innerhalb der TestPlan-JSON-Datei
VERBOTEN: Felder im TestPlan, die nicht im Schema `tests/e2e/generator/test-plan.schema.json` definiert sind
VERBOTEN: Strategy-IDs, die nicht in den Schema-Enums (`send`, `wait`, `evidence`, `evaluate`) gelistet sind
VERBOTEN: freie Modellnamen — nur Eintraege aus dem aktuellen Janus-Modellkatalog
VERBOTEN: Inline Playwright-Snippets oder JavaScript-Logik im TestPlan

PFLICHT: TestPlan-Output ausschliesslich als `documentation/test-runs/<test_run_id>_plan.json`
PFLICHT: JSON-Syntaxpruefung nach Erzeugung via `node -e "JSON.parse(require('fs').readFileSync('<plan_path>', 'utf8'))"`
PFLICHT: Schema-Konformitaet — die Datei MUSS vom Generator unter `tests/e2e/generator/generate-live-runner.mjs --plan <plan_path>` ohne Schema-Validation-Error verarbeitbar sein

---

## 🧠 ERROR HANDLING

Wenn TestSpec unvollstaendig:

```text
TESTSPEC INSUFFICIENT

Missing:
- <konkrete fehlende Teile>

Action:
→ TestSpec erweitern oder GPT-5.5 verwenden
```

---

## 🧠 OUTPUT GUARANTEE

Output ist immer:

deterministisch
testplan-orientiert
execution-ready fuer TestSkill 2
non-implementing
