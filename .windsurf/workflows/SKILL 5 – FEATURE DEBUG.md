---
description: Skill 5 – Iterativer Diamond-OS Feature-Debug mit datengetriebener Playwright-Auto-Verification, optionaler Janus-Sichtprüfung, SWE 1.6 und GPT-5.5-Eskalationshandover
---

# Skill 5 – Feature Debug

Dieser Workflow ist der **iterative Debug-Gate** der Diamond-OS Pipeline vor oder nach dem finalen Skill-6-Audit.

Skill 5 wird ausgeführt, wenn Skill 4, Skill 6, Playwright-/Audit-Evidence oder eine optionale Janus-Sichtprüfung eine Abweichung festgestellt hat.

## Zweck

Nutze Skill 5, wenn einer dieser Fälle eintritt:

- Skill 4 meldet `TASK EXECUTION FAILED`
- Skill 4 meldet `FIX LOOP LIMIT REACHED`
- Skill 6 meldet `BLOCKED`
- Skill 6 meldet `PASS WITH FIXES` und die Fixes sind nicht trivial oder nicht sicher isolierbar
- die automatisierte Gesamtverifikation aus Skill 4 (Playwright), eine optionale Janus-Sichtprüfung oder die Audit-Evidence aus Skill 6 weicht vom erwarteten Ergebnis ab
- ein Nutzer liefert tatsächlichen Janus-Output, Logs oder Screenshot, der nicht zum erwarteten Ergebnis passt

## Modell

Standard:

```text
SWE 1.6
```

Eskalation:

```text
GPT-5.5
```

nur wenn die Ursache nicht deterministisch eingrenzbar ist oder mehrere plausible Root Causes existieren oder fünf SWE-1.6-Iterationen nicht zum gewünschten Verhalten geführt haben.

## Required Input

Der User MUSS pro Iteration ein kompaktes Debug-Paket liefern:

```text
/SKILL 5 – FEATURE DEBUG

Skill 5 Debug Package:

Feature:
<Feature-Name>

Iteration:
1 | 2 | 3 | 4 | 5 | (optional – Skill 5 zählt automatisch, wenn nicht angegeben)

Task:
<task file / task id>

Spec:
<source spec file>

Pre-Check:
<PRE-CHECK PASSED oder relevante Pre-Check-Fehler>

Final Audit / Skill 6:
<PASS WITH FIXES | BLOCKED | relevante Findings>

Ist/Soll-Evidence (Playwright-Evidence bevorzugt; Janus optional):
- Auto-Verification / Evidence-Pfade: <`*_evidence.json`, Report-Pfade oder N/A>
- Optional Janus-Sichtprüfung — Prompt/Klickpfad: <was wurde getan | N/A>
- Erwartetes Ergebnis: <Soll>
- Tatsächliches Ergebnis: <Ist>
- Screenshot/Log/Output: <falls vorhanden>

Backend Log:
<relevanter Auszug oder Pfad/Datei>

Frontend Log:
<N/A | Pfad zu gefilterter Frontend-Log-Datei, z. B. frontend_log.md>

Changed Files:
- <Datei 1>
- <Datei 2>

Test Results:
- <Testname>: PASS | FAIL | N/A

Known Risks:
- <falls vorhanden>
```

**Automatische Iterationszählung:**
- Wenn der User keine Iterationsnummer angibt, zählt Skill 5 die Iterationen basierend auf der Anzahl der Debug-Pakete im aktuellen Chat.
- Skill 5 speichert die Iterationsnummer im Output-Format und verwendet sie für die nächste Iteration.
- Zähle nur Iterationen derselben Fehlerkette, d. h. gleiches Feature, gleicher Task und gleicher Ist/Soll-Konflikt.
- Wenn eine frühere Skill-5-Ausgabe im aktuellen Chat `Iteration: N` für dieselbe Fehlerkette enthält, ist die nächste Iteration `N+1`.
- Eine vom User angegebene Iteration darf nur übernommen werden, wenn sie zur bisherigen Fehlerkette passt; bei Widerspruch muss Skill 5 die erkannte Zählung offen melden.
- Iteration 1–5 sind SWE-1.6-Debug-Iterationen. Nach der **fünften** Iteration ohne erreichbare **§7-technische Freigabe** (Auto-Verification `PASS` und Final Feature Suite `PASS` auf dem Weg zu `FIXED`) darf keine sechste SWE-1.6-Fixrunde gestartet werden — es folgt nur noch Eskalation (siehe Eskalationsgrenze).
- **Progress-Validierung (Pflicht):** Ab Iteration 2 MUSS Skill 5 im Output explizit vergleichen: (a) Failure Code der **GENERATOR FAILURE TAXONOMY** (oder `N/A`, wenn keine Auto-Verification lief) und (b) das **Fehlerbild / Evidence** (Playwright-`*_evidence.json`-Pfad, Report-Pfade, manueller Ist-Text, relevante Log-/Screenshot-Hinweise, Auto-Verification-Excerpt) gegenüber der **unmittelbar vorherigen** Iteration derselben Fehlerkette. Dokumentiere im Block `Progress-Validierung` (siehe Output Format), ob sich Code und/oder Evidence geändert haben.
- **Intelligente Stopp-Regel:** Stoppe **vor Beginn der 5. Iteration** (d. h. es wird keine fünfte SWE-1.6-Fixrunde gestartet), wenn in **mindestens vier** aufeinanderfolgenden SWE-1.6-Iterationen **weder** der Failure Code **noch** das Fehlerbild (Evidence) gegenüber der jeweils vorherigen Iteration gewechselt hat. In diesem Fall MUSS Skill 5 `SKILL 5 ESCALATION REQUIRED` melden, die temporäre Eskalationsdatei anlegen und den GPT-5.5-Handover ausgeben — analog zur Eskalationsgrenze nach Iteration 5, mit Reason-Zeile `STAGNATION_NO_PROGRESS_ON_FAILURE_CODE_OR_EVIDENCE`.

Wenn Pflichtdaten fehlen:

```text
DEBUG PACKAGE INCOMPLETE

Missing:
- <konkrete fehlende Informationen>

Action:
→ Fehlende Debug-Artefakte nachreichen.
→ Keine Codeänderung ohne reproduzierbaren Ist/Soll-Konflikt.
```

**Evidence-Automation (ersetzt die frühere „Frontend-Log-Anforderung statt Konsolen-Copy“):**

**Playwright-Evidence hat Vorrang. Manuelle Logs sind der letzte Ausweg.**

- Skill 5 MUSS zuerst die Pipeline aus **AUTO-GENERATED VERIFICATION** nutzen: Mini-TestPlan JSON, Generator, Validator, Playwright-Runner (**headed**, **`workers=1`**), damit deterministische Artefakte entstehen (`playwright-report/`, `test-results/`, `documentation/test-results/<testRunId>/…`) inkl. **`*_evidence.json`** nach dem Lauf, sofern der Generator sie schreibt.
- **Manuelle** Logs (`frontend_log.md`, `Ctrl+Shift+L`, Backend-Auszüge in den Chat) **nur** als **letzter Ausweg**, wenn Playwright nicht anwendbar (`Auto-Verification: N/A` nach Skill-4-Regel), Evidence-Dateien fehlen, oder die Playwright-Evidence den Ist/Soll-Konflikt trotz **Diagnostics** (Trace/Network/Console-Strategien im TestPlan) nicht belegt — dann erst gezieltes, kompaktes Frontend-Log (**kein** vollständiges DevTools-Console-Copy).

Optionaler **letzter Ausweg** — kompaktes Frontend-Log anfordern:

```text
FRONTEND LOG REQUIRED (nur nach fehlender/unzureichender Playwright-Evidence)

Bitte führe genau diesen Test aus:
1. <konkreter Klickpfad oder Prompt>
2. <erwarteter sichtbarer Zustand>
3. <abweichenden Zustand nicht korrigieren, App offen lassen>

Danach bitte bereitstellen:
- Datei: per `Ctrl+Shift+L` erzeugter Pfad oder `frontend_log.md`
- Inhalt: nur Test-Zeitfenster, error/warn, API/IPC/Stacktrace
```

## Hard Rules

STRICT PROVIDER ISOLATION: Janus ist ein BYOK-Tool. Implementiere oder erlaube NIEMALS automatische Provider-Fallbacks (z.B. Gemini zu GPT) im Produktcode. Wenn ein Provider-spezifischer Test (z.B. Gemini) fehlschlägt, muss er als Fehler dieses Providers behandelt werden. Ein Ausweichen auf einen anderen Provider zur Fehlerumgehung ist STRENG VERBOTEN.

- Keine neuen Features.
- Keine Architekturänderungen.
- Kein Refactoring außerhalb des betroffenen Task-Scopes.
- Keine Spekulation ohne Ist/Soll-Vergleich.
- Nicht denselben Fix zweimal wiederholen.
- Maximal fünf Skill-5-Iterationen mit SWE 1.6 pro Fehlerkette.
- Jede Iteration muss **neue oder aktualisierte Evidence** liefern (z. B. Auto-Verification-Excerpt, geänderte `*_evidence.json`, Final-Suite-Lauf, kompaktes Backendlog). Reine wiederholte Nutzerprosa ohne neue Evidence reicht nicht.
- Bei frontendnahen Fehlern gilt nach **Evidence-Automation** ein neues oder aktualisiertes `frontend_log.md` bzw. `Ctrl+Shift+L`-Pfad als gültiges **manuelles** Debug-Artefakt (**letzter Ausweg**).
- **FRONTEND-LOG-DISZIPLIN:** Skill 5 darf bei frontendnahen Electron-/Renderer-Problemen nicht pauschal „komplette Console kopieren“ verlangen. **Zuerst** Playwright-Evidence und Mini-TestPlan-Diagnostics; **danach** gezieltes kompaktes Frontend-Log (`frontend_log.md` oder konkreter Pfad). Große Rohlogs müssen zusammengefasst oder gefiltert werden.
- Nach jeder Fix-Iteration muss Skill 5 zuerst **AUTO-GENERATED VERIFICATION** (sofern nicht N/A) ausfuehren; eine **optionale** Janus-Sichtprüfung darf parallel empfohlen werden, ersetzt aber keine `PASS`-Evidence.
- Nach `FIXED` (nur bei **Auto-Verification `- Status: PASS`** und bestandener **Final Feature Suite**, siehe §7) MUSS Skill 5 **im selben finalen Output** den grauen Skill-6-Re-Audit-Copy-Block ausgeben (`@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]`).
- Wenn es nach der fünften Iteration nicht wie gewünscht funktioniert: `SKILL 5 ESCALATION REQUIRED` melden und ein kompaktes GPT-5.5-Handover ausgeben.
- **Proaktive GPT-5.5-Empfehlung:** Bei Iteration 5 (oder wenn nach Iteration 5 weiterhin kein §7-`PASS`-Pfad erreichbar ist) MUSS Skill 5 proaktiv empfehlen, zu GPT-5.5 zu wechseln, und dabei angeben, ob ein neuer Chat zum Kostensparen sinnvoll ist. Optional bereits ab Iteration 4, wenn die Progress-Validierung zeigt, dass nur noch geringe Differenzierung möglich ist — Pflicht bleibt die Empfehlung spätestens bei Iteration 5 bzw. nach Stagnations-Stopp.
- Debugging läuft gegen Spec, Task, Pre-Check, Skill-6-Audit und tatsächlichen Output.
- Chatverlauf ist nicht bindend; Artefakte sind bindend.
- **AUTOMATISCHE FIX-IMPLEMENTIERUNG:** Wenn Root Cause und Fixplan eindeutig sind (LOW oder MEDIUM Risiko), MUSS Skill 5 den Fix SOFORT implementieren, nicht nur einen Plan vorschlagen. Nur bei HIGH Risiko oder mehrdeutigen Root Causes darf Skill 5 nur einen Plan vorschlagen.
- **KEINE SCHEINFIXES:** Skill 5 darf niemals behaupten, Fixes seien umgesetzt, wenn keine Dateiänderung durchgeführt wurde. Ein Fix gilt nur als umgesetzt, wenn Skill 5 im selben Lauf ein Edit-Tool verwendet, die geänderten Dateien nennt und die Änderung im Output als Implementierungsnachweis zusammenfasst.
- **KEIN "AUF NACHFRAGE":** Wenn ein eindeutiger LOW/MEDIUM-Fix möglich ist, darf Skill 5 nicht zuerst nur einen Vorschlag ausgeben und auf eine spätere Nachfrage warten. Der Fix muss im aktuellen Skill-5-Lauf umgesetzt werden.
- **PLAN-ONLY IST KEIN FIX:** Wenn Skill 5 wegen HIGH Risiko, unklarer Root Cause oder fehlenden Artefakten nicht editiert, muss der Status `BLOCKED`, `OUT OF SCOPE` oder `ESCALATION REQUIRED` lauten. `FIXED` oder `NEEDS RETEST` sind dann verboten.
- **TEMPORÄRE ESKALATIONSDATEI:** Nach der fünften SWE-1.6-Iteration ohne erreichbare §7-Freigabe **oder** bei Auslösung der **Intelligente Stopp-Regel** (Stagnation) muss Skill 5 eine temporäre Markdown-Datei unter `.windsurf/tmp/skill5_escalation_<feature-or-task>_<YYYYMMDD-HHMM>.md` erstellen. Diese Datei enthält das kompakte GPT-5.5-Handover und ersetzt das lange Backendlog.

## AUTO-GENERATED VERIFICATION & FAILURE TAXONOMY (verbindlich)

Skill 5 ersetzt das fruehere implizite "nur manuell retesten" fuer Chat-relevante Fixes durch **dieselbe** technische Janus-Live-Kette wie Skill 4 **### 5. AUTO-GENERATED VERIFICATION GATE** (Mini-TestPlan JSON, Generator, Validator, headed Playwright). Skill 5 fuehrt die Shell-Befehle selbst aus und protokolliert — keine reine Prosa ohne Lauf.

**Ausloesung:** Nach jedem Skill-5-Code-Fix, der Frontend-, Backend-Chat-, Tool-, Routing- oder Stream-Pfade beruehrt, MUSS Skill 5 (oder nachvollziehbar `Auto-Verification: N/A` mit gleicher Begruendungsregel wie Skill 4) ausfuehren:

1. `documentation/test-runs/<task_or_iteration_id>_verify.json` anlegen (Schema `tests/e2e/generator/test-plan.schema.json`, Strategies nur aus `strategy-registry.json`).
2. `node tests/e2e/generator/generate-live-runner.mjs --plan ... --out tests/e2e/generated/<id>_verify.live.spec.js`
3. `node tests/e2e/generator/validate-runner.mjs --plan ... --runner ...`
4. `npx playwright test tests/e2e/generated/<id>_verify.live.spec.js --headed --workers=1`

**Erst danach** optional: **Sichtprüfung Janus** (Produkt-UX, kein technisches Gate für `FIXED`). Wenn Auto-Verification **FAIL**: kein `FIXED` / kein `NEEDS RETEST` ohne erneute Fix-Runde; Root-Cause-Analyse MUSS untenstehende Taxonomie verwenden.

### GENERATOR FAILURE TAXONOMY (BINDEND — Fehleranalyse)

Quelle: `tests/e2e/generator/generate-live-runner.mjs`. Umetikettieren verboten.

| Failure Code | Bedeutung (kurz) | Suggested Triage Bucket |
|----------------|------------------|-------------------------|
| `RUNNER_PRECLICK_EMPTY` | Textarea leer nach Eingabe | Test Runner / Frontend Input Path |
| `RUNNER_PRECLICK_DOM_BROKEN` | Send-Button/Form-DOM gebrochen | Frontend DOM Regression |
| `RUNNER_SELECTOR_FAILURE` | Selector nicht gefunden | Test Runner / Selector Drift |
| `RUNNER_WAIT_FAILURE` | Wait nicht erfuellt | Test Runner / Wait Strategy |
| `RUNNER_STREAM_TIMEOUT` (A/B) | kein Stream / leere Bubble | Frontend Send vs SSE/Backend (Variante B: Ghost/SSE siehe Skill-4-Hinweise zu `[SSE-REANCHOR]` / `[SSE-FIRST-TEXT]`) |
| `FRONTEND_NOT_READY` | Dev-Server down | Infrastructure / Environment |
| `BACKEND_HEALTH_FAIL` | Health fail | Infrastructure / Environment |
| `PROVIDER_TIMEOUT` | Provider/Error-Bubble | Backend / Provider / Cost |
| `TOOL_ROUTING_FAILURE` | falsches Tool | Intent / Tool Routing |
| `ASSERTION_MISMATCH` | Text-Expectation | Capability Behavior / Spec Drift |

**FEHLER-PROTOKOLL (Pflicht bei FAIL):** Im Skill-5-Output Block `FAILURE LOG (BINDEND)` mit TestRunId, exaktem Failure Code, Suggested Triage aus Tabelle, Evidence-Pfaden (`playwright-report/`, `test-results/`, **`documentation/test-results/<testRunId>/<TESTCASE>_evidence.json`** bzw. alle vorhandenen `*_evidence.json` des Laufs), kurzem Excerpt — analog Skill 4.

## Ablauf

### 1. Reproduktionscheck

Ein Reproduktionscheck erfolgt **primär** durch die Erstellung eines **Mini-TestPlans** und die **Ausführung des Runners** (Generator/Validator/Playwright) mit im TestPlan aktivierten **Diagnostics**-Strategien (z. B. Network/Console/UI-State laut `strategy-registry.json`) — nicht durch Raten oder reines Chat-Repro ohne Artefakte.

Prüfe:

- Was war der erwartete Zustand?
- Was war der tatsächliche Zustand?
- Ist der Fehler reproduzierbar?
- Betrifft der Fehler den validierten Task-Scope?
- Ist der Fehler frontendnah und benötigt Renderer-/Frontend-Evidenz?

Wenn der Fehler frontendnah ist und **weder** Playwright-Evidence (`_*_evidence.json`, Report-Pfade) **noch** ein kompaktes manuelles Log vorliegt — nachdem die **Evidence-Automation** (oben) ausgeschöpft wurde:

```text
FRONTEND LOG REQUIRED (letzter Ausweg — siehe Evidence-Automation)

Reason:
- Der Ist/Soll-Konflikt betrifft Frontend/Renderer/UI/IPC/Client-State und ist mit vorhandener Playwright-Evidence noch nicht deterministisch eingrenzbar.

Bitte führe genau diesen Test aus:
1. <konkreter Prompt/Klickpfad aus der Repro (Janus oder definierter Smoke-Pfad)>
2. <erwartetes Ergebnis>
3. <tatsächliche Abweichung beobachten>

Danach bitte bereitstellen:
- Frontend Log: nach dem Repro in Janus `Ctrl+Shift+L` drücken und den angezeigten Pfad zur automatisch erzeugten Frontend-Log-Datei angeben
- Inhalt: nur Test-Zeitfenster, error/warn, API/IPC-Fehler, Stacktraces und relevante Console-Meldungen
- Nicht nötig: vollständiges DevTools-Console-Log

Action:
→ Keine Codeänderung, bis das frontendnahe Debug-Artefakt vorliegt oder der Fehler anderweitig deterministisch belegbar ist.
```

Wenn der Fehler nicht reproduzierbar ist:

```text
DEBUG BLOCKED – NOT REPRODUCIBLE

Action:
→ exakten Prompt/Klickpfad, Output und Logs nachreichen.
```

### 2. Scope-Gate

Prüfe, ob der Fehler innerhalb des ursprünglichen Task-Scopes liegt.

Wenn nein:

```text
DEBUG OUT OF SCOPE

Reason:
- <warum außerhalb des validierten Tasks>

Action:
→ neue Spec/Task über Skill 1/2 starten oder als separates Bugfix-Feature planen.
```

### 3. Root-Cause-Hypothese

PROVIDER FIDELITY: Stelle sicher, dass Tool-Calls und Intent-Detection exakt für den aktiven Provider funktionieren. Wenn ein Bug nur bei Gemini auftritt (z.B. Schema-Deduplizierung), darf der Fix nicht dazu führen, dass das System intern auf GPT-Logik zurückgreift. Debugge den Provider-spezifischen Stacktrace bis zur Wurzel.

Formuliere genau eine primäre Root Cause.

**Bei vorherigem oder gleichzeitigem Auto-Verification-FAIL:** Die Root Cause MUSS zum **exakten** `Failure Code` aus der GENERATOR FAILURE TAXONOMY (Abschnitt oben) in Beziehung stehen — derselbe Code im Feld `Ursache:` oder `Evidenz:` nennen, ohne Umbenennung. Der **Suggested Triage Bucket** aus der Tabelle MUSS als naechster technischer Suchraum genannt werden.

Format:

```text
Root Cause Candidate:
- Ursache: <konkret>
- Evidenz: <Datei/Test/Output/Log>
- Betroffene Datei(en): <Liste>
- Risiko: LOW | MEDIUM | HIGH
```

Wenn mehrere gleich plausible Ursachen existieren:

```text
MODEL SWITCH REQUIRED: SWE 1.6 → GPT-5.5

Reason:
- Mehrere plausible Root Causes, keine deterministische Entscheidung möglich.
```

### 4. Minimaler Fixplan

Erstelle nur einen minimalen Fixplan:

```text
Debug Fix Plan:
- Target File(s): <Liste>
- Change: <minimaler Fix>
- Tests: <gezielte Unit/Integration-Tests> + Auto-Verification (Mini-TestPlan-Pfad oder `N/A` mit Begruendung)
- Rollback Risk: LOW | MEDIUM | HIGH
```

### 5. Iteration und Fix-Ausführung

Implementiere SOFORT mit den verfügbaren Tools (edit, multi_edit, write_to_file), wenn Root Cause und Fixplan eindeutig sind.

**AUSNAHMEN (nur Plan vorschlagen, nicht implementieren):**
- Risiko = HIGH
- Mehrdeutige Root Causes (mehrere gleich plausible Ursachen)
- Root Cause nicht deterministisch eingrenzbar

**IMPLEMENTIERUNGS-PFLICHT:**
- Wenn Risiko = LOW oder MEDIUM und Root Cause eindeutig: MUSST du den Fix SOFORT implementieren, nicht nur einen Plan vorschlagen.
- Nutze die verfügbaren Tools: edit, multi_edit, write_to_file.
- Keine manuelle Eingabe durch den User erforderlich.
- Vor dem finalen Skill-5-Output muss ein Implementierungsnachweis vorliegen:
  - geänderte Datei(en)
  - konkrete Änderung in 1-3 Sätzen
  - ausgeführte oder begründet übersprungene gezielte Tests **und** Auto-Verification (Playwright-Kette oder `N/A` mit Begruendung)
- Wenn kein Edit-Tool verwendet wurde, darf `Geänderte Dateien` nicht so klingen, als seien Änderungen umgesetzt worden. Verwende dann `Keine — Plan-only, nicht umgesetzt` und melde keinen `FIXED`/`NEEDS RETEST`-Status.

Nach Fix:

- **AUTO-GENERATED VERIFICATION** (Mini-TestPlan + Generator + Validator + Playwright) ausfuehren, sofern nicht `N/A` nach Skill-4-Regel; bei `FAIL` FAILURE LOG mit Taxonomie ausgeben und keine Erfolgsstatus-Claims.
- gezielte Unit/Integration-Tests ausführen, die der Task/Fix verlangt
- **Finale Feature-Suite:** vor `FIXED` die vollständige Playwright-/E2E-Suite des Features ausführen (§7) — nicht nur den Mini-Plan.
- optional: User zur **Janus-Sichtprüfung** einladen (kein Pflicht-Gate für `FIXED`)
- Ergebnis gegen erwartetes Verhalten anhand **PASS**-Evidence prüfen
- bei erfüllter §7-Pflicht: **sofort** den grauen Skill-6-Re-Audit-Block (`@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]`) ausgeben — **One-Click Audit Handover**
- wenn nicht erfolgreich: nächste Skill-5-Iteration mit neuem Evidence-Paket starten

### 6. Eskalationsgrenze

**Harte Obergrenze:** Wenn nach **Iteration 5** weiterhin kein gültiger **§7-PASS-Pfad** (Auto-Verification `PASS` und Final Feature Suite `PASS` auf dem Weg zu `FIXED`) erreichbar ist, gilt `SKILL 5 ESCALATION REQUIRED` (Block unten).

**Intelligente Stopp-Regel:** Stoppe **vor Beginn der 5. Iteration** (keine fünfte SWE-1.6-Fixrunde), wenn in **mindestens vier** aufeinanderfolgenden SWE-1.6-Iterationen **weder** der Failure Code (Taxonomie) **noch** das Fehlerbild (Evidence) gegenüber der jeweils vorherigen Iteration gewechselt hat. Dann ebenfalls `SKILL 5 ESCALATION REQUIRED` mit Reason `STAGNATION_NO_PROGRESS_ON_FAILURE_CODE_OR_EVIDENCE` (temporäre Eskalationsdatei + GPT-5.5-Handover wie unten).

Wenn nach Iteration 5 die technische Freigabe gemäß §7 nicht erreichbar ist **oder** die Intelligente Stopp-Regel auslöst:

```text
SKILL 5 ESCALATION REQUIRED

Reason:
- Fünf SWE-1.6-Debug-Iterationen konnten die §7-Exit-Kriterien (Auto-Verification + Final Feature Suite) für `FIXED` nicht herstellen.
  ODER
- STAGNATION_NO_PROGRESS_ON_FAILURE_CODE_OR_EVIDENCE: mindestens vier aufeinanderfolgende Iterationen ohne Änderung an Failure Code oder Evidence (Progress-Validierung).

Action:
→ Erstelle eine temporäre Eskalationsdatei unter `.windsurf/tmp/skill5_escalation_<feature-or-task>_<YYYYMMDD-HHMM>.md`.
→ Öffne GPT-5.5 in einem neuen Chatfenster, um Tokens zu sparen.
→ Übergib GPT-5.5 kein vollständiges Backendlog.
→ Verwende nur die temporäre Eskalationsdatei und den Copy-Paste-Handover unten.
```

**Kostenoptimierung bei GPT-5.5-Wechsel:**
- Nach der **fünften** SWE-1.6-Iteration ohne §7-Freigabe **oder** nach Stagnations-Stopp MUSS Skill 5 immer einen neuen GPT-5.5-Chat empfehlen.
- Der neue Chat nutzt nur die temporäre Eskalationsdatei als kompakten Kontext.
- Diese Empfehlung MUSS im Output Format unter "Nächster Schritt" enthalten sein.

Die temporäre Datei MUSS kompakt sein und große Logs zusammenfassen.

Temporäre Datei:

```text
Pfad:
.windsurf/tmp/skill5_escalation_<feature-or-task>_<YYYYMMDD-HHMM>.md

Regeln:
- Datei nur bei `SKILL 5 ESCALATION REQUIRED` erstellen.
- Keine vollständigen Backendlogs einfügen.
- Nur harte Fehler, Trace IDs, Zeitfenster, wiederholte Symptome, ausgeschlossenen Noise und geänderte Dateien zusammenfassen.
- Am Ende vermerken: "Diese Datei ist temporär und muss von Skill 7 nach abgeschlossenem Debug-/Dokumentations-Gate gelöscht werden."
```

Format:

```text
GPT-5.5 Skill-5 Escalation Handover:

Feature:
<Feature-Name>

Task/Spec:
- Spec: <Pfad>
- Task: <Pfad/ID>

Expected Behavior:
<Soll aus Skill 6 / Spec / Playwright-Evidence>

Actual Behavior After up to 5 SWE-1.6 Iterations (or early stagnation stop):
<Ist kurz und konkret>

Iteration Summary:
1. <Root Cause Candidate, Fix, Test result>
2. <Root Cause Candidate, Fix, Test result>
3. <Root Cause Candidate, Fix, Test result>
4. <Root Cause Candidate, Fix, Test result oder N/A>
5. <Root Cause Candidate, Fix, Test result oder N/A>

Backend Log Compression:
- Hard Errors: <Liste der relevanten Fehlercodes/Tracebacks>
- Trace IDs: <falls vorhanden>
- Time Window: <Zeitfenster>
- Repeated Symptoms: <Muster>
- Excluded Noise: <was bewusst nicht relevant ist>

Frontend Log Compression:
- Frontend Log File: <Pfad oder N/A>
- Time Window: <Zeitfenster>
- Hard Errors: <Console/API/IPC/Stacktrace-Auszüge>
- Repeated Symptoms: <Muster>
- Excluded Noise: <was bewusst nicht relevant ist>

Changed Files:
- <Datei>: <kurzer Grund>

Tests:
- <Test>: PASS | FAIL | N/A

Open Question for GPT-5.5:
<eine präzise Frage, die SWE 1.6 nicht deterministisch lösen konnte>
```

Zusätzlich muss Skill 5 dem User diesen Copy-Paste-Handover für den neuen GPT-5.5-Chat ausgeben:

```text
BEGIN COPY FOR NEW GPT-5.5 CHAT
/SKILL 5 – FEATURE DEBUG

Modell: GPT-5.5

Bitte lies zuerst diese temporäre Eskalationsdatei:
<Pfad zu .windsurf/tmp/skill5_escalation_...md>

Führe Skill 5 auf Basis dieser Datei aus.
Wichtig:
- Verwende die temporäre Datei als kompaktes Debug-Handover.
- Fordere nicht das vollständige Backendlog an, außer die Datei enthält eine klar benannte fehlende Evidenz.
- Debugge nur die dort beschriebene Fehlerkette.
- Wenn du einen eindeutigen LOW/MEDIUM-Fix findest, implementiere ihn direkt und behaupte keine Umsetzung ohne tatsächliche Dateiänderung.
END COPY FOR NEW GPT-5.5 CHAT
```

### 7. Automated Final Verification & Audit Gate (Re-Audit-Handover)

**Technische Freigabe — `FIXED`:** `SKILL 5 DEBUG RESULT: **FIXED**` ist **nur** zulässig, wenn die **Auto-Verification** im Output einen Block **`Auto-Verification:`** mit der Zeile **`- Status: PASS`** enthält. Der **manuelle Janus-Test** ist **optional** (reine **Sichtprüfung**); er ist **kein** Pflicht-Gate mehr für `FIXED` und **kein** Ersatz für Playwright-Daten.

**Finale Test-Suite (Pflicht vor `FIXED`):** Bevor Skill 5 abgeschlossen wird und **`FIXED`** meldet, MUSS die für das **betroffene Feature** relevante **vollständige** Playwright-/E2E-Test-Suite **automatisiert** und **erfolgreich** durchlaufen — **nicht** nur der Mini-Verification-Plan. Quellen: Task, Spec, `documentation/test-runs/*.json`, `package.json` (z. B. `npm run test:e2e` / projektüblicher Gesamt-Playwright-Befehl). **Ohne** definierbare Suite: im Output **`FINAL SUITE: N/A WITH REASON`** — dann **kein** `FIXED` und **kein** Skill-6-Handover, bis eine Suite definiert oder eskaliert wurde (Skill 2 / Owner).

**One-Click Audit Handover:** Sobald **Auto-Verification `PASS`** **und** die **Finale Test-Suite** (soweit anwendbar) **`PASS`** sind, MUSS Skill 5 **im selben finalen Response** den **grauen** Copy-Paste-Block **`BEGIN COPY FOR SKILL 6 RE-AUDIT`** mit **`@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]`** ausgeben — ohne Warten auf eine manuelle Nutzerbeschreibung oder eine blockierende manuelle Bestätigungsrunde.

Ziel:
- maximale Audit-Qualität bei minimal nötigen Modellkosten
- kein voller Skill-5-Debug-Chatverlauf im Audit
- Audit gegen Spec, Task, ursprüngliches Skill-6-Finding, Debug-Fix, Diff, **alle** relevanten **Evidence-Pfade** (siehe Re-Audit-Paket) und automatisierte Testresultate

#### Audit Model Gate (Risiko-Kalkulator)

- Skill 5 MUSS eine konservative **Audit Risk**-Klasse und **`Audit Model To Use`** ausgeben.
- Skill 5 darf für das Re-Audit nur **`SWE 1.6`** oder **`GPT-5.5`** empfehlen. `Kimi k2.5` ist unzulässig.
- Format:
  - `Audit Risk: LOW | MEDIUM | HIGH | CRITICAL`
  - `Recommended Audit Model: SWE 1.6 | GPT-5.5`
  - `Audit Model To Use: SWE 1.6 | GPT-5.5` (**verbindlich** für den Copy-Block)
  - `Reason: <kurz>`

**LOW / MEDIUM (typisch lokaler Fix, Regex, Guard, kleine UI-Anpassung):** → **`Audit Model To Use: SWE 1.6`**, sofern die **Compiler-Regel** unten **nicht** GPT-5.5 erzwingt.

**HIGH / CRITICAL (u. a. Protokoll, Security-Bypasses, komplexe State-Maschinen, Provider-Kern, IPC, Persistenz):** → **`Audit Model To Use: GPT-5.5`** (Pflicht-Audit).

**Compiler-Regel — `Audit Model To Use` (überschreibt LOW/MEDIUM, wenn greifend):**
- Wenn **aktuelle Iterationsnummer > 3** **ODER** der Fix **security-relevant** ist (Auth, Trust, Secrets, Sandboxing) **ODER** **Code-Drift** / instabile Schnittstelle / mehrere Subsysteme ohne klare Isolation → **`Audit Model To Use: GPT-5.5`**.
- **Sonst** → **`Audit Model To Use: SWE 1.6`**, es sei denn `Audit Risk` ist **HIGH** oder **CRITICAL** oder die **Unsicherheitsregel** greift — dann immer **`GPT-5.5`**.

**Unsicherheitsregel:** Ist die Risikoklasse nicht eindeutig niedrig/mittel → **`GPT-5.5`**.

Skill-6-Re-Audit-Chat-Regel:
→ Skill 6 SOLL in einem neuen Audit-Chat mit **`Audit Model To Use`** ausgeführt werden.
→ Bei **`Audit Model To Use: GPT-5.5`** (oder `Audit Risk: HIGH|CRITICAL`) MUSS GPT-5.5 verwendet werden.
→ Der Skill-5-Debug-Chat darf nicht als Audit-Kontext verwendet werden.
→ Skill 6 darf nur aus dem kompakten Re-Audit-Paket auditieren.
→ Kein vollständiger Chatverlauf, keine Rohlogs, keine Debug-Diskussionen kopieren.
→ **`FIXED` finaler Output-Typ:** Der Response MUSS bei `FIXED` **immer** den grauen Block mit **`@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]`** enthalten (siehe Template).
→ Der Copy-Paste-Block MUSS die Zeile **`Audit Model To Use: SWE 1.6`** oder **`Audit Model To Use: GPT-5.5`** exakt setzen (konsistent mit Compiler-Regel und Audit Model Gate).

**Compiler-Validierung (FIXED-Abschluss):** Ein Response mit `SKILL 5 DEBUG RESULT: FIXED` gilt nur als konform, wenn (a) im Output **`Auto-Verification:`** mit **`- Status: PASS`** steht, (b) die **Finale Feature-Suite** gemäß §7 **`PASS`** geliefert hat (bzw. kein `FIXED` bei `FINAL SUITE: N/A WITH REASON`), und (c) **derselbe** finale Response den **grauen** Copy-Block **`BEGIN COPY FOR SKILL 6 RE-AUDIT`** mit **`@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]`** enthält — das ist der **verbindliche** Abschluss-Artefakt-Typ für `FIXED`; kein separates manuelles Gate.

Copy-Paste-Prompt für neuen Skill-6-Re-Audit-Chat:

```text
BEGIN COPY FOR SKILL 6 RE-AUDIT
@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]

WICHTIG:
- Dies ist ein neuer Re-Audit-Chat mit dem verbindlichen Audit-Modell.
- Audit Model To Use: <SWE 1.6 | GPT-5.5>
- Nutze ausschließlich dieses kompakte Re-Audit-Paket.
- Ignoriere früheren Chatverlauf, Debug-Diskussionen, Rohlogs und nicht genannte Dateien.
- Wenn die Compiler-Regel oder das Audit Model Gate GPT-5.5 vorschreibt, verwende GPT-5.5.

Audit Model Gate:
- Audit Risk: <LOW | MEDIUM | HIGH | CRITICAL>
- Recommended Audit Model: <SWE 1.6 | GPT-5.5>
- Audit Model To Use: <SWE 1.6 | GPT-5.5>
- Reason: <kurze Begründung>

Re-Audit Package:

Feature:
<Feature-Name>

Spec:
<source spec file>

Task:
<task file / task id>

Original Skill-6 Finding:
<PASS WITH FIXES | BLOCKED | konkretes Finding>

Skill-5 Debug Result:
- Iteration: <1 | 2 | 3 | 4 | 5>
- Root Cause: <konkret>
- Fix Summary: <kurz>

Changed Files:
- <Datei 1>
- <Datei 2>

Relevant Diff / Excerpts:
- <Datei 1>:
  - <kurze relevante Änderung>
- <Datei 2>:
  - <kurze relevante Änderung>

Test Results:
- Auto-Verification (Mini): PASS — <Mini-TestPlan-Pfad>
- Final Feature Suite: PASS — <Befehl + Referenz z. B. documentation/test-runs/FEATURE_plan.json oder package.json-Script>
- Unit/Integration: <PASS | N/A>

Accumulated Evidence Paths (alle erfolgreichen Debug-Iterationen / letzter grüner Lauf):
- Iteration 1: <`*_evidence.json`-Pfad(e), playwright-report/, test-results/, documentation/test-results/…>
- Iteration N: <…>
- Letzter grüner Lauf: <konsolidierte Pfadliste>

Optional UX Sichtprüfung (Janus, nicht bindend für FIXED):
- Kurznotiz: <freiwilliger User-Check / N/A>

Known Risks:
- <bekannte Risiken oder Keine>

Audit Scope:
Bitte prüfe nur, ob das ursprüngliche Skill-6-Finding durch den Skill-5-Fix behoben wurde, ob Spec/Task weiterhin erfüllt sind und ob der Fix Regressionen oder Scope Drift erzeugt.
Alle anderen Workspace-Änderungen sind out of scope.
END COPY FOR SKILL 6 RE-AUDIT
```

## Output Format

```text
SKILL 5 DEBUG RESULT: FIXED | NEEDS RETEST | ESCALATION REQUIRED | BLOCKED | OUT OF SCOPE

Zusammenfassung:
- Feature: <Name>
- Task: <ID>
- Iteration: 1 | 2 | 3 | 4 | 5
- Fehler: <kurz>
- Root Cause: <konkret>

Progress-Validierung (ab Iteration 2 verpflichtend; bei Iteration 1: `N/A — erste Iteration` für die drei Vergleichszeilen):
- Failure Code (diese Iteration): <Taxonomie-Code | N/A>
- Evidence / Fehlerbild geändert ggü. Iteration N-1: JA | NEIN
- Konsekutive Stagnation (weder Code noch Evidence gewechselt): <0–4+> aufeinanderfolgende Iterationen
- Intelligente Stopp-Regel ausgelöst: JA | NEIN (bei JA: Reason STAGNATION_NO_PROGRESS_ON_FAILURE_CODE_OR_EVIDENCE, kein Start Iteration 5)

Geänderte Dateien:
- <Datei>

Implementierungsnachweis:
- Edit-Tool verwendet: JA | NEIN
- Tatsächlich geänderte Dateien: <Liste oder Keine>
- Änderung umgesetzt: JA | NEIN
- Wenn NEIN: Status darf nicht FIXED oder NEEDS RETEST sein.

Tests:
- Auto-Verification (Mini, Playwright generated): PASS | FAIL | N/A — Mini-TestPlan: <Pfad> — Failure Code (bei FAIL): <Taxonomie-Code oder N/A>
- Final Feature Suite (vollständige E2E des Features, §7): PASS | FAIL | N/A — <Befehl + Plan-/Run-Referenz oder N/A WITH REASON laut §7>
- Unit/Integration: PASS | FAIL | N/A

Playwright Evidence (Pflicht, sofern Lauf stattfand):
- Pfad(e) zu `*_evidence.json` (typisch `documentation/test-results/<testRunId>/<TESTCASE>_evidence.json`): <Pfad(e) oder N/A mit Begründung>
- Playwright Report / test-results: <Pfad(e) oder N/A>

Frontend Log:
- Benötigt: JA | NEIN
- Datei: <frontend_log.md | Pfad | N/A>
- Status: VORHANDEN | ANGEFORDERT | N/A

Skill 6 Re-Audit Handover:
- Benötigt: JA bei FIXED (§7: Auto-Verification `- Status: PASS` + Final Feature Suite PASS; Copy-Block **im selben** finalen Output) | NEIN bei NEEDS RETEST/BLOCKED/OUT OF SCOPE/ESCALATION REQUIRED
- Audit Risk: LOW | MEDIUM | HIGH | CRITICAL | N/A
- Recommended Audit Model: SWE 1.6 | GPT-5.5 | N/A
- Audit Model To Use: SWE 1.6 | GPT-5.5 | N/A (bei FIXED verbindlich, konsistent mit §7 Compiler-Regel)
- Reason: <kurze Begründung oder N/A>
- Copy-Paste-Handover: bei FIXED **immer** einen einzelnen grauen `BEGIN COPY FOR SKILL 6 RE-AUDIT` Block ausgeben (finaler Output-Typ für `FIXED`, siehe §7 Compiler-Validierung)
- Der Block MUSS mit `@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]` beginnen und `Audit Model To Use: SWE 1.6` oder `Audit Model To Use: GPT-5.5` enthalten.

Optional UX Sichtprüfung (Janus, nicht bindend für FIXED):
1. Optional Janus öffnen.
2. Optional ausführen: <Prompt/Klickpfad>
3. Erwartetes Ergebnis: <Soll>
4. Wenn abweichend: kann zur Kontextlieferung an Skill 5 beitragen — ersetzt keine Playwright-`PASS`-Evidence.
5. Wenn frontendnah und Evidence-Lücke: `frontend_log.md` oder konkreten Frontend-Log-Pfad; keine komplette DevTools-Konsole kopieren.

Nächster Schritt:
- Wenn FIXED und §7 erfüllt und Skill 5 Code geändert hat: zuerst `/save` ausführen, dann Skill 6 Re-Audit in **neuem Chat** mit **`Audit Model To Use`** (der graue Block steht bereits im Skill-5-Output — User kopiert ihn nach Skill 6).
- Wenn FIXED und §7 erfüllt und Skill 5 keinen Code geändert hat: Skill 6 Re-Audit mit **`Audit Model To Use`** starten (Copy-Block aus demselben Skill-5-Output).
- Nach Skill 6 Re-Audit `PASS` oder `PASS WITH FIXES`: Skill 7 Dokumentationsupdate ausführen.
- Wenn NEEDS RETEST: Auto-Verification oder Final Suite erneut fahren bzw. fehlende Evidence nachziehen; optionale Janus-Sichtprüfung möglich.
- Wenn Auto-Verification oder Final Suite FAIL und Iteration < 5: Skill 5 erneut mit SWE 1.6 und aktualisiertem Evidence-Paket ausführen — zuvor **Progress-Validierung** (Failure Code + Evidence vs. vorherige Iteration). Wenn die **Intelligente Stopp-Regel** greift, keine fünfte Iteration starten; stattdessen `SKILL 5 ESCALATION REQUIRED` (§6).
- Wenn nach Iteration 5 weiterhin kein §7-PASS-Pfad:
  - **Proaktive Empfehlung:** Wechsle zu GPT-5.5, da fünf SWE-1.6-Iterationen die datengetriebene Freigabe nicht erreicht haben.
  - **Kostenoptimierung:** Starte immer einen neuen GPT-5.5-Chat und verwende nur die temporäre Eskalationsdatei statt des langen Logs.
  - **Temporäre Datei:** `.windsurf/tmp/skill5_escalation_<feature-or-task>_<YYYYMMDD-HHMM>.md` wurde erstellt.
  - **Copy-Paste-Handover:** Gib dem User den vollständigen `BEGIN COPY FOR NEW GPT-5.5 CHAT` Block aus.
- Wenn `SKILL 5 ESCALATION REQUIRED` wegen **STAGNATION_NO_PROGRESS_ON_FAILURE_CODE_OR_EVIDENCE** (vor Iteration 5): wie §6 — temporäre Eskalationsdatei + vollständiger `BEGIN COPY FOR NEW GPT-5.5 CHAT` Block.
- Wenn BLOCKED: Skill 2 Re-Evaluation oder GPT-5.5 Eskalation.
- Wenn OUT OF SCOPE: neues Feature/Bugfix-Task über Skill 1/2 starten.

Atomic Save Gate:
- `/save` ist Pflicht nach einem erfolgreichen Skill-5-Fix mit Codeänderung, wenn **`FIXED`** gemeldet wird (§7: Auto-Verification `PASS` + Final Feature Suite `PASS`).
- `/save` darf nicht ausgeführt werden, solange Skill 5 `NEEDS RETEST`, `ESCALATION REQUIRED`, `BLOCKED` oder `OUT OF SCOPE` meldet.
```
