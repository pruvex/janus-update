---
description: BACKLOG SKILL 3 – Routing + Execution Handoff | Model: SWE 1.6
---

# BACKLOG SKILL 3 – ROUTING + EXECUTION HANDOFF

**Required Model:** SWE 1.6  
**Purpose:** Ergänzt fehlende Routing-Metadaten für Backlog-Items und erzeugt auf Wunsch dashboard-fähige Diamond-Pipeline-Handoffs.  
**Do not use this skill for:** Priorisierung, Code-Implementation, Final Audit, Debugging oder Release.

---

## Ziel

Dieser Skill hat drei strikt getrennte Modi:

```text
Mode A: ROUTING_ENRICHMENT
Mode B: SELECTED_HANDOFF
Mode C: DASHBOARD_PREP
```

Default ist `DASHBOARD_PREP`.

### Mode A: ROUTING_ENRICHMENT

Idempotenter Routing-Enricher für alle Backlog-Items mit fehlendem Routing.

Er macht nur:

- `documentation/backlog/BACKLOG.md` lesen.
- Offene Items mit fehlendem `Entry Point` finden.
- Pro geeignetem Item genau einmal Routing-Metadaten ergänzen.
- Keine Prioritäten neu bewerten.
- Keine Handoff-Dateien erzeugen.
- Kein Item nach `IN PROGRESS` verschieben.

### Mode B: SELECTED_HANDOFF

Expliziter Single-Item-Handoff für genau ein ausgewähltes Backlog-Item.

Er macht:

- Ein bereits geroutetes oder eindeutig routbares `READY` Item auswählen.
- Je nach `Entry Point` eine Mini-Spec oder Task-Datei erzeugen.
- Einen Copy-Paste-Prompt für den nächsten offiziellen Skill ausgeben.
- Erst dann das Item nach `IN PROGRESS` verschieben.

### Mode C: DASHBOARD_PREP

Dashboard-Vorbereitung für alle geeigneten `READY` Items nach `BACKLOG SKILL 2`.

Er macht:

- Alle `READY` Items prüfen, die nach Backlog Skill 2 ausreichend beschrieben sind.
- Fehlende Routing-Metadaten ergänzen.
- Fehlende Handoff-Artefakte für dashboard-fähige Items erzeugen.
- `Handoff`, `Recommended next skill` und `Handoff created` setzen.
- Items im Status `READY` belassen.
- Keine Items nach `IN PROGRESS` verschieben.

Ziel:

Nach `DASHBOARD_PREP` soll das Dashboard für jedes vorbereitete Item direkt einen vollständigen Copy-Paste-Prompt für den korrekten Diamond-Pipeline-Entry-Point erzeugen können.

Die möglichen Einstiege in die bestehende Diamond-Pipeline sind:

```text
SKILL 1 – SPEC TO TASK COMPILER
SKILL 2 – TASK BREAKDOWN ENGINE
SKILL 3 – PRE-IMPLEMENTATION VERIFICATION
SKILL 4 – EXECUTIONER, nur wenn ein gültiger Skill-3-Precheck-PASS bereits existiert
```

Im Modus `SELECTED_HANDOFF` und `DASHBOARD_PREP` erzeugt er je nach Fall:

- eine Mini-Feature-Spec unter `documentation/Planned Features/`
- oder eine atomare Task-Datei unter `documentation/tasks/`
- oder einen `HANDOFF BLOCKED` Report mit fehlenden Informationen

---

## Hard Rules

- Default ist `DASHBOARD_PREP`; ein einfacher Aufruf von `/BACKLOG SKILL 3 – EXECUTION HANDOFF` bereitet alle geeigneten `READY` Items für das Dashboard vor.
- Ohne explizites `Mode: SELECTED_HANDOFF` darf kein Item in Umsetzung übergeben oder nach `IN PROGRESS` verschoben werden.
- `ROUTING_ENRICHMENT` darf mehrere Items routen, aber nur fehlende Routing-Metadaten ergänzen.
- `DASHBOARD_PREP` darf mehrere `READY` Items vorbereiten und Handoff-Artefakte erzeugen, darf aber kein Item nach `IN PROGRESS` verschieben.
- `SELECTED_HANDOFF` darf genau ein Backlog-Item verarbeiten.
- Nur Items mit Status `READY` dürfen per `SELECTED_HANDOFF` in Umsetzung übergeben werden.
- Nur Items mit Status `READY` dürfen per `DASHBOARD_PREP` Handoff-Artefakte erhalten.
- Keine Code-Implementation.
- Keine Architekturentscheidungen.
- Keine neue Priorisierung; Bewertungen aus Backlog Skill 2 bleiben bindend.
- Keine Spekulation über fehlende Informationen.
- Kein direkter Sprung zu Skill 4, außer ein gültiger Skill-3-Precheck-PASS existiert bereits als Artefakt.
- Jeder erfolgreiche `SELECTED_HANDOFF` Output muss eine konkrete Datei oder einen bereits gültigen Precheck-Artefaktpfad enthalten.
- Jeder erfolgreiche `SELECTED_HANDOFF` Output muss einen Copy-Paste-Prompt für den nächsten offiziellen Skill enthalten.
- Jeder erfolgreiche `DASHBOARD_PREP` Output muss pro vorbereitetem Item eine konkrete Datei oder einen bereits gültigen Artefaktpfad im Backlog verlinken.
- `DASHBOARD_PREP` muss nach der Backlog-Änderung den Dashboard-Snapshot synchronisieren oder den Nutzer explizit dazu auffordern.
- Nach erfolgreichem `SELECTED_HANDOFF` das Backlog-Item auf `IN PROGRESS` setzen und die erzeugte Datei verlinken.
- Dashboard-relevante Felder müssen maschinenlesbar als einzelne Markdown-Listenfelder geschrieben werden.
- Wenn ein Backlog-Status geändert wird, muss der komplette `### BACKLOG-XXX` Item-Block physisch unter die passende kanonische Statusüberschrift verschoben werden. Pro Status darf es genau eine Überschrift geben: `## NEEDS INFO`, `## READY`, `## IN PROGRESS`, `## DONE`, `## BLOCKED`.

### Output Completion Gate (HARD)

`BACKLOG SKILL 3 COMPLETE`, `BACKLOG DASHBOARD PREP COMPLETE` oder ein gleichwertiger Erfolgsstatus darf nur ausgegeben werden, wenn der Output am Ende konkrete Copy-Paste-Prompts fuer alle vorbereiteten Items enthaelt.

Pflicht:

- Pro vorbereitetem Item genau ein grauer `text` Copy-Kasten.
- Jeder Copy-Kasten muss mit dem Ziel-Slash-Skill beginnen.
- `SPEC_PIPELINE_START` muss einen `@[/SKILL 1 - SPEC TO TASK COMPILER]` Prompt mit `Spec:` unter `documentation/Planned Features/` ausgeben.
- `PRE_IMPLEMENTATION_VERIFICATION` muss einen `@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]` Prompt mit `Target Task:`, `Task:` und `Backlog Item:` ausgeben.
- `EXECUTION_READY` muss einen `@[/SKILL 4 - EXECUTIONER]` Prompt mit `Target Task:`, `Task:`, `Pre-Check:` und `Backlog Item:` ausgeben.

Verboten als finaler Output:

- Nur "Naechste Schritte" ohne Copyblock.
- Nur "BACKLOG-XXX kann mit SKILL X ausgefuehrt werden".
- `BACKLOG SKILL 3 COMPLETE` ohne `## Next Skill Copy Prompts`.
- Ein `SKILL 1` Prompt mit einer Datei unter `documentation/tasks/`.
- Ein `SKILL 3` Prompt mit einer Datei unter `documentation/Planned Features/`.

Wenn die Copy-Prompts nicht vollstaendig erzeugt werden koennen, muss der Skill statt Erfolg ausgeben:

```text
BACKLOG SKILL 3 BLOCKED: NEXT_SKILL_HANDOVER_MISSING
Reason: <konkreter fehlender Copy-Prompt oder Artefakt-Mismatch>
```

---

## Input

Default-Aufruf für Dashboard-Vorbereitung:

```text
/BACKLOG SKILL 3 – EXECUTION HANDOFF
```

Wenn kein Mode angegeben ist, gilt:

```text
Mode: DASHBOARD_PREP
```

Expliziter Aufruf nur für Routing-Enrichment ohne Artefakterzeugung:

```text
/BACKLOG SKILL 3 – EXECUTION HANDOFF

Mode: ROUTING_ENRICHMENT
```

Expliziter Aufruf für ein konkretes Handoff:

```text
/BACKLOG SKILL 3 – EXECUTION HANDOFF

Mode: SELECTED_HANDOFF
Backlog Item:
BACKLOG-XXX
```

Expliziter Aufruf für Dashboard-Vorbereitung aller READY Items:

```text
/BACKLOG SKILL 3 – EXECUTION HANDOFF

Mode: DASHBOARD_PREP
```

Optional begrenzt auf eine Auswahl:

```text
/BACKLOG SKILL 3 – EXECUTION HANDOFF

Mode: DASHBOARD_PREP
Backlog Items:
BACKLOG-001, BACKLOG-002, BACKLOG-003
```

Der Skill liest:

```text
documentation/backlog/BACKLOG.md
```

---

## Dashboard-Datenvertrag

Das spätere Dashboard liest den aus `documentation/backlog/BACKLOG.md` generierten Snapshot als Dashboard-Cache. `documentation/backlog/BACKLOG.md` bleibt Source of Truth.

Jedes Backlog-Item kann diese Felder enthalten:

```markdown
- **Typ:** BUG | CHANGE | ENHANCEMENT | IMPROVEMENT | TECH_DEBT | UNCLEAR
- **Entry Point:** SPEC_PIPELINE_START | TASK_BREAKDOWN | PRE_IMPLEMENTATION_VERIFICATION | EXECUTION_READY | ROUTING_BLOCKED
- **Routing reason:** <ein kurzer Satz>
- **Routing confidence:** HIGH | MEDIUM | LOW
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** YYYY-MM-DD
- **Handoff:** <path> | none
- **Recommended next skill:** SKILL 1 | SKILL 2 | SKILL 3 | SKILL 4 | none
- **Handoff created:** YYYY-MM-DD | none
```

Dashboard-Bedeutung:

- `Typ` bestimmt die sichtbare Dashboard-Spalte. Nicht-kanonische Werte werden im Active Board nicht angezeigt.
- `Entry Point` bestimmt den optimalen Pipeline-Einstieg.
- `Recommended next skill` bestimmt den anzuzeigenden nächsten Slash-Skill.
- `Handoff` verweist auf die konkrete Spec-/Task-Datei, falls bereits erzeugt.
- `Status` bestimmt Active/History View.
- `DONE` Items bleiben sichtbar und werden nicht gelöscht.
- Nach Änderungen an `documentation/backlog/BACKLOG.md` muss der Dashboard-Snapshot per `npm run sync:backlog` im Ordner `janus-dashboard` aktualisiert werden.

---

## Entry-Point-Entscheidungsmatrix

### Konsistenz-Gate (HARD)

`Entry Point`, `Handoff` und `Recommended next skill` muessen zueinander passen.

Gueltige Kombinationen:

```text
SPEC_PIPELINE_START -> documentation/Planned Features/...md -> SKILL 1
TASK_BREAKDOWN -> vorhandene Spec/Tasks -> SKILL 2
PRE_IMPLEMENTATION_VERIFICATION -> documentation/tasks/...md -> SKILL 3
EXECUTION_READY -> documentation/tasks/...md + Precheck artifact + Target Task -> SKILL 4
```

Ungueltige Kombinationen:

```text
SPEC_PIPELINE_START -> documentation/tasks/...md -> SKILL 1
PRE_IMPLEMENTATION_VERIFICATION -> documentation/Planned Features/...md -> SKILL 3
documentation/tasks/...md -> SKILL 1
Task-Datei erzeugt, aber "Spec-Datei zu erstellen" als Next Step
DASHBOARD_PREP COMPLETE ohne Next Skill Copy Prompt
```

Wenn `DASHBOARD_PREP` eine Task-Datei unter `documentation/tasks/` erzeugt oder wiederverwendet,
muss gelten:

```markdown
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Recommended next skill:** SKILL 3
- **Target Task:** <task id aus Datei>
```

Wenn `DASHBOARD_PREP` eine Spec-Datei unter `documentation/Planned Features/` erzeugt oder wiederverwendet,
muss gelten:

```markdown
- **Entry Point:** SPEC_PIPELINE_START
- **Recommended next skill:** SKILL 1
```

Bei einem Widerspruch darf `DASHBOARD_PREP COMPLETE` nicht ausgegeben werden. Stattdessen:

```text
DASHBOARD_PREP BLOCKED: ROUTING_ARTIFACT_MISMATCH
Reason: <konkreter Widerspruch zwischen Entry Point, Handoff und Recommended next skill>
```

### SPEC_PIPELINE_START

Setze diesen Entry Point, wenn:

- neue Funktion oder größere Ergänzung
- UI-/Produktverhalten nicht rein technisch ist
- mehrere Tasks wahrscheinlich sind
- Akzeptanzkriterien eine Feature-Spec benötigen
- Risiko `MEDIUM` oder `HIGH` ist
- Scope größer als ein atomarer Fix ist

Spätere Handoff-Datei:

```text
documentation/Planned Features/backlog_BACKLOG-XXX_<slug>.md
```

Nächster offizieller Skill:

```text
SKILL 1
```

### TASK_BREAKDOWN

Setze diesen Entry Point nur, wenn:

- bereits eine Mini-Spec existiert
- bereits grobe Tasks aus Backlog Skill 3 oder einem früheren Lauf existieren
- diese Tasks noch verfeinert werden müssen

Nächster offizieller Skill:

```text
SKILL 2
```

### PRE_IMPLEMENTATION_VERIFICATION

Setze diesen Entry Point, wenn:

- kleiner klarer Bugfix oder kleine lokale Änderung
- genau ein Ziel
- Akzeptanzkriterien klar
- betroffener Bereich klar
- keine Produktentscheidung offen
- Risiko `LOW` oder klar begrenztes `MEDIUM`

Spätere Handoff-Datei:

```text
documentation/tasks/backlog_BACKLOG-XXX_<slug>.md
```

Nächster offizieller Skill:

```text
SKILL 3
```

### EXECUTION_READY

Setze diesen Entry Point nur, wenn:

- ein gültiger Skill-3-Precheck-PASS bereits als Artefakt existiert
- ein konkreter Target Task eindeutig referenziert ist
- keine weitere Pre-Implementation-Verifikation notwendig ist

Pflichtfelder:

```markdown
- **Precheck artifact:** <path>
- **Target Task:** <task id>
```

Nächster offizieller Skill:

```text
SKILL 4
```

### ROUTING_BLOCKED

Setze diesen Entry Point, wenn:

- Pflichtinformationen fehlen
- Risiko/Scope nicht deterministisch einordenbar ist
- das Item `NEEDS INFO` oder `BLOCKED` ist
- konkurrierende Entry Points gleich plausibel sind

`ROUTING_BLOCKED` ist kein gueltiger Entry Point fuer Items mit:

- `Status: READY`
- `Umsetzungsreife: READY`
- `Empfehlung: DO NOW | NEXT | SCHEDULE`
- konkretem Problem, Quelle/TestRun und reproduzierbarem Blocker

Wenn ein Item als `READY` angelegt wird und nur groesser ist (z. B. `Aufwand: L`) oder eine
Test-Infrastruktur-/Backend-Startup-Aenderung braucht, muss Skill 3 einen ausfuehrbaren Entry Point
waehlen:

- `SPEC_PIPELINE_START`, wenn Analyse/Design/Scope-Schnitt fuer Infra-/Backend-Startup noetig ist.
- `PRE_IMPLEMENTATION_VERIFICATION`, wenn der Fix atomar genug fuer eine Task-Datei ist.

Ein Output mit `Status: READY` + `Entry Point: ROUTING_BLOCKED` ist ungueltig und muss korrigiert
werden. Wenn wirklich blockiert, muss der Status `NEEDS INFO` oder `BLOCKED` sein und der konkrete
fehlende Input genannt werden.

---

## Mode A: ROUTING_ENRICHMENT

### Verarbeitung

1. Lese `documentation/backlog/BACKLOG.md`.
2. Prüfe offene Items mit Status `READY`, `NEEDS INFO` und `BLOCKED`.
3. Überspringe Items, die bereits ein `Entry Point` Feld haben.
4. Überspringe `DONE` Items, außer sie enthalten widersprüchliche Routing-Felder.
5. Ergänze pro Item mit fehlendem Routing die Routing-Metadaten.

### Erlaubte Änderungen

Nur diese Felder dürfen ergänzt werden:

```markdown
- **Entry Point:** <value>
- **Routing reason:** <reason>
- **Routing confidence:** HIGH | MEDIUM | LOW
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** YYYY-MM-DD
```

Optional bei `ROUTING_BLOCKED`:

```markdown
- **Routing blocker:** <konkreter Grund>
```

### Verbotene Änderungen in ROUTING_ENRICHMENT

- Kein `Status: IN PROGRESS`.
- Keine Spec-Datei.
- Keine Task-Datei.
- Kein `Handoff created`.
- Keine Änderung an `Wichtigkeit`, `Umsetzungsrisiko`, `Aufwand`, `Empfehlung`.
- Keine Auswahl eines “nächsten besten” Items.

### Output

```markdown
# BACKLOG ROUTING ENRICHMENT COMPLETE

## Summary
- **Backlog file:** documentation/backlog/BACKLOG.md
- **Items scanned:** <n>
- **Routing added:** <n>
- **Already routed:** <n>
- **Routing blocked:** <n>
- **Items moved to IN PROGRESS:** 0
- **Artifacts created:** 0

## Routed Items
- **BACKLOG-XXX:** Entry Point `<value>` — <reason>

## Blocked Routing
- **BACKLOG-YYY:** ROUTING_BLOCKED — <reason>

## Dashboard Data
- **State source:** documentation/backlog/BACKLOG.md
- **Entry-point field:** `Entry Point`
- **Status field:** `Status`
- **History rule:** `Status == DONE`
```

---

## Mode B: SELECTED_HANDOFF

### Readiness Gate

Stoppe mit `HANDOFF BLOCKED`, wenn:

- kein `Backlog Item` angegeben ist
- Item nicht existiert
- Status nicht `READY` ist
- Akzeptanzkriterien fehlen
- erwartetes/tatsächliches Verhalten bei Bug fehlt
- Reproduktion bei Bug fehlt und der Bug nicht anderweitig eindeutig ist
- Scope mehrere unabhängige Ziele enthält
- Produktentscheidung offen ist
- Risiko `HIGH` ist und keine vollständige Spec existiert
- `Entry Point` fehlt und auch in diesem Lauf nicht deterministisch gesetzt werden kann
- `Entry Point` ist `ROUTING_BLOCKED`

---

## Mode C: DASHBOARD_PREP

### Zweck

`DASHBOARD_PREP` ist der Batch-Vorbereitungsmodus für den Dashboard-Workflow.

Er wird nach `BACKLOG SKILL 2 – REVIEW PRIORISIERUNG` genutzt, damit das Dashboard für alle geeigneten Backlog-Items sofort vollständige Handover-Prompts für den korrekten Diamond-Pipeline-Entry-Point anbieten kann.

### Verarbeitung

1. Lese `documentation/backlog/BACKLOG.md`.
2. Ermittle alle Items mit `Status: READY`, sofern keine optionale `Backlog Items` Auswahl angegeben wurde.
3. Überspringe `DONE`, `IN PROGRESS`, `NEEDS INFO` und `BLOCKED` Items.
4. Pruefe fuer jedes aktive Item den Dashboard-Typ. `Typ` MUSS einer von `BUG`, `CHANGE`, `ENHANCEMENT`, `IMPROVEMENT`, `TECH_DEBT`, `UNCLEAR` sein. Wenn ein nicht-kanonischer Typ gefunden wird, normalisiere ihn deterministisch, bevor der Snapshot synchronisiert wird:
   - `Security`, `Privacy`, `Prompt-Injection`, `Safety` -> `BUG`
   - `Cost`, `UX`, `Sonstiges` -> `IMPROVEMENT`, sofern es kein Defekt ist; sonst `BUG`
   - unklare Werte -> `UNCLEAR`
5. Ergänze fehlende Routing-Felder wie in `ROUTING_ENRICHMENT`.
   - Wenn ein Item `Status: READY` und `Entry Point: ROUTING_BLOCKED` hat, korrigiere es deterministisch zu `SPEC_PIPELINE_START` oder `PRE_IMPLEMENTATION_VERIFICATION`, wenn Problem/Quelle/Scope ausreichend beschrieben sind.
   - Wenn es nicht deterministisch korrigierbar ist, stoppe mit `DASHBOARD_PREP BLOCKED`; lasse kein READY+ROUTING_BLOCKED im Backlog stehen.
6. Für jedes `READY` Item mit deterministischem Entry Point:
   - Erzeuge fehlendes Handoff-Artefakt.
   - Überspringe Artefakterzeugung, wenn `Handoff` bereits auf eine passende vorhandene Datei zeigt.
   - Setze oder aktualisiere `Handoff`.
   - Setze oder aktualisiere `Recommended next skill`.
   - Setze `Handoff created`.
7. Belasse jedes vorbereitete Item im Status `READY`.
8. Verschiebe keine Item-Blöcke nach `IN PROGRESS`.
9. Synchronisiere anschließend den Dashboard-Snapshot:

```powershell
npm run sync:backlog
```

Arbeitsordner:

```text
janus-dashboard
```

### Erlaubte Backlog-Änderungen in DASHBOARD_PREP

```markdown
- **Entry Point:** <value>
- **Routing reason:** <reason>
- **Routing confidence:** HIGH | MEDIUM | LOW
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** YYYY-MM-DD
- **Handoff:** <created or existing artifact path>
- **Recommended next skill:** SKILL 1 | SKILL 2 | SKILL 3 | SKILL 4
- **Handoff created:** YYYY-MM-DD
```

Bei `EXECUTION_READY` zusätzlich nur wenn real vorhanden:

```markdown
- **Precheck artifact:** <path>
- **Target Task:** <task id>
```

### Verbotene Änderungen in DASHBOARD_PREP

- Kein Item nach `IN PROGRESS` verschieben.
- Keine Änderung an `Status`, außer ein Item ist wegen fehlender Pflichtinformationen eindeutig falsch als `READY` markiert; dann STOP und als `DASHBOARD_PREP BLOCKED` melden statt still ändern.
- Keine Änderung an Priorisierung aus Backlog Skill 2.
- Keine nicht-kanonischen Dashboard-Typen stehen lassen. Typ-Normalisierung ist erlaubt, wenn sie nur die Dashboard-Sichtbarkeit repariert.
- Keine Code-Implementation.
- Keine Final-Audit-, Debug- oder Release-Aktionen.
- Keine Spekulation über fehlende Informationen.
- Kein `@[/JANUS DASHBOARD]` als einziger Handoff. Dashboard-Sync ist ein Nebeneffekt, nicht der nächste Pipeline-Skill.
- Kein `Status: READY` + `Entry Point: ROUTING_BLOCKED` im Erfolgsoutput.

### Artefakt-Regeln

Für `SPEC_PIPELINE_START`:

```text
documentation/Planned Features/backlog_BACKLOG-XXX_<slug>.md
Recommended next skill: SKILL 1
```

Eine Task-Datei unter `documentation/tasks/` ist fuer `SPEC_PIPELINE_START` verboten.
Wenn nur eine Task-Datei erzeugt wurde, muss der Entry Point `PRE_IMPLEMENTATION_VERIFICATION`
sein oder die Spec-Datei muss tatsaechlich erzeugt und verlinkt werden.

Für `PRE_IMPLEMENTATION_VERIFICATION`:

```text
documentation/tasks/backlog_BACKLOG-XXX_<slug>.md
Recommended next skill: SKILL 3
```

Die Task-Datei muss im Abschnitt `NEXT STEP` einen Copy-Prompt zu
`@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]` enthalten. Ein NEXT STEP zu Skill 1 ist
bei einer Task-Datei ungueltig.

Für `TASK_BREAKDOWN`:

- Nutze vorhandene Spec-/Task-Artefakte, wenn eindeutig vorhanden.
- Wenn keine eindeutige Spec-/Task-Basis existiert, erstelle eine Mini-Spec und route stattdessen zu `SKILL 1`, oder blockiere das Item mit konkretem Grund.

Für `EXECUTION_READY`:

- Nur verwenden, wenn `Precheck artifact`, `Target Task` und Task-Datei real vorhanden sind.
- Sonst auf `PRE_IMPLEMENTATION_VERIFICATION` zurückstufen oder blockieren.

### Batch-Sicherheitsgrenze

Wenn mehr als 10 `READY` Items vorbereitet werden sollen:

```text
DASHBOARD_PREP CONFIRMATION REQUIRED

Reason:
- More than 10 READY items would create or update handoff artifacts.

Action:
- Nutzer muss Auswahl bestätigen oder `Max Items` angeben.
```

### Erfolgsoutput

```markdown
# BACKLOG DASHBOARD PREP COMPLETE

## Summary
- **Backlog file:** documentation/backlog/BACKLOG.md
- **Items scanned:** <n>
- **Items prepared:** <n>
- **Artifacts created:** <n>
- **Artifacts reused:** <n>
- **Items blocked:** <n>
- **Items moved to IN PROGRESS:** 0
- **Snapshot synced:** YES | NO

## Prepared Items
- **BACKLOG-XXX:** `<Entry Point>` → `<Handoff>` → `<Recommended next skill>`

## Next Skill Copy Prompts

Für jedes vorbereitete Item MUSS ein copy-fähiger Prompt für den nächsten offiziellen Skill ausgegeben werden. Das Dashboard und der User dürfen nach `DASHBOARD_PREP` nicht raten müssen.

Wenn `Prepared Items` nicht leer ist und `## Next Skill Copy Prompts` keinen konkreten
Copyblock pro vorbereitetem Item enthaelt, ist der Output ungueltig. Ein reines
"Handoff ist bereit fuer SKILL X" reicht nicht.

Die Copy-Prompts muessen der Artefakt-Identitaet entsprechen. `SKILL 1` akzeptiert nur `Spec:` und keine `Task:` Datei. `SKILL 3` akzeptiert nur `Task:` und keinen `Spec:` Einstieg.
Der Pfad im Copy-Prompt MUSS exakt dem `Handoff`-Feld in `documentation/backlog/BACKLOG.md`
entsprechen. Abweichungen wie `BACKLOG_052` statt `BACKLOG-052`, `TaskFile` statt `Task`, oder
anderer Dateiname sind ungueltig.

Fuer `Recommended next skill: SKILL 3` muss der Copy-Prompt vollstaendig sein. Kurzformen sind verboten:

```text
@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION] Mode=VALIDATION; ExecutionModel=SWE_1_6; TaskFile=<path>; SourceBacklog=<id>; Rules=VALIDATE_TASK_BEFORE_EXECUTION; ExpectedOutput=VALIDATION_RESULT_OR_TASK_REJECTED
```

Pflichtfelder fuer SKILL-3-Copy-Prompts:

```text
@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]
Target Task: <task id>
Task: <handoff path exactly as in BACKLOG.md>
Backlog Item: <BACKLOG-XXX>
Mode: PRE_IMPLEMENTATION_VERIFICATION
Execution Model: SWE 1.6
Context: <Quelle/Risiko/Finding kurz>
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_SKILL_4_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_SKILL_4_HANDOFF_OR_PRE_CHECK_BLOCKED
```

### BACKLOG-XXX – <Titel>

```text
@[/SKILL 1 - SPEC TO TASK COMPILER]
Spec: documentation/Planned Features/backlog_BACKLOG-XXX_<slug>.md
Backlog Item: BACKLOG-XXX
```

oder:

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-XXX
Task: documentation/tasks/backlog_BACKLOG-XXX_<slug>.md
Backlog Item: BACKLOG-XXX
```

oder:

```text
@[/SKILL 4 - EXECUTIONER]
Target Task: <target task id>
Task: <task file path>
Pre-Check: <precheck artifact path>
Backlog Item: BACKLOG-XXX
```

## Blocked Items
- **BACKLOG-YYY:** <konkreter Grund>

## Dashboard Result
- Dashboard kann für vorbereitete Items direkt den passenden Skill-Pipeline-Prompt kopieren.
```

### Blocked Output

```markdown
# BACKLOG DASHBOARD PREP BLOCKED

## Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>

## Reason
- <konkreter Grund>

## Required Next Step
- <fehlende Information oder manuelle Entscheidung>
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

## Backlog Update im Modus SELECTED_HANDOFF

Nach erfolgreichem `SELECTED_HANDOFF`:

- Verschiebe das Item aus `READY` nach `IN PROGRESS`.
- Verschiebe dabei den kompletten `### BACKLOG-XXX` Block unter die einzige kanonische Überschrift `## IN PROGRESS`; ändere nicht nur das `Status` Feld.
- Prüfe danach, dass keine doppelte Statusüberschrift existiert und dass der Abschnitt des Items zum `Status` Feld passt.
- Ergänze im Item:

```markdown
- **Handoff:** <created file path>
- **Recommended next skill:** <SKILL 1 | SKILL 2 | SKILL 3 | SKILL 4>
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

Für vorhandenen Precheck mit `EXECUTION_READY`:

```markdown
# BACKLOG HANDOFF READY

## Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>

## Existing Artifacts
- **Task:** <task file path>
- **Precheck:** <precheck artifact path>
- **Target Task:** <target task id>

## Recommended Next Skill
/SKILL 4 – EXECUTIONER

## Copy-Paste Prompt
/SKILL 4 – EXECUTIONER mit folgenden Artefakten:
Target Task: <target task id>
Task: <task file path>
Pre-Check: <precheck artifact path>
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

Wenn Routing oder Handoff nicht deterministisch entscheidbar ist:

```text
STOP
MODEL SWITCH REQUIRED: SWE 1.6 → GPT-5.5
```

Gib eine kompakte Begründung, die konkurrierenden Entry Points und die minimal nötige Entscheidungsfrage aus.
