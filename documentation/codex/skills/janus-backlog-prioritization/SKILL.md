---
name: janus-backlog-prioritization
description: Review and prioritize open Janus Backlog items with a token-saving DELTA mode. Use after Backlog intake, when the user asks what to do next, when open items need importance/risk/effort/readiness/recommendation fields, or before selecting an item for Diamond pipeline handoff.
---

# Janus Backlog Prioritization

## Overview

Evaluate open items in `C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md`, persist missing evaluation fields, and recommend the next best item. Do not implement, create handoff files, or route directly to execution.
This is primarily a ChatGPT-led prioritization skill. Codex should only consume a bounded prioritization handoff when a cross-actor backlog review or file update is explicitly needed.

## Source Reference

Legacy source:

- `C:\KI\Janus-Projekt\.windsurf\workflows\BACKLOG SKILL 2 – REVIEW PRIORISIERUNG.md`

Read only if exact wording is needed.

## Model Gate

Default recommendation:

- Model: `5.4` for meaningful prioritization.
- Intelligence: `medium`.
- Use `5.4` `low` for purely mechanical cache-field cleanup when the current `5.4` context is warm or prioritization continues in `5.4`.
- Use `5.4 mini` only for separated mechanical cleanup batches that are still likely cheaper than staying on warm `5.4`.
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
- Do not turn a raw user wish directly into a prioritization candidate; use `janus-backlog-intake` first unless the backlog item already exists.
- Do not invent product decisions, acceptance criteria, or implementation scope that are missing from the backlog source.
- Do not route directly to implementation, precheck, execution, or release.
- Persist changed evaluation fields in `BACKLOG.md`.
- Do not deeply re-review unchanged items that already have all cache fields.
- Use `BACKLOG_ACTIVE_SUMMARY.md` first and read `BACKLOG.md` only as deeply as the selected open item set requires.
- If the backlog item is still feature-ambiguous or product-decision-heavy, route back to `janus-feature-design` instead of forcing a priority verdict.
- If nothing changed, report `Bewertungs-Cache: unveraendert`.
- Do not treat a vague `ok` as a valid handoff substitute.

## Intake Boundary

Use this skill only after one of these is true:

- a backlog candidate already exists in `BACKLOG.md`
- `janus-backlog-intake` produced a valid intake result
- the user explicitly asks for backlog prioritization of existing open items

Do not use this skill as a replacement for:

- `janus-backlog-intake` when the request is still a raw wish, bug, or annoyance
- `janus-feature-design` when scope, desired behavior, or product tradeoffs are still unresolved

## Backlog Reading Rule

For overview and candidate selection, read `C:\KI\Janus-Projekt\documentation\backlog\BACKLOG_ACTIVE_SUMMARY.md` first when it exists.

Then read `C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md` to verify:

- exact cache fields
- exact status placement
- acceptance criteria
- contradictions or malformed sections

`BACKLOG.md` remains the binding source of truth.

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
4. Compare top candidates by importance, risk, effort, readiness, dependency shape, and likely pipeline cost.
5. Persist new/changed cache fields.

If multiple items remain equally plausible and the tie depends on missing product context, unresolved dependencies, or stale cache fields outside the chosen slice, stop and report the ambiguity instead of forcing a fake ranking.

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

If control moves across an actor or chat boundary, emit exactly one compact fenced `text` block with:

- `NEXT: janus-backlog-handoff` or `NEXT: janus-feature-design`
- the selected `BACKLOG-XXX` or blocked candidate cluster
- one short note about the decisive priority reason or ambiguity

For ChatGPT -> Codex transitions, place model/reasoning above the block.
A bare `ok` or similar acknowledgement is never a valid handoff replacement.
