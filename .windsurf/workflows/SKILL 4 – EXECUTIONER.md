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

Implementiere exakt:

- nur definierte Dateien
- nur definierte Logik
- nur definierter Scope

STRICT RULES:
- keine neuen Features
- keine ArchitekturÃ¤nderungen
- kein Refactoring auÃŸerhalb Task
- keine Optimierung auÃŸerhalb Scope

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
- Skill 4 darf `TASK COMPLETE` oder `READY FOR FINAL AUDIT` erst melden, wenn die erforderlichen automatischen Tests PASS sind oder nachvollziehbar N/A sind.
- Wenn automatische Tests fehlschlagen, MUSS Skill 4 gezielt fixen oder mit `TASK EXECUTION FAILED` / `FIX LOOP LIMIT REACHED` stoppen.

PIPELINE CONTINUATION GATE:

- Nach erfolgreicher automatischer Validierung MUSS Skill 4 prÃ¼fen, ob weitere Tasks aus derselben Task-Datei offen sind.
- Wenn weitere Tasks offen sind, MUSS Skill 4 stoppen und einen einzelnen grauen Copy-Block fÃ¼r den nÃ¤chsten Skill-4-Lauf mit dem nÃ¤chsten Target Task ausgeben.
- Wenn weitere Tasks offen sind, darf Skill 4 noch KEINEN Final-Audit-Handover ausgeben.
- Wenn weitere Tasks offen sind, ist ein manueller Gesamt-Janus-Test optional, aber NICHT das Final-Gate.
- Erst wenn keine weiteren Tasks offen sind, MUSS Skill 4 einen automatischen Gesamttest/Regressionstest fÃ¼r die gesamte Spec ausfÃ¼hren.
- Erst nach erfolgreichem Gesamttest darf Skill 4 das Manual Janus Validation Gate ausgeben.
- Nach dem letzten Task und erfolgreicher Gesamtvalidierung MUSS Skill 4 STOPPEN und nur das Manual Janus Validation Gate ausgeben.
- Skill 4 darf im selben Output wie `TASK COMPLETE` / `ALL TASKS COMPLETE` keinen Skill-6-Final-Audit-Copyblock ausgeben.
- Der Skill-6-Final-Audit-Copyblock darf ausschlieÃŸlich in einer separaten Antwort nach der User-Antwort `Manueller Test erfolgreich.` erzeugt werden.

MANUAL JANUS VALIDATION GATE NUR NACH LETZTEM TASK:

- Nach erfolgreicher automatischer Gesamtvalidierung MUSS Skill 4 den User auffordern, das vollstÃ¤ndig umgesetzte Feature real in Janus manuell zu testen.
- Skill 4 darf nicht direkt zum Final Audit weiterleiten, bevor der User den realen Janus-Gesamttest bestÃ¤tigt hat.
- Verboten: `BEGIN COPY @[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]` vor der User-BestÃ¤tigung `Manueller Test erfolgreich.`
- Skill 4 MUSS dem User genau zwei Optionen geben:

```text
MANUELLER JANUS-TEST ERFORDERLICH

Bitte teste jetzt das vollstÃ¤ndig umgesetzte Feature direkt in Janus.

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

Wenn derselbe Task nach zwei gezielten Fix-Versuchen weiterhin fehlschlÃ¤gt:

âž¡ STOP EXECUTION

```text
FIX LOOP LIMIT REACHED

Task: TASK-XXX

Failed Area:
- <konkreter Bereich: Tests / Build / Acceptance Criteria / Scope Conflict>

Attempts:
- 1: <kurze Zusammenfassung>
- 2: <kurze Zusammenfassung>

Action:
â†’ keine weiteren Blind-Fixes
â†’ Skill 2 Re-Evaluation oder GPT-5.5 Eskalation mit kompaktem Fehlerpaket
```

---

## OUTPUT FORMAT

```text id="skill4_output"
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
- nur technische Hinweise
- keine neuen Ideen

NÃ¤chster Schritt:
â†’ STOPP NACH DIESEM TASK
â†’ Automatische Tests/Validierungen MÃœSSEN bereits ausgefÃ¼hrt sein.
â†’ Wenn Code oder Tests geÃ¤ndert wurden und die automatische Task-Validierung PASS ist: zuerst `/save` ausfÃ¼hren.
â†’ Wenn weitere Tasks vorhanden sind: einen Copy-Handover fÃ¼r den nÃ¤chsten Skill-4-Lauf mit dem nÃ¤chsten Target Task ausgeben.
â†’ Wenn weitere Tasks vorhanden sind: KEIN Skill-6-Audit, KEIN Skill-5-Debug-Gate, KEIN Skill-7-Handover.
â†’ Wenn keine weiteren Tasks vorhanden sind: automatische Gesamtvalidierung ausfÃ¼hren.
â†’ Wenn keine weiteren Tasks vorhanden sind und Gesamtvalidierung PASS ist: User zum manuellen Janus-Gesamttest auffordern.
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
- Gib nach erfolgreichem Abschluss erneut entweder den nÃ¤chsten Skill-4-Handover oder, beim letzten Task, das Manual-Janus-Gesamttest-Gate aus.

NÃ¤chster erwarteter Output:
- Umsetzung genau dieses Target Tasks
- Automatische Test-/Validierungsergebnisse
- Pipeline Continuation Status
- Copy-Handover fÃ¼r den nÃ¤chsten Target Task oder finales Manual-Janus-Test-Gate
```

Gesamtvalidierung nach letztem Task:
- Wenn `Spec Implementation Complete: YES`, MUSS Skill 4 eine automatische Gesamtvalidierung der vollstÃ¤ndigen Spec-Umsetzung ausfÃ¼hren.
- Diese Gesamtvalidierung umfasst mindestens relevante Build-, Unit-, Integration-, E2E- oder Smoke-Tests fÃ¼r den kompletten Feature-Flow.
- Erst danach darf das Manual Janus Test Gate erscheinen.
- Nach dem Manual Janus Test Gate MUSS Skill 4 auf die User-Antwort warten.
- Vor der User-Antwort `Manueller Test erfolgreich.` oder einer Fehlerbeschreibung ist jeder Audit-/Debug-Copyblock verboten.

Finaler Skill-4-Output nach letztem Task und Gesamtvalidierung PASS:

```text
ALL TASKS COMPLETE - SPEC IMPLEMENTATION FINISHED

Completed Tasks:
- <alle abgeschlossenen Tasks>

Remaining Tasks:
- Keine

Spec Implementation Complete: YES

Gesamt-Test Results:
- <Build/Unit/Integration/E2E/Smoke>: PASS | N/A mit BegrÃ¼ndung

MANUELLER JANUS-GESAMTTEST ERFORDERLICH

Bitte teste jetzt das vollstÃ¤ndig umgesetzte Feature direkt in Janus.

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
- Manual Janus Test Evidence: <User-bestÃ¤tigter manueller Janus-Gesamttest nach Skill 4>
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
â†’ Der Skill-6-Handover darf erst nach erfolgreichem manuellem Janus-Test ausgegeben werden.
â†’ Nach User-Antwort `Manueller Test erfolgreich.` MUSS Skill 4 den Skill-6-Handover als einzelnen grauen Copy-Block ausgeben.
â†’ Nach User-Antwort `Es funktioniert nicht wie gewÃ¼nscht.` MUSS Skill 4 zuerst eine konkrete Fehlerbeschreibung einsammeln und danach den Skill-5-Handover als einzelnen grauen Copy-Block ausgeben.
â†’ Skill 4 darf in beiden FÃ¤llen keine weitere Implementation starten.

Manual Janus Test Gate:

```text
MANUELLER JANUS-TEST ERFORDERLICH

Bitte teste jetzt die Ã„nderung direkt in Janus.

Option 1:
Manueller Test erfolgreich.

Antwort dann exakt:
Manueller Test erfolgreich.

Option 2:
Es funktioniert nicht wie gewÃ¼nscht.

Antwort dann mit kurzer Fehlerbeschreibung:
- Was hast du in Janus getan?
- Was hast du erwartet?
- Was ist tatsÃ¤chlich passiert?
- Screenshot/Log/Output, falls vorhanden.
```

HANDOVER-GENERATION-GATE:

- Die folgenden Skill-6- und Skill-5-Copy-Paste-Prompts sind NUR bedingte Templates.
- Skill 4 darf sie NICHT automatisch zusammen mit `ALL TASKS COMPLETE` ausgeben.
- Skill 4 darf den Skill-6-Audit-Chat-Prompt NUR ausgeben, wenn die unmittelbar vorherige User-Antwort exakt oder sinngemÃ¤ÃŸ `Manueller Test erfolgreich.` bestÃ¤tigt.
- Skill 4 darf den Skill-5-Debug-Prompt NUR ausgeben, nachdem der User eine Fehlerbeschreibung fÃ¼r den manuellen Janus-Gesamttest geliefert hat.
- Wenn noch keine User-Antwort auf das Manual Janus Test Gate vorliegt, MUSS Skill 4 mit dem Manual-Test-Gate enden.

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

Manual Janus Test Evidence:
- Status: PRESENT
- Source: Skill 4 Manual Janus Validation Gate
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
