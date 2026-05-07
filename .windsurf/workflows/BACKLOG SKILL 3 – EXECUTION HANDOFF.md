---
description: BACKLOG SKILL 3 – Execution Handoff | Model: SWE 1.6
---

# BACKLOG SKILL 3 – EXECUTION HANDOFF

**Required Model:** SWE 1.6  
**Purpose:** Übersetzt ein ausgewähltes Backlog-Item in eine konkrete Diamond-Pipeline-Übergabe mit Artefaktdatei und Copy-Paste-Prompt.  
**Do not use this skill for:** Priorisierung, Code-Implementation, Final Audit, Debugging oder Release.

---

## Ziel

Dieser Skill nimmt genau ein ausgewähltes Backlog-Item und entscheidet den optimalen Einstieg in die bestehende Diamond-Pipeline:

```text
SKILL 1 – SPEC TO TASK COMPILER
SKILL 2 – TASK BREAKDOWN ENGINE
SKILL 3 – PRE-IMPLEMENTATION VERIFICATION
```

Er erzeugt je nach Fall:

- eine Mini-Feature-Spec unter `documentation/Planned Features/`
- oder eine atomare Task-Datei unter `documentation/tasks/`
- oder einen `HANDOFF BLOCKED` Report mit fehlenden Informationen

---

## Hard Rules

- Genau ein Backlog-Item verarbeiten.
- Nur Items mit Status `READY` dürfen in Umsetzung übergeben werden.
- Keine Code-Implementation.
- Keine Architekturentscheidungen.
- Keine Spekulation über fehlende Informationen.
- Kein direkter Sprung zu Skill 4, außer ein gültiger Skill-3-Precheck-PASS existiert bereits als Artefakt.
- Jeder Output muss eine konkrete Datei oder einen konkreten Blocker enthalten.
- Jeder erfolgreiche Output muss einen Copy-Paste-Prompt für den nächsten offiziellen Skill enthalten.
- Nach erfolgreichem Handoff das Backlog-Item auf `IN PROGRESS` setzen und die erzeugte Datei verlinken.

---

## Input

Minimaler Aufruf:

```text
/BACKLOG SKILL 3 – EXECUTION HANDOFF

Backlog Item:
BACKLOG-XXX
```

Der Skill liest:

```text
documentation/backlog/BACKLOG.md
```

---

## Readiness Gate

Stoppe mit `HANDOFF BLOCKED`, wenn:

- Item nicht existiert
- Status nicht `READY` ist
- Akzeptanzkriterien fehlen
- erwartetes/tatsächliches Verhalten bei Bug fehlt
- Reproduktion bei Bug fehlt und der Bug nicht anderweitig eindeutig ist
- Scope mehrere unabhängige Ziele enthält
- Produktentscheidung offen ist
- Risiko `HIGH` ist und keine vollständige Spec existiert

---

## Handoff-Entscheidungsmatrix

### Einstieg in SKILL 1

Wähle SKILL 1, wenn:

- neue Funktion oder größere Ergänzung
- UI-/Produktverhalten nicht rein technisch ist
- mehrere Tasks wahrscheinlich sind
- Akzeptanzkriterien eine Feature-Spec benötigen
- Risiko `MEDIUM` oder `HIGH` ist
- Scope größer als ein atomarer Fix ist

Erzeuge:

```text
documentation/Planned Features/backlog_BACKLOG-XXX_<slug>.md
```

### Einstieg in SKILL 2

Wähle SKILL 2 nur, wenn:

- bereits eine Mini-Spec existiert
- bereits grobe Tasks aus Backlog Skill 3 oder einem früheren Lauf existieren
- diese Tasks noch verfeinert werden müssen

### Einstieg in SKILL 3

Wähle SKILL 3, wenn:

- kleiner klarer Bugfix oder kleine lokale Änderung
- genau ein Ziel
- Akzeptanzkriterien klar
- betroffener Bereich klar
- keine Produktentscheidung offen
- Risiko `LOW` oder klar begrenztes `MEDIUM`

Erzeuge:

```text
documentation/tasks/backlog_BACKLOG-XXX_<slug>.md
```

---

## Mini-Spec Format für SKILL 1

```markdown
# JANUS FEATURE SPEC – DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-XXX
- **Backlog Title:** <Titel>
- **Type:** BUG | CHANGE | ENHANCEMENT | IMPROVEMENT | TECH_DEBT

## 2. Problem / Wunsch
<aus Backlog-Eintrag>

## 3. Expected Behavior
<klar und prüfbar>

## 4. Current Behavior
<falls relevant>

## 5. Scope
### IN SCOPE
- <Punkte>

### OUT OF SCOPE
- <explizite Grenzen>

## 6. Functional Requirements
- <Requirement>

## 7. Acceptance Criteria
- [ ] <prüfbares Kriterium>

## 8. Evidence
- <Logs/Screenshots/Notizen oder none>

## 9. Risks
- <Risiko>

## 10. Validation Mapping
- <Akzeptanzkriterium> → <Test/Prüfung>

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.
```

---

## Task-Datei Format für SKILL 3

```markdown
# BACKLOG TASK – BACKLOG-XXX – <Titel>

## 1. Ziel
<ein atomares Ziel>

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-XXX
- **Beeinflusst:** <betroffene Dateien/Module/Bereiche>
- **Risiko-Einschätzung:** LOW | MEDIUM | HIGH

## 3. Scope
### IN SCOPE
- <Punkte>

### OUT OF SCOPE
- <Grenzen>

## 4. Umsetzungsschritte
- <deterministische Schritte ohne Code-Details zu erfinden>

## 5. Acceptance Criteria
- [ ] <prüfbares Kriterium>

## 6. Tests / Validierung
- <gezielte Prüfung>

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Fix.
```

---

## Backlog Update

Nach erfolgreichem Handoff:

- Verschiebe das Item aus `READY` nach `IN PROGRESS`.
- Ergänze im Item:

```markdown
- **Handoff:** <created file path>
- **Recommended next skill:** <SKILL 1 | SKILL 2 | SKILL 3>
- **Handoff created:** YYYY-MM-DD
```

---

## Erfolgsoutput

Für Mini-Spec:

```markdown
# BACKLOG HANDOFF READY

## Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>

## Created Artifact
- **Spec:** documentation/Planned Features/backlog_BACKLOG-XXX_<slug>.md

## Recommended Next Skill
/SKILL 1 – SPEC TO TASK COMPILER

## Copy-Paste Prompt
/SKILL 1 – SPEC TO TASK COMPILER mit folgender Spec-Datei:
documentation/Planned Features/backlog_BACKLOG-XXX_<slug>.md
```

Für Task-Datei:

```markdown
# BACKLOG HANDOFF READY

## Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>

## Created Artifact
- **Task:** documentation/tasks/backlog_BACKLOG-XXX_<slug>.md

## Recommended Next Skill
/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION

## Copy-Paste Prompt
/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION mit folgenden Artefakten:
Target Task: BACKLOG-XXX
Task: documentation/tasks/backlog_BACKLOG-XXX_<slug>.md
```

---

## Blocked Output

```markdown
# BACKLOG HANDOFF BLOCKED

## Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>

## Reason
- <konkreter Grund>

## Missing Information
- <konkrete Liste>

## Required Next Step
Nutze BACKLOG SKILL 1 mit diesen Zusatzinfos:
<Copy-Paste-Anfrage>
```

---

## Model Switch Rule

Wenn nicht deterministisch entscheidbar ist, ob SKILL 1, SKILL 2 oder SKILL 3 der richtige Einstieg ist:

```text
STOP
MODEL SWITCH REQUIRED: SWE 1.6 → GPT-5.5
```

Gib eine kompakte Begründung und die konkurrierenden Optionen aus.
