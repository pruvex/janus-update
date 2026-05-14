---
description: SWE 1.6 Diamantstandard Phase 4 â€“ Execution Engine. FÃ¼hrt einzelne, vollstÃ¤ndig spezifizierte und durch Skill 3 validierte Tasks deterministisch aus. Implementiert Code, Tests und Validierung. Keine Architekturentscheidungen.
---

## ðŸŽ¯ PURPOSE

Dieser Skill fÃ¼hrt exakt **einen validierten Task aus Skill 2** aus.

Er ist eine reine **Execution Engine** fÃ¼r Janus.

KEINE PLANUNG. KEINE ARCHITEKTUR. KEINE INTERPRETATION.

---

## ðŸ¤– DEFAULT MODEL

SWE 1.6

Ausnahme:
- Kimi k2.5 nur wenn im Task explizit angegeben
- GPT-5.5 nur bei expliziter Eskalation aus Skill 2 oder Skill 3

---

## ðŸ“¥ INPUT

- TASK-ID (aus Skill 2)
- Task Definition (vollstÃ¤ndig)
- Files / Scope
- Acceptance Criteria
- Model Annotation
- optional: Feature Spec und Pre-Check Ergebnis als Referenz
- bei Task-Dateien mit mehreren Tasks: exakt eine Target Task ID

---

## ðŸ“Œ AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer eine Task-Datei, eine Spec-Datei und optional ein Pre-Check Ergebnis nennt, sind diese Artefakte automatisch die verbindlichen AusfÃ¼hrungsquellen.

Der Skill MUSS dann:

- die genannte Task-Datei vollstÃ¤ndig lesen
- die genannte Spec-Datei als Scope-Referenz lesen
- das Pre-Check Ergebnis berÃ¼cksichtigen, falls angegeben
- bei mehreren Tasks in einer Datei exakt die vom User genannte Target Task isolieren
- ausschlieÃŸlich den validierten Task-Scope implementieren
- Chatverlauf, frÃ¼here Diskussionen und zusÃ¤tzliche mÃ¼ndliche Nebeninformationen ignorieren, sofern sie den Artefakten widersprechen oder Ã¼ber sie hinausgehen
- keine Requirements, Produktentscheidungen oder Architekturentscheidungen aus dem Chatkontext ergÃ¤nzen
- stoppen, wenn Task, Spec und Pre-Check nicht konsistent sind
- stoppen, wenn das aktive Modell nicht dem im Target Task festgeschriebenen Modell entspricht
- keine anderen Tasks aus derselben Datei implementieren

Minimaler gÃ¼ltiger User-Aufruf:

```text
/SKILL 4 â€“ EXECUTIONER mit folgenden Artefakten:
Target Task: TASK-XXX.Y
Assigned Model: <SWE 1.6 | Kimi k2.5>
Spec: documentation/Planned Features/<FEATURE_NAME>.md
Task: documentation/tasks/<TASK_FILE>.md
Pre-Check: <PRE-CHECK PASSED Ergebnis oder Datei, falls vorhanden>
```

Wenn eine Datei nicht lesbar ist, kein validierter Task vorliegt, keine Target Task ID genannt wurde oder Artefakte widersprÃ¼chlich sind:

```text
EXECUTION ARTIFACTS INVALID

Issue:
- <konkretes Problem>

Action:
â†’ korrekte Artefakte angeben oder Skill 3 Pre-Implementation Verification erneut ausfÃ¼hren
```

---

## ðŸ§© SINGLE-TASK EXECUTION GATE (HARD PROTOCOL)

Skill 4 fÃ¼hrt immer genau einen Task aus.

Wenn die Task-Datei mehrere Tasks enthÃ¤lt:

- Target Task ID ist Pflicht
- nur dieser Target Task darf implementiert werden
- alle spÃ¤teren Tasks bleiben unberÃ¼hrt
- nach Abschluss MUSS Skill 4 stoppen
- Skill 4 darf nicht automatisch mit dem nÃ¤chsten Task fortfahren
- Skill 4 MUSS bei weiteren offenen Tasks einen Copy-Handover fÃ¼r den nÃ¤chsten Target Task an Skill 4 ausgeben
- Der User startet den nÃ¤chsten Skill-4-Lauf bewusst per Copy-Handover

Modellbindung:

- das aktive Modell muss dem im Target Task festgeschriebenen Modell entsprechen
- bei Abweichung wird nicht implementiert

```text
EXECUTION MODEL MISMATCH

Target Task: TASK-XXX.Y
Required Model: <SWE 1.6 | Kimi k2.5>
Active Model: <SWE 1.6 | Kimi k2.5 | other>

Action:
â†’ Starte Skill 4 erneut mit dem Required Model.
```

---

## âš™ï¸ EXECUTION FLOW

---

### 1. TASK LOADING

- Task vollstÃ¤ndig lesen
- Scope exakt extrahieren
- Acceptance Criteria isolieren

âŒ KEINE Interpretation
âŒ KEINE Erweiterung

---

### 2. IMPLEMENTATION

**Strukturelle Sperre — Kein Edit ohne Command Commit:** Kein Edit-/Write-Tool auf Produkt-/Task-Scope, **bevor** der **Mandatory Command Commit** erfüllt ist (vollständiger Mini-TestPlan-JSON im Output — §5). Verletzung = **PROTOKOLL-VERSTOẞ**.

**Command-First (Mandatory Command Commit — siehe §5):** Keine Änderung an Produkt-/Task-Dateien (keine Edit-/Write-Tools auf Implementierungs-Scope), bevor der geplante Mini-TestPlan als **vollständige JSON-Struktur** im Output steht — ausser bei zulässigem **Auto-Verification: N/A**-Pfad: dort zuerst den begründeten **N/A-Planblock** (Begründung + betroffene Pfade) ausgeben, dann erst Edits.

Implementiere exakt:

- nur definierte Dateien
- nur definierte Logik
- nur definierter Scope

STRICT RULES:
- keine neuen Features
- keine ArchitekturÃ¤nderungen
- kein Refactoring auÃŸerhalb Task
- keine Optimierung auÃŸerhalb Scope

**Scope-Lock (Playwright / Auto-Verification-Fixpfad):** Tritt ein Playwright- oder anderer Auto-Verification-Fehler auf, dürfen Korrekturen **ausschließlich** in den Dateien und Modulen erfolgen, die im **ursprünglichen Task-Scope** (Task-Definition: „nur definierte Dateien“ / „nur definierte Logik“) vorgegeben sind. Weicht die naheliegende Ursache auf Dateien **ausserhalb** dieses Scopes aus (z. B. Fix im Router statt in der Engine, obwohl nur die Engine im Task steht), liegt ein **Scope-Breach** vor: **sofort STOP**, kein weiterer Fix-Versuch in Skill 4.
**Sollte eine Korrektur Änderungen an Dateien außerhalb des definierten Task-Scopes erfordern, MUSS die Ausführung sofort gestoppt und an Skill 5 übergeben werden.**

**Protocol-Integrität (Anti-Dirty-Hack):** Skill 4 darf **niemals** das **Kommunikations-Protokoll** oder die semantische API-/Transport-Charakteristik des Produkts ändern, **nur** um einen Test grün zu bekommen — z. B. **Streaming → synchron**, SSE-/Stream-Pipeline abschalten oder Endpunkte so umbiegen, dass Playwright zufrieden ist, aber Janus fachlich ein anderes Produkt wäre. Gültige Korrekturen bleiben **innerhalb** des Task-Scopes und **ohne** Protokoll-Bruch.

PROVIDER FIDELITY: Stelle sicher, dass Tool-Calls und Intent-Detection exakt für den aktiven Provider funktionieren. Wenn ein Bug nur bei Gemini auftritt (z.B. Schema-Deduplizierung), darf der Fix nicht dazu führen, dass das System intern auf GPT-Logik zurückgreift. Debugge den Provider-spezifischen Stacktrace bis zur Wurzel.

---

### 3. TEST IMPLEMENTATION

Erstelle Tests gemÃ¤ÃŸ Task:

- Unit Tests fÃ¼r Logik
- Integration Tests bei Modulen
- E2E nur bei expliziten User Flows

Wenn keine Tests definiert:
â†’ minimaler Unit Test fÃ¼r Kernfunktion

---

### 4. VALIDATION

#### Execution Pressure (Anti-Modell-Inertia — HART)

- Skill 4 neigt zur **Modell-Inertia** (Playwright-Pflicht wird still übersprungen). Diese Sektion ist die strukturelle Gegenwehr.
- **PROTOKOLL-VERSTOẞ:** Jede funktionale Code-Änderung ohne **sofortige** Janus-Playwright-Verifikation (Generator-Pipeline in §5, sofern nicht zulässiges **N/A**) gilt als Verstoß und führt zur **sofortigen Ablehnung** des Tasks — kein nachträgliches „nachholen“ im selben Lauf ohne erneuten vollständigen Zyklus.
- **Kein Weg an Command-First vorbei:** Ohne vorab im Chat ausgegebenen Mini-TestPlan-JSON (§5 / §2) gibt es keine gültige Validierung und kein `TASK COMPLETE` mit `PASS`-Kette.
- **Shell-Pflicht:** Prosa-„wir haben getestet“ ohne ausgeführte Befehle aus §5 = **PROTOKOLL-VERSTOẞ**.

#### Anti-Hacking Guard (Auto-Verification / Playwright)

- Es ist verboten, die **System-Architektur** oder **API-Endpunkte** (Routing, Protokoll, Request-Lifecycle) zu verändern, um eine **fehlgeschlagene Auto-Verification** zu umgehen. **Scope-Lock (§2)** gilt bei jedem `Auto-Verification: FAIL` unverändert: nur Fixes im Task-Scope, sonst sofort Skill 5.

PrÃ¼fe:

- Code lÃ¤uft / kompiliert
- Tests bestehen
- Acceptance Criteria erfÃ¼llt
- kein Scope-Drift
- keine ungewollten Nebenwirkungen

AUTOMATISCHE TESTPFLICHT:

- Skill 4 MUSS nach jeder Implementierung automatisch alle fÃ¼r den Task erforderlichen Validierungen ausfÃ¼hren.
- Skill 4 darf nicht auf eine Nachfrage des Users warten, bevor Build-, Unit-, Integration-, E2E- oder task-spezifische Tests ausgefÃ¼hrt werden.
- Wenn der Task Testbefehle nennt, MÃœSSEN diese ausgefÃ¼hrt werden.
- Wenn der Task keine Testbefehle nennt, MUSS Skill 4 anhand der geÃ¤nderten Dateien die kleinste sinnvolle Validierung wÃ¤hlen und ausfÃ¼hren.
- Wenn keine automatisierte Validierung sinnvoll mÃ¶glich ist, MUSS Skill 4 das explizit als `Automated Validation: N/A` begrÃ¼nden und danach trotzdem das Pipeline-Continuation-Gate ausgeben.
- Skill 4 darf `READY FOR FINAL AUDIT` erst melden, wenn die erforderlichen automatischen Tests PASS sind oder nachvollziehbar N/A sind **und** die **TASK-COMPLETE-REIHENFOLGE** (Output Format) eingehalten ist.
- **`TASK COMPLETE` ist PASS-only:** Es darf nur ausgegeben werden, wenn unmittelbar zuvor `Auto-Verification` mit **`- Status: PASS`** steht (siehe Output Format). **`N/A` berechtigt nicht zu `TASK COMPLETE`** — N/A-Abschlüsse ohne Playwright nutzen den separaten Abschlusstyp **`N/A-SCOPE CLOSURE`** (siehe OUTPUT FORMAT), niemals das Token `TASK COMPLETE`.
- Wenn automatische Tests fehlschlagen, MUSS Skill 4 gezielt fixen oder mit `TASK EXECUTION FAILED` / `FIX LOOP LIMIT REACHED` stoppen.

**AUTO-GENERATED VERIFICATION (VOLLSTAENDIG):** Die verbindliche Mini-TestPlan-Generator-Validator-Playwright-Prozedur, die **GENERATOR FAILURE TAXONOMY** und das **FEHLER-PROTOKOLL** stehen unter **### 5. AUTO-GENERATED VERIFICATION GATE** weiter unten (direkt nach PIPELINE CONTINUATION GATE). Skill 4 fuehrt diese Schritte selbst aus (Shell/Terminal) — keine reine Prosa-Deklaration ohne tatsaechlich gelaufene Befehle.

Gate-Reihenfolge (Kurzfassung — Details im genannten Abschnitt):

1. AUTOMATISCHE TESTPFLICHT: Build/Unit/Integration/E2E nach Task.
2. AUTO-GENERATED VERIFICATION: Mini-TestPlan + Generator + Validator + Playwright-Runner.
3. Erst bei `Auto-Verification: PASS` (oder begruendetem `N/A`) folgt das **USER SIGN-OFF GATE** (Produktcheck + Skill-6/5-Routing).
4. Bei `FAIL`: Fix-Loop; **USER SIGN-OFF GATE** ist verboten bis PASS oder klarer Eskalationsstopp.

INVESTIGATION-INCONCLUSIVE GATE:

- Wenn ein Task als Debug/Investigation/Handoff aus Backlog oder Test-Pipeline kommt und Skill 4 keine Ursache isolieren oder keinen Fix implementieren kann, darf Skill 4 NICHT einfach `TASK COMPLETE` mit nur einer Empfehlung ausgeben.
- `TASK COMPLETE` ist nur erlaubt, wenn ein konkretes Ziel des Investigation-Tasks erreicht wurde **und** die **PASS-only-Regel** für `TASK COMPLETE` (Output Format) erfüllt ist: Ursache isoliert, Fix umgesetzt, Test/Logging-Hardening umgesetzt, oder eindeutige Nicht-Reproduzierbarkeit mit Evidence belegt — sonst `TASK NEEDS EVIDENCE` / `N/A-SCOPE CLOSURE` statt `TASK COMPLETE`.
- Wenn Backend-Logs, Network-Logs, Provider-Logs oder andere Pflicht-Evidence fehlen, muss Skill 4 `TASK NEEDS EVIDENCE` ausgeben.
- `TASK NEEDS EVIDENCE` muss dem User genau sagen, welche Evidence gebraucht wird, wo sie herkommt, und was danach zu tun ist.
- Wenn die fehlende Evidence in einem User-Terminal liegt, muss Skill 4 den User um genau diese Logs bitten und darf nicht spekulativ abschliessen.
- Wenn der Fehler ohne weitere Evidence nicht isolierbar ist, aber wiederholt/reproduzierbar die Pipeline blockiert, muss Skill 4 einen Copy-Handover zu `SKILL 5 – FEATURE DEBUG` oder zum passenden Backlog-/Debug-Folgeprozess ausgeben.

```text
TASK NEEDS EVIDENCE: <TASK-ID>

Status: BLOCKED_BY_MISSING_EVIDENCE

Was wurde festgestellt:
- <kurze Evidence-Zusammenfassung>

Fehlende Evidence:
- <konkreter Log/Evidence-Punkt>

User-Aktion erforderlich:
1. <konkreter Schritt>
2. <konkreter Schritt>
3. Antworte danach mit: EVIDENCE READY

Danach:
- Skill 4 setzt die Investigation mit der neuen Evidence fort
- oder gibt einen Copy-Handover zu SKILL 5 – FEATURE DEBUG aus, wenn ein Debug-Fix noetig ist
```

PIPELINE CONTINUATION GATE:

- Nach erfolgreicher automatischer Validierung MUSS Skill 4 prÃ¼fen, ob weitere Tasks aus derselben Task-Datei offen sind.
- Pro Task MUSS Skill 4 nach erfolgreicher AUTOMATISCHE TESTPFLICHT auch die AUTO-GENERATED VERIFICATION (Mini-TestPlan + Generator + Validator + Runner) ausfuehren, sofern die Aenderung nicht unter die N/A-Ausnahme faellt.
- Wenn weitere Tasks offen sind, MUSS Skill 4 stoppen und einen einzelnen grauen Copy-Block fÃ¼r den nÃ¤chsten Skill-4-Lauf mit dem nÃ¤chsten Target Task ausgeben.
- Wenn weitere Tasks offen sind, darf Skill 4 noch KEINEN Final-Audit-Handover ausgeben.
- Wenn weitere Tasks offen sind, ist ein manueller Gesamt-Janus-Test optional, aber NICHT das Final-Gate.
- Erst wenn keine weiteren Tasks offen sind, MUSS Skill 4 einen automatischen Gesamttest/Regressionstest fÃ¼r die gesamte Spec ausfÃ¼hren.
- Vor dem USER SIGN-OFF GATE MUSS das Ergebnis der AUTO-GENERATED VERIFICATION (PASS/FAIL/N/A) im Output sichtbar stehen. Bei `FAIL` ist das User-Sign-off-Gate verboten.
- Erst nach erfolgreichem Gesamttest **und** `Auto-Verification: PASS` (oder ausnahmsweise begruendetem `N/A`) darf Skill 4 das USER SIGN-OFF GATE ausgeben.
- Nach dem letzten Task und erfolgreicher Gesamtvalidierung MUSS Skill 4 STOPPEN und nur das USER SIGN-OFF GATE ausgeben.
- Skill 4 darf im selben Output wie `TASK COMPLETE` / `ALL TASKS COMPLETE` keinen Skill-6-Final-Audit-Copyblock ausgeben.
- Der Skill-6-Final-Audit-Copyblock darf ausschlieÃŸlich in einer separaten Antwort nach der User-Antwort `Manueller Test erfolgreich.` erzeugt werden.

### 5. AUTO-GENERATED VERIFICATION GATE (ersetzt das fruehere reine Manual-Gate als technisches Freigabe-Gate)

**Mandatory Command Commit & Command-First (JSON vor jedem Edit):** Bevor die Implementation (dieser Abschnitt) startet, MUSS der Agent den geplanten Mini-TestPlan (**JSON-Struktur** gemäss `tests/e2e/generator/test-plan.schema.json`, inkl. `tests`-Array und Pflichtfelder) im **Chat-Output** als **vollständigen, validierbaren JSON-Entwurf** ausgeben — **dieser Output ist der Command Commit.** Ohne diesen sichtbaren Plan darf **keine** Datei geändert werden. Liegt die Änderung unter der **AUSNAHME-REGEL** (Auto-Verification **N/A**), MUSS stattdessen vor jedem Edit ein **N/A-Planblock** derselben Strenge ausgegeben werden (Begründung, betroffene Pfade, Bestätigung „kein Chat-/Provider-/Stream-Pfad“). **Modell-Inertia:** Das Überspringen dieser Ausgabe zugunsten direkter Edits ist verboten und zählt als **PROTOKOLL-VERSTOẞ**.

Dieser Abschnitt ist das **verbindliche** Janus-Live-Verifikations-Gate. Der fruehere Schwerpunkt auf ausschliesslich manuellem Janus-Test ohne vorherigen generierten Playwright-Lauf entfaellt. Stattdessen: **zuerst** Mini-TestPlan + Generator + Validator + Runner (Skill 4 fuehrt die Shell-Befehle selbst aus und protokolliert). **Danach** erst das **USER SIGN-OFF GATE** (Produktnahe Bestaetigung + Skill-6/5-Routing).

### Ausloesung und Pflicht

Nach jedem funktionalen Fix (Code-Aenderung, die einen User-spuerbaren Code-Pfad beruehrt) und vor jedem **USER SIGN-OFF GATE** MUSS Skill 4 die folgenden Schritte ausfuehren — ausser bei zulaessigem `Auto-Verification: N/A` (siehe unten).

### Schritt 1 — Mini-TestPlan erzeugen

- Skill 4 erstellt eine Datei unter `documentation/test-runs/<task_id>_verify.json` (z. B. `documentation/test-runs/TASK-XXX_verify.json` oder `TASK-001.1_verify.json`).
- Die Datei MUSS dem JSON-Schema in `tests/e2e/generator/test-plan.schema.json` entsprechen (Single Source of Truth — siehe Skill 1) und den **vor Implementierung** im Output ausgegebenen JSON-Entwurf (**Command-First**) widerspiegeln.
- Pflichtfelder im Mini-TestPlan:
  - `testRunId`: Form `TASK-XXX-VERIFY-YYYY-MM-DD-NNN`
  - `title`: kurzer Fix-Titel
  - `executionMode`: `LIVE_VISUAL`
  - `target`: `JANUS_CHAT`
  - `chatWindow`: `A` (Default)
  - `baseUrl`, `backendHealthUrl`, `timeouts`, `strategies` gemaess Schema
  - `tests`: mindestens **ein** TestCase mit konkretem Prompt + `expected.containsAny` / `mustNotContain` fuer den betroffenen Code-Pfad
- Nur reine JSON-Datei (kein Markdown-Testplan).
- Keine erfundenen Strategy-IDs — nur Eintraege aus `tests/e2e/generator/strategy-registry.json`.

### Schritt 2 — Generator (Pflicht)

```text
node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/<task_id>_verify.json --out tests/e2e/generated/<task_id>_verify.live.spec.js
```

- Bei Generator-Fehler: `Auto-Verification: FAIL`; Skill 4 korrigiert den TestPlan und wiederholt — **kein** USER SIGN-OFF GATE.

### Schritt 3 — Validator (Pflicht)

```text
node tests/e2e/generator/validate-runner.mjs --plan documentation/test-runs/<task_id>_verify.json --runner tests/e2e/generated/<task_id>_verify.live.spec.js
```

- Bei Validator-Fehler: `Auto-Verification: FAIL`.

### Schritt 4 — Playwright-Runner (Pflicht)

```text
npx playwright test tests/e2e/generated/<task_id>_verify.live.spec.js --headed --workers=1
```

- `--headed --workers=1` ist der harte Default (parallele visuelle Beobachtung).
- Skill 4 darf diesen Lauf nicht durch reine Behauptung ersetzen — Befehl muss im Workspace ausgefuehrt worden sein (oder Eskalation / `TASK EXECUTION FAILED` mit konkretem Shell-Grund).

### Schritt 5 — Ergebnis und FEHLER-PROTOKOLL (Pflicht)

- Zusammenfassung im Output: `Auto-Verification: PASS | FAIL | N/A` mit Begruendung.
- Bei **PASS**: TestCase-IDs, Provider/Models, Pfade zu `tests/e2e/generated/<task_id>_verify.live.spec.js`, `playwright-report/` (oder `npx playwright show-report`), relevante `test-results/`-Ordner.
- Bei **FAIL**: verbindlich:
  - **Failure Code** exakt nach **GENERATOR FAILURE TAXONOMY** (unten) — keine Umetikettierung, keine Prosa-Umbenennung
  - **Suggested Triage Bucket** aus derselben Tabelle
  - Kurzer Fehlerauszug (erste relevante Zeilen aus stderr/Playwright)
  - Pfade: generierter Spec, `playwright-report/`, `test-results/`, optional `documentation/test-results/<testRunId>/` falls Evidence dort landet
  - Optional: JSON-Evidence `documentation/test-results/<testRunId>/<TESTCASE>_evidence.json` wenn vom Lauf erzeugt

```text
FAILURE LOG (BINDEND)

TestRunId: <aus Mini-TestPlan>
Failure Code: <exakt ein Code aus Taxonomie>
Suggested Triage: <Bucket aus Taxonomie-Tabelle>
Evidence Paths:
- <Pfad 1>
- <Pfad 2>
Excerpt: <kurz>
```

### GENERATOR FAILURE TAXONOMY (BINDEND — Fehleranalyse)

Quelle der Wahrheit: `tests/e2e/generator/generate-live-runner.mjs` (Failure-Taxonomy-Header). Skill 4 MUSS bei jeder Auto-Verification-**FAIL**-Analyse diese Codes und Buckets verwenden — keine eigenen Synonyme.

| Failure Code | Quelle im Runner | Bedeutung | Suggested Triage Bucket |
|--------------|------------------|-----------|-------------------------|
| `RUNNER_PRECLICK_EMPTY` | preClickDiag | Textarea `#user-input-<win>` nach Eingabe leer; Submit-Guard. | Test Runner / Frontend Input Path |
| `RUNNER_PRECLICK_DOM_BROKEN` | preClickDiag | `#send-button-<win>` nicht in `#chat-form-<win>`; Form-Submit gebrochen. | Frontend DOM Regression |
| `RUNNER_SELECTOR_FAILURE` | Taxonomy-Header | Erwartetes DOM-Element nicht gefunden. | Test Runner / Selector Drift |
| `RUNNER_WAIT_FAILURE` | Taxonomy-Header | Wait-Condition nicht aufgeloest. | Test Runner / Wait Strategy |
| `RUNNER_STREAM_TIMEOUT` (A: `no POST /api/chat/stream`) | Runner-Catch | Kein Stream-Request — Send-/Trigger-Pfad. | Frontend Send Path / SSE Trigger Issue |
| `RUNNER_STREAM_TIMEOUT` (B: `bubble empty or only contains "..."`) | toPass-Polling | Stream lief, Bubble leer/`...` — Ghost/SSE/Backend-Content. | Frontend SSE Rendering / Ghost-Bubble oder Backend Stream |
| `FRONTEND_NOT_READY` | webServer | Frontend-Dev-Server nicht erreichbar. | Infrastructure / Environment |
| `BACKEND_HEALTH_FAIL` | webServer | Backend `/api/health` nicht OK. | Infrastructure / Environment |
| `PROVIDER_TIMEOUT` | Runner + Error-Bubble | Provider antwortet nicht oder Error-Bubble. | Backend / Provider / Cost |
| `TOOL_ROUTING_FAILURE` | Evaluator | Falsches/fehlendes Tool. | Intent / Tool Routing |
| `ASSERTION_MISMATCH` | Evaluator | Text-Expectation nicht erfuellt. | Capability Behavior / Spec Drift |

**Erweiterte Symptom-Triage (Hinweis, nicht eigener Generator-Code):** `RUNNER_STREAM_TIMEOUT` (B) + `[SSE-REANCHOR]` mit `reanchorCount > 0` in Console-Logs → DOM-Wipe-Quelle / `loadChat`-Konflikt. Ohne `[SSE-FIRST-TEXT]` → Backend/Provider/SSE-Routing. `[SSE-FINAL]` mit Text aber kein `.message.assistant` im DOM → Ghost-Bubble / DOM-Race.

### AUSNAHME-REGEL (Auto-Verification N/A)

Fuer rein optische CSS-, reine Doku- oder reine `.windsurf/workflows/`-Aenderungen darf Playwright als `Auto-Verification: N/A` entfallen, wenn explizit begruendet und keine JS/TS/Backend/Routing/Tool/Stream-Logik beruehrt wurde. UX-TRANSLATION RULE gilt trotzdem im USER SIGN-OFF GATE (`Test-Prompt: N/A - interne Aenderung ohne Chat-Pfad`).

### Verbote (Auto-Verification)

- `N/A` ohne Begruendung oder fuer Backend/FE-Logik-Aenderungen verboten.
- `PASS` ohne generierten und ausgefuehrten Spec verboten.
- Fremden, nicht task-spezifischen Spec wiederverwenden verboten.

---

### 6. USER SIGN-OFF GATE (NUR NACH LETZTEM TASK / NACH AUTO-VERIFICATION PASS)

- Erst wenn **AUTO-GENERATED VERIFICATION** `PASS` oder zulaessiges `N/A` meldet, darf Skill 4 dieses Gate ausgeben.
- Skill 4 darf nicht direkt zum Final Audit weiterleiten, bevor der User die folgende Auswahl trifft.
- Verboten: `BEGIN COPY @[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]` vor der User-Bestaetigung `Manueller Test erfolgreich.`
- Skill 4 MUSS dem User genau zwei Optionen geben.

UX-TRANSLATION RULE (PFLICHT — gilt fuer dieses User-Sign-off-Gate):

- Skill 4 darf in keinem Sign-off-Gate rein technische Anweisungen geben (z. B. "Pruefe Variable X", "Validiere SSE-Buffer-Flush").
- Skill 4 MUSS den technischen Fix in eine menschliche, produktnahe Handlung uebersetzen.
- PFLICHT 1 — Beispiel-Prompt: mindestens ein konkreter, kopierbarer Prompt fuer den Janus-Chat-Pfad.
- PFLICHT 2 — Erwartete Reaktion: Produktsprache (Stream, Tool sichtbar, Modal, Bild, Fehler weg).
- PFLICHT 3 — UX-Erfolgskriterium: sichtbares User-Kriterium (kein reines Backend-Log-Gate).
- Ausgabe als nummerierter Block `MANUELLER UX-CHECK ERFORDERLICH` VOR Option 1/2.
- Interne-only-Aenderungen: `Test-Prompt: N/A - interne Aenderung ohne Chat-Pfad` + alternative UX-Bestaetigung.
- Verboten: Gate ohne `MANUELLER UX-CHECK ERFORDERLICH`-Block.

Nach dem UX-Check-Block folgt der Auswahl-Block mit genau zwei Optionen:

```text
USER SIGN-OFF — JANUS-PRODUKT-CHECK ERFORDERLICH

Automatische Playwright-Verifikation: PASS | N/A (siehe oben Auto-Verification-Block).

Bitte pruefe das umgesetzte Feature zusaetzlich in Janus (Produkt-Sicht), falls noch nicht parallel zum headed-Lauf geschehen.

### MANUELLER UX-CHECK ERFORDERLICH

1. **Test-Prompt:** "[Hier konkreten Prompt einfuegen, der den vom Fix betroffenen Code-Pfad triggert]"
2. **Erwartete Reaktion:** "[Was Janus in Produktsprache tun soll - z. B. Antwort streamt fluessig, Tool-Call wird sichtbar, Bild erscheint im Chat]"
3. **UX-Erfolgskriterium:** "[Woran du erkennst, dass es geklappt hat - z. B. Kein Haengenbleiben bei `...`, keine `win is not defined`-Bubble, Antwortstrom bricht nicht ab]"

Option 1:
Manueller Test erfolgreich.

Ergebnis:
â†’ Skill 4 gibt den Copy-Handover fÃ¼r SKILL 6 â€“ DIAMANTSTANDARD FINAL AUDIT mit Audit-Modell-Empfehlung aus.

Option 2:
Es funktioniert nicht wie gewÃ¼nscht.

Bitte beschreibe kurz:
- Was hast du in Janus getan?
- Was hast du erwartet?
- Was ist tatsÃ¤chlich passiert?
- Screenshot/Log/Output, falls vorhanden.

Ergebnis:
â†’ Skill 4 gibt danach einen Copy-Handover fÃ¼r SKILL 5 â€“ FEATURE DEBUG aus.
```

---

## FIX LOOP LIMIT

**Strukturelle Ursachen — zwingend Skill 5:** Fix-Versuche in Skill 4 sind **nur** für **logische oder syntaktische** Fehler **innerhalb** des definierten Task-Scopes (Task-Dateien/Logik) zulässig. **Strukturelle** Probleme — z. B. **Timeouts** (z. B. `RUNNER_STREAM_TIMEOUT` / `PROVIDER_TIMEOUT` ohne eindeutigen Einzeiler-Fix im Scope), **Protokoll-Fehler**, Infrastruktur, Routing- oder Architektur-Bruch **ausserhalb** der Task-Dateien — **dürfen nicht** durch weitere Skill-4-Blind-Fixes „weggedrückt“ werden: **sofort** Ausführung stoppen und **Handover an `@[/SKILL 5 – FEATURE DEBUG]`** mit Evidence (Failure Code, Logs, Mini-TestPlan-Pfad).

**Zwei Scope-interne Versuche:** Wenn derselbe Task nach **zwei** gezielten Fix-Versuchen, die **ausschließlich** den Task-Scope und die **Protocol-Integrität** (§2) einhalten, weiterhin fehlschlägt:

âž¡ STOP EXECUTION

```text
FIX LOOP LIMIT REACHED

Task: TASK-XXX

Failed Area:
- <konkreter Bereich: Tests / Build / Acceptance Criteria / Scope Conflict — nur scope-intern>

Attempts:
- 1: <kurze Zusammenfassung>
- 2: <kurze Zusammenfassung>

Action:
â†’ keine weiteren Blind-Fixes innerhalb Skill 4
â†’ bei strukturellen/Protokoll-Themen: zuerst `@[/SKILL 5 – FEATURE DEBUG]` (siehe Regel oben)
â†’ bei erschöpften scope-internen Versuchen: Skill 2 Re-Evaluation oder GPT-5.5 Eskalation mit kompaktem Fehlerpaket
```

---

## OUTPUT FORMAT

### TASK-COMPLETE-REIHENFOLGE (HART — sonst INVALID / PROTOKOLL-VERSTOẞ)

**`TASK COMPLETE` ist PASS-only:** Das Wort **`TASK COMPLETE`** darf im finalen Output **nur unmittelbar nach** einem Block, der mit **`Auto-Verification`** beginnt, erscheinen, wenn die Zeile **`- Status: PASS`** (exakt) in diesem Block enthalten ist — dazwischen keine Überschrift, kein Fliesstext, keine andere Liste. **`N/A` disqualifiziert `TASK COMPLETE` vollständig.** **Jede andere Reihenfolge ist INVALID** und zählt als **PROTOKOLL-VERSTOẞ** (Task sofort ablehnen / neu ausführen).

**`ALL TASKS COMPLETE`:** nur unmittelbar nach dem finalen **`Auto-Verification`**-Block mit **`- Status: PASS`** (Gesamt-Playwright-Pflicht erfüllt). **`N/A`** am letzten Task: statt `ALL TASKS COMPLETE` den Abschlusstyp **`N/A-SCOPE CLOSURE (ALL TASKS)`** verwenden (gleiche Pflichtfelder wie Gesamttemplate, aber **ohne** die Zeichenkette `ALL TASKS COMPLETE`).

Bei **`Auto-Verification:`** mit Status **`FAIL`** darf im selben Output **kein** `TASK COMPLETE` oder `ALL TASKS COMPLETE` erscheinen — nur Fix-Loop, `TASK EXECUTION FAILED` oder Eskalation.

### N/A-SCOPE CLOSURE (ohne TASK COMPLETE / ohne ALL TASKS COMPLETE)

Nur bei zulässigem **`Auto-Verification: N/A`**. Statt `TASK COMPLETE` / `ALL TASKS COMPLETE`:

```text
Auto-Verification:
- Status: N/A (mit Begruendung)
- ...

N/A-SCOPE CLOSURE: TASK-XXX
```

Derselbe **Command-First**-Pfad (N/A-Planblock vor Edits) bleibt Pflicht; **kein** `TASK COMPLETE`-Token.

### Index — Harte Verbote (manuelle Test-Aufforderungen statt Playwright)

Skill 4 darf dem User **nicht** die folgenden **indexierten** Formulierungen (auch sinngemäß / als „Ersatz“ für die Generator-Pipeline) ausgeben:

1. „Du kannst das jetzt manuell prüfen“
2. „Manuelle Validierung erforderlich (ohne Playwright)“
3. „Bitte teste selbst in der App, ich habe nicht automatisiert.“
4. „Playwright überspringen / aus Zeitgründen nicht ausgeführt.“
5. „Reicht ein manueller Klicktest statt E2E.“
6. „Validierung: User übernimmt.“ / „Du musst das Verhalten selbst verifizieren.“

### NO-ORPHAN-OUTPUT RULE

Skill 4 darf den User niemals ohne eindeutige naechste Aktion zuruecklassen.

Jeder finale Output MUSS genau einen der folgenden Abschluss-Typen enthalten:
- `TASK COMPLETE` **nur** PASS-only gemäß **TASK-COMPLETE-REIHENFOLGE** (unmittelbar nach `Auto-Verification` mit **`- Status: PASS`**), plus Pipeline Continuation Status und entweder `/save`-Gate, naechster Skill-4-Copy-Handover oder finales USER SIGN-OFF GATE (Abschnitt 6).
- `ALL TASKS COMPLETE` **nur** unmittelbar nach finalem `Auto-Verification` mit **`- Status: PASS`**, plus USER SIGN-OFF GATE mit exakt zwei Antwortoptionen.
- **`N/A-SCOPE CLOSURE`** bzw. **`N/A-SCOPE CLOSURE (ALL TASKS)`** statt `TASK COMPLETE` / `ALL TASKS COMPLETE`, wenn `Auto-Verification: N/A` zulässig ist (siehe Abschnitt oben).
- `TASK NEEDS EVIDENCE` plus konkrete User-Aktion und Copy-Handover oder Fortsetzungsantwort-Trigger.
- `TASK EXECUTION FAILED` oder `FIX LOOP LIMIT REACHED` plus Copy-Handover zu `@[/SKILL 5 – FEATURE DEBUG]`, `@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]` oder GPT-5.5-Eskalation.
- `EXECUTION ARTIFACTS INVALID` oder `EXECUTION MODEL MISMATCH` plus konkrete Re-Run-Anweisung.

Verboten sind finale Abschluesse wie:

- `SKILL 4 abgeschlossen`
- `TASK COMPLETE mit Empfehlung zur weiteren Untersuchung`
- `Test konnte nicht vollstaendig ausgefuehrt werden`
- `Naechster Schritt: Skill 5 – PRE-IMPLEMENTATION VERIFICATION`

Wenn der naechste Schritt ein anderer Skill ist, MUSS am Ende ein einzelner grauer Copy-Paste-Block mit `@[/... ]` stehen. Eine reine Prosa-Empfehlung ist ungueltig.

Self-Check vor finaler Antwort:

- Gibt es einen eindeutigen naechsten Skill oder eine eindeutige User-Aktion?
- Falls naechster Skill: ist ein kopierbarer `@[/... ]`-Block vorhanden?
- Falls User-Aktion: steht exakt da, was der User antworten soll?
- Wurde die **TASK-COMPLETE-REIHENFOLGE** eingehalten (`TASK COMPLETE` / `ALL TASKS COMPLETE` **nur** mit vorangehendem `Auto-Verification` und **`- Status: PASS`**, bzw. **`N/A-SCOPE CLOSURE`** bei N/A)?
- Wurde bei Chat-relevanten Aenderungen **### 5. AUTO-GENERATED VERIFICATION** wirklich per Shell ausgefuehrt (oder zulaessiges `N/A` begruendet), und bei `FAIL` ein `FAILURE LOG (BINDEND)` mit Taxonomie-Code ausgegeben?

```text id="skill4_output"
Auto-Verification:
- Status: PASS
- Mini-TestPlan: documentation/test-runs/<task_id>_verify.json
- Generated Runner: tests/e2e/generated/<task_id>_verify.live.spec.js
- Runner Command: npx playwright test tests/e2e/generated/<task_id>_verify.live.spec.js --headed --workers=1
- Result Summary: <PASS-IDs>

TASK COMPLETE: TASK-XXX

Status: SUCCESS | PARTIAL | FAILED

Implemented:
- <Liste Ã„nderungen>

Files Changed:
- <Dateien>

Tests:
- Unit: PASS | FAIL
- Integration: PASS | FAIL
- E2E: PASS | FAIL

Notes:
- **`TASK COMPLETE` nur bei obigem `- Status: PASS`.** Bei **FAIL** oder **N/A** diesen Block nicht so verwenden: FAIL → Fix/`TASK EXECUTION FAILED`; N/A → **`N/A-SCOPE CLOSURE`**-Template (kein `TASK COMPLETE`).
- nur technische Hinweise
- keine neuen Ideen

NÃ¤chster Schritt:
â†’ STOPP NACH DIESEM TASK
â†’ Automatische Tests/Validierungen MÃœSSEN bereits ausgefÃ¼hrt sein.
â†’ Wenn Code oder Tests geÃ¤ndert wurden und die automatische Task-Validierung PASS ist: zuerst `/save` ausfÃ¼hren.
â†’ Wenn weitere Tasks vorhanden sind: einen Copy-Handover fÃ¼r den nÃ¤chsten Skill-4-Lauf mit dem nÃ¤chsten Target Task ausgeben.
â†’ Wenn weitere Tasks vorhanden sind: KEIN Skill-6-Audit, KEIN Skill-5-Debug-Gate, KEIN Skill-7-Handover.
â†’ Wenn keine weiteren Tasks vorhanden sind: automatische Gesamtvalidierung ausfÃ¼hren.
â†’ Wenn keine weiteren Tasks vorhanden sind und Gesamtvalidierung PASS ist: USER SIGN-OFF GATE (Abschnitt 6) ausgeben.
â†’ Nach Gesamtvalidierung PASS: STOPP. Kein Skill-6-Copyblock im selben Output.
â†’ Skill 4 darf erst nach User-BestÃ¤tigung "Manueller Test erfolgreich" den Skill-6-Audit-Handover ausgeben.
â†’ Wenn der User nach dem Gesamttest meldet "Es funktioniert nicht wie gewÃ¼nscht", MUSS Skill 4 eine Fehlerbeschreibung anfordern und danach einen Skill-5-Debug-Handover ausgeben.

Atomic Save Gate:
```text
/save
```

Regel:
- `/save` erst nach erfolgreicher Task-Validierung ausfÃ¼hren.
- `/save` nicht ausfÃ¼hren, wenn Tests fehlschlagen oder Skill 4 `TASK EXECUTION FAILED` meldet.
- Erst nach erfolgreichem `/save` den nÃ¤chsten Skill starten.

Pipeline Continuation Status:
- Current Target Task: <TASK-XXX.Y>
- Current Task Status: COMPLETE
- Completed Tasks:
  - <Liste inkl. gerade abgeschlossenem Target Task>
- Remaining Tasks:
  - <nÃ¤chster offener Task oder "keine">
- Spec Implementation Complete: YES | NO

Copy-Paste-Prompt fÃ¼r nÃ¤chsten Skill-4-Lauf, wenn `Spec Implementation Complete: NO`:

```text
@[/SKILL 4 – EXECUTIONER] mit folgendem Target Task:
Spec: <source spec file>
Task: <task file>
Target Task: <nÃ¤chster offener TASK-XXX.Y>
Assigned Model: <SWE 1.6 | Kimi k2.5>
Mode: SINGLE_TASK_EXECUTION

Pipeline Status:
- Previous Target Task: <gerade abgeschlossener TASK-XXX.Y>
- Completed Tasks:
  - <Liste inkl. gerade abgeschlossenem Target Task>
- Remaining Tasks:
  - <Liste inkl. nÃ¤chstem Target Task>

Arbeitsregel:
- Nutze die genannte Spec-Datei und Task-Datei als verbindliche Artefakte.
- Implementiere ausschlieÃŸlich den genannten Target Task.
- Ignoriere widersprÃ¼chliche oder zusÃ¤tzliche Chat-Kontexte.
- FÃ¼hre nach der Implementierung automatisch alle erforderlichen Tests/Validierungen aus.
- FÃ¼hre keine spÃ¤teren Tasks im selben Lauf aus.
- Gib nach erfolgreichem Abschluss erneut entweder den nÃ¤chsten Skill-4-Handover oder, beim letzten Task, das USER SIGN-OFF GATE (Abschnitt 6) aus.

NÃ¤chster erwarteter Output:
- Umsetzung genau dieses Target Tasks
- Automatische Test-/Validierungsergebnisse
- Pipeline Continuation Status
- Copy-Handover fÃ¼r den nÃ¤chsten Target Task oder finales USER SIGN-OFF GATE
```

Gesamtvalidierung nach letztem Task:
- Wenn `Spec Implementation Complete: YES`, MUSS Skill 4 eine automatische Gesamtvalidierung der vollstÃ¤ndigen Spec-Umsetzung ausfÃ¼hren.
- Diese Gesamtvalidierung umfasst mindestens relevante Build-, Unit-, Integration-, E2E- oder Smoke-Tests fÃ¼r den kompletten Feature-Flow.
- Erst danach darf das USER SIGN-OFF GATE (Abschnitt 6) erscheinen.
- Nach dem USER SIGN-OFF GATE MUSS Skill 4 auf die User-Antwort warten.
- Vor der User-Antwort `Manueller Test erfolgreich.` oder einer Fehlerbeschreibung ist jeder Audit-/Debug-Copyblock verboten.

Finaler Skill-4-Output nach letztem Task und Gesamtvalidierung PASS:

```text
Auto-Verification (Playwright):
- Status: PASS
- Mini-TestPlan: documentation/test-runs/<task_id>_verify.json
- Generated Runner: tests/e2e/generated/<task_id>_verify.live.spec.js
- Runner Command: npx playwright test tests/e2e/generated/<task_id>_verify.live.spec.js --headed --workers=1
- Per-Task-Verification-Results:
  - <task_id_1>: PASS
  - <task_id_n>: PASS

ALL TASKS COMPLETE - SPEC IMPLEMENTATION FINISHED

Completed Tasks:
- <alle abgeschlossenen Tasks>

Remaining Tasks:
- Keine

Spec Implementation Complete: YES

Gesamt-Test Results:
- <Build/Unit/Integration/E2E/Smoke>: PASS | N/A mit BegrÃ¼ndung

MANUELLER JANUS-GESAMTTEST / USER SIGN-OFF (Abschnitt 6)

Bitte teste jetzt das vollstÃ¤ndig umgesetzte Feature direkt in Janus (ergaenzend zur Auto-Verification, falls nicht schon parallel beobachtet).

### MANUELLER UX-CHECK ERFORDERLICH

1. **Test-Prompt:** "[Hier konkreten Prompt einfuegen, der den vom Fix betroffenen Code-Pfad triggert]"
2. **Erwartete Reaktion:** "[Was Janus in Produktsprache tun soll - z. B. Antwort streamt fluessig, Tool-Call wird sichtbar, Bild erscheint im Chat]"
3. **UX-Erfolgskriterium:** "[Woran du erkennst, dass es geklappt hat - z. B. Kein Haengenbleiben bei `...`, keine `win is not defined`-Bubble, Antwortstrom bricht nicht ab]"

Option 1:
Manueller Test erfolgreich.

Antwort dann exakt:
Manueller Test erfolgreich.

Ergebnis:
â†’ Skill 4 gibt danach den Copy-Handover fÃ¼r SKILL 6 â€“ DIAMANTSTANDARD FINAL AUDIT aus.

Option 2:
Es funktioniert nicht wie gewÃ¼nscht.

Antwort dann mit kurzer Fehlerbeschreibung:
- Was hast du in Janus getan?
- Was hast du erwartet?
- Was ist tatsÃ¤chlich passiert?
- Screenshot/Log/Output, falls vorhanden.

Ergebnis:
â†’ Skill 4 gibt danach den Copy-Handover fÃ¼r SKILL 5 â€“ FEATURE DEBUG aus.

WICHTIG:
- Kein Skill-6-Audit-Handover vor deiner Antwort.
- Kein Skill-5-Debug-Handover vor deiner Fehlerbeschreibung.
```

Compact Audit Package fÃ¼r Skill 6:
- Spec: <source spec file>
- Task: <task file>
- Target Task: ALL COMPLETED
- Pre-Check: <PRE-CHECK PASSED summary/result>
- Changed Files: <Liste der tatsÃ¤chlich geÃ¤nderten Dateien>
- Relevant Diff / Excerpts: <kurze relevante AuszÃ¼ge oder Diff-Zusammenfassung>
- Test Results: <ausgefÃ¼hrte Tests und Ergebnis>
- Gesamt-Test Results: <ausgefÃ¼hrte Gesamtvalidierung und Ergebnis>
- Auto-Verification: <PASS | N/A mit Begruendung> + Mini-TestPlan-Pfad + Generated-Runner-Pfad
- User Sign-off Evidence: <User-bestÃ¤tigter Produktcheck nach Skill 4 Abschnitt 6>
- Known Risks: <bekannte Risiken, Scope-Hinweise, unrelated Workspace Changes>
- Pipeline Status: <Completed Tasks = alle, Remaining Tasks = keine>

Audit Model Gate:
- Skill 4 MUSS vor dem Copy-Paste-Prompt eine konservative Audit-Modell-Empfehlung ausgeben.
- Ziel: maximale Audit-QualitÃ¤t bei minimal nÃ¶tigen Modellkosten.
- Format:
  - `Audit Risk: LOW | MEDIUM | HIGH | CRITICAL`
  - `Recommended Audit Model: Kimi k2.5 | SWE 1.6 | GPT-5.5`
  - `Reason: <kurze BegrÃ¼ndung anhand Scope, geÃ¤nderter Dateien, Tests, Risiken>`
- LOW:
  - reine Doku-/Text-/Workflow-Ã„nderung
  - kleine lokale UI-/CSS-/Label-Ã„nderung
  - einzelne deterministische Test-/Config-ErgÃ¤nzung
  - keine Backend-/Persistenz-/IPC-/Security-/Release-Ã„nderung
  - alle Validierungen PASS
  - Empfehlung: `Kimi k2.5` oder `SWE 1.6`
- MEDIUM:
  - kleine bis mittlere mehrdateiige Ã„nderung
  - UI/API-Kopplung ohne Persistenz/Security/Release
  - Tests PASS und Scope eindeutig
  - Empfehlung: `SWE 1.6`
- HIGH oder CRITICAL:
  - Backend-Kernlogik, Persistenz, DB, Migration, Auth/Security, Electron/IPC, Release/Packaging/Auto-Update, Model Routing, Provider, Tool Calls, Memory, Context, RAG oder mehrere Subsysteme
  - fehlende/fehlgeschlagene Tests, `PARTIAL`, Known Risks, Fix-Loop, unklare Akzeptanz oder mÃ¶gliche Regression
  - Empfehlung/Pflicht: `GPT-5.5`
- Unsicherheitsregel:
  - Wenn Skill 4 die Audit-Risikoklasse nicht eindeutig niedrig oder mittel begrÃ¼nden kann, MUSS `GPT-5.5` empfohlen werden.

Audit-Chat-Regel:
â†’ Skill 6 SOLL in einem neuen Chat mit dem empfohlenen Audit-Modell ausgeführt werden.
â†’ Bei `Audit Risk: HIGH` oder `Audit Risk: CRITICAL` MUSS GPT-5.5 verwendet werden.
â†’ Der aktuelle Skill-4-Chat darf nicht als Audit-Kontext verwendet werden.
â†’ Skill 6 darf nur aus dem Compact Audit Package auditieren.
â†’ Kein vollständiger Chatverlauf, keine Debug-Diskussionen, keine Nebeninformationen kopieren.
â†’ Der Skill-6-Handover darf erst nach erfolgreichem USER SIGN-OFF (User-Antwort Abschnitt 6) ausgegeben werden.
â†’ Nach User-Antwort `Manueller Test erfolgreich.` MUSS Skill 4 den Skill-6-Handover als einzelnen grauen Copy-Block ausgeben.
â†’ Nach User-Antwort `Es funktioniert nicht wie gewÃ¼nscht.` MUSS Skill 4 zuerst eine konkrete Fehlerbeschreibung einsammeln und danach den Skill-5-Handover als einzelnen grauen Copy-Block ausgeben.
â†’ Skill 4 darf in beiden FÃ¤llen keine weitere Implementation starten.

USER SIGN-OFF GATE (Abschnitt 6 — volles Template siehe oben unter EXECUTION FLOW):

- Duplikat-Templates sind verboten. Nutze denselben Block wie unter **### 6. USER SIGN-OFF GATE** inkl. `MANUELLER UX-CHECK ERFORDERLICH` und Option 1/2.

HANDOVER-GENERATION-GATE:

- Die folgenden Skill-6- und Skill-5-Copy-Paste-Prompts sind NUR bedingte Templates.
- Skill 4 darf sie NICHT automatisch zusammen mit `ALL TASKS COMPLETE` ausgeben.
- Skill 4 darf den Skill-6-Audit-Chat-Prompt NUR ausgeben, wenn die unmittelbar vorherige User-Antwort exakt oder sinngemÃ¤ÃŸ `Manueller Test erfolgreich.` bestÃ¤tigt.
- Skill 4 darf den Skill-5-Debug-Prompt NUR ausgeben, nachdem der User eine Fehlerbeschreibung fÃ¼r den USER SIGN-OFF (Abschnitt 6) geliefert hat.
- Wenn noch keine User-Antwort auf das USER SIGN-OFF GATE vorliegt, MUSS Skill 4 mit dem USER SIGN-OFF-Gate enden.

Skill-6-Dateiliste:
- <source spec file>
- <task file>
- <jede tatsÃ¤chlich geÃ¤nderte Datei>
- <optional: Testdateien / Diffdatei / Testoutput-Datei, falls vorhanden>

Copy-Paste-Prompt fÃ¼r neuen Skill-6-Audit-Chat:

```text
@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]

WICHTIG:
- Dies ist ein neuer Audit-Chat mit dem von Skill 4 empfohlenen Audit-Modell.
- Nutze ausschließlich dieses Compact Audit Package.
- Ignoriere jeden früheren Chatverlauf und alle nicht genannten Dateien.
- Erfinde keine zusätzlichen Anforderungen.
- Wenn das Audit Model Gate HIGH/CRITICAL oder unklar ergibt, verwende GPT-5.5.

Audit Model Gate:
- Audit Risk: <LOW | MEDIUM | HIGH | CRITICAL>
- Recommended Audit Model: <Kimi k2.5 | SWE 1.6 | GPT-5.5>
- Reason: <kurze BegrÃ¼ndung>

Compact Audit Package:

Feature:
<Feature-Name>

Spec:
<source spec file>

Task:
<task file>

Target Task:
ALL COMPLETED

Pre-Check:
<PRE-CHECK PASSED summary/result>

Changed Files:
- <Datei 1>
- <Datei 2>

Relevant Diff / Excerpts:
- <Datei 1>:
  - <kurze relevante Ã„nderung>
- <Datei 2>:
  - <kurze relevante Ã„nderung>

Test Results:
- <Testtyp>: <PASS | FAIL | N/A>
- <konkrete Testnamen und Ergebnisse>

Gesamt-Test Results:
- <Build/Unit/Integration/E2E/Smoke>: PASS | FAIL | N/A
- <konkrete Gesamtvalidierung und Ergebnis>

User Sign-off Evidence:
- Status: PRESENT
- Source: Skill 4 USER SIGN-OFF GATE (Abschnitt 6)
- Ergebnis: PASS
- User Confirmation: Manueller Test erfolgreich.

Known Risks:
- <bekannte Risiken>
- <unrelated Workspace Changes, falls vorhanden>

Pipeline Status:
- Completed Tasks:
  - <alle abgeschlossenen Tasks>
- Remaining Tasks:
  - keine
- Spec Implementation Complete: YES

Audit Scope:
Bitte die vollstÃ¤ndige Spec-Umsetzung und die oben genannten Dateien prÃ¼fen.
Alle anderen Workspace-Ã„nderungen sind out of scope.
```

Copy-Paste-Prompt fÃ¼r Skill-5-Debug nach fehlgeschlagenem manuellem Janus-Test:

```text
@[/SKILL 5 – FEATURE DEBUG]

Skill 5 Debug Package:

Feature:
<Feature-Name>

Iteration:
1

Task:
<task file / target task id>

Spec:
<source spec file>

Pre-Check:
<PRE-CHECK PASSED summary/result>

Final Audit / Skill 6:
N/A – Fehler wurde im manuellen Janus-Test direkt nach Skill 4 festgestellt.

Manueller Janus-Test:
- Prompt/Klickpfad: <was der User in Janus getan hat>
- Erwartetes Ergebnis: <Soll>
- TatsÃ¤chliches Ergebnis: <Ist>
- Screenshot/Log/Output: <falls vorhanden>

Backend Log:
<relevanter Auszug oder N/A>

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

Stop-Regel:
â†’ Validieren oder implementiere keinen weiteren Task automatisch.
ðŸš¨ MODEL SWITCH RULE (HARD PROTOCOL)

Wenn wÃ¤hrend Execution:

Task unklar wird
Scope nicht deterministisch umsetzbar ist
mehrere Implementationswege gleich plausibel sind
Codebase Inkonsistenzen auftreten

âž¡ STOP EXECUTION

MODEL SWITCH REQUIRED: SWE 1.6 â†’ GPT-5.5

Reason:
- <z. B. ambiguity / multi-file conflict / non-deterministic logic>

Action:
â†’ neuer Chat starten
â†’ Skill 4 erneut mit GPT-5.5 ausfÃ¼hren
ðŸš« RESTRICTIONS

STRICT PROVIDER ISOLATION: Janus ist ein BYOK-Tool. Implementiere oder erlaube NIEMALS automatische Provider-Fallbacks (z.B. Gemini zu GPT) im Produktcode. Wenn ein Provider-spezifischer Test (z.B. Gemini) fehlschlägt, muss er als Fehler dieses Providers behandelt werden. Ein Ausweichen auf einen anderen Provider zur Fehlerumgehung ist STRENG VERBOTEN.

KEINE Architekturentscheidungen
KEINE neuen Features
KEINE Scope-Erweiterung
KEINE Design-Refactors
KEINE Task-Interpretation
ðŸ§  ERROR HANDLING

Wenn Task nicht ausfÃ¼hrbar:

TASK EXECUTION FAILED

Reason:
- <konkreter Grund>

Action:
â†’ Skill 2 re-evaluate oder GPT-5.5 Escalation
ðŸ§  OUTPUT GUARANTEE

Output ist immer:

deterministic
implementation-only
test-driven
scope-strict
