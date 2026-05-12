---
description: SWE 1.6 Test Pipeline Phase 4 – Finding Triage and Routing. Bewertet alle Findings aus dem TestResult, entscheidet ueber Sofortfix, Backlog oder Blocker, und routet Ergebnisse ins Dashboard/Backlog. Keine Code-Implementation, ausser eindeutig erlaubte LOW-risk Markdown/Config-Fixes.
---

# TEST SKILL 4 – FINDING TRIAGE AND ROUTING

## 🎯 PURPOSE

Dieser Skill bewertet alle Findings aus dem TestResult und entscheidet ueber den naechsten Schritt.

Er entscheidet:
→ kein Problem | Sofortfix moeglich | Backlog Item noetig | Security Blocker | TestSpec-Anpassung noetig | Retest noetig

KEINE CODE-IMPLEMENTATION, ausser eindeutig erlaubte LOW-risk Markdown-/Config-Fixes.
Sicherer Standard: Findings ins Backlog.

---

## 🤖 DEFAULT MODEL

SWE 1.6

Ausnahme:
- GPT-5.5 nur bei HIGH/CRITICAL Security-Finding oder unklarem Scope

---

## 📥 INPUT

- TestSpec aus `documentation/TEST_SPEC/`
- TestPlan aus `documentation/test-runs/`
- TestResult aus `documentation/test-results/`

---

## 📌 AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer TestSpec, TestPlan und TestResult nennt, sind diese Artefakte automatisch die verbindlichen Quellen.

Der Skill MUSS dann:

- die genannte TestSpec-Datei vollstaendig lesen
- die genannte TestPlan-Datei vollstaendig lesen
- die genannte TestResult-Datei vollstaendig lesen
- die Findings ausschliesslich gegen diese Artefakte bewerten
- Chatverlauf, fruehere Diskussionen und zusaetzliche muendliche Nebeninformationen ignorieren, sofern sie den Artefakten widersprechen oder ueber sie hinausgehen
- keine Requirements, Produktentscheidungen oder Architekturentscheidungen aus dem Chatkontext ergaenzen
- stoppen, wenn Artefakte widerspruechlich sind

Minimaler gueltiger User-Aufruf:

```text
/TEST SKILL 4 – FINDING TRIAGE AND ROUTING mit folgenden Artefakten:
TestSpec: documentation/TEST_SPEC/<TESTSPEC>.md
TestPlan: documentation/test-runs/<TEST_RUN_ID>_plan.md
TestResult: documentation/test-results/<TEST_RUN_ID>_results.md
```

Wenn Artefakte unlesbar oder widerspruechlich:

```text
FINDING TRIAGE ARTIFACTS INVALID

Issue:
- <konkretes Problem>

Action:
→ korrekte Artefakte angeben oder TEST SKILL 3 erneut ausfuehren
```

---

## ⚙️ EXECUTION FLOW

---

### 1. LOAD ARTIFACTS

- TestSpec laden
- TestPlan laden
- TestResult laden
- Alle Findings extrahieren (inkl. Nebenbefunde ausserhalb TestScope)

---

### 2. FINDING TRIAGE

Fuer jedes Finding entscheide:

- **kein Problem**: Erwartetes Verhalten, kein Handlungsbedarf
- **Sofortfix moeglich**: Eindeutiger kleiner LOW-risk Markdown-/Config-/Dokumentations-Fix
- **Backlog Item noetig**: Bug, Verbesserung, UX-Problem, Cost-Problem, Routing-Problem
- **Security Blocker**: Security-, Privacy- oder Prompt-Injection-Problem
- **TestSpec-Anpassung noetig**: TestSpec war unzutreffend, Scope unklar
- **Retest noetig**: Test nicht deterministisch durchfuehrbar, Daten fehlten

Wenn `RETEST REQUIRED` entschieden wird, MUSS der Skill:

- klar sagen, warum kein Produktbug/Backlog-Item erzeugt wurde oder welches Finding vor dem Retest behoben werden muss
- den direkten naechsten Schritt nennen
- am Ende einen einzelnen grauen Copy-Handover zum passenden naechsten Skill ausgeben
- bei Test-Infrastruktur-, Backend-Timeout-, Runner-Selector-, Auth-, API-Key-, Healthcheck- oder fehlender-Evidence-Problemen standardmaessig zu `TEST SKILL 3 – LIVE JANUS TEST EXECUTION` mit `Mode: LIVE_RETEST` routen
- niemals ohne Copy-Handover mit nur einer Prosazusammenfassung enden

---

### 3. BACKLOG INTEGRATION (HARD RULE)

Alle echten Bugs, Verbesserungen, Security-/Privacy-Probleme, Prompt-Injection-Probleme, Cost-Probleme, Intent-/Routing-Probleme und auch Nebenbefunde ausserhalb des direkten TestScopes MUeSSEN als Backlog-Items in `documentation/backlog/BACKLOG.md` erfasst werden, wenn sie nicht eindeutig irrelevant sind.

#### 3.1 ID-DETERMINATION RULE (PFLICHT)

**VOR der Erstellung eines neuen Items MUSS die KI die gesamte Datei `documentation/backlog/BACKLOG.md` lesen und die aktuell hoechste `BACKLOG-XXX`-Nummer identifizieren. Die neue ID MUSS zwingend `[Hoechste ID] + 1` lauten. Es ist STRENG VERBOTEN, IDs zu raten oder ohne vorherigen File-Scan zu vergeben.**

Konkretes Vorgehen (verbindlich, in dieser Reihenfolge):

1. Vollstaendiges Einlesen von `documentation/backlog/BACKLOG.md` mit dem Read-Tool (kein partieller Read, keine Annahme aus dem Kontext, keine Schaetzung).
2. Alle Vorkommen des Musters `^### BACKLOG-(\d{3}) – ` extrahieren (Grep mit `^### BACKLOG-\d+`).
3. Die numerisch hoechste Nummer ueber **alle** Sektionen (`READY`, `IN PROGRESS`, `DONE`, `NEEDS INFO`, jeder anderen) identifizieren — nicht nur in einer Status-Sektion suchen.
4. Naechste ID = `max(gefundene IDs) + 1`, formatiert als `BACKLOG-NNN` mit dreistelliger Zahl (z. B. `BACKLOG-026`).
5. **Kollisions-Self-Check**: Vor dem Schreiben MUSS verifiziert werden, dass die berechnete ID im File noch NICHT existiert. Bei Kollision -> Schritt 3 wiederholen.
6. Erst nach erfolgreichem Self-Check das neue Item mit der ermittelten ID einfuegen.

**STRENG VERBOTEN**:

- IDs aus dem Gedaechtnis, aus Chat-Kontext oder aus aelteren Snapshots vergeben.
- Auf `janus-dashboard/data/backlog.snapshot.json` statt auf `BACKLOG.md` als ID-Quelle stuetzen.
- "Sicherheitsabstand" lassen oder IDs ueberspringen (z. B. `BACKLOG-100` waehlen, weil "es noch frei sein duerfte").
- Items mit identischer ID-Header ablegen — bei Verdacht einer Doppelvergabe MUSS der Konflikt sofort durch Umnummerierung des juengeren Eintrags geloest werden.

#### 3.2 BACKLOG-ITEM TEMPLATE

Backlog Items MUeSSEN dashboard-kompatible Felder enthalten. Wichtig: Die Felder muessen exakt im parser-kompatiblen Format `- **Feldname:** Wert` geschrieben werden.

```text
### BACKLOG-XXX – <Titel>

- **Typ:** Bug | Change | Enhancement | Security | Privacy | Prompt-Injection | Cost | UX | Sonstiges
- **Status:** READY
- **Quelle:** TestRun
- **TestRun:** TEST-RUN-YYYY-MM-DD-NNN
- **Kurzbeschreibung:** <eine Zeile>
- **Erwartetes Verhalten:** <aus TestSpec/TestPlan>
- **Tatsächliches Verhalten:** <aus TestResult>
- **Reproduktion / Kontext:** <konkrete Schritte>
- **Betroffener Bereich:** <Modul / Skill / Tool>
- **Nachweise:** <Log-Pfade, Screenshots, Ergebnis-IDs>
- **Wichtigkeit:** LOW | MEDIUM | HIGH | CRITICAL
- **Umsetzungsrisiko:** LOW | MEDIUM | HIGH
- **Aufwand:** S | M | L | XL
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW | NEXT | LATER | BACKLOG
- **Entry Point:** SPEC_PIPELINE_START | TASK_BREAKDOWN | PRE_IMPLEMENTATION_VERIFICATION | EXECUTION_READY | ROUTING_BLOCKED
- **Routing reason:** <Begruendung inklusive GPT-5.5-Audit-Hinweis bei HIGH/CRITICAL, falls erforderlich>
- **Routing confidence:** HIGH | MEDIUM | LOW
- **Handoff:** <path> | none
- **Recommended next skill:** SKILL 1 | SKILL 2 | SKILL 3 | SKILL 4 | none
- **Handoff created:** YYYY-MM-DD | none
```

---

### 4. ROUTING-REGELN

- **kleine klare lokale Bugs**: `PRE_IMPLEMENTATION_VERIFICATION` / `SKILL 3`
- **groessere Feature-/UX-/Safety-Fragen**: `SPEC_PIPELINE_START` / `SKILL 1`
- **bereits klare atomare Tasks**: `SKILL 3`
- **high risk/security**: eher `SPEC_PIPELINE_START` oder GPT-5.5 Audit-Hinweis
- **keine DONE Items reopen**: neue Follow-up-Items erzeugen, Original referenzieren

---

### 5. DASHBOARD-SYNC-HINWEIS

Nach **jeder** Backlog-Aenderung MUSS der Skill den folgenden Sync-Hinweis ausgeben. Sync-pflichtig sind insbesondere:

- Neues Backlog-Item angelegt
- Bestehendes Item editiert (Status-, Routing-, Empfehlungs-, Wichtigkeits-, Handoff-Felder)
- **ID-Aenderung / Umnummerierung** eines Items (z. B. wegen Kollision-Fix gemaess Section 3.1)
- Loeschung eines Items
- Konsolidierung mehrerer Items
- Snapshot-Drift vermutet (Snapshot in `janus-dashboard/data/backlog.snapshot.json` weicht von `BACKLOG.md` ab)

```text
Dashboard-Sync Hinweis:
→ Fuehre im Ordner janus-dashboard aus:
   npm run sync:backlog
→ Dadurch wird der Dashboard-Snapshot aktualisiert.
→ Bei ID-Umnummerierungen oder Kollisionsfixes ist der Sync ZWINGEND, sonst zeigt das Dashboard veraltete IDs.
→ Sonst: empfohlen, aber nicht erzwungen, falls User-Freigabe noetig ist.
```

---

## 🌐 OUTPUT LANGUAGE

Alle user-facing Zusammenfassungen, Bewertungen, Titel, Zielbeschreibungen, Next Steps und Fehlermeldungen MUeSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Klassennamen, Funktionsnamen und Modellnamen bleiben unveraendert.

---

## 📤 OUTPUT FORMAT

```text
FINDING TRIAGE COMPLETE

TestRun: <TEST-RUN-ID>

Findings Uebersicht:
- Kein Problem: <Anzahl>
- Sofortfix: <Anzahl>
- Backlog Item: <Anzahl>
- Security Blocker: <Anzahl>
- TestSpec-Anpassung: <Anzahl>
- Retest noetig: <Anzahl>

Erzeugte Backlog Items:
- BACKLOG-XXX: <Titel> – <Routing>
- BACKLOG-YYY: <Titel> – <Routing>

Sofortfixes (falls keine: "Keine"):
- <Fix-Beschreibung und Datei>

Blocker (falls keine: "Keine"):
- <Blocker-Beschreibung>

Dashboard-Sync:
- Empfohlen: npm run sync:backlog in janus-dashboard

Naechster Schritt:
- <TEST SKILL 3 Retest | TEST SKILL 5 Audit | BACKLOG SKILL 2/3 | BLOCKED>
- Grund: <kurze konkrete Begruendung>

Copy-Handover:
- Wird unten als einzelner grauer Block ausgegeben: JA
```

Output ist UNGUELTIG, wenn nach `FINDING TRIAGE COMPLETE` kein einzelner Copy-Block mit `@[/... ]` fuer den naechsten Skill folgt.

Wenn der Skill `RETEST REQUIRED` entscheidet, ist folgender Abschluss verboten:

```text
TEST SKILL 4 abgeschlossen. Entscheidung: RETEST REQUIRED ...
```

Stattdessen MUSS direkt danach ein grauer Copy-Block nach Variante C folgen.

---

## 📋 COPY-PASTE HANDOVER (PFLICHT)

Am Ende MUSS immer ein einzelner grauer Copy-Block ausgegeben werden, wenn der Prozess fortgesetzt werden kann.

Der Copy-Block MUSS den direkten naechsten Schritt enthalten und darf nicht durch reine Prosa ersetzt werden.

Self-Check vor finaler Antwort:

- Enthaelt die Antwort `FINDING TRIAGE COMPLETE`? Dann MUSS sie auch genau einen Copy-Block mit `@[/... ]` enthalten.
- Entscheidung `RETEST REQUIRED`? Dann MUSS der Copy-Block `@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]` und `Mode: LIVE_RETEST` enthalten.
- Kein vollstaendiges valides TestResult? Dann darf kein Handover zu TEST SKILL 5 ausgegeben werden.
- Fehlt der Copy-Block, MUSS der Skill die Antwort nicht abschliessen, sondern den Copy-Block ergaenzen.

Routing:

- Wenn `RETEST REQUIRED`: Variante C verwenden.
- Wenn neue/unklare/high-risk Backlog-Findings offen sind: Variante A verwenden.
- Wenn keine blockierenden Findings und ein valides vollstaendiges TestResult existiert: Variante B verwenden.
- Wenn das TestResult wegen Test-Infrastruktur nicht vollstaendig gemessen wurde: NICHT Variante B verwenden, sondern Variante C.
- Wenn derselbe Timeout nach Config-Fix und Backend-Neustart weiterhin oder intermittierend auftritt, darf Skill 4 nicht endlos nur `RETEST REQUIRED` ausgeben. Dann MUSS Skill 4 entweder ein Backlog-Item fuer Runtime-/Testinfrastruktur-Stabilitaet erzeugen oder explizit begruenden, welche konkrete Evidence noch vor Backlog-Erstellung fehlt.

### Variante A: Blockierende Findings offen

Wenn blockierende Findings offen sind, darf TEST SKILL 4 genau einen der folgenden Copy-Bloecke ausgeben:

- `BACKLOG SKILL 2`, wenn neue/unklare/high-risk Findings priorisiert oder bewertet werden muessen.
- `BACKLOG SKILL 3`, wenn die Findings bereits READY und ausreichend bewertet sind und nur Dashboard-Handoffs vorbereitet werden sollen.

Es duerfen niemals beide Bloecke gleichzeitig ausgegeben werden.

```text
@[/BACKLOG SKILL 2 – REVIEW PRIORISIERUNG]

Mode: DELTA
Execution Model: GPT-5.5

Context:
- Quelle: TestRun <TEST-RUN-ID>
- Neue Backlog Items aus TestFindings: <Liste>
- Security Blocker vorhanden: JA | NEIN

Arbeitsregel:
- Bewerte neue TestRun-Findings zusammen mit bestehendem Backlog.
- Priorisiere Security-/Privacy-/Prompt-Injection-Findings hoch.
- Empfehle naechste Backlog-Items fuer Execution Handoff.
```

Oder fuer direkten Dashboard-Prep:

```text
@[/BACKLOG SKILL 3 – EXECUTION HANDOFF]

Mode: DASHBOARD_PREP
Execution Model: SWE 1.6

Context:
- Quelle: TestRun <TEST-RUN-ID>
- Neue Backlog Items erzeugt: <Liste>
- Routing-Ergaenzung fuer TestFindings erforderlich.

Arbeitsregel:
- Fuelle fehlende Routing-Metadaten fuer neue Backlog-Items.
- Erstelle/reuse Handoff-Artefakte.
- Bewege NICHTS nach IN PROGRESS.
- Sync Dashboard-Snapshot via npm run sync:backlog.
```

### Variante B: Keine blockierenden Findings

```text
@[/TEST SKILL 5 – DIAMOND RETEST AUDIT]

Mode: RETEST_AUDIT
Execution Model: SWE 1.6
TestSpec: <source test spec file>
TestPlan: <source test plan file>
TestResult: documentation/test-results/<test_run_id>_results.md
Target TestRun: <TEST-RUN-ID>

Context:
- Capability: <Name>
- TEST SKILL 4 Ergebnis: FINDING TRIAGE COMPLETE
- Blockierende Findings: keine
- Offene Backlog Items: <Liste oder keine>

Arbeitsregel:
- Nutze TestSpec, TestPlan und TestResult als verbindliche Artefakte.
- Ignoriere widerspruechliche oder zusaetzliche Chat-Kontexte.
- Erzeuge keine Implementation.
- Berechne Diamond Confidence Score und Production Confidence.
- Kein PASS ohne kompletten Retest nach relevanten Fixes.
- Preserve security/privacy/prompt-injection gates.
- Preserve provider/model matrix.

Naechster erwarteter Output:
- Diamond Confidence Score: x/10
- Production Confidence: y%
- Final Result: PASS | PASS WITH FOLLOW-UP | RETEST REQUIRED | BLOCKED
- Copy-Handover zu SKILL 7 – DOKUMENTATIONSUPDATE (bei PASS)
```

### Variante C: Retest erforderlich

Diese Variante ist PFLICHT bei `RETEST REQUIRED`. Sie muss auch dann ausgegeben werden, wenn keine Backlog Items erzeugt wurden und das Finding als Test-Infrastruktur bewertet wurde.

```text
@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]

Mode: LIVE_RETEST
Execution Model: SWE 1.6
TestSpec: <source test spec file>
TestPlan: <source test plan file>
Previous TestResult: <source test result file>
Source TestRun: <TEST-RUN-ID>
Target TestRun: <TEST-RUN-ID>-RETEST-001

Context:
- Capability: <Name>
- TEST SKILL 4 Ergebnis: RETEST REQUIRED
- Retest Reason: <konkreter Grund, z. B. BACKEND_TIMEOUT_ISSUE | TEST_RUNNER_SELECTOR_BUG | fehlende Evidence>
- Produktbug belegt: JA | NEIN
- Backlog Items erzeugt: <Liste oder keine>
- Nicht ausgefuehrte TestCases: <Liste oder Anzahl>

Pre-Retest Requirements:
- Backend Health pruefen: http://localhost:8001/api/health
- Backend-Logs auf Startup-/Runtime-Fehler pruefen
- API-Key/Auth-Konfiguration verifizieren, falls Browser-E2E genutzt wird
- Runner-Fidelity pruefen: echter lokaler E2E-JWT, `X-Janus-Internal-Key`, Chat-Fenster-A Selector, Antwort aus `#chat-messages-A`
- Bei Timeout: Network/API Evidence und Backend-Log-Auszug fuer den betroffenen Chat-Request erfassen

Arbeitsregel:
- Nutze TestSpec, TestPlan und Previous TestResult als verbindliche Artefakte.
- Ignoriere widerspruechliche oder zusaetzliche Chat-Kontexte.
- Fuehre den kompletten TestRun erneut durch, nicht nur den fehlgeschlagenen TestCase.
- Wenn Pre-Retest Requirements nicht erfuellt sind: `LIVE TEST AUTOMATION BLOCKED` mit exaktem Grund ausgeben.
- Wenn der Retest laeuft: Ergebnisse mit Prompt, Antworttext, Status, Notes, relevanter Network/API Evidence und Logs nach `documentation/test-results/` schreiben.
- Kein PASS ohne echte Antwort aus dem realen Janus-Live-Pfad.

Naechster erwarteter Output:
- DIAMOND LIVE PREFLIGHT
- LIVE JANUS AUTOMATION READY oder LIVE TEST AUTOMATION BLOCKED
- aktualisiertes TestResult
```

Pflicht-Spezialfall `BACKEND_TIMEOUT_ISSUE`:

Wenn TEST SKILL 3 `FAIL (Backend Timeout Issue)` oder ein Finding `BACKEND_TIMEOUT_ISSUE` meldet und keine eindeutige Backend-/Network-Evidence fuer einen Produktbug vorliegt, MUSS Skill 4 `RETEST REQUIRED` ausgeben und Variante C mit folgenden Zusatzpunkten verwenden:

- `Retest Reason: BACKEND_TIMEOUT_ISSUE`
- `Produktbug belegt: NEIN`
- `Backlog Items erzeugt: keine`
- `Pre-Retest Requirements` enthalten Backend Health, Backend Logs, API-Key/Auth und Network/API Evidence
- Keine Route zu TEST SKILL 5, solange kein vollstaendiges valides TestResult existiert
- Der letzte Output-Teil MUSS ein grauer Copy-Block fuer `@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]` sein.
- Wenn `Auto-Fix Applied: LOCAL_E2E_CONFIG_CREATE_OR_REPAIR (SUCCESS)` genannt wird und Timeout weiter besteht, MUSS `Pre-Retest Requirements` zusaetzlich Backend-Neustart, API-Key-Konsistenz zwischen Config und laufendem Backend, Backend-Logs und Network/API Evidence fuer den Chat-Request enthalten.

Pflicht-Spezialfall `INTERMITTENT_BACKEND_TIMEOUT`:

Wenn nach erfolgreichem Config-Fix und Backend-Neustart mindestens ein TestCase PASS und ein spaeterer TestCase wegen Backend-/Chat-Timeout FAIL ist, MUSS Skill 4 das Finding als wiederholtes Stabilitaetsfinding behandeln.

Skill 4 darf es nur dann als reine Test-Infrastruktur ohne Backlog abschliessen, wenn alle folgenden Evidence-Punkte im TestResult vorhanden sind:

- Backend-Log zeigt eindeutig externes/temporäres Testumgebungsproblem und keinen Janus-Codepfad-Fehler.
- Network/API Evidence zeigt, dass der Chat-Request nicht valide beim Backend ankam oder eindeutig durch lokale Testumgebung blockiert wurde.
- Es gibt eine konkrete, einmalige, behobene Ursache, nach der ein erneuter Retest sinnvoll ist.

Wenn diese Evidence fehlt oder die Ursache nur vermutet wird, MUSS Skill 4 ein Backlog-Item erzeugen:

```text
### BACKLOG-XXX – Intermittierender Backend Timeout bei Janus Live-Chat Retest

- **Typ:** Bug
- **Status:** READY
- **Quelle:** TestRun
- **TestRun:** <TEST-RUN-ID>
- **Kurzbeschreibung:** Janus beantwortet aufeinanderfolgende Live-Chat-Anfragen im automatisierten Retest nicht zuverlässig; ein TestCase PASS, ein Folge-TestCase Timeout.
- **Erwartetes Verhalten:** Janus verarbeitet aufeinanderfolgende Chat-/Intent-Anfragen stabil oder liefert einen kontrollierten Timeout-/Fallback-Hinweis.
- **Tatsächliches Verhalten:** Nach erfolgreichem Config-Fix und Backend-Neustart schlägt ein Folge-TestCase durch Backend-/Chat-Timeout fehl.
- **Reproduktion / Kontext:** <TestRun, TC-IDs, Laufzeiten, Runner, relevante Evidence-Pfade>
- **Betroffener Bereich:** Backend Chat Processing / Intent Routing / Runtime Stability / Test Infrastructure
- **Nachweise:** <TestResult, Backend-Logs, Network/API Evidence oder "noch zu erheben">
- **Wichtigkeit:** MEDIUM
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** M
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Wiederholtes/intermittierendes Timeout blockiert Live-Test-Pipeline; Debug muss Ursache zwischen Backend Runtime, Chat Processing, API-Key/Auth und Test-Infrastruktur isolieren.
- **Routing confidence:** MEDIUM
- **Handoff:** none
- **Recommended next skill:** SKILL 3
- **Handoff created:** none
```

Nach Erzeugung dieses Backlog-Items MUSS Skill 4 Variante A fuer `BACKLOG SKILL 3 – EXECUTION HANDOFF` ausgeben, nicht Variante C. Ein weiterer direkter Retest ohne Debug-/Backlog-Fix ist nur erlaubt, wenn eine konkrete externe Ursache behoben wurde.

---

## GPT-5.5 ESCALATION HANDOVER (COST-SAFE)

Wenn GPT-5.5 erforderlich ist, darf der Skill nicht mit voller Chat-Historie weiterarbeiten.

Stattdessen MUSS der Skill stoppen und genau einen kompakten Copy-Block fuer einen frischen GPT-5.5-Chat ausgeben.

```text
MODEL SWITCH REQUIRED: SWE 1.6 -> GPT-5.5

Reason:
- <konkreter Eskalationsgrund>

BEGIN COPY FOR NEW GPT-5.5 CHAT

@[/TEST SKILL 4 – FINDING TRIAGE AND ROUTING]

Mode: ESCALATION_REVIEW
Execution Model: GPT-5.5

Binding Artifacts:
- TestSpec: <path>
- TestPlan: <path>
- TestResult: <path>
- Finding(s): <kompakte Liste der unklaren/high-risk Findings>

Escalation Question:
- Wie muessen diese Findings sicher geroutet werden: Backlog, Blocker, TestSpec-Fix, Retest oder PASS_TO_CONTINUE?

Relevant Evidence:
- <nur relevante Finding-IDs, Risk-Level, Evidence-Auszüge, keine vollstaendigen Logs>

Hard Rules:
- Use only listed artifacts and evidence as source of truth.
- Ignore previous chat history.
- Do not add product requirements.
- Do not implement code.
- Do not request full logs unless absolutely required.
- Decide only the escalation question.
- Do not mutate `documentation/backlog/BACKLOG.md` directly in GPT-5.5 unless explicitly instructed by the user after this review.

Expected Output:
- Decision: PASS_TO_CONTINUE | BLOCKED | REQUIRED_FIX_ROUTING | REQUIRED_TESTSPEC_FIX | REQUIRED_RETEST
- Reason:
- Required next skill:
- Recommended model:
- Copy handover back to SWE 1.6 if continuation is possible.

END COPY
```

---

## 🚫 RESTRICTIONS

KEINE Code-Implementation (ausser eindeutig erlaubte LOW-risk Markdown/Config-Fixes)
KEINE Architekturentscheidungen
KEINE Scope-Erweiterung
KEINE Task-Neuerfindung

---

## 🧠 ERROR HANDLING

Wenn Findings nicht eindeutig triagiert werden koennen:

```text
FINDING TRIAGE BLOCKED

Reason:
- <konkreter Grund>

Action:
→ GPT-5.5 fuer Klaerung oder TestSpec-Anpassung
```

Auch `FINDING TRIAGE BLOCKED` darf nicht ohne grauen Copy-Handover enden.

Pflicht:

- Wenn GPT-5.5 erforderlich ist: den `GPT-5.5 ESCALATION HANDOVER` ausgeben.
- Wenn Artefakte fehlen/ungueltig sind: konkreten Re-Run-Copy-Handover zu `@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION]` oder zum passenden Artefakt-Skill ausgeben.
- Wenn ein Retest noetig ist: Variante C mit `Mode: LIVE_RETEST` ausgeben.
- Reine Prosa wie `Triage blockiert, bitte pruefen` ist ungueltig.

---

## 🧠 OUTPUT GUARANTEE

Output ist immer:

deterministisch
triage-only
routing-clear
non-implementing (default)
