---
description: SWE 1.6 Diamantstandard Phase 3 â€“ Pre-Implementation Verification Gate. Validiert Task-Files aus Skill 2 vor AusfÃ¼hrung durch Skill 4. PrÃ¼ft Impact-Analyse, Konsistenz, Risiken und Execution Readiness. Keine Implementierung erlaubt.
---

## ðŸŽ¯ PURPOSE

Dieser Skill ist ein **harte QualitÃ¤ts- und Sicherheits-Gate** vor der Code-AusfÃ¼hrung.

Er entscheidet ausschlieÃŸlich:

â†’ IST DER TASK AUSFÃœHRBAR ODER BLOCKIERT?

KEINE IMPLEMENTATION. KEIN CODE. KEINE PLANUNG.

---

## ðŸ“¥ INPUT

- TASK-ID oder TASK-Datei aus `documentation/tasks/`
- vollstÃ¤ndiger Task-Inhalt
- optional: Feature Spec als Referenz
- optional: Backlog-Referenz aus `documentation/backlog/BACKLOG.md`, wenn die Task-Datei durch `BACKLOG SKILL 3 – EXECUTION HANDOFF` erzeugt wurde
- bei Task-Dateien mit mehreren Tasks: exakt eine Target Task ID

---

## ðŸ“Œ AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer eine Task-Datei und optional eine Spec-Datei nennt, sind diese Artefakte automatisch die verbindlichen PrÃ¼fquellen.

Der Skill MUSS dann:

- die genannte Task-Datei vollstÃ¤ndig lesen
- die genannte Spec-Datei als Referenz lesen, falls angegeben
- die Backlog-Referenz lesen, falls die Task-Datei aus einem `BACKLOG-XXX` Handoff stammt
- bei mehreren Tasks in einer Datei exakt die vom User genannte Target Task isolieren
- die AusfÃ¼hrbarkeit ausschlieÃŸlich gegen Task-Inhalt, Spec-Referenz und realen Codebase-Kontext validieren
- Chatverlauf, frÃ¼here Diskussionen und zusÃ¤tzliche mÃ¼ndliche Nebeninformationen ignorieren, sofern sie den Artefakten widersprechen oder Ã¼ber sie hinausgehen
- keine Requirements, Produktentscheidungen oder Architekturentscheidungen aus dem Chatkontext ergÃ¤nzen
- bei unklarer Task-/Spec-Konsistenz blockieren statt interpretieren
- keine anderen Tasks aus derselben Datei validieren oder fÃ¼r Skill 4 freigeben

Minimaler gÃ¼ltiger User-Aufruf:

```text
/SKILL 3 â€“ PRE-IMPLEMENTATION VERIFICATION mit folgenden Artefakten:
Target Task: TASK-XXX.Y
Spec: documentation/Planned Features/<FEATURE_NAME>.md
Task: documentation/tasks/<TASK_FILE>.md
```

Wenn eine Datei nicht lesbar ist, der Task nicht eindeutig aus Skill 2 oder `BACKLOG SKILL 3 – EXECUTION HANDOFF` stammt oder bei mehreren Tasks keine Target Task ID genannt wurde:

```text
PRE-CHECK ARTIFACTS INVALID

Issue:
- <konkretes Problem>

Action:
â†’ korrekte Artefakte angeben, Skill 2 erneut artefaktbasiert ausfÃ¼hren oder `BACKLOG SKILL 3 – EXECUTION HANDOFF` erneut ausfÃ¼hren
```

---

## ðŸ§© SINGLE-TASK VALIDATION GATE (HARD PROTOCOL)

Skill 3 validiert immer genau einen Task.

Wenn die Task-Datei mehrere Tasks enthÃ¤lt:

- Target Task ID ist Pflicht
- nur dieser Target Task darf geprÃ¼ft werden
- andere Tasks dÃ¼rfen nicht validiert, verÃ¤ndert, zusammengefasst oder freigegeben werden
- das im Target Task festgeschriebene Modell muss im Output genannt werden

Wenn die Target Task ID fehlt:

```text
PRE-CHECK ARTIFACTS INVALID

Issue:
- Multiple tasks found but no Target Task ID was provided.

Action:
â†’ Skill 3 erneut mit exakt einer Target Task ID starten.
```

---

## âš™ï¸ EXECUTION FLOW

---

### 1. LOAD TASK

- Task vollstÃ¤ndig laden
- Struktur parsen
- alle Sections extrahieren

---

### 2. IMPACT-ANALYSE VALIDATION (HARD REQUIREMENT)

Section 2 MUSS enthalten:

- **Basiert auf** â†’ nicht leer
- **Beeinflusst** â†’ nicht leer
- **Risiko-EinschÃ¤tzung** â†’ MUSS sein:
  - LOW
  - MEDIUM
  - HIGH

---

### 3. FORMAL AUTO-FIX (LIMITED SCOPE ONLY)

Erlaubt:

- "Basiert auf" fehlt â†’ aus `source_spec` ableiten
- "Beeinflusst" fehlt â†’ aus Codebase/Task Kontext extrahieren
- "Risiko" fehlt â†’ aus Risk Register ableiten
- Formatkorrekturen (nur strukturell)
- Normalisierung (DE â†’ EN LOW/MEDIUM/HIGH)

âŒ NICHT ERLAUBT:
- neue Features
- neue Architektur
- neue Tasks
- Scope-Erweiterung
- Interpretation auÃŸerhalb Task

---

### 4. CONSISTENCY CHECK

PrÃ¼fe:

- Task logisch konsistent
- keine widersprÃ¼chlichen Anforderungen
- Dependencies realistisch
- Files existieren im Projektkontext
- Ziel eindeutig

---

### 5. EXECUTION READINESS CHECK

Task MUSS erfÃ¼llen:

- atomar (1 Ziel)
- implementierbar ohne Designentscheidungen
- klare Acceptance Criteria
- keine offenen Architekturfragen
- deterministisch ausfÃ¼hrbar

---

## ðŸš¨ MODEL SWITCH RULE (HARD PROTOCOL)

Wenn:

- Task nicht deterministisch validierbar ist
- Struktur inkonsistent ist
- Scope nicht sicher interpretierbar ist
- mehrere plausible Bedeutungen existieren
- Auto-Fix nicht ausreicht

âž¡ STOP EXECUTION

```text id="model_switch_skill3"
MODEL SWITCH REQUIRED: SWE 1.6 â†’ GPT-5.5

Reason:
- <konkrete Ursache: ambiguity / inconsistent structure / non-deterministic validation>

Action:
â†’ neuer Chat starten
â†’ Skill 3 erneut mit GPT-5.5 ausfÃ¼hren
ðŸ“¤ OUTPUT STATES
âœ… PRE-CHECK PASSED
PRE-CHECK PASSED

Task: TASK-XXX

Zusammenfassung:
- Ziel: <kurz>
- Risiko: LOW | MEDIUM | HIGH
- Files: <liste>
- Assigned Model: <SWE 1.6 | Kimi k2.5>

Status:
Implementierung darf nur fÃ¼r diesen Target Task Ã¼ber Skill 4 fortgesetzt werden.

NÃ¤chster Schritt:
â†’ Starte Skill 4 mit dem zugewiesenen Modell:
   Target Task: TASK-XXX.Y
   Assigned Model: <SWE 1.6 | Kimi k2.5>
   Spec: documentation/Planned Features/<FEATURE_NAME>.md
   Task: documentation/tasks/<TASK_FILE>.md
   Pre-Check: this PRE-CHECK PASSED result

Skill-4-Dateiliste:
- documentation/Planned Features/<FEATURE_NAME>.md
- documentation/tasks/<TASK_FILE>.md
- <alle im Pre-Check validierten Dateien>

Copy-Paste-Prompt fÃ¼r Skill 4:
```text
/SKILL 4 â€“ EXECUTIONER mit folgenden Artefakten:
Target Task: TASK-XXX.Y
Assigned Model: <SWE 1.6 | Kimi k2.5>
Spec: documentation/Planned Features/<FEATURE_NAME>.md
Task: documentation/tasks/<TASK_FILE>.md
Pre-Check:
PRE-CHECK PASSED
Task: TASK-XXX.Y
Ziel: <kurz>
Risiko: LOW | MEDIUM | HIGH
Files: <liste>
Assigned Model: <SWE 1.6 | Kimi k2.5>

Scope-Regel:
Implementiere ausschlieÃŸlich diesen Target Task.
Validiere oder implementiere keine spÃ¤teren Tasks automatisch.
```

Stop-Regel:
â†’ FÃ¼hre keinen spÃ¤teren Task im selben Lauf aus.
âš ï¸ AUTO-FIX APPLIED
PRE-CHECK AUTO-FIX APPLIED

Changes:
- <konkrete Fixes>

Result:
- Task now structurally valid

Action:
â†’ Re-run Skill 3 validation
âŒ PRE-CHECK FAILED
PRE-CHECK FAILED

Missing Fields:
- Basiert auf
- Beeinflusst
- Risiko-EinschÃ¤tzung

Reason:
- Task not execution-ready

Action:
â†’ Fix in Skill 2 required
ðŸš« PRE-CHECK BLOCKED
PRE-CHECK BLOCKED

Reason:
- inconsistent or non-inferable Task structure

No safe execution path available.
ðŸš« RESTRICTIONS
KEINE CodeausfÃ¼hrung
KEINE Implementation
KEINE Architekturentscheidungen
KEINE Scope-Erweiterung
KEINE Task-Neuerfindung
ðŸ§  ERROR HANDLING

Wenn Task nicht lesbar:

PRE-CHECK FAILED: Task file not accessible
ðŸ§  OUTPUT GUARANTEE

Output ist immer:

deterministic
validation-only
non-executing
safe-before-run gate
