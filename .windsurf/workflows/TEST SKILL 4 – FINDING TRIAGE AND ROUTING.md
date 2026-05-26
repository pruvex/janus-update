---
description: SWE 1.6 Test Pipeline Phase 4 â€“ Finding Triage and Routing. Bewertet alle Findings aus dem TestResult, entscheidet ueber Sofortfix, Backlog oder Blocker, und routet Ergebnisse ins Dashboard/Backlog. Keine Code-Implementation, ausser eindeutig erlaubte LOW-risk Markdown/Config-Fixes.
---

# TEST SKILL 4 â€“ FINDING TRIAGE AND ROUTING

## ðŸŽ¯ PURPOSE

Dieser Skill bewertet alle Findings aus dem TestResult und entscheidet ueber den naechsten Schritt.

Er entscheidet:
â†’ kein Problem | Sofortfix moeglich | Backlog Item noetig | Security Blocker | TestSpec-Anpassung noetig | Retest noetig

KEINE CODE-IMPLEMENTATION, ausser eindeutig erlaubte LOW-risk Markdown-/Config-Fixes.
Sicherer Standard: Findings ins Backlog.

---

## ðŸ¤– DEFAULT MODEL

SWE 1.6

Ausnahme:
- GPT-5.5 nur bei HIGH/CRITICAL Security-Finding oder unklarem Scope

---

## ðŸ“¥ INPUT

- TestSpec aus `documentation/TEST_SPEC/`
- TestPlan aus `documentation/test-runs/`
- TestResult-JSON aus `documentation/test-results/<TEST_RUN_ID>_results.json` (primaere Evidence)
- TestResult-MD aus `documentation/test-results/<TEST_RUN_ID>_results.md` (Fallback/Lesekontext)

---

## ðŸ“Œ AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer TestSpec, TestPlan und TestResult nennt, sind diese Artefakte automatisch die verbindlichen Quellen. Wenn ein maschinenlesbares `TestResultJson` genannt wird oder unter `documentation/test-results/<TEST_RUN_ID>_results.json` existiert, ist diese Datei die primaere Findings-Quelle.

Der Skill MUSS dann:

- die genannte TestSpec-Datei vollstaendig lesen
- die genannte TestPlan-Datei vollstaendig lesen
- die genannte TestResult-JSON-Datei vollstaendig lesen und gegen `tests/e2e/generator/test-result.schema.json` plausibilisieren
- die genannte TestResult-MD-Datei lesen, falls vorhanden, aber nur als Lesekontext/Fallback nutzen
- die Findings ausschliesslich gegen diese Artefakte bewerten
- Failure Codes, Status, TestCase-IDs und Evidence-Pfade aus `TestResultJson.results[]` unveraendert uebernehmen
- Chatverlauf, fruehere Diskussionen und zusaetzliche muendliche Nebeninformationen ignorieren, sofern sie den Artefakten widersprechen oder ueber sie hinausgehen
- keine Requirements, Produktentscheidungen oder Architekturentscheidungen aus dem Chatkontext ergaenzen
- stoppen, wenn Artefakte widerspruechlich sind

Minimaler gueltiger User-Aufruf:

```text
/TEST SKILL 4 â€“ FINDING TRIAGE AND ROUTING mit folgenden Artefakten:
TestSpec: documentation/TEST_SPEC/<TESTSPEC>.md
TestPlan: documentation/test-runs/<TEST_RUN_ID>_plan.md
TestResult: documentation/test-results/<TEST_RUN_ID>_results.md
TestResultJson: documentation/test-results/<TEST_RUN_ID>_results.json
```

Wenn Artefakte unlesbar oder widerspruechlich:

```text
FINDING TRIAGE ARTIFACTS INVALID

Issue:
- <konkretes Problem>

Action:
â†’ korrekte Artefakte angeben oder TEST SKILL 3 erneut ausfuehren
```

---

## âš™ï¸ EXECUTION FLOW

---

### 1. LOAD ARTIFACTS

- TestSpec laden
- TestPlan laden
- TestResultJson laden (primaer)
- TestResult-MD laden, falls vorhanden (Fallback/Lesekontext)
- Alle Findings aus `results[]` extrahieren (inkl. `result`, `classification`, `evidencePath`, `notes`, `durationMs`)
- Summary aus `summary` und Gesamtstatus aus `status` uebernehmen
- Nebenbefunde ausserhalb TestScope nur aus Evidence/Notes/TestResult-MD ableiten, nicht aus Chat-Gedaechtnis

### 1.1 MACHINE-READABLE TESTRESULT GATE (V3.1)

Primaerquelle:

```text
documentation/test-results/<TEST_RUN_ID>_results.json
```

Erwartete Struktur:

- `schemaVersion: janus.test-result.v1`
- `testRunId`
- `status: PASS | FAIL | PARTIAL | BLOCKED | RUNNING`
- `summary`
- `artifacts.resultJson`
- `results[]` mit `testCaseId`, `result`, `classification`, `evidencePath`

Regeln:

- Wenn `TestResultJson` vorhanden und valide ist, MUSS Skill 4 daraus triagieren.
- Markdown darf Failure Codes aus JSON nicht ueberschreiben.
- Wenn JSON und Markdown widersprechen, gilt JSON und der Widerspruch wird als Finding `TEST_RESULT_ARTIFACT_DRIFT` behandelt.
- Wenn JSON fehlt, aber MD vorhanden ist: `TestResultJson: MISSING` im Output nennen und Markdown nur als Fallback verwenden; bei unklaren Findings Retest/Skill-3-Handover statt PASS.
- Wenn JSON unlesbar/ungueltig ist: `FINDING TRIAGE ARTIFACTS INVALID` mit Handover zu TEST SKILL 3 `LIVE_RETEST`.

---

### 2. FINDING TRIAGE

Fuer jedes Finding entscheide:

- **kein Problem**: Erwartetes Verhalten, kein Handlungsbedarf
- **Sofortfix moeglich**: Eindeutiger kleiner LOW-risk Markdown-/Config-/Dokumentations-Fix
- **Backlog Item noetig**: Bug, Verbesserung, UX-Problem, Cost-Problem, Routing-Problem
- **Security Blocker**: Security-, Privacy- oder Prompt-Injection-Problem
- **Runtime/Product Blocker**: Backend-, Provider-, Runtime-, Produkt- oder Testausfuehrungsfehler, der einzelne fachliche TestCases blockiert, aber kein Security-/Privacy-Blocker ist
- **TestSpec-Anpassung noetig**: TestSpec war unzutreffend, Scope unklar
- **Retest noetig**: Test nicht deterministisch durchfuehrbar, Daten fehlten

Wenn `RETEST REQUIRED` entschieden wird, MUSS der Skill:

- klar sagen, warum kein Produktbug/Backlog-Item erzeugt wurde oder welches Finding vor dem Retest behoben werden muss
- den direkten naechsten Schritt nennen
- am Ende einen einzelnen grauen Copy-Handover zum passenden naechsten Skill ausgeben
- bei Test-Infrastruktur-, Backend-Timeout-, Runner-Selector-, Auth-, API-Key-, Healthcheck- oder fehlender-Evidence-Problemen standardmaessig zu `TEST SKILL 3 â€“ LIVE JANUS TEST EXECUTION` mit `Mode: LIVE_RETEST` routen
- niemals ohne Copy-Handover mit nur einer Prosazusammenfassung enden

---

### 3. BACKLOG INTEGRATION (HARD RULE)

Alle echten Bugs, Verbesserungen, Security-/Privacy-Probleme, Prompt-Injection-Probleme, Cost-Probleme, Intent-/Routing-Probleme und auch Nebenbefunde ausserhalb des direkten TestScopes MUeSSEN als Backlog-Items in `documentation/backlog/BACKLOG.md` erfasst werden, wenn sie nicht eindeutig irrelevant sind.

#### 3.1 ID-DETERMINATION RULE (PFLICHT)

**VOR der Erstellung eines neuen Items MUSS die KI die gesamte Datei `documentation/backlog/BACKLOG.md` lesen und die aktuell hoechste `BACKLOG-XXX`-Nummer identifizieren. Die neue ID MUSS zwingend `[Hoechste ID] + 1` lauten. Es ist STRENG VERBOTEN, IDs zu raten oder ohne vorherigen File-Scan zu vergeben.**

Konkretes Vorgehen (verbindlich, in dieser Reihenfolge):

1. Vollstaendiges Einlesen von `documentation/backlog/BACKLOG.md` mit dem Read-Tool (kein partieller Read, keine Annahme aus dem Kontext, keine Schaetzung).
2. Alle Vorkommen des Musters `^### BACKLOG-(\d{3}) â€“ ` extrahieren (Grep mit `^### BACKLOG-\d+`).
3. Die numerisch hoechste Nummer ueber **alle** Sektionen (`READY`, `IN PROGRESS`, `DONE`, `NEEDS INFO`, jeder anderen) identifizieren â€” nicht nur in einer Status-Sektion suchen.
4. Naechste ID = `max(gefundene IDs) + 1`, formatiert als `BACKLOG-NNN` mit dreistelliger Zahl (z. B. `BACKLOG-026`).
5. **Kollisions-Self-Check**: Vor dem Schreiben MUSS verifiziert werden, dass die berechnete ID im File noch NICHT existiert. Bei Kollision -> Schritt 3 wiederholen.
6. Erst nach erfolgreichem Self-Check das neue Item mit der ermittelten ID einfuegen.

**STRENG VERBOTEN**:

- IDs aus dem Gedaechtnis, aus Chat-Kontext oder aus aelteren Snapshots vergeben.
- Auf `janus-dashboard/data/backlog.snapshot.json` statt auf `BACKLOG.md` als ID-Quelle stuetzen.
- "Sicherheitsabstand" lassen oder IDs ueberspringen (z. B. `BACKLOG-100` waehlen, weil "es noch frei sein duerfte").
- Items mit identischer ID-Header ablegen â€” bei Verdacht einer Doppelvergabe MUSS der Konflikt sofort durch Umnummerierung des juengeren Eintrags geloest werden.

#### 3.2 BACKLOG-ITEM TEMPLATE

Backlog Items MUeSSEN dashboard-kompatible Felder enthalten. Wichtig: Die Felder muessen exakt im parser-kompatiblen Format `- **Feldname:** Wert` geschrieben werden.

```text
### BACKLOG-XXX â€“ <Titel>

- **Typ:** BUG | CHANGE | ENHANCEMENT | IMPROVEMENT | TECH_DEBT | UNCLEAR
- **Status:** READY
- **Quelle:** TestRun
- **TestRun:** TEST-RUN-YYYY-MM-DD-NNN
- **Kurzbeschreibung:** <eine Zeile>
- **Erwartetes Verhalten:** <aus TestSpec/TestPlan>
- **TatsÃ¤chliches Verhalten:** <aus TestResult>
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

Dashboard-Typ-Regel (HARD):

- `Typ` MUSS exakt einer der Dashboard-kanonischen Werte sein: `BUG`, `CHANGE`, `ENHANCEMENT`, `IMPROVEMENT`, `TECH_DEBT`, `UNCLEAR`.
- Security-, Privacy-, Prompt-Injection-, Cost- oder UX-Findings sind KEINE `Typ`-Werte. Diese Information gehoert in Titel, `Betroffener Bereich`, `Kurzbeschreibung` und `Routing reason`.
- Deterministische Zuordnung:
  - Security / Privacy / Prompt-Injection / Safety-Regressions -> `BUG`
  - Test-Oracle-, Spec-, Dokumentations- oder Pipeline-Verbesserungen -> `IMPROVEMENT` oder `TECH_DEBT`
  - Produkt-Feature-Wunsch ohne Defekt -> `ENHANCEMENT`
  - Unklare Klassifikation -> `UNCLEAR`
- Vor dem finalen Output MUSS geprueft werden, dass jedes neu erzeugte Backlog-Item im Dashboard sichtbar waere. Nicht-kanonische Typen wie `Security`, `Prompt-Injection`, `Privacy`, `Cost`, `UX`, `Sonstiges` sind BLOCKER und muessen vor `FINDING TRIAGE COMPLETE` korrigiert werden.

---

### 4. ROUTING-REGELN

- **kleine klare lokale Bugs**: `PRE_IMPLEMENTATION_VERIFICATION` / `SKILL 3`
- **groessere Feature-/UX-/Safety-Fragen**: `SPEC_PIPELINE_START` / `SKILL 1`
- **bereits klare atomare Tasks**: `SKILL 3`
- **high risk/security**: eher `SPEC_PIPELINE_START` oder GPT-5.5 Audit-Hinweis
- **keine DONE Items reopen**: neue Follow-up-Items erzeugen, Original referenzieren

---

### 5. DASHBOARD-SYNC-HINWEIS

HARD RULE:

Wenn Skill 4 selbst Backlog-Items erzeugt oder bestehende Backlog-Items veraendert, ist der Dashboard-Sync NICHT optional.

- `Dashboard-Sync: Empfohlen` ist in diesem Fall verboten.
- Skill 4 muss entweder `Dashboard-Sync: DURCHGEFUEHRT` mit Ergebnis melden oder `Dashboard-Sync: PFLICHT FUER NAECHSTEN SKILL` ausgeben.
- Wenn der Sync an den naechsten Skill delegiert wird, MUSS der Copy-Handover `Sync Dashboard-Snapshot via npm run sync:backlog` als harte Arbeitsregel enthalten.
- `FINDING TRIAGE COMPLETE` ist ungueltig, wenn neue/geaenderte Backlog-Items genannt werden und weder durchgefuehrter Sync noch Pflicht-Sync im naechsten Handover enthalten ist.

Nach **jeder** Backlog-Aenderung MUSS der Skill den folgenden Sync-Hinweis ausgeben. Sync-pflichtig sind insbesondere:

- Neues Backlog-Item angelegt
- Bestehendes Item editiert (Status-, Routing-, Empfehlungs-, Wichtigkeits-, Handoff-Felder)
- **ID-Aenderung / Umnummerierung** eines Items (z. B. wegen Kollision-Fix gemaess Section 3.1)
- Loeschung eines Items
- Konsolidierung mehrerer Items
- Snapshot-Drift vermutet (Snapshot in `janus-dashboard/data/backlog.snapshot.json` weicht von `BACKLOG.md` ab)

```text
Dashboard-Sync Hinweis:
â†’ Fuehre im Ordner janus-dashboard aus:
   npm run sync:backlog
â†’ Dadurch wird der Dashboard-Snapshot aktualisiert.
â†’ Bei ID-Umnummerierungen oder Kollisionsfixes ist der Sync ZWINGEND, sonst zeigt das Dashboard veraltete IDs.
â†’ Sonst: empfohlen, aber nicht erzwungen, falls User-Freigabe noetig ist.
```

---

## ðŸŒ OUTPUT LANGUAGE

Alle user-facing Zusammenfassungen, Bewertungen, Titel, Zielbeschreibungen, Next Steps und Fehlermeldungen MUeSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Klassennamen, Funktionsnamen und Modellnamen bleiben unveraendert.

---

## ðŸ“¤ OUTPUT FORMAT

### Artifact-Mutation Gate (HARD)

`FINDING TRIAGE COMPLETE` ist nur erlaubt, wenn die Triage-Entscheidung auch in den
kanonischen Artefakten umgesetzt wurde.

Pflicht bei offenen/teilweise behobenen Findings:

- Neue Backlog-Items, Follow-up-Items oder Reopen-/Status-Korrekturen muessen in `documentation/backlog/BACKLOG.md` geschrieben sein.
- Wenn ein bestehendes Item als effektiv geloest bewertet wird, aber Test-Oracle/Expectation falsch ist, darf das Original nicht einfach auf `DONE/PASS` gesetzt werden; es braucht entweder Retest-Evidence oder ein neues Test-Oracle-Follow-up.
- DONE-Items duerfen nicht "reopened" werden. Erzeuge ein neues Follow-up-Item und referenziere das Original in `Follow-up zu`.
- Nach Backlog-Aenderung MUSS `npm run sync:backlog` in `janus-dashboard` ausgefuehrt oder als BLOCKER gemeldet werden.
- Der Output muss die erzeugten/geaenderten Backlog-IDs nennen. Reine Prosa wie `Routing: Reopen BACKLOG-041` ist ungueltig, wenn keine Artefakt-Aenderung erfolgt ist.

Verboten:

```text
BEGIN COPY FOR TEST SKILL 4
@[/TEST SKILL 4 â€“ FINDING TRIAGE AND ROUTING] FINDING TRIAGE COMPLETE
NEXT ACTION: Reopen BACKLOG-041 ...
Routing: Backlog-Item fÃ¼r ...
```

Wenn Skill 4 noch keine Backlog-Artefakte geschrieben hat, muss der Abschluss lauten:

```text
FINDING TRIAGE BLOCKED
Reason: TRIAGE_ARTIFACTS_NOT_WRITTEN
Required Action: Backlog-Follow-up-Items oder Status-Korrekturen in documentation/backlog/BACKLOG.md schreiben und Dashboard-Snapshot synchronisieren.
```

### Test-Oracle vs Product-Fix Routing

Wenn ein TestCase wegen `ASSERTION_MISMATCH` fehlschlaegt, aber Evidence fachlich korrektes
Produktverhalten zeigt, MUSS Skill 4 das als `TEST_ORACLE_TOO_NARROW` oder
`TEST_EXPECTATION_PROBLEM` triagieren und ein Backlog-Follow-up fuer TestPlan/TestSpec/Oracle
erzeugen. Es darf nicht als Produktbug oder erneuter System-Prompt-Fix geroutet werden.

Wenn ein Fix die urspruengliche Produktanforderung teilweise loest, aber einzelne Security- oder
Prompt-Faelle weiterhin falsches Verhalten zeigen, MUSS ein neues Follow-up-Item erzeugt werden,
statt das alte DONE/PENDING-Item direkt zu "reopenen".

### Generator-/TestPlan-Oracle Evidence Gate (HARD)

Skill 4 darf keinen Generator-, Compiler- oder TestPlan-Transfer-Bug behaupten, bevor der
aktuelle TestPlan und die konkrete Evidence fuer die fehlgeschlagenen TestCases geprueft wurden.

Wenn Skill 4 eine Diagnose oder ein Backlog-Item mit einer der folgenden Aussagen erzeugen will:

- `Generator uebertraegt Patterns nicht`
- `TestPlan enthaelt erwartete containsAny-Patterns nicht`
- `Compiler-/Generator-Bug`
- `TestPlan-Generator-Transferfehler`
- `TestSpec wurde nicht in den TestPlan uebernommen`

dann gilt zwingend:

1. Der aktuelle `TestPlan` aus dem Handover MUSS gelesen werden.
2. Fuer jeden betroffenen TestCase MUSS `expected.containsAny` und `expected.mustNotContain`
   aus dem aktuellen TestPlan gegen die Evidence verglichen werden.
3. Die Diagnose ist nur erlaubt, wenn die konkret erwarteten Patterns im aktuellen TestPlan
   wirklich fehlen.
4. Wenn die relevanten Patterns im aktuellen TestPlan vorhanden sind, ist ein Generator- oder
   Transfer-Bug als Routing verboten. Dann MUSS die tatsaechliche Assertion-Ursache anhand der
   Evidence triagiert werden.

Wenn ein vorhandener TestPlan bereits Klarstellungs-/Ablehnungs-Patterns enthaelt, aber der
Test trotzdem fehlschlaegt, MUSS Skill 4 zwischen diesen Faellen unterscheiden:

- `TEST_ORACLE_TOO_STRICT_MUST_NOT_CONTAIN_CONTEXT`: Die Antwort ist eine sichere
  Klaerungsfrage oder Ablehnung, aber `mustNotContain` trifft ein Wort im ungefaehrlichen
  Kontext, z.B. `geloescht` in `Was genau soll geloescht werden?`.
- `TEST_ORACLE_TOO_NARROW_REFUSAL_ACCEPTANCE`: Die Antwort ist eine sichere Ablehnung oder
  Security-Policy-Antwort, aber `containsAny` akzeptiert diese sichere Antwort noch nicht.
- `PRODUCT_ROUTING_OR_MEMORY_LEAK`: Die Antwort bearbeitet eine falsche Domaene, ruft
  falsches Memory/Wissen ab oder gibt fachlich falsches Produktverhalten aus, z.B.
  Calendar/Security-Prompt fuehrt zu Nikola-Tesla-Memory-Antwort.

Repair-Regel:

Wenn `Mode=FINDING_TRIAGE_REPAIR` gesetzt ist, MUSS Skill 4 alte Triage-Claims aus dem
vorherigen Output gegen den aktuellen TestPlan und die aktuelle Evidence neu pruefen. Stale
Backlog-Items, die durch den aktuellen TestPlan widerlegt sind, duerfen nicht weitergeroutet
werden. Stattdessen muss die Triage korrigiert und der naechste Copy-Handover auf die
tatsaechliche Ursache zeigen.

```text
FINDING TRIAGE COMPLETE

TestRun: <TEST-RUN-ID>
TestResultJson: <path | MISSING>
Machine Result Status: PASS | FAIL | PARTIAL | BLOCKED | RUNNING

Findings Uebersicht:
- Kein Problem: <Anzahl>
- Sofortfix: <Anzahl>
- Backlog Item: <Anzahl>
- Security Blocker: <Anzahl>
- Runtime/Product Blocker: <Anzahl>
- TestSpec-Anpassung: <Anzahl>
- Retest noetig: <Anzahl>

Erzeugte Backlog Items:
- BACKLOG-XXX: <Titel> â€“ <Routing>
- BACKLOG-YYY: <Titel> â€“ <Routing>

Sofortfixes (falls keine: "Keine"):
- <Fix-Beschreibung und Datei>

Security Blocker (falls keine: "Keine"):
- <Security-/Privacy-/Prompt-Injection-Blocker>

Runtime/Product Blocker (falls keine: "Keine"):
- <Backend-/Provider-/Runtime-/Produkt-Blocker>

Dashboard-Sync:
- DURCHGEFUEHRT: <sync result> | PFLICHT FUER NAECHSTEN SKILL: npm run sync:backlog in janus-dashboard | Nicht erforderlich: <Grund>

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

## ðŸ“‹ COPY-PASTE HANDOVER (PFLICHT)

Am Ende MUSS immer ein einzelner grauer Copy-Block ausgegeben werden, wenn der Prozess fortgesetzt werden kann.

Der Copy-Block MUSS den direkten naechsten Schritt enthalten und darf nicht durch reine Prosa ersetzt werden.

Self-Check vor finaler Antwort:

- Enthaelt die Antwort `FINDING TRIAGE COMPLETE`? Dann MUSS sie auch genau einen Copy-Block mit `@[/... ]` enthalten.
- Entscheidung `RETEST REQUIRED`? Dann MUSS der Copy-Block `@[/TEST SKILL 3 â€“ LIVE JANUS TEST EXECUTION]` und `Mode: LIVE_RETEST` enthalten.
- Entscheidung `NO_FINDINGS` bei `ResultStatus=PASS`? Dann MUSS der Copy-Block `@[/SKILL 7 - DOKUMENTATIONSUPDATE]` enthalten.
- Kein vollstaendiges valides TestResult? Dann darf kein Handover zu TEST SKILL 5 ausgegeben werden.
- Fehlt der Copy-Block, MUSS der Skill die Antwort nicht abschliessen, sondern den Copy-Block ergaenzen.
- Enthaelt die Antwort `Status: FINDINGS_TRIAGED`, `FINDINGS TRIAGED`, `Routing: All`, `routed to BACKLOG`, `findings to BACKLOG`, `Neue Backlog Items` oder `Total Findings`? Dann MUSS sie entweder konkrete neue/geaenderte Backlog-IDs nennen UND einen Copy-Block zu `BACKLOG SKILL 2` oder `BACKLOG SKILL 3` enthalten, oder mit `FINDING TRIAGE BLOCKED: BACKLOG_ARTIFACTS_NOT_CREATED` blocken.

Verboten ohne direkt folgenden Copy-Handover:

```text
Handoff Complete
Result: FINDINGS_TRIAGED
Routing: 4 findings to BACKLOG
BACKLOG-XXX: COMPLETED
BACKLOG-XXX: READY FOR RETEST
Next Steps
New Backlog Items: Create backlog items
```

Wenn ein TestRun gleichzeitig einen alten Infra-/Produktfix validiert und neue fachliche Findings zeigt:

- Validierte alte Items duerfen im Text als `VALIDATED_BY_RETEST` genannt werden.
- Sie duerfen nicht einfach als `DONE` behauptet werden, ausser der Output enthaelt einen direkten `SKILL 7`-Copyblock oder einen Backlog-/Dashboard-Handoff, der die Statusaenderung erledigt.
- Neue Findings haben Vorrang fuer den naechsten Copy-Handover: Variante A (`BACKLOG SKILL 2` oder `BACKLOG SKILL 3`) verwenden.
- Der Copy-Handover muss die validierten Items im Context nennen, damit der naechste Skill sie nicht erneut als offene Ursache triagiert.
- Wenn neue oder bestehende aktive Items aus diesem TestRun `Handoff: none`, `Handoff: null` oder keinen passenden Handoff-Pfad haben, ist ein direkter `SKILL 7`-Handover verboten.
- In diesem Fall muss der finale Copy-Handover zu `BACKLOG SKILL 3 – EXECUTION HANDOFF` gehen, damit Handoff-Artefakte erzeugt und der Dashboard-Snapshot synchronisiert werden.

Verboten:

```text
Handoff to SKILL 7
@[/SKILL 7 – DOKUMENTATIONSUPDATE] ...
```

wenn im selben Output `New Items Created`, `Existing Items Covering Findings`, `Handoff: none`,
`Handoff created: none` oder aktive Backlog-Items ohne Handoff vorkommen.

Routing:

- Wenn `RETEST REQUIRED`: Variante C verwenden.
- Wenn neue/unklare/high-risk Backlog-Findings offen sind: Variante A verwenden.
- Wenn offene Findings vollstaendig einem bereits existierenden READY-Backlog-Item mit gueltigem Handoff zugeordnet sind: Variante D verwenden.
- Wenn `ResultStatus=PASS`, `Failed=0`, `Blocked=0`, `ManualGate=0`, `FailureCode=NONE` und keine Findings vorhanden sind: Variante E verwenden und direkt zu `SKILL 7 - DOKUMENTATIONSUPDATE` routen.
- Wenn keine blockierenden Findings vorhanden sind, aber noch ein expliziter Audit-/Production-Confidence-Schritt benoetigt wird: Variante B verwenden.
- Wenn das TestResult wegen Test-Infrastruktur nicht vollstaendig gemessen wurde: NICHT Variante B verwenden, sondern Variante C.
- Wenn derselbe Timeout nach Config-Fix und Backend-Neustart weiterhin oder intermittierend auftritt, darf Skill 4 nicht endlos nur `RETEST REQUIRED` ausgeben. Dann MUSS Skill 4 entweder ein Backlog-Item fuer Runtime-/Testinfrastruktur-Stabilitaet erzeugen oder explizit begruenden, welche konkrete Evidence noch vor Backlog-Erstellung fehlt.

### Terminal-PASS Gate (HARD)

Wenn alle folgenden Bedingungen erfuellt sind, MUSS TEST SKILL 4 den TestRun als abgeschlossen behandeln und darf nicht ohne Handover enden:

- `ResultStatus=PASS`
- `TotalTests > 0`
- `Passed = TotalTests`
- `Failed=0`
- `Blocked=0`
- `ManualGate=0`
- `FailureCode=NONE`
- Triage-Ergebnis: `NO_FINDINGS` oder keine blockierenden Findings
- `TestResultJson` ist vorhanden, lesbar und passt zum `Target TestRun`

In diesem Fall gilt:

- `FINDING TRIAGE COMPLETE` muss ausgegeben werden.
- `Findings: NONE` bzw. `NO_FINDINGS` muss klar genannt werden.
- Der naechste Schritt ist `SKILL 7 - DOKUMENTATIONSUPDATE`, nicht `TEST SKILL 5`, nicht `BACKLOG SKILL 3` und nicht erneut `TEST SKILL 4`.
- Der finale Output MUSS genau einen grauen `text` Copy-Block nach Variante E enthalten.
- Wenn der TestRun ein Backlog-Item oder eine Task validiert, MUSS der Skill das Item/Task im Skill-7-Handover benennen. Falls `BacklogItem` nicht explizit im Input steht, muss der Skill es aus TestPlan-Titel, TestResult-Titel, Task-Datei oder TestSpec-Kontext inferieren; wenn keine sichere Inferenz moeglich ist, `BacklogItem=N_A` verwenden und trotzdem zu Skill 7 routen.
- Bei Backlog-Items lautet die Completion Action: `MARK_BACKLOG_DONE_AND_SYNC_DASHBOARD`.
- Bei reinen TestSpec-/Capability-Runs ohne Backlog-Item lautet die Completion Action: `RECORD_TEST_PIPELINE_PASS_AND_SYNC_DOCUMENTATION`.

Verboten bei Terminal-PASS:

```text
Action Required: NONE
Conclusion: ... kann als DONE markiert werden.
```

ohne direkt folgenden Skill-7-Copyblock.

### Audit-Routing Gate (HARD)

TEST SKILL 4 darf nur zu `TEST SKILL 5 - DIAMOND RETEST AUDIT` routen, wenn alle folgenden Bedingungen erfuellt sind:

- `ResultStatus` ist `PASS` oder alle nicht-PASS Findings sind explizit als nicht-blockierende Follow-ups mit Empfehlung `LATER`/`BACKLOG` geroutet.
- Es gibt kein offenes `READY` oder `IN PROGRESS` Backlog-Item mit `Empfehlung: DO NOW`, das direkt aus diesem TestRun oder dessen Retest-Serie stammt.
- Es gibt kein offenes Test-Oracle-/TestSpec-Finding, das aktuelle FAILs erklaert und als `SPEC_PIPELINE_START` oder `PRE_IMPLEMENTATION_VERIFICATION` weiterbearbeitet werden muss.
- Security-/Prompt-Injection-Fixes sind entweder durch einen vollstaendigen Retest PASS bestaetigt oder verbleibende FAILs sind nachweislich nur Test-Oracle-Probleme UND das Oracle-Item ist nicht `DO NOW`.

Wenn `ResultStatus=FAIL` und die Ursache `TEST_ORACLE_TOO_NARROW`, `TEST_EXPECTATION_PROBLEM` oder ein bestehendes `BACKLOG-XXX:READY` ist, ist ein Handover zu TEST SKILL 5 verboten.

Stattdessen MUSS Skill 4 direkt zum naechsten Bearbeitungsschritt des offenen Items routen:

```text
SPEC_PIPELINE_START -> @[/SKILL 1 - SPEC TO TASK COMPILER]
PRE_IMPLEMENTATION_VERIFICATION -> @[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
EXECUTION_READY -> @[/SKILL 4 - EXECUTIONER]
```

Verbotene Outputs in diesem Fall:

```text
BEGIN COPY FOR TEST SKILL 5
ProductionConfidence=PRODUCTION_READY_WITH_TEST_ORACLE_RESERVE
ProductFixes=BACKLOG-043:DONE; TestOracleFixes=BACKLOG-042:READY
```

### Variante A: Blockierende Findings offen

Wenn blockierende Findings offen sind, darf TEST SKILL 4 genau einen der folgenden Copy-Bloecke ausgeben:

- `BACKLOG SKILL 2`, wenn neue/unklare/high-risk Findings priorisiert oder bewertet werden muessen.
- `BACKLOG SKILL 3`, wenn die Findings bereits READY und ausreichend bewertet sind und nur Dashboard-Handoffs vorbereitet werden sollen.

Es duerfen niemals beide Bloecke gleichzeitig ausgegeben werden.

```text
@[/BACKLOG SKILL 2 â€“ REVIEW PRIORISIERUNG]

Mode: DELTA
Execution Model: GPT-5.5

Context:
- Quelle: TestRun <TEST-RUN-ID>
- Neue Backlog Items aus TestFindings: <Liste>
- Security Blocker vorhanden: JA | NEIN
- Runtime/Product Blocker vorhanden: JA | NEIN

Arbeitsregel:
- Bewerte neue TestRun-Findings zusammen mit bestehendem Backlog.
- Priorisiere Security-/Privacy-/Prompt-Injection-Findings hoch.
- Empfehle naechste Backlog-Items fuer Execution Handoff.
- Sync Dashboard-Snapshot via npm run sync:backlog oder blocke mit konkretem Grund.
```

Oder fuer direkten Dashboard-Prep:

```text
@[/BACKLOG SKILL 3 â€“ EXECUTION HANDOFF]

Mode: DASHBOARD_PREP
Execution Model: SWE 1.6

Context:
- Quelle: TestRun <TEST-RUN-ID>
- Neue Backlog Items erzeugt: <Liste>
- Routing-Ergaenzung fuer TestFindings erforderlich.
- Runtime/Product Blocker vorhanden: JA | NEIN

Arbeitsregel:
- Fuelle fehlende Routing-Metadaten fuer neue Backlog-Items.
- Erstelle/reuse Handoff-Artefakte.
- Bewege NICHTS nach IN PROGRESS.
- Sync Dashboard-Snapshot via npm run sync:backlog.
```

### Variante B: Keine blockierenden Findings, Audit noch erforderlich

```text
@[/TEST SKILL 5 â€“ DIAMOND RETEST AUDIT]

Mode: RETEST_AUDIT
Execution Model: SWE 1.6
TestSpec: <source test spec file>
TestPlan: <source test plan file>
TestResult: documentation/test-results/<test_run_id>_results.md
TestResultJson: documentation/test-results/<test_run_id>_results.json
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
- Copy-Handover zu SKILL 7 â€“ DOKUMENTATIONSUPDATE (bei PASS)
```

Variante B ist NICHT erlaubt, wenn das Terminal-PASS Gate erfuellt ist. Dann MUSS Variante E verwendet werden.

### Variante E: Terminal PASS / NO_FINDINGS -> Skill 7

Diese Variante ist PFLICHT, wenn das Terminal-PASS Gate erfuellt ist.

Der Copyblock MUSS als ein einzelner grauer `text` Block ausgegeben werden.

Wenn die lokalen Generator-Skripte verfuegbar sind, MUSS der Skill den Copyblock deterministisch erzeugen:

```text
node tests/e2e/generator/create-test-skill7-handover.mjs --spec <spec> --plan <plan> --run <TEST-RUN-ID> --result <results.md> --result-json <results.json> --backlog-item <BACKLOG-XXX|N_A> --task <task_id|N_A>
```

```text
@[/SKILL 7 - DOKUMENTATIONSUPDATE] Mode=COMPLETE_TASK; ExecutionModel=SWE_1_6; BacklogItem=<BACKLOG-XXX|N_A>; Task=<task_id|N_A>; TestSpec=<source test spec file>; TestPlan=<source test plan file>; TestResult=documentation/test-results/<test_run_id>_results.md; TestResultJson=documentation/test-results/<test_run_id>_results.json; TargetTestRun=<TEST-RUN-ID>; ResultStatus=PASS; TotalTests=<n>; Passed=<n>; Failed=0; Blocked=0; ManualGate=0; PassRatePct=100.00; ProviderPassRatePct=<Provider:100.00,...>; TypePassRatePct=<type:100.00,...>; Findings=NONE; CompletionAction=<MARK_BACKLOG_DONE_AND_SYNC_DASHBOARD|RECORD_TEST_PIPELINE_PASS_AND_SYNC_DOCUMENTATION>; Rules=USE_ARTIFACTS_ONLY_RECORD_COMPLETED_ONLY_NO_PENDING_RECORD; ExpectedOutput=TASK_COMPLETED_DASHBOARD_SYNCED
```

Pflichtfelder:

- `BacklogItem` darf nur `BACKLOG-XXX` oder `N_A` sein.
- `Task` darf ein konkreter Task-Identifier oder `N_A` sein.
- `TestResult` MUSS auf die `.md`-Datei zeigen. Wenn sie fehlt, muss sie aus dem validen `TestResultJson` erzeugt werden oder der Skill muss `FINDING TRIAGE ARTIFACTS INVALID` ausgeben.
- `PassRatePct`, `ProviderPassRatePct` und `TypePassRatePct` muessen aus `TestResultJson`/TestPlan berechnet werden, nicht aus Prosa.
- `ChangedFiles` gehoert nicht in diesen Skill-7-Handover; Skill 7 rekonstruiert die Dokumentations-/Backlog-Aenderungen aus den Artefakten.

Verbotene Terminal-PASS-Ausgaben:

```text
FINDING TRIAGE COMPLETE
Findings: NONE
Action Required: NONE
Conclusion: BACKLOG-XXX kann als DONE markiert werden.
```

ohne Variante-E-Copyblock.

### Variante D: Bestehendes READY-Backlog-Item ist der naechste Schritt

Diese Variante ist PFLICHT, wenn alle verbleibenden FAILs einem bestehenden READY-Backlog-Item zugeordnet sind und dieses Item einen gueltigen `Handoff` besitzt.

Fuer `SPEC_PIPELINE_START`:

```text
@[/SKILL 1 - SPEC TO TASK COMPILER]
Spec: <handoff path aus BACKLOG.md unter documentation/Planned Features/>
Backlog Item: <BACKLOG-XXX>

Context:
- Quelle: TestRun <TEST-RUN-ID>
- Grund: Verbleibende FAILs sind Test-Oracle/TestSpec-Findings und muessen vor Audit geloest werden.
- Blockiert TEST SKILL 5 bis neuer Retest PASS oder nicht-blockierende Follow-ups bestaetigt sind.
```

Fuer `PRE_IMPLEMENTATION_VERIFICATION`:

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: <BACKLOG-XXX oder Target Task aus Task-Datei>
Task: <handoff path aus BACKLOG.md unter documentation/tasks/>
Backlog Item: <BACKLOG-XXX>

Context:
- Quelle: TestRun <TEST-RUN-ID>
- Grund: Verbleibende FAILs sind einem offenen READY-Fix zugeordnet und muessen vor Audit geloest werden.
- Blockiert TEST SKILL 5 bis neuer Retest PASS oder nicht-blockierende Follow-ups bestaetigt sind.
```

Wenn der passende Handoff-Pfad fehlt oder zur Entry-Point-Art nicht passt, darf Skill 4 nicht zu TEST SKILL 5 routen. Dann muss Variante A mit `BACKLOG SKILL 3 - EXECUTION HANDOFF` ausgegeben werden.

### Variante C: Retest erforderlich

Diese Variante ist PFLICHT bei `RETEST REQUIRED`. Sie muss auch dann ausgegeben werden, wenn keine Backlog Items erzeugt wurden und das Finding als Test-Infrastruktur bewertet wurde.

```text
@[/TEST SKILL 3 â€“ LIVE JANUS TEST EXECUTION]

Mode: LIVE_RETEST
Execution Model: SWE 1.6
TestSpec: <source test spec file>
TestPlan: <source test plan file>
Previous TestResult: <source test result file>
Previous TestResultJson: documentation/test-results/<test_run_id>_results.json
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
- Der letzte Output-Teil MUSS ein grauer Copy-Block fuer `@[/TEST SKILL 3 â€“ LIVE JANUS TEST EXECUTION]` sein.
- Wenn `Auto-Fix Applied: LOCAL_E2E_CONFIG_CREATE_OR_REPAIR (SUCCESS)` genannt wird und Timeout weiter besteht, MUSS `Pre-Retest Requirements` zusaetzlich Backend-Neustart, API-Key-Konsistenz zwischen Config und laufendem Backend, Backend-Logs und Network/API Evidence fuer den Chat-Request enthalten.

Pflicht-Spezialfall `INTERMITTENT_BACKEND_TIMEOUT`:

Wenn nach erfolgreichem Config-Fix und Backend-Neustart mindestens ein TestCase PASS und ein spaeterer TestCase wegen Backend-/Chat-Timeout FAIL ist, MUSS Skill 4 das Finding als wiederholtes Stabilitaetsfinding behandeln.

Skill 4 darf es nur dann als reine Test-Infrastruktur ohne Backlog abschliessen, wenn alle folgenden Evidence-Punkte im TestResult vorhanden sind:

- Backend-Log zeigt eindeutig externes/temporÃ¤res Testumgebungsproblem und keinen Janus-Codepfad-Fehler.
- Network/API Evidence zeigt, dass der Chat-Request nicht valide beim Backend ankam oder eindeutig durch lokale Testumgebung blockiert wurde.
- Es gibt eine konkrete, einmalige, behobene Ursache, nach der ein erneuter Retest sinnvoll ist.

Wenn diese Evidence fehlt oder die Ursache nur vermutet wird, MUSS Skill 4 ein Backlog-Item erzeugen:

```text
### BACKLOG-XXX â€“ Intermittierender Backend Timeout bei Janus Live-Chat Retest

- **Typ:** Bug
- **Status:** READY
- **Quelle:** TestRun
- **TestRun:** <TEST-RUN-ID>
- **Kurzbeschreibung:** Janus beantwortet aufeinanderfolgende Live-Chat-Anfragen im automatisierten Retest nicht zuverlÃ¤ssig; ein TestCase PASS, ein Folge-TestCase Timeout.
- **Erwartetes Verhalten:** Janus verarbeitet aufeinanderfolgende Chat-/Intent-Anfragen stabil oder liefert einen kontrollierten Timeout-/Fallback-Hinweis.
- **TatsÃ¤chliches Verhalten:** Nach erfolgreichem Config-Fix und Backend-Neustart schlÃ¤gt ein Folge-TestCase durch Backend-/Chat-Timeout fehl.
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

Nach Erzeugung dieses Backlog-Items MUSS Skill 4 Variante A fuer `BACKLOG SKILL 3 â€“ EXECUTION HANDOFF` ausgeben, nicht Variante C. Ein weiterer direkter Retest ohne Debug-/Backlog-Fix ist nur erlaubt, wenn eine konkrete externe Ursache behoben wurde.

---

## GPT-5.5 ESCALATION HANDOVER (COST-SAFE)

Wenn GPT-5.5 erforderlich ist, darf der Skill nicht mit voller Chat-Historie weiterarbeiten.

Stattdessen MUSS der Skill stoppen und genau einen kompakten Copy-Block fuer einen frischen GPT-5.5-Chat ausgeben.

```text
MODEL SWITCH REQUIRED: SWE 1.6 -> GPT-5.5

Reason:
- <konkreter Eskalationsgrund>

BEGIN COPY FOR NEW GPT-5.5 CHAT

@[/TEST SKILL 4 â€“ FINDING TRIAGE AND ROUTING]

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
- <nur relevante Finding-IDs, Risk-Level, Evidence-AuszÃ¼ge, keine vollstaendigen Logs>

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

## ðŸš« RESTRICTIONS

KEINE Code-Implementation (ausser eindeutig erlaubte LOW-risk Markdown/Config-Fixes)
KEINE Architekturentscheidungen
KEINE Scope-Erweiterung
KEINE Task-Neuerfindung

---

## ðŸ§  ERROR HANDLING

Wenn Findings nicht eindeutig triagiert werden koennen:

```text
FINDING TRIAGE BLOCKED

Reason:
- <konkreter Grund>

Action:
â†’ GPT-5.5 fuer Klaerung oder TestSpec-Anpassung
```

Auch `FINDING TRIAGE BLOCKED` darf nicht ohne grauen Copy-Handover enden.

Pflicht:

- Wenn GPT-5.5 erforderlich ist: den `GPT-5.5 ESCALATION HANDOVER` ausgeben.
- Wenn Artefakte fehlen/ungueltig sind: konkreten Re-Run-Copy-Handover zu `@[/TEST SKILL 3 â€“ LIVE JANUS TEST EXECUTION]` oder zum passenden Artefakt-Skill ausgeben.
- Wenn ein Retest noetig ist: Variante C mit `Mode: LIVE_RETEST` ausgeben.
- Reine Prosa wie `Triage blockiert, bitte pruefen` ist ungueltig.

---

## ðŸ§  OUTPUT GUARANTEE

Output ist immer:

deterministisch
triage-only
routing-clear
non-implementing (default)
