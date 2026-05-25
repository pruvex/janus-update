---
name: janus-backlog-prioritization
description: Review and prioritize open Janus Backlog items with a token-saving DELTA mode. Use after Backlog intake, when the user asks what to do next, when open items need importance/risk/effort/readiness/recommendation fields, or before selecting an item for Diamond pipeline handoff.
---

# Janus Backlog Prioritization

## Overview

Evaluate open items in `C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md`, persist missing evaluation fields, and recommend the next best item. Do not implement, create handoff files, or route directly to execution.

## Source Reference

Legacy source:

- `C:\KI\Janus-Projekt\.windsurf\workflows\BACKLOG SKILL 2 – REVIEW PRIORISIERUNG.md`

Read only if exact wording is needed.

## Model Gate

Default recommendation:

- Model: `5.4` for meaningful prioritization.
- Intelligence: medium/high.
- Use `5.4 mini` only for purely mechanical cache-field cleanup.
- Use `5.5` only for release/security/privacy-critical prioritization.

## Mode

Default:

```text
Modus: DELTA
Max Deep Review: 5
```

Use `FULL` only when explicitly requested, the review basis is inconsistent, more than 10 open items changed, multiple critical/release blockers compete, or a roadmap/release decision needs broad review.

## Hard Rules

- Ignore `DONE` items for content prioritization.
- Do not mark `NEEDS INFO` as ready.
- Do not create handoff files.
- Persist changed evaluation fields in `BACKLOG.md`.
- Do not deeply re-review unchanged items that already have all cache fields.
- If nothing changed, report `Bewertungs-Cache: unveraendert`.

## Evaluation Cache Fields

For each deeply reviewed open item, set or update:

```markdown
- **Wichtigkeit:** LOW | MEDIUM | HIGH | CRITICAL
- **Umsetzungsrisiko:** LOW | MEDIUM | HIGH
- **Aufwand:** XS | S | M | L | XL
- **Umsetzungsreife:** READY | NEEDS INFO | BLOCKED
- **Empfehlung:** DO NOW | SCHEDULE | NEEDS INFO FIRST | DEFER | DO NOT START
```

## DELTA Review Procedure

1. Count open `READY`, `NEEDS INFO`, and `BLOCKED` items.
2. Build compact item cards: ID, title, type, status, updated date, short description, affected area, missing info, acceptance criteria summary.
3. Deep-review only items with missing cache fields, changed core fields, contradictory status/section, obvious inconsistency, explicit focus, or Top-next relevance.
4. Compare top candidates by importance, risk, effort, readiness, and pipeline cost.
5. Persist new/changed cache fields.

## Output

Use:

```markdown
# BACKLOG REVIEW

## Zusammenfassung
- **Review-Modus:** DELTA | FULL
- **Deep Reviewed:** <n>
- **Kompakt geprueft/uebernommen:** <n>
- **Full Review empfohlen:** JA | NEIN
- **Open READY:** <n>
- **Needs Info:** <n>
- **Blocked:** <n>
- **Empfohlener naechster Punkt:** BACKLOG-XXX – <Titel>
- **Bewertungs-Cache:** aktualisiert | unveraendert

## Priorisierte offene Punkte nach Kategorien
<BUG, CHANGE, ENHANCEMENT, IMPROVEMENT, TECH_DEBT, UNCLEAR as needed>

## Empfehlung
- **Naechster sinnvoller Punkt:** BACKLOG-XXX – <Titel>
- **Warum:** <kurze Begruendung mit Wichtigkeit, Risiko, Aufwand und Umsetzungsreife>

## Auswahl-Handoff
Wenn du diesen Punkt in die Umsetzung uebergeben willst, nutze `janus-backlog-handoff` mit `Mode: SELECTED_HANDOFF` und `Backlog Item: BACKLOG-XXX`.
```

If the user chooses an item, do not implement. Hand off to `janus-backlog-handoff`.
