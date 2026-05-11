# Janus Pipeline Run Log

Zweck: Dieses Log sammelt kompakte, auswertbare Beobachtungen aus echten Janus Pipeline-Runs. Es ersetzt nicht `SESSION_LOG.md`, Backlog, Spec-Artefakte oder Dashboard-Telemetrie. Es dient dazu, nach mehreren vollständigen Runs wiederkehrende Fehler, Reibungspunkte und Optimierungspotential in Skill-Routen, Handoffs und Dashboard-Feldern zu erkennen.

## Nutzungsregel

- **Eintrag pro Run**: Ein Run ist ein abgeschlossener oder klar abgebrochener Backlog-/Spec-/Task-Durchlauf durch die relevante Skill-Route.
- **Kurz halten**: Bei sauberem Verlauf reicht ein kompakter Eintrag.
- **Nur beobachtete Fakten**: Keine Vermutungen als Fakten eintragen.
- **Optimierungen sammeln, nicht sofort umbauen**: Workflow-Änderungen erst nach Auswertung mehrerer Runs beschließen.
- **Dashboard bleibt Quelle für Task-Ausführungsdauer**: Dieses Log ergänzt qualitative Pipeline-Beobachtungen.

## Run-Template

```md
### RUN-YYYY-MM-DD-XXX – <BACKLOG-ID | SPEC | TASK> – <Titel>

- **Datum**: YYYY-MM-DD
- **Quelle**: Backlog | Spec | Direkt-Task | Sonstiges
- **Artefakte**: <Backlog/Spec/Task-Dateien oder N/A>
- **Pipeline-Route**: <z. B. BACKLOG SKILL 3 -> SKILL 3 -> SKILL 4 -> SKILL 6 -> SKILL 7>
- **Dashboard-Handoff korrekt**: JA | NEIN | N/A
- **Routing vollständig**: JA | NEIN | N/A
- **Skill-Ergebnisse**:
  - BACKLOG SKILL 1: PASS | BLOCKED | N/A
  - BACKLOG SKILL 2: PASS | BLOCKED | N/A
  - BACKLOG SKILL 3: PASS | BLOCKED | N/A
  - SKILL 1: PASS | BLOCKED | N/A
  - SKILL 2: PASS | BLOCKED | N/A
  - SKILL 3: PASS | BLOCKED | N/A
  - SKILL 4: PASS | PASS WITH FIXES | BLOCKED | FIX LOOP | N/A
  - SKILL 5/6 Debug: FIXED | ESCALATION | NOT NEEDED | N/A
  - SKILL 6 Final Audit: PASS | PASS WITH FIXES | BLOCKED | N/A
  - SKILL 7: PASS | BLOCKED | N/A
  - SKILL 8: PASS | BLOCKED | N/A
- **Automatische Validierung**: PASS | FAIL | N/A – <Befehl/Evidenz>
- **Manueller Janus-Test**: PASS | FAIL | N/A – <Kurznotiz>
- **Fehler/Reibungspunkte**:
  - Keine
- **Optimierungspotential**:
  - Keine
- **Follow-up**: <Backlog-ID | Task | N/A>
- **Gesamtergebnis**: PASS | PASS WITH FIXES | BLOCKED | ABGEBROCHEN
```

## Run Log

### RUN-YYYY-MM-DD-001 – Beispiel – Sauberer Durchlauf

- **Datum**: YYYY-MM-DD
- **Quelle**: Backlog
- **Artefakte**: BACKLOG-XXX, `documentation/tasks/...md`
- **Pipeline-Route**: BACKLOG SKILL 3 -> SKILL 3 -> SKILL 4 -> SKILL 7
- **Dashboard-Handoff korrekt**: JA
- **Routing vollständig**: JA
- **Skill-Ergebnisse**:
  - BACKLOG SKILL 1: N/A
  - BACKLOG SKILL 2: N/A
  - BACKLOG SKILL 3: PASS
  - SKILL 1: N/A
  - SKILL 2: N/A
  - SKILL 3: PASS
  - SKILL 4: PASS
  - SKILL 5/6 Debug: NOT NEEDED
  - SKILL 6 Final Audit: N/A
  - SKILL 7: PASS
  - SKILL 8: N/A
- **Automatische Validierung**: PASS – <Befehl/Evidenz>
- **Manueller Janus-Test**: PASS – <Kurznotiz>
- **Fehler/Reibungspunkte**:
  - Keine
- **Optimierungspotential**:
  - Keine
- **Follow-up**: N/A
- **Gesamtergebnis**: PASS

## Auswertungsbereich

Dieser Bereich wird nach mehreren echten Runs gepflegt, z. B. nach 5-10 Runs oder nach einigen Arbeitstagen.

### Beobachtete Muster

- Noch keine Auswertung.

### Häufige Blocker

- Noch keine Auswertung.

### Skill-Routing-Qualität

- Noch keine Auswertung.

### Dashboard-Handoff-Qualität

- Noch keine Auswertung.

### Test- und Validierungsqualität

- Noch keine Auswertung.

### Beschlossene Optimierungen

- Noch keine Beschlüsse.

### Offene Optimierungsideen

- Noch keine Ideen.
