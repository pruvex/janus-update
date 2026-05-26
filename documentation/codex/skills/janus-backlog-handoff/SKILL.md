---
name: janus-backlog-handoff
description: Enrich Janus Backlog routing metadata, prepare dashboard-ready handoff artifacts, and create selected Diamond pipeline handoffs. Use after Backlog prioritization, when the user selects a Backlog item, asks to prepare the dashboard, asks to route READY items, or needs copy-paste prompts for the next Janus Diamond skill.
---

# Janus Backlog Handoff

## Overview

Route `READY` Backlog items into the correct Diamond pipeline entry point. Do not prioritize, implement, debug, final-audit, or release.

## Source Reference

Legacy source:

- `C:\KI\Janus-Projekt\.windsurf\workflows\BACKLOG SKILL 3 – EXECUTION HANDOFF.md`

Read only if exact wording is needed.

## Modes

Default is `DASHBOARD_PREP`.

- `ROUTING_ENRICHMENT`: add missing routing metadata only.
- `DASHBOARD_PREP`: add routing metadata and dashboard-ready handoff artifacts for suitable `READY` items; keep items `READY`.
- `SELECTED_HANDOFF`: process exactly one selected `READY` item, create/reuse the handoff artifact, then move it to `IN PROGRESS`.

## Hard Rules

- No code changes.
- No architecture decisions.
- No new prioritization.
- Only `READY` items can receive handoff artifacts.
- `SELECTED_HANDOFF` requires exactly one Backlog ID.
- Do not move items to `IN PROGRESS` unless mode is `SELECTED_HANDOFF`.
- If status changes, physically move the entire item block under the canonical status heading.
- Dashboard fields must be individual markdown list fields.
- After Backlog changes, sync dashboard snapshot with `npm run sync:backlog` in `C:\KI\Janus-Projekt\janus-dashboard` or explicitly report why not run.

## Dashboard Fields

Write:

```markdown
- **Entry Point:** SPEC_PIPELINE_START | TASK_BREAKDOWN | PRE_IMPLEMENTATION_VERIFICATION | EXECUTION_READY | ROUTING_BLOCKED
- **Routing reason:** <short reason>
- **Routing confidence:** HIGH | MEDIUM | LOW
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** YYYY-MM-DD
- **Handoff:** <path> | none
- **Recommended next skill:** SKILL 1 | SKILL 2 | SKILL 3 | SKILL 4 | none
- **Handoff created:** YYYY-MM-DD | none
```

## Entry Point Matrix

Valid combinations:

```text
SPEC_PIPELINE_START -> documentation/Planned Features/...md -> SKILL 1
TASK_BREAKDOWN -> existing Spec/Tasks -> SKILL 2
PRE_IMPLEMENTATION_VERIFICATION -> documentation/tasks/...md -> SKILL 3
EXECUTION_READY -> documentation/tasks/...md + Precheck artifact + Target Task -> SKILL 4
ROUTING_BLOCKED -> none -> none
```

Invalid combinations must block completion.

## Entry Point Rules

Use `SPEC_PIPELINE_START` for new features, larger enhancements, product/UX behavior, multiple likely tasks, medium/high risk, or non-atomic scope.

Use `PRE_IMPLEMENTATION_VERIFICATION` for small clear bugfixes or local changes with one target, clear acceptance criteria, and low or bounded medium risk.

Use `TASK_BREAKDOWN` only if a suitable spec or coarse task artifact already exists but needs breakdown.

Use `EXECUTION_READY` only if a valid Skill-3 precheck PASS artifact and Target Task already exist.

Use `ROUTING_BLOCKED` if required information is missing, risk/scope is ambiguous, status is not `READY`, or multiple entry points are equally plausible.

## Artifacts

For `SPEC_PIPELINE_START`, create or reuse:

```text
C:\KI\Janus-Projekt\documentation\Planned Features\backlog_BACKLOG-XXX_<slug>.md
```

For `PRE_IMPLEMENTATION_VERIFICATION`, create or reuse:

```text
C:\KI\Janus-Projekt\documentation\tasks\backlog_BACKLOG-XXX_<slug>.md
```

Use concise artifact content. Do not invent product requirements beyond the Backlog item.

## Completion Gate

A success output must include `## Next Skill Copy Prompts`.

Each prepared item gets exactly one fenced `text` copy block:

```text
@[/SKILL 1 - SPEC TO TASK COMPILER]
Spec: documentation/Planned Features/...
Backlog Item: BACKLOG-XXX
```

or

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: <task id>
Task: documentation/tasks/...
Backlog Item: BACKLOG-XXX
```

or

```text
@[/SKILL 4 - EXECUTIONER]
Target Task: <task id>
Task: documentation/tasks/...
Pre-Check: <artifact path>
Backlog Item: BACKLOG-XXX
```

If prompts cannot be produced, output:

```text
BACKLOG SKILL 3 BLOCKED: NEXT_SKILL_HANDOVER_MISSING
Reason: <missing prompt or artifact mismatch>
```

## Validator

When checking Backlog structure after edits, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-backlog-handoff\scripts\validate_backlog.py C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md
```
