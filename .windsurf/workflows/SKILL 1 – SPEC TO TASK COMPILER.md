---
description: SWE 1.6 Diamantstandard Phase 1 â€“ Spec â†’ Task Compiler. Zerlegt eine Feature-Spec deterministisch in ausfÃ¼hrbare, atomare Task-Files fÃ¼r Janus. Keine Architekturentscheidungen, keine Implementation.
---

# SKILL 1 – SPEC TO TASK COMPILER

## ðŸŽ¯ PURPOSE

Dieser Skill transformiert eine **Feature-Spec (Janus Diamantstandard)** in eine **deterministische Task-Struktur**.

Er erzeugt:
â†’ klare, atomare, ausfÃ¼hrbare Tasks fÃ¼r Skill 2â€“3

KEINE CODE-IMPLEMENTATION. KEINE ARCHITEKTUR. KEINE FREIEN ENTSCHEIDUNGEN.

---

## ðŸ“¥ INPUT

- Feature Spec (MD Datei oder Text)
- Zielsystem: Janus Codebase Kontext
- optional: bestehende Module / Registry

---

## ðŸ“Œ AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer eine Spec-Datei nennt, ist diese Datei automatisch die **Single Source of Truth**.

Der Skill MUSS dann:

- die genannte Spec-Datei lesen
- ausschlieÃŸlich die finale Spec in dieser Datei als Feature-Grundlage verwenden
- Chatverlauf, frÃ¼here Diskussionen und zusÃ¤tzliche mÃ¼ndliche Nebeninformationen ignorieren, sofern sie der Spec widersprechen oder Ã¼ber sie hinausgehen
- keine Produktentscheidungen aus dem Chatkontext ergÃ¤nzen
- keine Blocking-Question-Historie, alte EntwÃ¼rfe oder externe Notizen als Requirements verwenden

Minimaler gÃ¼ltiger User-Aufruf:

```text
/SKILL 1 â€“ SPEC TO TASK COMPILER mit folgender Spec-Datei:
documentation/Planned Features/<FEATURE_NAME>.md
```

Wenn die Datei nicht lesbar ist oder keine finale Janus Feature Spec enthÃ¤lt:

```text
SPEC FILE INVALID

Issue:
- <konkretes Problem>

Action:
â†’ korrekte Spec-Datei angeben oder finale Spec erneut speichern
```

---

## âš™ï¸ EXECUTION FLOW

---

## ðŸŒ OUTPUT LANGUAGE

Alle user-facing Zusammenfassungen, Bewertungen, Task-Titel, Zielbeschreibungen, Acceptance Criteria, Next Steps und Fehlermeldungen MÃœSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Klassennamen, Funktionsnamen und Modellnamen bleiben unverÃ¤ndert.

---

### 1. SPEC PARSING

Analysiere:

- Feature Name
- Core Idea
- Functional Requirements
- System Behavior
- Constraints
- Test Requirements

Extrahiere nur explizite Informationen.

âŒ Keine Interpretation
âŒ Keine ErgÃ¤nzungen

---

### 2. TASK DECOMPOSITION

Zerlege Spec in:

- atomare Tasks (1 Task = 1 Ziel)
- logisch sequenziell ausfÃ¼hrbar
- ohne AbhÃ¤ngigkeiten, die Designentscheidungen erfordern
- echte Execution Tasks, die in Skill 4 zu einer konkreten Ã„nderung, einem konkreten Test oder einer konkreten validierbaren Anpassung fÃ¼hren

Jeder Task MUSS enthalten:

- eindeutiges Ziel
- betroffene Dateien (falls bekannt)
- klare Output-Erwartung
- Acceptance Criteria
- Testanforderung

---

### 2.1 EXECUTION TASK ELIGIBILITY (HARD GATE)

Skill 1 darf KEINE eigenstÃ¤ndigen Execution Tasks erzeugen, die nur aus Prozessarbeit bestehen.

Verbotene eigenstÃ¤ndige Task-Typen:

- reine Analyse-Tasks
- reine Design-Tasks
- reine Recherche-Tasks
- reine Review-Tasks
- reine Verify-Tasks
- reine Non-Regression-Tasks
- reine Dokumentations-/Spec-Markierungs-Tasks
- Tasks, deren einziger Output "verstanden", "geprÃ¼ft", "bestÃ¤tigt" oder "designed" ist

Diese Inhalte MÃœSSEN stattdessen integriert werden als:

- Steps innerhalb eines Implementierungs- oder Testtasks
- Acceptance Criteria
- Testanforderungen
- Skill-3-Precheck-PrÃ¼fpunkte

Ein gÃ¼ltiger Execution Task MUSS mindestens eines erzeugen:

- CodeÃ¤nderung in konkret benannter Datei
- TestÃ¤nderung in konkret benannter Testdatei
- Konfigurations-/DatenÃ¤nderung, falls explizit von der Spec erlaubt
- validierbare DokumentationsÃ¤nderung nur dann, wenn die Spec ausdrÃ¼cklich Dokumentation als Feature-Scope fordert

Wenn nach Anwendung dieser Regel nur Analyse/Design/Verify Ã¼brig bleibt:

```text
NO EXECUTION TASKS GENERATED

Reason:
- Die Spec erfordert keine implementierbare Ã„nderung.

Action:
â†’ Spec prÃ¼fen oder als Dokumentations-/Audit-Thema auÃŸerhalb der Implementierung behandeln.
```

---

### 3. MODEL ANNOTATION

Jedem Task wird ein Standard-Execution Model zugewiesen:

- SWE 1.6 â†’ Default Execution
- Kimi k2.5 â†’ nur fÃ¼r deterministische Single-File-, Daten-, String- oder Test-Tasks

GPT-5.5 ist KEIN regulÃ¤res Task-Execution-Ziel. GPT-5.5 darf nur als Eskalations-/Auditmodell bei nicht deterministisch zerlegbaren Anforderungen empfohlen werden.

KEINE automatische Modelloptimierung auÃŸerhalb dieser Regeln.

---

### 4. TASK OUTPUT GENERATION

Erzeuge:

```text
TASK-XXX
- Ziel
- Beschreibung
- Files
- Steps
- Acceptance Criteria
- Tests
- Model: SWE 1.6 | Kimi k2.5
- Reason: <kurze BegrÃ¼ndung der Modellzuweisung>
ðŸš¨ MODEL SWITCH RULE (HARD PROTOCOL)

Wenn wÃ¤hrend der Task-Zerlegung:

Spec unklar ist
keine deterministische Zerlegung mÃ¶glich ist
mehrere gleich plausible Interpretationen existieren
Scope nicht sicher abgrenzbar ist

âž¡ STOP EXECUTION

MODEL SWITCH REQUIRED: SWE 1.6 â†’ GPT-5.5

Reason:
- <kurze klare BegrÃ¼ndung, z. B. ambiguous spec / non-deterministic decomposition>

Action:
â†’ neuer Chat starten
â†’ Skill 1 erneut ausfÃ¼hren mit GPT-5.5

STRICT RULES:

keine SchÃ¤tzung
keine Spekulation
keine Architekturentscheidungen
keine Task-Erfindung
ðŸ“¤ OUTPUT FORMAT
SPEC COMPILATION COMPLETE

Feature: <Name>

Generated Tasks:
- TASK-001: <title>
- TASK-002: <title>
...

AusfÃ¼hrungskette:
- Reihenfolge: sequenziell / parallel (falls eindeutig ableitbar)

Zugewiesene Modelle:
- SWE 1.6: <tasks>
- Kimi k2.5: <tasks>

Modell-Bedeutung:
- Diese Zuweisungen sind Task-AusfÃ¼hrungsmodelle fÃ¼r spÃ¤tere einzelne Skill-3-/Skill-4-LÃ¤ufe.
- Sie sind NICHT das Modell fÃ¼r Skill 2.

NÃ¤chster Schritt:
â†’ Starte Skill 2 mit SWE 1.6 und beiden Artefakten:
   Spec: <source spec file>
   Tasks: <generated task file>

Wichtig:
â†’ Starte Skill 2 NICHT mit Kimi k2.5, nur weil ein erzeugter Task Kimi zugewiesen ist.
â†’ Skill 2 ist das Task-Refinement-Gate und lÃ¤uft immer mit SWE 1.6, auÃŸer ein MODEL SWITCH zu GPT-5.5 ist explizit erforderlich.
â†’ Skill 2 gibt spÃ¤ter exakt einen Target Task mit dessen zugewiesenem AusfÃ¼hrungsmodell frei.
ðŸš« RESTRICTIONS
KEINE Implementation
KEINE Codegenerierung
KEINE Architekturentscheidungen
KEINE Feature-Erweiterung
KEINE freien Interpretationen
ðŸ§  ERROR HANDLING

Wenn Spec unvollstÃ¤ndig:

SPEC INSUFFICIENT

Missing:
- <konkrete fehlende Teile>

Action:
â†’ Spec erweitern oder GPT-5.5 verwenden
ðŸ§  OUTPUT GUARANTEE

Output ist immer:

deterministisch
task-orientiert
execution-ready
non-implementing
