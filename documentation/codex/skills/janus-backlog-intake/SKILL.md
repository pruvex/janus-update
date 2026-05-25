---
name: janus-backlog-intake
description: Capture raw Janus bugs, changes, enhancements, improvements, and technical debt as structured Backlog items. Use when the user reports a bug, asks for a small change, mentions annoying behavior, provides logs/screenshots/manual findings, or wants something added to the Janus Backlog before prioritization or implementation.
---

# Janus Backlog Intake

## Overview

Turn raw Janus input into one or more structured items in `C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md`. Do not prioritize, implement, create handoff files, or route directly to execution.

## Source Reference

Legacy source:

- `C:\KI\Janus-Projekt\.windsurf\workflows\BACKLOG SKILL 1 – INTAKE TRIAGE.md`

Read only if exact wording is needed.

## Hard Rules

- No code changes.
- No architecture decisions.
- No direct Skill 1-8 handoff.
- Do not reactivate `DONE` items. Create a new follow-up item instead.
- Split unrelated topics into separate Backlog items or ask the user to choose one.
- If required information is missing, create/update an item under `NEEDS INFO` and ask one concrete follow-up.
- Every new item gets the next free `BACKLOG-XXX` ID.
- Physically place the item under its canonical status heading.

## Classification

Choose exactly one:

- `BUG`: expected behavior differs from actual behavior or errors occur.
- `CHANGE`: existing behavior should change.
- `ENHANCEMENT`: small addition to an existing feature.
- `IMPROVEMENT`: quality, UX, stability, or clarity improvement without new core behavior.
- `TECH_DEBT`: cleanup, maintainability, tests, structure.
- `UNCLEAR`: goal, expected behavior, or scope is missing.

## Required Fields

Every item must include:

```markdown
### BACKLOG-XXX – <kurzer Titel>

- **Typ:** BUG | CHANGE | ENHANCEMENT | IMPROVEMENT | TECH_DEBT | UNCLEAR
- **Status:** NEEDS INFO | READY | IN PROGRESS | DONE | BLOCKED
- **Quelle:** User Intake | Screenshot | Log | Audit | Manual Test | System Health | Other
- **Erstellt:** YYYY-MM-DD
- **Aktualisiert:** YYYY-MM-DD
- **Kurzbeschreibung:** <1-3 Saetze>
- **Erwartetes Verhalten:** <falls relevant>
- **Tatsaechliches Verhalten:** <falls relevant>
- **Reproduktion / Kontext:** <Schritte, Kontext, Beispiel>
- **Betroffener Bereich:** <UI/API/Backend/Frontend/Electron/Doku/Unklar>
- **Nachweise:** <Logs, Screenshots, Dateien oder "fehlt">
- **Akzeptanzkriterien:**
  - [ ] <pruefbares Kriterium>
- **Fehlende Informationen:**
  - <konkrete Frage oder "Keine">
- **Notizen:** <optional>
```

Use existing file style where it already differs slightly, but preserve all dashboard-required fields.

## Status Decision

- `NEEDS INFO`: required details are missing.
- `READY`: sufficient for prioritization and routing.
- `BLOCKED`: external decision or dependency blocks progress.

Do not set new intake directly to `IN PROGRESS` or `DONE`.

## Follow-Up Rule

If the new issue follows up on a `DONE` item:

- Create a new item with a new ID.
- Add `- **Follow-up zu:** BACKLOG-XXX – <Titel>` to the new item.
- Add a backlink to the old `DONE` item if safe and unambiguous.
- Never move the old item out of `DONE`.

## Output

For missing information:

```markdown
# BACKLOG ITEM NEEDS INFO

## Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>
- **Typ:** <Typ>

## Fehlende Informationen
- **[Info]:** <warum benoetigt>

## Bitte liefere als Naechstes
<konkrete Copy-Paste-Anfrage an den Nutzer>
```

For ready items:

```markdown
# BACKLOG ITEM READY

## Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>
- **Typ:** <Typ>
- **Status:** READY

## Naechster Schritt
Nutze `janus-backlog-prioritization`.
```
