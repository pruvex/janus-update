---
description: Diamantstandard Phase 2 â€“ Task Designer. Verfeinert Tasks aus Skill 1 zu vollstÃ¤ndig ausfÃ¼hrbaren, konsistenten, atomaren Implementationsaufgaben fÃ¼r Skill 3. Keine Code-Implementation.
---

## ðŸŽ¯ PURPOSE

Dieser Skill nimmt **roh generierte Tasks aus Skill 1** und macht sie:

â†’ vollstÃ¤ndig ausfÃ¼hrbar  
â†’ eindeutig spezifiziert  
â†’ implementierungsbereit fÃ¼r Skill 3  

KEINE ARCHITEKTURENTSCHEIDUNGEN. KEIN CODE. KEINE NEUEN FEATURES.

---

## ðŸ“ INPUT

- TASK-Liste aus Skill 1
- Feature Spec (Referenz)
- optional: Codebase Kontext (nur lesend)

---

## ðŸ“Š AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer eine Task-Datei und eine Spec-Datei nennt, sind diese Dateien automatisch die **einzigen Requirements-Quellen**.

Der Skill MUSS dann:

- die genannte Task-Datei aus Skill 1 lesen
- die genannte Spec-Datei als verbindliche Referenz lesen
- Tasks ausschlieÃŸlich gegen diese Spec validieren und verfeinern
- Chatverlauf, frÃ¼here Diskussionen und zusÃ¤tzliche mÃ¼ndliche Nebeninformationen ignorieren, sofern sie den Artefakten widersprechen oder Ã¼ber sie hinausgehen
- keine neuen Requirements, Produktentscheidungen oder Architekturentscheidungen aus dem Chatkontext ergÃ¤nzen
- keine alten Task-EntwÃ¼rfe, Blocking-Question-Historie oder externe Notizen als Requirements verwenden

Minimaler gÃ¼ltiger User-Aufruf:

```text
/SKILL 2 â€“ TASK BREAKDOWN ENGINE mit folgenden Artefakten:
Spec: documentation/Planned Features/<FEATURE_NAME>.md
Tasks: documentation/tasks/<TASK_FILE>.md
```

Wenn eine Datei nicht lesbar ist, die Spec keine finale Janus Feature Spec enthÃ¤lt oder die Task-Datei nicht eindeutig aus Skill 1 stammt:

```text
TASK ARTIFACTS INVALID

Issue:
- <konkretes Problem>

Action:
â†’ korrekte Spec- und Task-Dateien angeben oder Skill 1 erneut artefaktbasiert ausfÃ¼hren
```

---

## ðŸ”„ EXECUTION FLOW

---

## ðŸŒ OUTPUT LANGUAGE

Alle user-facing Zusammenfassungen, Bewertungen, Task-Titel, Zielbeschreibungen, Acceptance Criteria, Next Steps und Fehlermeldungen MÃœSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Klassennamen, Funktionsnamen und Modellnamen bleiben unverÃ¤ndert.

---

### 1. TASK VALIDATION

FÃ¼r jeden Task prÃ¼fen:

- Ist Ziel eindeutig?
- Ist Scope klar begrenzt?
- Sind Files realistisch existierend?
- Sind Acceptance Criteria testbar?

Wenn NICHT:

â†’ Task muss repariert werden (nur innerhalb Spec!)

---

### 1.1 EXECUTION TASK ELIGIBILITY VALIDATION (HARD GATE)

Skill 2 MUSS prÃ¼fen, ob jeder Skill-1-Task ein echter Execution Task ist.

Verbotene eigenstÃ¤ndige Task-Typen:

- reine Analyse-Tasks
- reine Design-Tasks
- reine Recherche-Tasks
- reine Review-Tasks
- reine Verify-Tasks
- reine Non-Regression-Tasks
- reine Dokumentations-/Spec-Markierungs-Tasks
- Tasks, deren einziger Output "verstanden", "geprÃ¼ft", "bestÃ¤tigt" oder "designed" ist

Solche Tasks dÃ¼rfen NICHT an Skill 3/4 weitergegeben werden.

Skill 2 MUSS sie stattdessen:

- als Steps in passende Implementierungs- oder Testtasks integrieren
- als Acceptance Criteria Ã¼bernehmen
- als Testanforderungen Ã¼bernehmen
- als Skill-3-Precheck-PrÃ¼fpunkte markieren
- oder entfernen, wenn sie auÃŸerhalb der Spec liegen

Wenn Skill 1 ausschlieÃŸlich Prozess-Tasks erzeugt hat und keine echte Implementierungs-/Testaufgabe ableitbar ist:

```text
TASK DESIGN BLOCKED

Reason:
- Keine echten Execution Tasks vorhanden.

Action:
â†’ Skill 1 erneut mit gehÃ¤rteter Task-Decomposition ausfÃ¼hren oder Spec prÃ¼fen.
```

---

### 2. TASK REFINEMENT

Jeder Task wird transformiert zu:

- atomar (1 Ziel = 1 Task)
- implementierbar ohne Designentscheidungen
- testbar
- deterministisch ausfÃ¼hrbar
- frei von eigenstÃ¤ndigen Analyse-/Design-/Verify-only Tasks

Refinement-Regel:

- Analyse gehÃ¶rt in Steps.
- Design gehÃ¶rt in Steps oder Acceptance Criteria.
- Verify gehÃ¶rt in Acceptance Criteria oder Tests.
- Non-Regression gehÃ¶rt in Tests oder Acceptance Criteria.
- Dokumentationsupdate gehÃ¶rt nicht in die Implementation Chain, auÃŸer die Spec fordert Dokumentation ausdrÃ¼cklich als Feature-Verhalten.

---

### 3. FILE & SCOPE NORMALIZATION

PrÃ¼fe:

- existieren referenzierte Dateien logisch im System?
- sind Pfade konsistent?
- sind Module korrekt benannt?

Falls unklar:

â†’ KEINE Erfindung
â†’ Task muss reduziert oder eskaliert werden

---

### 3.1 TESTSPEC-/ORACLE SOURCE-OF-TRUTH GATE (HARD)

Wenn ein Task eine TestSpec-, Test-Oracle-, Assertion-, `containsAny`-, `mustNotContain`-,
Response-Format- oder Erwartungswert-Anpassung betrifft, MUSS Skill 2 vor der Freigabe
pruefen, welches Artefakt die dauerhafte Quelle ist.

Pflichtregeln:

- `documentation/TEST_SPEC/*.md` ist die Source of Truth fuer Test-Oracle-Aenderungen.
- `documentation/test-runs/*_plan.json` ist ein generiertes Artefakt und darf bei Oracle-Fixes
  nur als Evidence/Baseline/Referenz verwendet werden.
- Skill 2 darf keinen Target Task freigeben, dessen einziger `Files`-Scope ein alter
  `documentation/test-runs/*_plan.json` ist.
- Wenn die Task-Datei oder Skill-1-Ausgabe nur einen alten TestPlan patchen will, MUSS Skill 2
  den Task korrigieren: Primary File = passende `documentation/TEST_SPEC/*.md`, alter TestPlan =
  `Reference/Baseline Plan`.
- Acceptance Criteria muessen enthalten, dass nach der TestSpec-Aenderung ein frischer TestPlan
  durch `TEST SKILL 1 - TESTSPEC TO TEST PLAN` erzeugt wird.
- Skill 2 darf `TEST-RUN-..._plan.json` nicht als alleinige Implementierungsdatei fuer einen
  Oracle-Fix an Skill 3 weitergeben.

BLOCKED-Ausgabe, wenn die Source-of-Truth-TestSpec nicht sicher bestimmbar ist:

```text
TASK DESIGN BLOCKED

Reason:
- Test-Oracle-Fix wuerde nur ein generiertes TestPlan-Artefakt patchen.
- Source-of-Truth TestSpec ist nicht eindeutig.

Required Fix:
→ Source TestSpec bestimmen und Task so verfeinern, dass documentation/TEST_SPEC/<...>.md
  die Primary File ist; alter TestPlan nur als Reference Plan verwenden.
```

---

### 4. TEST ENRICHMENT

Falls Tests fehlen:

- Unit Tests verpflichtend fÃ¼r Logik
- Integration Tests bei Multi-Module Verhalten
- E2E nur wenn User Flow existiert

KEINE OVERTESTING-ERWEITERUNG

---

### 5. MODEL ASSIGNMENT VALIDATION

Ãœbernehme Modell aus Skill 1, aber prÃ¼fe:

- ist SWE 1.6 ausreichend?
- ist Kimi k2.5 nur fÃ¼r deterministische Single-File-, Daten-, String- oder Test-Tasks verwendet?
- wird GPT-5.5 ausschlieÃŸlich als Eskalations-/Auditmodell behandelt?

KEINE freie Modellwahl

---

### 6. SINGLE-TASK HANDOFF GATE (HARD PROTOCOL)

Skill 2 darf nach der Task-Verfeinerung NIEMALS eine vollstÃ¤ndige Task-Kette zur automatischen AusfÃ¼hrung freigeben.

Wenn mehrere Tasks existieren:

- bestimme den ersten noch nicht erledigten Task in der Execution Chain
- gib nur diesen einen Task als nÃ¤chsten ausfÃ¼hrbaren Task frei
- nenne exakt das im Task festgeschriebene Modell
- gib keine Freigabe fÃ¼r spÃ¤tere Tasks
- fordere nach Abschluss dieses Tasks eine erneute Skill-2- oder Skill-3-Ãœbergabe fÃ¼r den nÃ¤chsten Task

Bei gemischten Modellzuweisungen gilt:

- ein SWE-1.6-Lauf darf keine Kimi-k2.5-Tasks ausfÃ¼hren
- ein Kimi-k2.5-Lauf darf keine SWE-1.6-Tasks ausfÃ¼hren
- jeder Task muss einzeln durch Skill 3 validiert und einzeln durch Skill 4 ausgefÃ¼hrt werden
- nach jedem abgeschlossenen Task MUSS die Pipeline stoppen und den User Ã¼ber den nÃ¤chsten Task und das dafÃ¼r festgelegte Modell informieren

Der Next Step von Skill 2 MUSS deshalb immer auf genau einen Ziel-Task zeigen:

```text
Next Step:
â†’ Run Skill 3 for exactly one task:
   Target Task: TASK-XXX.Y
   Assigned Model: <SWE 1.6 | Kimi k2.5>
   Spec: documentation/Planned Features/<FEATURE_NAME>.md
   Tasks: documentation/tasks/<TASK_FILE>.md

Stop Rule:
â†’ Do not validate or execute TASK-XXX.(Y+1) in the same run.
```

COPY-PASTE HANDOVER FÃœR SKILL 3 (PFLICHT):

Am Ende der Antwort MUSS zusÃ¤tzlich ein einzelner grauer Copy-Block ausgegeben werden.
Dieser Block MUSS direkt kopierbar sein und darf keine ErklÃ¤rung auÃŸerhalb des Blocks benÃ¶tigen.

Bei Backlog-Tasks oder Subtask-Breakdowns ist ein minimalistischer Skill-3-Handover ungueltig.
Der Copyblock MUSS enthalten: `Spec`, `Task`, `Backlog Item`, `Target Task`, optional
`Target Subtask`, `Mode`, `Execution Model`, `Context`, `Rules` und `Expected Output`.

Verboten als finaler Skill-3-Handover:

```text
@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]
Spec: <path>
Task: <path>
Execution Model: SWE 1.6
Target Subtask: <id>
```

Ein solcher Kurzblock muss durch den vollstaendigen Copyblock unten ersetzt werden.

```text
@[/SKILL 3 â€“ PRE-IMPLEMENTATION VERIFICATION] mit folgendem Target Task:
Spec: <source spec file>
Task: <task file>
Backlog Item: <BACKLOG-XXX | N/A>
Target Task: <TASK-XXX.Y>
Target Subtask: <SUBTASK-XXX-YY | N/A>
Mode: SINGLE_TASK_PRECHECK
Execution Model: <SWE 1.6 | Kimi k2.5>

Kontext:
- Skill-2 Ergebnis: TASK DESIGN COMPLETE
- Readiness: READY FOR SKILL 3 SINGLE-TASK PRE-CHECK
- Backlog Item: <BACKLOG-XXX | N/A>
- Target Task: <TASK-XXX.Y>
- Target Subtask: <SUBTASK-XXX-YY | N/A>
- Assigned Model: <SWE 1.6 | Kimi k2.5>
- Source Spec File: <source spec file>
- Task File: <task file>

Arbeitsregel:
- Nutze die genannte Spec-Datei und Task-Datei als verbindliche Artefakte.
- Validere ausschlieÃŸlich den genannten Target Task.
- Ignoriere widersprÃ¼chliche oder zusÃ¤tzliche Chat-Kontexte.
- Erzeuge keine Implementation.
- Validere Pre-Implementation-Readiness, Scope, Dateien, Tests und Risiken fÃ¼r genau diesen Task.
- Gib keine Freigabe fÃ¼r spÃ¤tere Tasks.

Stop Rule:
- Nur dieser Target Task darf validiert werden.
- SpÃ¤tere Tasks benÃ¶tigen einen separaten user-triggered Handover.
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_SKILL_4_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR

NÃ¤chster erwarteter Output:
- Pre-Implementation Verification fÃ¼r genau diesen Target Task
- Eindeutiger Handover zu SKILL 4 â€“ EXECUTIONER bei PASS
- BLOCKED oder MODEL SWITCH REQUIRED bei fehlender AusfÃ¼hrungsreife
Expected Output: PRE_CHECK_PASSED_PLUS_SKILL_4_HANDOFF_OR_PRE_CHECK_BLOCKED
```

Der Copy-Block ist PFLICHT, auch wenn davor bereits eine normale Zusammenfassung ausgegeben wurde.

---

## ðŸš¨ MODEL SWITCH RULE (HARD PROTOCOL)

Wenn Task nicht eindeutig refinierbar ist:

- unklare Anforderungen
- fehlende Scope-Grenzen
- mehrere mÃ¶gliche Implementationen
- Codebase Inkonsistenz

â†’ STOP EXECUTION

```text id="model_switch_skill2"
MODEL SWITCH REQUIRED: SWE 1.6 â†’ GPT-5.5

Reason:
- <konkrete Ursache: ambiguity / missing constraints / multi interpretation>

Action:
â†’ neuer Chat starten
â†’ Skill 2 erneut mit GPT-5.5 ausfÃ¼hren
ðŸ“ OUTPUT FORMAT
TASK DESIGN COMPLETE

Task ID: TASK-XXX

Final Definition:
- TASK-XXX.Y: <deutscher Task-Titel>
  Ziel: <klarer Satz>
  Scope: <exakt begrenzt>
  Files: <konkret>
  Steps: <implementierbar>
  Acceptance Criteria: <testbar>
  Tests: Unit | Integration | E2E (falls nÃ¶tig)
  Model: <SWE 1.6 | Kimi k2.5>
  Reason: <kurze BegrÃ¼ndung>

Model:
- SWE 1.6 | Kimi k2.5

Readiness:
â†’ READY FOR SKILL 3 SINGLE-TASK PRE-CHECK

Next Step:
â†’ Run Skill 3 for exactly one task:
   Target Task: TASK-XXX.Y
   Assigned Model: <SWE 1.6 | Kimi k2.5>
   Spec: documentation/Planned Features/<FEATURE_NAME>.md
   Tasks: documentation/tasks/<TASK_FILE>.md

Stop Rule:
â†’ Only this Target Task may be validated next.
â†’ Later tasks require a separate user-triggered handoff.

COPY-PASTE HANDOVER FÃœR SKILL 3 (PFLICHT):

Am Ende der Antwort MUSS zusÃ¤tzlich ein einzelner grauer Copy-Block ausgegeben werden.
Dieser Block MUSS direkt kopierbar sein und darf keine ErklÃ¤rung auÃŸerhalb des Blocks benÃ¶tigen.

```text
@[/SKILL 3 â€“ PRE-IMPLEMENTATION VERIFICATION] mit folgendem Target Task:
Spec: <source spec file>
Task: <task file>
Backlog Item: <BACKLOG-XXX | N/A>
Target Task: <TASK-XXX.Y>
Target Subtask: <SUBTASK-XXX-YY | N/A>
Mode: SINGLE_TASK_PRECHECK
Execution Model: <SWE 1.6 | Kimi k2.5>

Kontext:
- Skill-2 Ergebnis: TASK DESIGN COMPLETE
- Readiness: READY FOR SKILL 3 SINGLE-TASK PRE-CHECK
- Backlog Item: <BACKLOG-XXX | N/A>
- Target Task: <TASK-XXX.Y>
- Target Subtask: <SUBTASK-XXX-YY | N/A>
- Assigned Model: <SWE 1.6 | Kimi k2.5>
- Source Spec File: <source spec file>
- Task File: <task file>

Arbeitsregel:
- Nutze die genannte Spec-Datei und Task-Datei als verbindliche Artefakte.
- Validere ausschlieÃŸlich den genannten Target Task.
- Ignoriere widersprÃ¼chliche oder zusÃ¤tzliche Chat-Kontexte.
- Erzeuge keine Implementation.
- Validere Pre-Implementation-Readiness, Scope, Dateien, Tests und Risiken fÃ¼r genau diesen Task.
- Gib keine Freigabe fÃ¼r spÃ¤tere Tasks.

Stop Rule:
- Nur dieser Target Task darf validiert werden.
- SpÃ¤tere Tasks benÃ¶tigen einen separaten user-triggered Handover.
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_SKILL_4_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR

NÃ¤chster erwarteter Output:
- Pre-Implementation Verification fÃ¼r genau diesen Target Task
- Eindeutiger Handover zu SKILL 4 â€“ EXECUTIONER bei PASS
- BLOCKED oder MODEL SWITCH REQUIRED bei fehlender AusfÃ¼hrungsreife
Expected Output: PRE_CHECK_PASSED_PLUS_SKILL_4_HANDOFF_OR_PRE_CHECK_BLOCKED
```

Der Copy-Block ist PFLICHT, auch wenn davor bereits eine normale Zusammenfassung ausgegeben wurde.
ðŸš« RESTRICTIONS

STRICT PROVIDER ISOLATION: Janus ist ein BYOK-Tool. Implementiere oder erlaube NIEMALS automatische Provider-Fallbacks (z.B. Gemini zu GPT) im Produktcode. Wenn ein Provider-spezifischer Test (z.B. Gemini) fehlschlÃ¤gt, muss er als Fehler dieses Providers behandelt werden. Ein Ausweichen auf einen anderen Provider zur Fehlerumgehung ist STRENG VERBOTEN.

KEINE Codegenerierung
KEINE ArchitekturÃ¤nderungen
KEINE neuen Features
KEINE Scope-Erweiterung
KEINE Designentscheidungen
ðŸš¨ ERROR HANDLING

Wenn Task nicht sinnvoll refinebar:

TASK AMBIGUOUS â€“ NEED SPEC CLARIFICATION

Issue:
- <konkretes Problem>

Action:
â†’ Skill 1 erneut ausfÃ¼hren oder GPT-5.5 Escalation
ðŸš¨ OUTPUT GUARANTEE

Output ist immer:

execution-ready
deterministic
strictly scoped
implementation-safe
