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
â†’ Nutzer informieren:
   "TASK-XXX.Y wurde mit <Assigned Model> abgeschlossen. Starte den nÃ¤chsten Pipeline-Schritt manuell."
â†’ Wenn Code oder Tests geÃ¤ndert wurden und die Task-Validierung PASS ist: zuerst `/save` ausfÃ¼hren.
â†’ Wenn weitere Tasks vorhanden sind, starte Skill 3 fÃ¼r den nÃ¤chsten Target Task mit dessen zugewiesenem Modell.
â†’ Wenn keine weiteren Tasks vorhanden sind: NICHT im aktuellen Chat auditieren.
â†’ Nutzer explizit informieren:
   "Öffne für Skill 5 einen NEUEN Chat mit GPT-5.5 und kopiere nur das folgende Compact Audit Handover hinein."
â†’ Skill 4 MUSS dafür ein vollständiges Copy-Paste-Handover ausgeben.

Atomic Save Gate:
```text
/save
```

Regel:
- `/save` erst nach erfolgreicher Task-Validierung ausfÃ¼hren.
- `/save` nicht ausfÃ¼hren, wenn Tests fehlschlagen oder Skill 4 `TASK EXECUTION FAILED` meldet.
- Erst nach erfolgreichem `/save` den nÃ¤chsten Skill starten.

Compact Audit Package fÃ¼r Skill 5:
- Spec: <source spec file>
- Task: <task file>
- Pre-Check: <PRE-CHECK PASSED summary/result>
- Changed Files: <Liste der tatsÃ¤chlich geÃ¤nderten Dateien>
- Relevant Diff / Excerpts: <kurze relevante AuszÃ¼ge oder Diff-Zusammenfassung>
- Test Results: <ausgefÃ¼hrte Tests und Ergebnis>
- Known Risks: <bekannte Risiken, Scope-Hinweise, unrelated Workspace Changes>

Audit-Chat-Regel:
â†’ Skill 5 SOLL in einem neuen Chat mit GPT-5.5 ausgeführt werden.
â†’ Der aktuelle Skill-4-Chat darf nicht als Audit-Kontext verwendet werden.
â†’ Skill 5 darf nur aus dem Compact Audit Package auditieren.
â†’ Kein vollständiger Chatverlauf, keine Debug-Diskussionen, keine Nebeninformationen kopieren.

Skill-5-Dateiliste:
- <source spec file>
- <task file>
- <jede tatsÃ¤chlich geÃ¤nderte Datei>
- <optional: Testdateien / Diffdatei / Testoutput-Datei, falls vorhanden>

Copy-Paste-Prompt fÃ¼r neuen GPT-5.5 Skill-5-Chat:
BEGIN COPY
```text
/Skill 5 â€“ Diamantstandard Final Audit

WICHTIG:
- Dies ist ein neuer Audit-Chat mit GPT-5.5.
- Nutze ausschließlich dieses Compact Audit Package.
- Ignoriere jeden früheren Chatverlauf und alle nicht genannten Dateien.
- Erfinde keine zusätzlichen Anforderungen.

Compact Audit Package:

Feature:
<Feature-Name>

Spec:
<source spec file>

Task:
<task file>

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

Known Risks:
- <bekannte Risiken>
- <unrelated Workspace Changes, falls vorhanden>

Audit Scope:
Bitte nur diesen Task und die oben genannten Dateien prÃ¼fen.
Alle anderen Workspace-Ã„nderungen sind out of scope.
```
END COPY

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
