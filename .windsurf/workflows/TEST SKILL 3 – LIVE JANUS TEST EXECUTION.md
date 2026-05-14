---
description: SWE 1.6 Test Pipeline Phase 3 – Automation-first Live Janus Test Execution. Orchestriert Generator, Runner und Evidence Aggregation aus TestSpec/TestPlan, holt User-OK ein, fuehrt Janus automatisiert, sammelt Evidence/Logs und schreibt TestResult. Keine Produktimplementation.
---

# TEST SKILL 3 – LIVE JANUS TEST EXECUTION

## 🎯 PURPOSE

Dieser Skill fuehrt **reale Live-Tests im offenen Janus automation-first** aus.

Skill 3 ist **kein freier Playwright-Code-Autor**. Skill 3 ist der Orchestrator fuer drei versionierte Test-Services:

1. Generator Service: TestPlan + Strategy Registry -> generierter Playwright Runner
2. Runner Service: generierter Playwright Runner -> Live-Ausfuehrung + Raw Evidence
3. Evidence Aggregator: Raw Evidence -> TestResult Artefakte

Er sammelt Evidence aus:
→ Playwright-Resultaten, Screenshots/Trace, Frontend-Debug-Log, Backend-Log, Network/API-Evidence, Kosten/Token-Anzeigen, Tool-/Intent-Hinweisen und nur wenn noetig User-Beobachtung.

Der Skill behauptet **nur dann**, Janus getestet zu haben, wenn ein Playwright-Live-Run oder ein vom User bestaetigter manueller Gate-Schritt Evidence erzeugt hat.

KEINE Produktimplementation. KEINE Architekturentscheidungen. Test-Runner/Fixtures duerfen nur als test-run-spezifische Automationsartefakte erzeugt werden.

---

## 🤖 DEFAULT MODEL

SWE 1.6

Ausnahme:
- GPT-5.5 nur bei unklarem Testverhalten oder Security-Eskalation waehrend des Tests

---

## 📥 INPUT

- TestSpec aus `documentation/TEST_SPEC/`
- TestPlan aus `documentation/test-runs/`
- Precheck Result aus TEST SKILL 2
- Optional: User-OK fuer Live-Ausfuehrung gegen geoeffnetes Janus

---

## 📌 AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer TestSpec, TestPlan und optional Precheck Result nennt, sind diese Artefakte automatisch die verbindlichen Testquellen.

Der Skill MUSS dann:

- die genannte TestSpec-Datei vollstaendig lesen
- die genannte TestPlan-Datei vollstaendig lesen
- das Precheck Result beruecksichtigen, falls angegeben
- ausschliesslich die definierten Testfaelle durchfuehren lassen
- Chatverlauf, fruehere Diskussionen und zusaetzliche muendliche Nebeninformationen ignorieren, sofern sie den Artefakten widersprechen oder ueber sie hinausgehen
- keine Requirements, Produktentscheidungen oder Architekturentscheidungen aus dem Chatkontext ergaenzen
- stoppen, wenn TestSpec und TestPlan nicht konsistent sind

Minimaler gueltiger User-Aufruf:

```text
/TEST SKILL 3 – LIVE JANUS TEST EXECUTION mit folgenden Artefakten:
TestSpec: documentation/TEST_SPEC/<TESTSPEC>.md
TestPlan: documentation/test-runs/<TEST_RUN_ID>_plan.json
Precheck: READY FOR LIVE TEST
```

Wenn Artefakte unlesbar oder widerspruechlich:

```text
LIVE TEST ARTIFACTS INVALID

Issue:
- <konkretes Problem>

Action:
→ korrekte Artefakte angeben oder TEST SKILL 1/2 erneut ausfuehren
```

---

## 💎 DIAMOND AUTOMATION STANDARD

Skill 3 ist **Automation-first**.

Manuelles Prompt-fuer-Prompt-Testen ist nur erlaubt, wenn:

- Playwright technisch nicht starten kann,
- Janus ein nicht automatisierbares OS-/Electron-/Permission-Gate zeigt,
- ein destruktiver oder externer Schritt eine ausdrueckliche User-Freigabe braucht,
- oder der TestPlan selbst manuelle Beobachtung als zwingende Evidence definiert.

Harte Negativregel:

- `Requires live Janus chat interaction` ist **kein** gueltiger Grund fuer `MANUAL_GATE_REQUIRED`.
- Externe API-Aufrufe wie Wetter, Wikipedia, Geo oder RSS sind **kein** gueltiger Grund fuer manuelle Prompt-Ausfuehrung.
- UX-Beobachtung ist **kein** gueltiger Grund fuer manuelle Prompt-Ausfuehrung, solange Playwright UI-Zustaende, Antworttexte, Screenshots oder Fehlerzustaende erfassen kann.
- Normale Chat-Prompts MUeSSEN durch Playwright automatisch eingegeben und abgesendet werden.
- Wenn Provider-/Model-Switching manuell ist, darf nur der Switch ein Manual Gate sein; die Prompts danach muessen automatisch weiterlaufen.

Default ist:

1. TestSpec/TestPlan laden.
2. TestPlan gegen Schema/Strategy Registry pruefen.
3. Playwright-Live-Runner ausschliesslich ueber den Generator Service erzeugen.
4. Generierten Runner statisch validieren.
5. **Connectivity-Guard:** `baseUrl` (optional `backendHealthUrl`) aus TestPlan prüfen — bei Fehlschlag `LIVE TEST BLOCKED — INFRASTRUCTURE OFFLINE` (kein User-OK).
6. User um Start-OK bitten (`OK START LIVE TEST` — nur wenn Schritt 5 PASS).
7. Janus automatisch oeffnen oder vorhandene Testinstanz transparent nutzen.
8. Generierten Runner ausfuehren.
9. Antworten, API/Network-Evidence, UI-State, Screenshots/Trace und Logs sammeln.
10. Bei manuellem Gate klar stoppen: was der User tun muss, woran PASS/FAIL erkannt wird, wie er OK gibt.
11. Nach OK automatisch fortsetzen.
12. TestResult aus maschineller Evidence erzeugen.

---

## ⚡ AUTO-PILOT MODE (SOFORTAUSFUEHRUNG)

Skill 3 ist im Auto-Pilot-Modus optimiert. Manuelle Zwischenstopps zwischen Skill-Aufruf und User-OK sind verboten — **ausgenommen** der automatisierte **Connectivity-Guard** (keine Rückfrage, kein „JA“ vor Prüfung).

**Sofort-Aktionen beim Skill-Aufruf (ohne Rueckfrage)**:

1. **Phase 3A SOFORT** — Generator-Befehl unmittelbar nach `LOAD ARTIFACTS` ausfuehren:

   ```text
   node tests/e2e/generator/generate-live-runner.mjs --plan <plan_path> --out <spec_path>
   ```

2. **Phase 3B SOFORT** — Validator-Befehl unmittelbar nach erfolgreichem Generator-Lauf ausfuehren:

   ```text
   node tests/e2e/generator/validate-runner.mjs --plan <plan_path> --runner <spec_path>
   ```

3. **Phase 3C Connectivity-Guard** — unmittelbar nach erfolgreichem Validator-Lauf: Erreichbarkeit von `baseUrl` (optional `backendHealthUrl`) aus dem TestPlan prüfen (siehe Section `Connectivity-Guard` oben). Bei FAIL: Block-Output `LIVE TEST BLOCKED — INFRASTRUCTURE OFFLINE` — **kein** `USER-OK LIVE GATE`.
4. **Erst danach** den kompakten Auto-Pilot-Output gemaess Section `USER-OK LIVE GATE` ausgeben und auf `OK START LIVE TEST` warten.

**Auto-Pilot Default-Einstellungen** (werden ohne jede User-Rueckfrage gesetzt — stillschweigend):

- `Live Visual Mode` = `LIVE_VISUAL` (Default — Browserfenster sichtbar)
- `Watch target` = `PLAYWRIGHT_BROWSER` (Default — sichtbares Chromium-Fenster)
- `Start command` = Playwright `webServer` auto-start via `playwright.config.js`, sofern der Stack erreichbar ist; bei Offline-Stack zuerst **`npm run start-dev`** (siehe Connectivity-Guard).
- `Runner command` = `npx playwright test <spec_path> --headed --workers=1` — **immer**, ausser der User hat im laufenden Auftrag explizit etwas anderes verlangt
- `Janus Status` = **Connectivity-Guard PASS** vor READY-Block, danach `ASSUMED_STABLE_FOR_RUN` — Skill 3 fragt **nicht** nach `JANUS TEST INSTANCE RUNNING` im Default-Browserpfad

**Connectivity-Guard (Pflicht — nach Phase 3B, vor USER-OK LIVE GATE):**

1. Lese `baseUrl` und `backendHealthUrl` aus dem gebundenen TestPlan-JSON (Single Source of Truth).
2. Führe **eine** kurze Erreichbarkeitsprüfung aus (z. B. `curl` mit Timeout oder `node -e` mit `fetch`/`http.get`) gegen **`baseUrl`** — **bevor** du `LIVE JANUS AUTOMATION READY` ausgibst oder `Antworte mit: OK START LIVE TEST` forderst.
3. **Optional:** wenn `backendHealthUrl` gesetzt ist, gleiches gegen diese URL (kurzer Timeout).
4. **Bei Verbindung abgelehnt** (`ERR_CONNECTION_REFUSED`, `ECONNREFUSED`, `net::ERR_CONNECTION_REFUSED`, gleichwertig) oder **keine TCP-Antwort** bis Timeout: **kein** User-OK-Trigger. Sofort:

```text
LIVE TEST BLOCKED — INFRASTRUCTURE OFFLINE

Blocker: Janus läuft nicht. Keine Verbindung zu <baseUrl> (aus TestPlan).
Bitte starte aus dem Repository-Root: npm run start-dev

Connectivity-Guard fehlgeschlagen — kein OK START LIVE TEST.
```

5. **Danach** erst den kompakten Ready-Block mit `Antworte mit: OK START LIVE TEST` ausgeben.

**Janus Port Sanity (Konsistenz mit TEST SKILL 1):** Wenn der TestPlan abweichende Ports enthält, den Guard gegen **genau** diese URLs fahren — nicht raten. Default-Erwartung ohne Spec-Bruch: Frontend **`5173`**, Backend-Health **`8001`** — **niemals `8000`**, es sei denn, die TestSpec/TestPlan nennt 8000 ausdrücklich.

**Nach erfolgreichem Connectivity-Guard** gilt für den anschließenden Playwright-Lauf: Laufzeitfehler werden weiterhin mit den Taxonomie-Codes des Runners dokumentiert (`FRONTEND_NOT_READY`, `BACKEND_HEALTH_FAIL`, **`INFRASTRUCTURE_OFFLINE`** bei Refused nach Start, siehe Generator).

**Verboten (weiterhin):** zusätzliche Health-Spiralen, Port-Scans, „läuft Janus schon?“-Dialoge **nach** dem Guard **und parallel** zum READY-Block; mehrfache nervöse Re-Pings ohne neuen Blocker.

Wenn der User explizit Electron-Desktop-Beobachtung (`ELECTRON_DESKTOP`) oder Headless-Evidence (`HEADLESS_EVIDENCE`) im laufenden Auftrag fordert, werden die entsprechenden Defaults ueberschrieben — der Connectivity-Guard gegen die URLs aus dem TestPlan bleibt **Pflicht** vor dem READY-Block.

**Auto-Pilot-Stopper (Sofort-Block, nicht auf User-OK warten)**:

- Generator-Fehler -> `LIVE TEST AUTOMATION BLOCKED` mit `Block Reason: GENERATOR_NOT_READY` oder `TESTPLAN_STRATEGY_INVALID`
- Validator-Fehler -> `LIVE TEST AUTOMATION BLOCKED` mit `Block Reason: GENERATOR_VALIDATION_FAILED`
- **Connectivity-Guard FAIL** (Refused/Timeout auf `baseUrl` oder `backendHealthUrl`) -> `LIVE TEST BLOCKED — INFRASTRUCTURE OFFLINE` (siehe Connectivity-Guard-Template; kein `OK START LIVE TEST`)
- Verbotene Modelle im TestPlan -> `LIVE TEST BLOCKED: Provider-/Model-Matrix verwendet veraltete Textmodelle`
- Fehlende lokale E2E-Config -> `LIVE TEST AUTOMATION BLOCKED` mit `Block Reason: JANUS_CONFIG_OR_AUTH_MISSING` (Auto-Fix-Pfad anbieten)

In jedem dieser Faelle gibt Skill 3 sofort den Block-Output plus Copy-Handover gemaess der jeweiligen Block-Section aus — KEIN Auto-Pilot-OK-Gate.

---

## 🧪 PLAYWRIGHT LIVE-RUNNER REQUIREMENTS

Der Skill MUSS vor Live-Ausfuehrung einen test-run-spezifischen Playwright-Runner ueber den Generator Service vorbereiten oder einen vorhandenen Runner gegen TestPlan und Validator erneut validieren.

Zielpfade:

```text
tests/e2e/generated/<test_run_id>.live.spec.js
documentation/test-results/<test_run_id>/
documentation/test-results/<test_run_id>_results.md
debug_logs/frontend_log_<test_run_id>_<timestamp>.md
debug_logs/backend_log_<test_run_id>_<timestamp>.md
```

Generator-Service Binding:

```text
Generator Script: tests/e2e/generator/generate-live-runner.mjs
Validator Script: tests/e2e/generator/validate-runner.mjs
Strategy Registry: tests/e2e/generator/strategy-registry.json
TestPlan Schema: tests/e2e/generator/test-plan.schema.json
Generated Runner: tests/e2e/generated/<test_run_id>.live.spec.js
```

Harte Generator-Regeln:

- Sobald `tests/e2e/generator/generate-live-runner.mjs` vorhanden und ausfuehrbar ist, MUSS Skill 3 diesen Generator verwenden.
- Skill 3 darf keine freie Playwright-Spec mehr aus Chat-Kontext, eigener Interpretation oder LLM-Text generieren.
- `tests/e2e/generated/*.live.spec.js` ist ein Build-Artefakt und darf nicht manuell gepatcht werden.
- Wenn der generierte Runner falsch ist, MUeSSEN TestPlan, Strategy Registry, Generator oder Validator korrigiert werden; danach MUSS neu generiert werden.
- Wenn der Generator fehlt, fehlschlaegt oder keine valide Spec erzeugt, MUSS Skill 3 `LIVE TEST AUTOMATION BLOCKED` mit Block Reason `GENERATOR_NOT_READY` oder `GENERATOR_VALIDATION_FAILED` ausgeben.
- Ein manueller Playwright-Code-Fallback ist verboten.
- Strategy-IDs im TestPlan muessen in `strategy-registry.json` existieren; unbekannte Strategien blockieren den Live-Test.
- PASS/FAIL-Semantik darf nicht frei im Skill-Prompt erfunden werden; sie muss aus TestPlan/Strategy Registry/Validator/Evaluator ableitbar sein.

Der Runner MUSS vorhandene Janus-E2E-Patterns wiederverwenden:

- App unter `http://localhost:5173/` laden.
- Backend unter `http://localhost:8001/` pruefen.
- echten E2E-JWT aus lokaler Janus Config erzeugen, wenn noetig.
- `X-Janus-Internal-Key` fuer `/api/**` Requests injizieren, wenn Browser-Kontext den Electron-Key nicht setzt.
- Chat-Fenster A verwenden.
- Chat-Input MUSS ueber `page.getByRole('region', { name: 'Chat-Fenster A' }).getByPlaceholder(/Nachricht an Janus senden/)` oder einen gleichwertig auf Fenster A gescopeten Selector gefunden werden.
- Globale Chat-Selektoren wie `page.getByPlaceholder('Nachricht an Janus senden')` sind verboten, wenn mehrere Chat-Fenster existieren.
- Antwort-Assertions MUeSSEN auf `#chat-messages-A` oder einen gleichwertig auf Chat-Fenster A gescopeten Message-Container begrenzt sein.
- vor Teststart neuen Chat erzeugen und leeren Zustand verifizieren.
- Chatnachrichten ueber denselben Sendepfad wie die App senden.
- Fake-Auth wie `e2e-test-fake-token` ist fuer Live-Runner verboten; der Runner MUSS einen gueltigen lokalen E2E-JWT erzeugen oder `LIVE TEST AUTOMATION BLOCKED` melden.
- Tests seriell ausfuehren, nicht parallel.

Real-Operation-Fidelity:

- Ein gruener Playwright-Test darf nur PASS sein, wenn der Prompt ueber den echten Janus-UI-Sendepfad in Chat-Fenster A abgeschickt wurde.
- Ein gruener Playwright-Test darf nur PASS sein, wenn die bewertete Antwort aus demselben Chat-Fenster A stammt.
- Jeder TestCase MUSS Prompt, Antworttext, Status und Notes speichern, damit nachvollziehbar ist, was bei welchem Prompt passiert ist.
- Runner duerfen keine PASS-Ergebnisse nur aus Mock-Daten, Fake-Login, falschem Fenster, unspezifischen globalen Selektoren oder blossen UI-Sichtbarkeitschecks ableiten.
- Wenn der Runner diese Fidelity-Regeln nicht erfuellt, MUSS der Skill `LIVE TEST AUTOMATION BLOCKED` oder `RETEST REQUIRED (Test-Runner Fidelity Issue)` ausgeben.

Der Runner MUSS pro TestCase mindestens speichern:

- TestCase-ID
- Provider
- Model
- Prompt
- erwartetes Routing/Tool
- Antworttext
- erkannte UI-Fehler
- relevante API/Network Requests
- relevante Console Errors
- Screenshot bei FAIL/PARTIAL/BLOCKED
- Status: PASS | PARTIAL | FAIL | BLOCKED | NOT RUN WITH REASON

Automation-Minimum:

- Functional GPT TestCases muessen `AUTOMATED` sein.
- Intent/Routing TestCases muessen `AUTOMATED` sein.
- UX-TestCases muessen mindestens fuer UI-/Antwortzustand `AUTOMATED` sein.
- Functional Gemini TestCases muessen `AUTOMATED` sein, wenn Provider-/Model-Auswahl automatisierbar ist.
- Wenn Provider-/Model-Auswahl nicht automatisierbar ist, ist nur der Provider-Switch `MANUAL_GATE_REQUIRED`; Gemini-Prompts bleiben danach `AUTOMATED`.
- Security/PINJ duerfen `MANUAL_GATE_REQUIRED` oder `BACKEND_EVIDENCE_REQUIRED` sein, muessen aber im Runner/TestResult erscheinen.
- Cost/Token darf `BACKEND_EVIDENCE_REQUIRED` sein, muss aber im TestResult erscheinen.
- Wenn Functional GPT, Intent/Routing oder UX pauschal `MANUAL_GATE_REQUIRED` sind, MUSS der Start blockieren.

---

## ✅ USER-OK LIVE GATE

Nachdem der Preflight (Phase 3A Generator und Phase 3B Validator) **und** der **Connectivity-Guard** (Phase 3C) erfolgreich durchgelaufen sind, gibt Skill 3 **ausschliesslich** eine einzige, schlanke Ready-Meldung aus und wartet auf genau ein Kommando: `OK START LIVE TEST`.

**ABSOLUTE REGEL — STRENG VERBOTEN**:

- Verboten: Nachfrage nach `JANUS TEST INSTANCE RUNNING`, Backend-Health, Frontend-Status oder ob Janus laeuft — **im Default-Browserpfad** (der Guard hat bereits geantwortet).
- Verboten: Nachfrage nach `LIVE_VISUAL` vs. `HEADLESS_EVIDENCE` oder Visual-Mode-Bestaetigung.
- Verboten: Nachfrage nach `Watch target` (Electron vs. Browser).
- Verboten: Frage "Soll ich Janus automatisch starten?" und alle Synonyme **zwischen** Guard-PASS und `OK START LIVE TEST` (Hinweis `npm run start-dev` nur im **INFRASTRUCTURE OFFLINE**-Block, nicht als Rückfrage).
- Verboten: Listen mit "Erforderlichen Bestaetigungen" oder "User action required".
- Verboten: jede zusaetzliche Frage zwischen Preflight+Guard-Erfolg und dem `OK START LIVE TEST`-Trigger.
- Verboten: **zusätzliche** Health-/Reachability-Checks jenseits des **einmaligen** Connectivity-Guards gegen die URLs aus dem TestPlan (keine Doppel-Pings, kein Raten von Ports).
- Default-Annahmen werden stillschweigend gesetzt (siehe `Auto-Assume Defaults` unten); der User bekommt sie als kurze Statuszeile zu sehen, aber **nicht als Frage**.

**READY-KLAUSEL (nach Connectivity-Guard PASS):**

Wenn der Connectivity-Guard **PASS** ist, MUSS Skill 3 den Ready-Block ausgeben und mit `Antworte mit: OK START LIVE TEST` enden. War der Guard **FAIL**, ist der Ready-Block **verboten** — stattdessen nur den **INFRASTRUCTURE OFFLINE**-Block (siehe AUTO-PILOT MODE).

**Pflichtausgabe (Single-Trigger Form — exakt diese Struktur)**:

```text
LIVE JANUS AUTOMATION READY

TestRun: <TEST-RUN-ID>
Generator: SUCCESS | Validator: PASSED
Connectivity-Guard: PASS

Scope:
| TestCase-ID | Type | Provider/Model | Status |
|-------------|------|----------------|--------|
| TC-001 | functional | GPT / gpt-5.4-nano | AUTOMATED |
| TC-NNN | <type> | <provider/model> | AUTOMATED | MANUAL_GATE_REQUIRED |

Alle <N> Tests validiert. Bereit fuer LIVE_VISUAL Dauerlauf.

Antworte mit: OK START LIVE TEST
```

Der Block MUSS mit `Antworte mit: OK START LIVE TEST` als letzter Zeile enden. Keine Liste davor, kein Fragenkatalog danach.

**Auto-Assume Defaults (stillschweigend gesetzt, keine Nachfrage)**:

- `Visual Mode = LIVE_VISUAL` (sichtbares Chromium-Fenster)
- `Watch target = PLAYWRIGHT_BROWSER`
- `Runner Command = npx playwright test <spec_path> --headed --workers=1`
- `Test Instance = Playwright webServer auto-start via playwright.config.js`
- `Janus Status = CONNECTIVITY_GUARD_PASS` — vor Ready-Block verifiziert; danach kann der Runner bei Laufzeitfehlern weiterhin `FRONTEND_NOT_READY` / `BACKEND_HEALTH_FAIL` / `INFRASTRUCTURE_OFFLINE` melden
- Diese Defaults gelten **immer**, ausser der User hat im laufenden Auftrag explizit etwas anderes verlangt (z. B. ein User-Prompt enthielt explizit `HEADLESS_EVIDENCE`, `ELECTRON_DESKTOP` oder `npm run start-dev` als Anweisung). In dem Fall wird der entsprechende Default ueberschrieben — aber immer noch ohne neue Frage an den User.

**Laufzeit vs. Guard:**

- Der **Connectivity-Guard** fängt typische **ERR_CONNECTION_REFUSED**-Fälle vor dem User-OK ab (`LIVE TEST BLOCKED — INFRASTRUCTURE OFFLINE`).
- **Nach** `OK START LIVE TEST` können weiterhin `BACKEND_HEALTH_FAIL`, `FRONTEND_NOT_READY` oder **`INFRASTRUCTURE_OFFLINE`** (vom generierten Runner, z. B. `page.goto` während des Laufs) im TestResult als `FAIL` landen — dann Evidence 1:1 an Skill 4.
- Keine redundanten Health-Loops **nach** erfolgreichem Guard und **vor** Runner-Start.

**Verhalten nach OK** (Dauerlauf-Regel — siehe auch Section 4):

Nach `OK START LIVE TEST` fuehrt der Skill den Runner aus, ueberwacht den Browser-Stream live und schreibt das finale TestResult ohne weitere Stopps. Keine zusaetzliche `JANUS TEST INSTANCE RUNNING`-Bestaetigung, keine Zwischen-Eingriffe — ausser ein TestCase markiert sich explizit als `MANUAL_GATE_REQUIRED`.

---

### USER-OK LIVE GATE — INTERNE COMPLIANCE-CHECKLISTE (NICHT an User ausgeben)

Die folgenden Pruefpunkte sind **rein interne** Validation-Schritte, die Skill 3 selbst durchfuehrt, BEVOR der Single-Trigger-Block ausgegeben wird. Sie sind **keine Fragen an den User**, sie werden **nicht als Liste ausgegeben** und sie produzieren **keine Confirm-Prompts**. Ergebnis ist binaer: alle gruen -> Single-Trigger-Block ausgeben, sonst -> `LIVE TEST AUTOMATION BLOCKED`-Block ausgeben.

Pruefpunkte (Default-Werte fett markiert):

- `Generator Status`: GENERATED | REUSED_AFTER_VALIDATION | BLOCKED
- `Validator Status`: PASSED | FAILED | NOT RUN WITH REASON
- **`Connectivity-Guard`**: **PASS** | FAIL (FAIL -> kein READY-Block, nur INFRASTRUCTURE OFFLINE)
- `Generated Runner manually edited`: **NEIN** (UNKNOWN -> BLOCKED)
- `Source TestRun` vs. `Automation TestRun`: identisch | mit Begruendung
- Provider/Model Matrix: smallest-viable je Provider vorhanden, `Forbidden models found` MUSS **NO** sein
- `Live Visual Mode`: **LIVE_VISUAL** (Default) | HEADLESS_EVIDENCE (nur bei explizitem User-Wunsch)
- `Watch target`: **PLAYWRIGHT_BROWSER** (Default) | ELECTRON_DESKTOP (nur bei explizitem Electron-Test-Auftrag)
- `Start command`: **Playwright webServer auto-start** (Default) | npm run start-dev | npm run start-backend-only
- Scope Coverage je Kategorie (Functional GPT, Functional Gemini, Intent/Routing, Security, Prompt Injection, UX, Cost/Token, Provider Switching): Runner-Status und Evidence-Strategie pro TestPlan-ID dokumentiert
- Non-Automated Items: jedes `MANUAL_GATE_REQUIRED`/`BACKEND_EVIDENCE_REQUIRED`/`BLOCKED_WITH_REASON`-Item mit konkretem Grund

Harte Regeln (Verletzung -> `LIVE TEST AUTOMATION BLOCKED`):

- `Forbidden models found` MUSS `NO` sein.
- Security-, Prompt-Injection-, Provider- und Cost/Token-Tests duerfen nicht entfallen.
- Functional GPT, Intent/Routing und UX duerfen nicht pauschal `MANUAL_GATE_REQUIRED` sein.
- `Requires live Janus chat interaction` ist als Manual-Gate-Begruendung verboten.
- `External API call required` ist als Manual-Gate-Begruendung verboten.
- Wenn der Runner nur ein `manual execution guide` ist, MUSS `LIVE TEST AUTOMATION BLOCKED` ausgegeben werden.
- Bei `LIVE_VISUAL` MUSS der Runner-Befehl `--headed --workers=1` enthalten.
- Wenn der User die Electron-/Desktop-Janus-App sehen will, MUSS `Watch target: ELECTRON_DESKTOP` gesetzt und der Startbefehl `npm run start-dev` ausgegeben werden — der Auto-Pilot-Default schaltet dann aus.
- `npm run start-backend-only` darf NICHT als Startbefehl fuer Electron-Beobachtung ausgegeben werden.
- `LIVE JANUS AUTOMATION READY` darf nur ausgegeben werden, wenn alle internen Pruefpunkte gruen sind.

Wenn die Compliance-Checkliste fehlschlaegt, ist die Ausgabe nicht der kompakte Ready-Block, sondern ein vollstaendiger `LIVE TEST AUTOMATION BLOCKED`-Block mit konkretem Block Reason gemaess Section 2 (`GENERATOR_NOT_READY` | `GENERATOR_VALIDATION_FAILED` | `TESTPLAN_STRATEGY_INVALID` | `JANUS_CONFIG_OR_AUTH_MISSING` | **`INFRASTRUCTURE_OFFLINE` (Connectivity-Guard)** | sonstige) plus Copy-Handover.

Ohne explizites `OK START LIVE TEST` darf kein Live-Test gestartet werden.

---

## ⚙️ EXECUTION FLOW

Reihenfolge im Auto-Pilot-Modus (Default):

1. **LOAD ARTIFACTS** — sofort beim Skill-Aufruf
2. **GENERATE OR VALIDATE PLAYWRIGHT LIVE-RUNNER** (Phase 3A+3B) — sofort und ohne Rueckfrage nach Schritt 1
3. **CONNECTIVITY-GUARD** — Erreichbarkeit `baseUrl` / optional `backendHealthUrl` aus TestPlan; bei FAIL: Block, kein Schritt 4
4. **USER-OK GATE** — kompakte LIVE_VISUAL-Ready-Ausgabe, warte ausschliesslich auf `OK START LIVE TEST`
5. **RUN PLAYWRIGHT LIVE EXECUTION** — Dauerlauf nach OK, keine weiteren Stopps
6. **EVIDENCE AGGREGATION AND TESTRESULT PACKAGING** — automatisch nach Runner-Exit
7. **Skill-4-Copy-Handover** — automatisch nach TestResult

Schritte 1–3 laufen ohne User-Interaktion ab. Schritt 4 ist der einzige reguläre Stopp-Punkt. Schritte 5–7 laufen wieder ohne User-Interaktion ab, ausgenommen explizit `MANUAL_GATE_REQUIRED`-markierte TestCases.

---

### 1. LOAD ARTIFACTS

- TestSpec vollstaendig laden
- TestPlan vollstaendig laden
- Scope exakt extrahieren
- Testfaelle isolieren

---

### 2. GENERATE OR VALIDATE PLAYWRIGHT LIVE-RUNNER

**Auto-Pilot-Pflicht**: Skill 3 fuehrt Generierung (Phase 3A) und Validierung (Phase 3B) **SOFORT nach Skill-Aufruf ohne Rueckfrage** aus. Anschließend **Connectivity-Guard** (Phase 3C). Erst wenn Generator **und** Validator **und** Guard **PASS** sind, darf der USER-OK-Gate-Block (Section USER-OK LIVE GATE) ausgegeben werden.

Skill 3 Phase 3A ist ausschliesslich Orchestrierung der drei versionierten Test-Services. Der Skill ist KEIN Playwright-Code-Autor.

Der Test-Generator unter `tests/e2e/generator/generate-live-runner.mjs` ist die einzige Quelle fuer Playwright-Specs. Er beherrscht das `Promise.all`-Sende-Pattern, `pressSequentially` mit Frontend-Eingabe-Validation und robustes SSE-Rendering-/DOM-Resilience-Check; Reproduktion dieser Logik im Skill-Prompt ist verboten.

Die drei Pflichtbefehle (harte Fakten — exakt so verwenden, keine Varianten):

**Generator-Befehl**:

```text
node tests/e2e/generator/generate-live-runner.mjs --plan <plan_path> --out <spec_path>
```

Beispiel:

```text
node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/<test_run_id>_plan.json --out tests/e2e/generated/<test_run_id>.live.spec.js
```

**Validator-Befehl** (MUSS nach jedem Generator-Lauf ausgefuehrt werden):

```text
node tests/e2e/generator/validate-runner.mjs --plan <plan_path> --runner <spec_path>
```

Beispiel:

```text
node tests/e2e/generator/validate-runner.mjs --plan documentation/test-runs/<test_run_id>_plan.json --runner tests/e2e/generated/<test_run_id>.live.spec.js
```

**Runner-Befehl** (Standard fuer `LIVE_VISUAL`; siehe Phase 4 fuer Varianten):

```text
npx playwright test <spec_path> --headed --workers=1
```

Beispiel:

```text
npx playwright test tests/e2e/generated/<test_run_id>.live.spec.js --headed --workers=1
```

Der Skill MUSS:

- TestCases aus TestPlan extrahieren, aber nicht frei umformulieren.
- Provider-/Model-Matrix vor Generator-Ausfuehrung validieren.
- Generator-Ausgabe als Build-Artefakt behandeln.
- Runner nur unter `tests/e2e/generated/` erzeugen oder aktualisieren.
- Nach jeder Generator-Ausfuehrung den Validator ausfuehren und dessen Exit-Code im Preflight melden.
- Im Preflight Generator-Status und Validator-Status nennen.
- Bei Fehlschlag den exakten Generator-/Validator-Fehlertext unveraendert in den Block uebernehmen.
- Keine Produktdateien aendern.

Der Skill DARF NICHT:

- Playwright-Code frei schreiben oder aus Chat-Kontext rekonstruieren.
- die Generator-Pflichtbefehle mit eigenen Optionen, Flags oder Pfaden veraendern.
- generierte Runner manuell patchen.
- bei Generatorfehlern einen eigenen Runner als Fallback erstellen.
- TestCases, Strategien oder Assertions aus dem Chatkontext erfinden.
- Strategien direkt im Spec-File einfuegen — neue Strategien gehoeren in `tests/e2e/generator/strategy-registry.json` und werden anschliessend ueber Generator/Validator validiert.

Wenn Generator oder Validator fehlschlagen:

```text
LIVE TEST AUTOMATION BLOCKED

Block Reason: GENERATOR_NOT_READY | GENERATOR_VALIDATION_FAILED | TESTPLAN_STRATEGY_INVALID

Details:
- Generator: tests/e2e/generator/generate-live-runner.mjs
- Validator: tests/e2e/generator/validate-runner.mjs
- TestPlan: <path>
- Runner: tests/e2e/generated/<test_run_id>.live.spec.js
- Error: <konkrete Fehlermeldung>

Required Action:
- Generator, Strategy Registry oder TestPlan korrigieren.
- Danach Runner neu generieren und erneut validieren.
- Keinen manuellen Patch an tests/e2e/generated/*.live.spec.js vornehmen.
```

Pflicht fuer Chat-Antwort-Waiting:

- Der Runner darf nicht nur auf `.message.assistant` warten und bei Timeout generisch abbrechen.
- Jeder automatisierte Chat-Prompt MUSS Network-/Console-/RequestFailure-Evidence fuer den Zeitraum zwischen Send und Timeout sammeln.
- Beim Timeout MUSS der Runner unterscheiden:
  - UI hat Prompt angenommen, aber kein Chat-/Message-API-Request wurde beobachtet.
  - Chat-/Message-API-Request wurde gesendet, aber Backend/Provider antwortet nicht oder haengt.
  - Backend antwortet mit sichtbarer Fehler-/Systemmeldung.
  - Backend antwortet erfolgreich, aber UI rendert keine Assistant-Message.
- Der Fehlertext MUSS die relevanten API Events, Request-Failures und Console/PageErrors enthalten.
- Reines Erhoehen des Timeouts ist kein ausreichender Fix.
- `page.waitForResponse` ist nur erlaubt, wenn der erwartete Request deterministisch durch genau diese User-Aktion entstehen MUSS; fuer optionale oder fehleranfaellige Chat-/Provider-Antworten MUSS ein Timeout-/Evidence-Fallback genutzt werden.
- Wenn der Runner interne Frontend-Funktionen wie `sendMessage()` nutzt, darf er die Funktion nicht bis zum SSE-/Provider-Ende blockierend `await`en.
- Chat-Send muss als User-Interaktion oder Fire-and-forget ausgelöst werden; danach muss Playwright parallel auf Network-/UI-Evidence warten.
- Der Runner muss auf eine echte Assistant-Antwort warten, nicht nur auf die sofortige Loading-Bubble `...`.

Evidence-Gate fuer SSE-/Backend-Findings:

- Skill 3 darf ein Finding NICHT als `Backend SSE Stream sendet keine Text-Deltas` oder `Backend/Provider/SSE-Stream-Problem` klassifizieren, wenn kein konkreter `POST /api/chat/stream` fuer den Prompt beobachtet wurde.
- `GET /api/chats/<id>` oder `GET /api/chats/<id>/messages` beweisen nur Chat-/Message-Loading und reichen nicht als Beleg fuer erreichten SSE-Send-Pfad.
- Wenn die Assistant-Bubble sichtbar wird, aber kein `POST /api/chat/stream` in der Evidence steht, MUSS das Finding als `Test Runner / Frontend Send Path / SSE Diagnostics Incomplete` oder `Frontend/Test-Runner Trigger Issue` geroutet werden.
- Erst wenn `POST /api/chat/stream` fuer den Prompt beobachtet wurde und die Bubble trotzdem bei `...` oder leer bleibt, darf Skill 3 `Backend/Provider/SSE-Stream` als wahrscheinliche Kategorie vorschlagen.
- Der Handover zu Skill 4 MUSS die Evidence-Luecke explizit nennen, wenn `POST /api/chat/stream` fehlt.

Wenn kein Runner generiert werden kann:

```text
LIVE TEST AUTOMATION BLOCKED

Reason:
- <konkreter Grund>

Fallback:
- Nur die nicht automatisierbaren Schritte manuell ausfuehren lassen.
- Alle automatisierbaren Schritte bleiben Playwright-pflichtig.

Naechster Schritt:
- <konkrete User-Aktion oder Workflow-Route>

Copy-Handover:
- Wird unten als einzelner grauer Block ausgegeben: JA
```

Wenn der Runner nur eine manuelle Anleitung ist:

```text
LIVE TEST AUTOMATION BLOCKED

Reason:
- Generated Runner ist nur ein manual execution guide und fuehrt Janus-Prompts nicht automatisch aus.

Required Action:
- Playwright Runner so generieren, dass er Janus oeffnet, Chat-Fenster A nutzt, Prompts automatisch sendet, Antworten abwartet und Evidence sammelt.

Naechster Schritt:
- TEST SKILL 3 nach Runner-Korrektur erneut ausfuehren.

Copy-Handover:
- Wird unten als einzelner grauer Block ausgegeben: JA
```

Wenn Live-Retest/Preflight wegen Umgebung, Config, Auth, Healthcheck, API-Key, fehlender Janus-Config, Runner-Fidelity oder Evidence-Anforderung blockiert:

- Der Skill MUSS `LIVE TEST AUTOMATION BLOCKED` ausgeben.
- Der Skill MUSS einen Abschnitt `Erforderliche Aktion` mit konkreten Schritten ausgeben.
- Der Skill MUSS einen Abschnitt `Naechster Schritt` ausgeben.
- Der Skill MUSS am Ende einen einzelnen grauen Copy-Handover fuer `@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]` mit `Mode: LIVE_RETEST` ausgeben.
- Der Skill darf nicht nur mit einer Prosazusammenfassung enden.

Pflicht-Spezialfall fehlende Janus-Config/Auth:

Wenn `config.json`, `jwt_secret_key` oder `api_key` fehlen:

```text
LIVE TEST AUTOMATION BLOCKED

Block Reason: JANUS_CONFIG_OR_AUTH_MISSING

Details:
- Config Path: <konkreter Pfad>
- Missing: config.json | jwt_secret_key | api_key
- Impact: Playwright Live Runner kann keinen echten E2E-JWT erzeugen und/oder keinen X-Janus-Internal-Key injizieren.

Erforderliche Aktion:
1. Pruefen, ob ein sicherer lokaler E2E-Config-Auto-Fix moeglich ist.
2. Wenn sicher moeglich: `AUTO-FIX AVAILABLE: LOCAL_E2E_CONFIG_CREATE_OR_REPAIR` ausgeben.
3. User-OK einholen: `OK CREATE LOCAL E2E CONFIG`.
4. Danach lokale Config erzeugen oder fehlende Keys ergaenzen, ohne vorhandene Werte zu ueberschreiben.
5. Keine Secrets in den Chat kopieren.
6. Danach `USER-OK LIVE GATE` Compliance-Check erneut ausfuehren und LIVE_RETEST fortsetzen.

Naechster Schritt:
- Wenn User `OK CREATE LOCAL E2E CONFIG` bestaetigt: lokalen E2E-Config-Fix anwenden und Preflight erneut ausfuehren.
- Wenn Auto-Fix nicht sicher ist: Copy-Handover fuer manuellen Fix und erneuten LIVE_RETEST ausgeben.
```

### LOCAL E2E CONFIG AUTO-FIX (SAFE EXCEPTION)

Skill 3 darf als sichere Ausnahme lokale E2E-Testkonfiguration ausserhalb des Repos erstellen oder reparieren, wenn alle Bedingungen erfuellt sind:

- Der Blockgrund ist ausschliesslich `JANUS_CONFIG_OR_AUTH_MISSING`.
- Betroffen ist nur die lokale Janus-Config unter `%APPDATA%\Janus-Projekt\config.json` oder ein aequivalenter lokaler Janus-AppData-Pfad.
- Es werden nur lokale Test-/Dev-Secrets fuer `jwt_secret_key` und/oder `api_key` erzeugt.
- Es werden keine Produktdateien im Repo geaendert.
- Es werden keine externen Provider-Keys erzeugt, erfragt oder veraendert.
- Eine vorhandene Config wird nicht ueberschrieben.
- Fehlende Keys duerfen nur ergaenzt werden, vorhandene Werte bleiben unveraendert.
- Secrets duerfen niemals im Chat, TestResult oder Log-Auszug ausgegeben werden.
- Vor dem Schreibzugriff muss der User explizit `OK CREATE LOCAL E2E CONFIG` bestaetigen.

Wenn diese Bedingungen erfuellt sind, MUSS Skill 3 nicht nur blockieren, sondern folgende Option ausgeben:

```text
AUTO-FIX AVAILABLE: LOCAL_E2E_CONFIG_CREATE_OR_REPAIR

Proposed Action:
- Create directory if missing: <config directory>
- Create config.json if missing.
- Add missing local-only `jwt_secret_key`.
- Add missing local-only `api_key`.
- Preserve all existing config values.
- Do not print generated secrets.

User OK required:
- Antworte mit: OK CREATE LOCAL E2E CONFIG

After Auto-Fix:
- Re-run `USER-OK LIVE GATE` compliance check (Generator + Validator + Scope) and re-emit the compact READY block.
- If config/auth is valid, continue LIVE_RETEST.
- If another blocker appears, output LIVE TEST AUTOMATION BLOCKED with new exact reason and Copy-Handover.
```

Wenn der User `OK CREATE LOCAL E2E CONFIG` gibt, darf Skill 3 den lokalen Config-Fix ausfuehren und danach denselben Live-Retest ohne erneute manuelle Workflow-Neustart-Anforderung fortsetzen.

Wenn Auto-Fix nicht sicher ist, MUSS Skill 3 erklaeren warum, keine Datei schreiben und den Pflicht-Copy-Handover bei `LIVE TEST AUTOMATION BLOCKED` ausgeben.

Pflicht-Copy-Handover bei `LIVE TEST AUTOMATION BLOCKED`:

```text
@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]

Mode: LIVE_RETEST
Execution Model: SWE 1.6

Source TestRun: <source test run id>
Target TestRun: <target retest id>

TestSpec: <path>
TestPlan: <path>
Previous TestResult: <path>
Generated Runner: tests/e2e/generated/<test_run_id>.live.spec.js

Context:
- Previous Skill 3 Result: LIVE TEST AUTOMATION BLOCKED
- Block Reason: <konkreter Blockgrund>
- Required Fix Before Retest: <konkrete Aktion>
- Auto-Fix Available: JA | NEIN
- Auto-Fix Status: NOT_REQUESTED | USER_OK_REQUIRED | APPLIED | NOT_SAFE
- Product bug proven: NEIN

Pre-Retest Requirements:
- Backend Health erneut pruefen: http://localhost:8001/api/health
- Lokale Janus-Config pruefen, falls E2E-JWT/API-Key benoetigt werden
- Runner-Fidelity pruefen: echter lokaler E2E-JWT, X-Janus-Internal-Key, Chat-Fenster-A Selector, Antwort aus #chat-messages-A
- Keine Secrets in Chat oder TestResult schreiben

Arbeitsregel:
- Nutze TestSpec, TestPlan, Previous TestResult und Generated Runner als verbindliche Artefakte.
- Wenn der Blockgrund weiter besteht: erneut `LIVE TEST AUTOMATION BLOCKED` mit exaktem Grund und Copy-Handover ausgeben.
- Wenn der Blockgrund behoben ist: `USER-OK LIVE GATE` Compliance-Check erneut ausfuehren und Live-Retest fortsetzen.
```

---

### 3. USER-OK GATE

Im Auto-Pilot-Modus sind Phase 3A (Generator), Phase 3B (Validator) und Phase 3C (**Connectivity-Guard**) hier bereits abgeschlossen.

- Interne Compliance-Checkliste aus Section `USER-OK LIVE GATE` MUSS gruen sein, sonst statt Ready-Block einen `LIVE TEST AUTOMATION BLOCKED`-Block ausgeben.
- Bei gruener Checkliste den **einzigen** zugelassenen Ready-Block ausgeben: Scope-Tabelle + `Generator: SUCCESS | Validator: PASSED` + **`Connectivity-Guard: PASS`** + `Alle <N> Tests validiert. Bereit fuer LIVE_VISUAL Dauerlauf.` + `Antworte mit: OK START LIVE TEST`.
- Keine Scope-Teile stillschweigend entfernen.
- **STRENG VERBOTEN**: jede Nachfrage nach Janus-Status, Backend-Health, Visual Mode, Watch target oder sonstigen Default-Parametern **nach** bestandenem Guard. Es gibt genau ein Trigger-Kommando: `OK START LIVE TEST`.
- **Nach** Guard-PASS: Laufzeit-Ausfälle werden vom Runner klassifiziert (`BACKEND_HEALTH_FAIL` / `FRONTEND_NOT_READY` / **`INFRASTRUCTURE_OFFLINE`**).
- Auf explizites `OK START LIVE TEST` warten.
- Keine Live-Ausfuehrung vor OK.

Ausnahme: Wenn der User im laufenden Auftrag explizit `Watch target: ELECTRON_DESKTOP` gefordert hat, ist der Auto-Assume-Default deaktiviert; in diesem Fall MUSS Skill 3 zusaetzlich den `npm run start-dev`-Befehl ausgeben und auf `JANUS TEST INSTANCE RUNNING` warten, bevor `OK START LIVE TEST` akzeptiert wird.

---

### 4. RUN PLAYWRIGHT LIVE EXECUTION

Skill 3 Phase 3B ist ausschliesslich Orchestrierung des Runner Service.

Input:

```text
tests/e2e/generated/<test_run_id>.live.spec.js
```

Output:

```text
documentation/test-results/<test_run_id>/
playwright-report/
test-results/
debug_logs/
```

Der Runner Service darf nur eine zuvor generierte und validierte Spec ausfuehren.

**Dauerlauf-Regel (Auto-Pilot)**:

Nach `OK START LIVE TEST` fuehrt Skill 3 den Runner direkt aus, ueberwacht den Browser-Stream live und schreibt das finale TestResult **ohne weitere Stopps**. Verboten:

- zusaetzliche `JANUS TEST INSTANCE RUNNING`-Bestaetigung anfordern
- Zwischen-User-OKs zwischen TestCases einholen
- nach Runner-Exit erneut auf eine Freigabe warten, bevor das TestResult geschrieben wird
- nach TestResult auf eine Freigabe warten, bevor der Skill-4-Copy-Handover ausgegeben wird

Erlaubt sind ausschliesslich Stopps, wenn ein TestCase intern explizit als `MANUAL_GATE_REQUIRED` markiert ist — und auch dann nur fuer genau diesen einen Schritt; alle anderen TestCases laufen weiter.

**Runner-Default-Befehl (verbindlich)**:

```text
npx playwright test tests/e2e/generated/<test_run_id>.live.spec.js --headed --workers=1
```

**Harte Regel**: Skill 3 nutzt **immer** `--headed --workers=1`, es sei denn, der User hat im vorherigen Prompt explizit etwas anderes verlangt (z. B. `HEADLESS_EVIDENCE`, `--workers=N`, andere Reporter-Variante). Es gibt keine Default-Variante ohne `--headed`. Es gibt keine Frage an den User, ob `--headed` gewuenscht ist.

**Alternative Varianten** (nur wenn der User sie explizit im Auftrag genannt hat):

- HEADLESS_EVIDENCE-Mode (vom User explizit verlangt):

  ```text
  npx playwright test tests/e2e/generated/<test_run_id>.live.spec.js --workers=1
  ```

- Reporter-Variante mit npm-Skript (funktional aequivalent, wenn `package.json` ein `test:e2e`-Script enthaelt):

  ```text
  npm run test:e2e -- tests/e2e/generated/<test_run_id>.live.spec.js --headed --workers=1 --reporter=list
  ```

**Test-Instance-Start (nach Connectivity-Guard PASS)**:

Nach bestandenem Guard nimmt Skill 3 an, dass die im TestPlan genannten Endpunkte für den **Playwright-Lauf** erreichbar bleiben. Playwright kann Frontend/Backend im Zweifel via `playwright.config.js` (`webServer.reuseExistingServer: true`) starten. **Keine** weiteren Ad-hoc-`curl`/`fetch`-Proben gegen `localhost` zwischen Guard-PASS und `OK START LIVE TEST`. Skill 3 verlangt im Default-Browserpfad **keine** `JANUS TEST INSTANCE RUNNING`-Bestätigung.

Wenn Backend oder Frontend **während** des Laufs nicht erreichbar sind, schlaegt der Runner fehl. Der Skill MUSS in diesem Fall:

- den Failure Code `BACKEND_HEALTH_FAIL` (bei `/api/health`-Failure) bzw. `FRONTEND_NOT_READY` (Frontend-Load/webServer) bzw. **`INFRASTRUCTURE_OFFLINE`** (vom Runner bei `ERR_CONNECTION_REFUSED` auf `page.goto`/`baseUrl`, siehe Generator) in die Evidence schreiben,
- den betroffenen TestCase im TestResult als `FAIL` markieren,
- den Original-Fehlertext aus dem Runner-Output in `Console/Network Evidence` uebernehmen,
- die Triage `Infrastructure / Environment` an Skill 4 weiterreichen.

Ausnahmepfad — nur wenn der User explizit `Watch target: ELECTRON_DESKTOP` im laufenden Auftrag gefordert hat: Skill 3 gibt den Vorab-Befehl `npm run start-dev` aus und wartet auf `JANUS TEST INSTANCE RUNNING`, bevor `OK START LIVE TEST` akzeptiert wird. Dieser Pfad ist die einzige zulaessige Ausnahme zum Auto-Assume-Default.

**Wichtige Klarstellungen** (bleiben bestehen):

- Playwright oeffnet ein eigenes Chromium-Fenster — ein bereits offenes Electron-Janus-Fenster wird durch normale Playwright-Browser-Tests nicht automatisch ferngesteuert.
- Visuelle Verifikation erfolgt im sichtbaren Playwright-Browserfenster, sofern kein spezieller Electron-Automation-Runner existiert.
- Ein bereits offenes Electron-Janus-Fenster ist nur dann Beobachtungsziel, wenn der Runner explizit als Electron-Automation-Runner gebaut ist.

Waehrend der Ausfuehrung:

- Der User beobachtet die Interaktion im sichtbaren Playwright-Browserfenster (LIVE_VISUAL-Default).
- Der Skill fordert nur dann Eingriff an, wenn der Runner einen `MANUAL_GATE_REQUIRED`-Status meldet.
- Nach Runner-Exit faehrt Skill 3 sofort mit Phase 3C (Evidence Aggregation, Section 5) und anschliessend mit dem Skill-4-Copy-Handover fort — ohne zusaetzliche User-Bestaetigung.

---

### 4A. GENERATOR FAILURE TAXONOMY (HARD FACTS)

Der Test-Generator wirft im generierten Runner deterministische Fehlerklassen. Skill 3 MUSS jede dieser Klassen exakt erkennen, in der Evidence festhalten und im Triage-Handover an Skill 4 unveraendert nennen. Eigene Umetikettierung, generische Begriffe oder Prosa-Umformulierungen sind verboten.

Quelle der Wahrheit ist `tests/e2e/generator/generate-live-runner.mjs` (Failure-Taxonomy-Header). Die folgende Tabelle ist die verbindliche Mapping-Referenz:

| Failure Code | Quelle im Runner | Bedeutung | Suggested Triage Bucket fuer Skill 4 |
|--------------|------------------|-----------|--------------------------------------|
| `RUNNER_PRECLICK_EMPTY` | preClickDiag im generierten Spec | Textarea `#user-input-<win>` ist nach `pressSequentially` leer; Frontend-Submit-Handler wuerde am `!promptText`-Guard abbrechen. | Test Runner / Frontend Input Path |
| `RUNNER_PRECLICK_DOM_BROKEN` | preClickDiag im generierten Spec | `#send-button-<win>` ist nicht in `#chat-form-<win>` genested; native Form-Submission ist unmoeglich. | Frontend DOM Regression |
| `RUNNER_SELECTOR_FAILURE` | Failure-Taxonomy-Header | Playwright hat ein erwartetes DOM-Element nicht gefunden. | Test Runner / Selector Drift |
| `RUNNER_WAIT_FAILURE` | Failure-Taxonomy-Header | Wait-Condition (z. B. `toPass`) hat nicht aufgeloest. | Test Runner / Wait Strategy |
| `RUNNER_STREAM_TIMEOUT` (Variante A: `no POST /api/chat/stream`) | Runner-Catch nach `Promise.all` | Frontend hat keinen Stream-Request gesendet — Click-/sendMessage-Pfad gebrochen. | Frontend Send Path / SSE Trigger Issue |
| `RUNNER_STREAM_TIMEOUT` (Variante B: `bubble empty or only contains "..."`) | toPass-Polling | Stream-Request lief, aber Assistant-Bubble bleibt leer/`...`. Mögliche Ursachen: Detached-Bubble (Ghost), SSE-Renderer-Bug, Backend liefert keinen Content. | Frontend SSE Rendering / Ghost-Bubble |
| `FRONTEND_NOT_READY` | playwright.config.js webServer | Frontend-Dev-Server unter `http://localhost:5173/` ist nicht erreichbar. | Infrastructure / Environment |
| `BACKEND_HEALTH_FAIL` | playwright.config.js webServer | Backend `/api/health` antwortet nicht. | Infrastructure / Environment |
| `INFRASTRUCTURE_OFFLINE` | `beforeEach` / `page.goto(baseUrl)` | TCP-Verbindung abgelehnt (`ERR_CONNECTION_REFUSED` / `ECONNREFUSED` / `net::ERR_CONNECTION_REFUSED`) — Janus-Stack nicht erreichbar. **Notes/Evidence** MUSS Hinweis enthalten: Repository-Root **`npm run start-dev`**. | Infrastructure / Environment |
| `PROVIDER_TIMEOUT` | Runner-Catch + sichtbare Error-Bubble | LLM-Provider antwortet nicht oder Janus rendert sichtbare Error-Bubble. | Backend / Provider / Cost |
| `TOOL_ROUTING_FAILURE` | Evaluator | Erwartetes Tool/Intent wurde nicht aufgerufen. | Intent / Tool Routing |
| `ASSERTION_MISMATCH` | Evaluator | Antwort-Text matched die TestPlan-Expectations nicht. | Capability Behavior / Spec Drift |

Erweiterte Klassen (vom Skill als Hinweis zu erkennen, nicht vom Generator emittiert):

- `GHOST_BUBBLE_DETECTED` ist KEIN aktuell vom Generator geworfener Code. Er beschreibt das Symptom, dass die Assistant-Bubble waehrend des SSE-Streams aus dem DOM entfernt wurde (z. B. Race mit `loadChat()`/Sidebar-Restore). Im Frontend `frontend/js/chat.js` existiert dafuer ein Re-Anchor-Mechanismus, der diagnostische Logs `[SSE-REANCHOR]` ausgibt. Skill 3 MUSS pruefen:
  - Wenn `RUNNER_STREAM_TIMEOUT` (Variante B) auftritt UND in den `Console [SSE]`-Logs `[SSE-REANCHOR]` mit `reanchorCount > 0` erscheint, ist der Frontend-Re-Anchor aktiv geworden — der echte Bug liegt in der DOM-Wipe-Quelle, nicht im SSE-Renderer.
  - Wenn `RUNNER_STREAM_TIMEOUT` (Variante B) auftritt OHNE `[SSE-FIRST-TEXT]`-Log, hat das Frontend keine Text-Deltas empfangen — Backend-/Provider-/SSE-Stream-Routing zu Skill 4.
  - Wenn `RUNNER_STREAM_TIMEOUT` (Variante B) auftritt MIT `[SSE-FINAL] bubbleFinalLen > 15` ABER `DOM eval` keine `.message.assistant` zeigt, ist es eine `GHOST_BUBBLE_DETECTED`-Situation — Triage als `Frontend DOM Race / loadChat-Stream-Conflict`.

Evidence-Gate (verbindlich):

- Skill 3 darf einen Failure-Code NICHT umetikettieren. Wenn der Runner `RUNNER_STREAM_TIMEOUT` wirft, ist der TestCase-Status im TestResult `FAIL` mit Notes-Eintrag `Failure Code: RUNNER_STREAM_TIMEOUT (<Variante>)` und der vollstaendige Original-Error-Body in `Console/Network Evidence`.
- Wenn der Runner `PROVIDER_TIMEOUT` wirft, MUSS Skill 3 die `Stream Events`-Liste aus dem Error-Body in die Evidence uebernehmen, bevor `Backend/Provider/SSE-Stream` als Triage-Bucket vorgeschlagen wird.
- Wenn `[SSE-REANCHOR]`-Logs mit `reanchorCount > 0` vorliegen, MUSS Skill 3 dies als Hinweis auf eine DOM-Wipe-Quelle in den Handover an Skill 4 schreiben, auch wenn der TestCase letztlich `PASS` ist.

---

### 5. EVIDENCE AGGREGATION AND TESTRESULT PACKAGING

Vor fachlicher Auswertung MUSS Skill 3 die **Evidence-Aggregations-Phase** abschliessen.

Skill 3 **Evidence-Aggregation** ist Evidence Aggregation und TestResult Packaging.

Input:

```text
documentation/test-results/<test_run_id>/
playwright-report/
test-results/
debug_logs/
```

Output:

```text
documentation/test-results/<test_run_id>_results.md
```

Der Evidence Aggregator MUSS:

- Generator Command, Validator Command und Runner Command im TestResult dokumentieren.
- pro TestCase vorhandene Evidence-Dateien aus `documentation/test-results/<test_run_id>/` referenzieren.
- Network/API Evidence, Console Errors, UI State, Screenshots/Trace und Log-Auszüge verlinken oder als `N/A WITH REASON` markieren.
- technische Fehlerklassen aus dem Runner uebernehmen, ohne sie zu beschönigen.
- bei fehlender Pflicht-Evidence `BLOCKED` oder `FAIL` ausweisen, nicht PASS.

Der Evidence Aggregator DARF NICHT:

- neue TestCases erfinden.
- generierte Runner nachtraeglich patchen.
- fachliche PASS/FAIL-Ergebnisse ohne TestPlan-/Evaluator-Basis behaupten.

---

### 6. PROVIDER-/MODEL-MATRIX TESTS

Fuehre fuer jeden definierten Provider das smallest viable Model zuerst:

- **GPT smallest viable model**: `gpt-5.4-nano`
- **Gemini smallest viable model**: `gemini-3-flash-preview`
- **Default/Quality**: nur wenn im TestPlan definiert und noetig: `gpt-5.4-mini`, `gpt-5.4` oder `gemini-3.1-pro-preview`
- **GPT-5.5**: nur als Eskalation/Audit, nie als Regeltest

Wenn der TestPlan alte Textmodelle wie `gpt-4o-mini`, `gpt-4o`, `gemini-1.5-flash`, `Gemini Pro` oder `Pro model` enthaelt, darf kein Live-Test starten. Ausgabe:

```text
LIVE TEST BLOCKED: Provider-/Model-Matrix verwendet veraltete Textmodelle
```

Resultate pro Testfall dokumentieren als:
- PASS | PARTIAL | FAIL | BLOCKED | NOT RUN WITH REASON

---

### 7. USER EXPERIENCE TESTS

Pruefe laut TestPlan:

- Sichtbare UI-Reaktion
- Modale/Toasts/Anzeigen
- Fehlerdarstellung
- Ladezustaende
- Abbruchmoeglichkeiten

---

### 8. INTENT RECOGNITION TESTS

Pruefe laut TestPlan:

- Natuerlichsprachliche Prompts aus Intent Matrix
- Erwartetes Routing tritt ein?
- Falsche Intents werden abgelehnt oder umgeleitet?

---

### 9. SKILL/TOOL ROUTING TESTS

Pruefe laut TestPlan:

- Korrektes Skill-/Tool-Routing
- Fallback-Verhalten
- Fehler bei Routing-Fehlern

---

### 10. SECURITY SAFETY TESTS

Pruefe laut TestPlan:

- User-Daten bleiben sicher
- Destruktive Aktionen sind abgesichert
- Keine unerwarteten Seiteneffekte

---

### 11. PROMPT INJECTION RESISTANCE TESTS

Pruefe laut TestPlan:

- Prompt-Injection-Inhalte werden als Daten behandelt
- Keine Ausfuehrung fremder Instruktionen
- System-Prompt bleibt intakt

---

### 12. COST/TOKEN EFFICIENCY TESTS

Pruefe laut TestPlan:

- Token-Anzahl im erwarteten Bereich?
- Kosten im Budget?
- Einsparpotential messbar?

---

### 13. OBSERVABILITY/LOGGING TESTS

Pruefe laut TestPlan:

- Relevante Events werden geloggt?
- Keine sensiblen Daten in Logs?
- Telemetrie-Events korrekt?

---

### 14. CAPABILITY EXPLANATION TESTS

Pruefe laut TestPlan:

- Janus erklaert die Faehigkeit korrekt?
- Produktsprachlich, keine technischen Interna?
- Hilfe-Antwort entspricht Capability Explanation Target?

---

## 🌐 OUTPUT LANGUAGE

Alle user-facing Zusammenfassungen, Bewertungen, Titel, Zielbeschreibungen, Next Steps und Fehlermeldungen MUeSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Klassennamen, Funktionsnamen und Modellnamen bleiben unveraendert.

---

## 📤 OUTPUT ARTIFACT

Schreibe nach `documentation/test-results/<test_run_id>_results.md`:

```markdown
# TestResult: <TEST-RUN-ID>

## Metadata

- **TestRun-ID**: <TEST-RUN-ID>
- **Datum**: YYYY-MM-DD
- **TestSpec**: <Pfad>
- **TestPlan**: <Pfad>
- **Generator**: tests/e2e/generator/generate-live-runner.mjs
- **Validator**: tests/e2e/generator/validate-runner.mjs
- **Strategy Registry**: tests/e2e/generator/strategy-registry.json
- **Playwright Runner**: tests/e2e/generated/<test_run_id>.live.spec.js
- **Playwright Report/Trace**: <Pfad oder N/A>
- **Frontend Log**: <Pfad oder N/A>
- **Backend Log**: <Pfad oder N/A>

## Zusammenfassung

- Gesamtergebnis: <PASS | PARTIAL | FAIL | BLOCKED>
- Ausgefuehrte Testfaelle: <Anzahl>
- Blockierte Testfaelle: <Anzahl>
- Nicht ausgefuehrte Testfaelle: <Anzahl>

## Ergebnisse pro Testfall

| TestCase-ID | Beschreibung | Ergebnis | Evidence | Notizen |
|-------------|--------------|----------|----------|---------|
| TC-001 | ... | PASS | ... | ... |

## Automation Evidence

- Generator command: node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/<test_run_id>_plan.json --out tests/e2e/generated/<test_run_id>.live.spec.js
- Validator command: node tests/e2e/generator/validate-runner.mjs --plan documentation/test-runs/<test_run_id>_plan.json --runner tests/e2e/generated/<test_run_id>.live.spec.js
- Validator result: PASSED | FAILED | NOT RUN WITH REASON
- Runner: tests/e2e/generated/<test_run_id>.live.spec.js
- Command: npm run test:e2e -- tests/e2e/generated/<test_run_id>.live.spec.js --workers=1 --reporter=list
- Playwright exit code: <0|non-zero|N/A>
- Manual gates: <Anzahl und IDs>
- Screenshots/Trace: <Pfade oder N/A>
- Frontend log excerpt/hash: <Pfad/hash oder N/A>
- Backend log excerpt/hash: <Pfad/hash oder N/A>

## Provider-/Model-Matrix Ergebnisse

| Provider | Modell | Ergebnis | Evidence |
|----------|--------|----------|----------|
| GPT | <smallest> | PASS | ... |
| Gemini | <smallest> | PASS | ... |

## Security Gate Ergebnisse

| Gate | Ergebnis | Evidence |
|------|----------|----------|
| Userdaten sicher | JA | ... |
| Destruktive Aktionen isoliert | JA | ... |
| Prompt-Injection-Risiko | NONE | ... |

## Findings

- <Liste oder "Keine">

## Nebenbefunde ausserhalb TestScope

- <Liste oder "Keine">

## Naechster Schritt

- TEST SKILL 4 – FINDING TRIAGE AND ROUTING
```

---

## 📋 COPY-PASTE HANDOVER FUER TEST SKILL 4 (PFLICHT)

Am Ende MUSS ein einzelner grauer Copy-Block ausgegeben werden.

NO-ORPHAN-OUTPUT RULE:

TEST SKILL 3 darf den User niemals ohne eindeutige naechste Aktion zuruecklassen.

Jeder finale Output MUSS genau einen der folgenden Abschluss-Typen enthalten:

- `TestResult` plus Copy-Handover zu `@[/TEST SKILL 4 – FINDING TRIAGE AND ROUTING]`.
- `LIVE TEST AUTOMATION BLOCKED` plus konkrete User-Aktion und Copy-Handover zu `@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]` mit `Mode: LIVE_RETEST`.
- `MODEL SWITCH REQUIRED` plus kompakten Copy-Handover fuer GPT-5.5-Eskalation.

Verboten sind finale Abschluesse wie:

- `Test abgeschlossen`
- `Bitte erneut versuchen`
- `Backend pruefen`
- `Retest empfohlen`
- `Test konnte nicht vollstaendig ausgefuehrt werden`

Wenn kein vollstaendiges TestResult geschrieben wurde, darf TEST SKILL 3 nicht zu TEST SKILL 4 routen, sondern muss `LIVE TEST AUTOMATION BLOCKED` oder ein klar als `BLOCKED` markiertes TestResult mit Handover ausgeben.

```text
@[/TEST SKILL 4 – FINDING TRIAGE AND ROUTING]

Mode: FINDING_TRIAGE
Execution Model: SWE 1.6
TestSpec: <source test spec file>
TestPlan: <source test plan file>
TestResult: documentation/test-results/<test_run_id>_results.md
Target TestRun: <TEST-RUN-ID>

Context:
- Capability: <Name>
- TEST SKILL 3 Ergebnis: <Zusammenfassung>

Automation Provenance:
- Generator: tests/e2e/generator/generate-live-runner.mjs
- Generator Command: node tests/e2e/generator/generate-live-runner.mjs --plan <plan_path> --out <spec_path>
- Validator: tests/e2e/generator/validate-runner.mjs
- Validator Command: node tests/e2e/generator/validate-runner.mjs --plan <plan_path> --runner <spec_path>
- Validator Result: PASSED | FAILED | NOT_RUN
- Runner Command: npx playwright test <spec_path> --headed --workers=1
- Playwright Exit Code: <0 | non-zero | N/A>

Detected Failure Codes:
- <TestCase-ID>: <Failure Code aus Generator-Taxonomy> | NONE
- <TestCase-ID>: <Failure Code aus Generator-Taxonomy> | NONE
- Erlaubte Codes: RUNNER_PRECLICK_EMPTY | RUNNER_PRECLICK_DOM_BROKEN | RUNNER_SELECTOR_FAILURE | RUNNER_WAIT_FAILURE | RUNNER_STREAM_TIMEOUT | FRONTEND_NOT_READY | BACKEND_HEALTH_FAIL | INFRASTRUCTURE_OFFLINE | PROVIDER_TIMEOUT | TOOL_ROUTING_FAILURE | ASSERTION_MISMATCH | NONE
- Hinweis-Codes (nicht vom Generator emittiert, aus Console-Evidence abgeleitet): GHOST_BUBBLE_DETECTED

Suggested Triage Buckets (laut Generator Failure Taxonomy in Skill 3 Section 4A):
- <TestCase-ID>: <Triage Bucket>
- Erlaubte Buckets: Test Runner / Frontend Input Path | Frontend DOM Regression | Test Runner / Selector Drift | Test Runner / Wait Strategy | Frontend Send Path / SSE Trigger Issue | Frontend SSE Rendering / Ghost-Bubble | Frontend DOM Race / loadChat-Stream-Conflict | Infrastructure / Environment | Backend / Provider / Cost | Intent / Tool Routing | Capability Behavior / Spec Drift

SSE Diagnostics Hints (falls relevant):
- [SSE-REANCHOR] reanchorCount > 0 observed: JA | NEIN
- [SSE-FIRST-TEXT] observed: JA | NEIN
- POST /api/chat/stream observed: JA | NEIN
- Final bubbleFinalLen > 15 but DOM eval shows no .message.assistant: JA | NEIN

Arbeitsregel:
- Nutze TestSpec, TestPlan und TestResult als verbindliche Artefakte.
- Ignoriere widerspruechliche oder zusaetzliche Chat-Kontexte.
- Erzeuge keine Implementation.
- Uebernimm die Failure Codes exakt; etikettiere sie nicht um.
- Bewerte alle Findings und entscheide: kein Problem, Sofortfix, Backlog, Security Blocker, TestSpec-Anpassung, Retest.
- Alle echten Bugs/Security/UX/Cost/Routing-Findings muessen als Backlog-Items erfasst werden, wenn nicht eindeutig irrelevant.
- Backlog-Items muessen dashboard-kompatible Felder enthalten.
- Nach Backlog-Aenderung: Hinweis auf Dashboard-Snapshot-Sync via npm run sync:backlog in janus-dashboard.
- Preserve security/privacy/prompt-injection gates.
- Produce no code changes unless explicitly allowed.

Naechster erwarteter Output:
- FINDING TRIAGE COMPLETE
- Liste erzeugter Backlog Items
- Entscheidung: Handover zu TEST SKILL 5, BACKLOG SKILL 2/3, oder RETEST REQUIRED
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

@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]

Mode: ESCALATION_REVIEW
Execution Model: GPT-5.5

Binding Artifacts:
- TestSpec: <path>
- TestPlan: <path>
- TestResult Draft: <path or compact excerpt>
- Precheck Result: <compact excerpt>

Escalation Question:
- Wie ist die widerspruechliche oder sicherheitskritische Live-Test-Evidence zu bewerten?

Relevant Evidence:
- <nur relevante TestCase-IDs, Provider-Abweichungen, Security-/Prompt-Injection-Evidence, keine vollstaendigen Logs>

Hard Rules:
- Use only listed artifacts and evidence as source of truth.
- Ignore previous chat history.
- Do not add product requirements.
- Do not implement code.
- Do not request full logs unless absolutely required.
- Decide only the escalation question.

Expected Output:
- Decision: PASS_TO_CONTINUE | BLOCKED | REQUIRED_RETEST | REQUIRED_FIX_ROUTING
- Reason:
- Required next skill:
- Recommended model:
- Copy handover back to SWE 1.6 if continuation is possible.

END COPY
```

---

## 🚫 RESTRICTIONS

Skill 3 ist strikt **Orchestrator der drei versionierten Test-Services** (Generator, Validator, Runner). Er ist KEIN Playwright-Code-Autor.

KEINE Produktimplementation
KEINE Architekturentscheidungen
KEINE Scope-Erweiterung
KEINE Aenderung an Produktdateien ausser explizit beauftragt

VERBOTEN: freie Playwright-Code-Generierung im Skill-Prompt
VERBOTEN: Reproduktion oder Inline-Kopie des `Promise.all`-Sende-Patterns, `pressSequentially`-Logik oder SSE-Rendering-Checks im Skill-Prompt — diese Logik gehoert ausschliesslich in den Generator unter `tests/e2e/generator/`
VERBOTEN: manuelle Patches an `tests/e2e/generated/*.live.spec.js`
VERBOTEN: Anpassung der drei Pflichtbefehle durch eigene Flags, Pfade oder Optionen — die Befehlssignaturen in Section 2 sind verbindliche Fakten
VERBOTEN: eigene Umetikettierung der Failure-Codes aus Section 4A — Skill 3 reicht die Original-Codes 1:1 an Skill 4 weiter
VERBOTEN: Inline-Strategy-Definitionen im Spec-File — neue Strategien gehoeren in `tests/e2e/generator/strategy-registry.json` und werden anschliessend ueber Generator/Validator validiert

ERLAUBT: Ausfuehrung des Generator Service exakt mit `node tests/e2e/generator/generate-live-runner.mjs --plan <plan_path> --out <spec_path>`
ERLAUBT: Ausfuehrung des Validator Service exakt mit `node tests/e2e/generator/validate-runner.mjs --plan <plan_path> --runner <spec_path>`
ERLAUBT: Ausfuehrung des Runner Service mit `npx playwright test <spec_path> --headed --workers=1` (oder ohne `--headed` fuer `HEADLESS_EVIDENCE`-Mode) nach explizitem User-OK
ERLAUBT: Schreiben von TestResult-, Evidence- und Log-Artefakten unter `documentation/test-results/` und `debug_logs/`
ERLAUBT: Korrektur von TestPlan oder `strategy-registry.json` mit anschliessender Neu-Generierung — niemals direkte Patches am generierten Spec

---

## 🧠 ERROR HANDLING

Wenn Testfaelle nicht durchfuehrbar:

```text
LIVE TEST PARTIAL

Blocked Cases:
- <konkrete Begruendung>

Action:
→ TEST SKILL 4 mit verfuegbaren Ergebnissen
```

---

## 🧠 OUTPUT GUARANTEE

Output ist immer:

deterministisch
test-automation-and-documentation-only
executing only after explicit `OK START LIVE TEST`
evidence-collecting
