---
name: janus-backlog-handoff
description: Enrich Janus Backlog routing metadata, prepare dashboard-ready handoff artifacts, and create selected Diamond pipeline handoffs. Use after Backlog prioritization, when the user selects a Backlog item, asks to prepare the dashboard, asks to route READY items, or needs copy-paste prompts for the next Janus Diamond skill.
---

# Janus Backlog Handoff

## Overview

Route `READY` Backlog items into the correct Diamond pipeline entry point. Do not prioritize, implement, debug, final-audit, or release.
This is primarily a ChatGPT-side routing skill. Codex normally consumes the resulting handoff rather than executing this skill as the next actor.

## Tri-Modal Rollout Note

Global delegation vocabulary across Janus is now:

- `1 = Codex`
- `2 = OpenRouter`
- `3 = Cursor Composer`
- `4 = Cursor API`

This skill's bounded selected-handoff review lane is now wired through the shared manifest-backed `documentation/codex/model-routing/scripts/janus_delegate.py` entry. Cursor API is now a valid short-review option, while OpenRouter remains available as fallback.

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

## Bounded Delegation Gate

For a narrowly bounded `SELECTED_HANDOFF` review slice, this skill may offer the shared tri-modal operator gate only when all of the following are true:

- exactly one `READY` backlog item is selected
- the delegated task is recommendation-only and bounded to routing plus handoff suggestion
- no authoritative backlog write, status move, artifact write, Git action, release action, or final routing decision is delegated
- Codex remains the final reviewer and local writer of any backlog or task artifact

Binding implementation artifact:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_backlog_handoff_review_runner.py`

Current bounded winner for the representative `BACKLOG-109` selected-handoff slice:

- `qwen/qwen3-coder-30b-a3b-instruct`

Use the shared delegate entry first:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane backlog_handoff_review --task-id TASK-BH-001 --workflow-id WF-BACKLOG-HANDOFF-REVIEW-001 --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-backlog-handoff/backlog_handoff_input_package.json --estimated-codex-saved-tokens 12000 --estimated-delegation-overhead-tokens 4000
```

Current lane behavior:

- `1 = Codex`
- `2 = OpenRouter`
- `4 = Cursor API`
- Cursor API is the current recommended backend for this bounded short-review slice.
- The existing `codex_backlog_handoff_review_runner.py` remains the downstream OR helper planned by `janus_delegate.py`.

Gate rules:

- if the user chooses `1`, `local`, or `codex`, invoke the same runner with `--operator-choice local`
- if the user chooses `2`, `or`, `openrouter`, or `opr`, invoke the same runner with `--operator-choice delegated --input-package-json <bounded package>`
- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, invoke the shared delegate and keep the task bounded to the same review package
- use only a bounded review package; do not delegate full backlog writing
- accepted delegated output remains review material only; Codex must still perform any real backlog/task artifact changes locally

Forbidden inside this path:

- delegated backlog status changes
- delegated handoff artifact creation as authoritative repo state
- delegated next-skill authority
- delegated Git, release, routing-table, or `CURRENT_STATE` writes

## Context Budget

Work on the smallest Backlog slice possible:

- one selected `BACKLOG-XXX` in `SELECTED_HANDOFF`
- one filtered READY cluster in `DASHBOARD_PREP`
- one metadata-only item set in `ROUTING_ENRICHMENT`

Do not reread unrelated `DONE` history when routing a current READY item unless duplicate or lifecycle identity is unclear.

## Backlog Reading Rule

For orchestration and quick READY-state orientation, read `C:\KI\Janus-Projekt\documentation\backlog\BACKLOG_ACTIVE_SUMMARY.md` first when it exists.

Then verify the selected item in `C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md` before creating or reusing handoff artifacts.
Do not deep-read the full backlog when one selected `READY` item block or one contradiction check is enough.

Always fall back to `BACKLOG.md` when:

- routing metadata must be written back
- acceptance criteria or risk fields matter
- section structure or item status looks contradictory

`BACKLOG.md` remains the binding source of truth.

## Dashboard Fields

Write:

```markdown
- **Entry Point:** SPEC_PIPELINE_START | TASK_BREAKDOWN | PRE_IMPLEMENTATION_VERIFICATION | EXECUTION_READY | ROUTING_BLOCKED
- **Routing reason:** <short reason>
- **Routing confidence:** HIGH | MEDIUM | LOW
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** YYYY-MM-DD
- **Handoff:** <path> | none
- **Recommended next skill:** janus-feature-design | janus-task-breakdown | janus-preimplementation-check | janus-executioner | none
- **Handoff created:** YYYY-MM-DD | none
```

## Entry Point Matrix

Valid combinations:

```text
SPEC_PIPELINE_START -> documentation/Planned Features/...md -> janus-feature-design
TASK_BREAKDOWN -> existing Spec/Tasks -> janus-task-breakdown
PRE_IMPLEMENTATION_VERIFICATION -> documentation/tasks/...md -> janus-preimplementation-check
EXECUTION_READY -> documentation/tasks/...md + Precheck artifact + Target Task -> janus-executioner
ROUTING_BLOCKED -> none -> none
```

Invalid combinations must block completion.

## Entry Point Rules

Use `SPEC_PIPELINE_START` for new features, larger enhancements, product/UX behavior, multiple likely tasks, medium/high risk, or non-atomic scope.

Use `PRE_IMPLEMENTATION_VERIFICATION` for small clear bugfixes or local changes with one target, clear acceptance criteria, and low or bounded medium risk.

Use `TASK_BREAKDOWN` only if a suitable spec or coarse task artifact already exists but needs breakdown.

Use `EXECUTION_READY` only if a valid `janus-preimplementation-check` PASS artifact and Target Task already exist.

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

Prefer a compact handoff package inside the artifact or response:

```text
HANDOFF_SCOPE:
- Backlog Item:
- Entry Point:
- Required Artifact:
- Required Next Skill:
- Evidence Paths:
- Dropped Context:
```

## Completion Gate

A success output must include `## Next Skill Copy Prompts`.
A bare `ok` or similar acknowledgement is never a valid handoff replacement.

For every ChatGPT -> Codex transition, output:

- model/reasoning header above the handoff
- exactly one fenced `text` block per prepared item
- short, artifact-bound, cache-friendly wording

Each prepared item gets exactly one fenced `text` copy block:

```text
NEXT: janus-feature-design
NEW_CHAT_HANDOFF
Spec Seed: documentation/Planned Features/...
Backlog Item: BACKLOG-XXX
```

or

```text
NEXT: janus-preimplementation-check
Task: documentation/tasks/...
Backlog Item: BACKLOG-XXX
```

or

```text
NEXT: janus-executioner
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

Every successful handoff should also state:

```text
Keep Context:
- selected backlog item
- created/reused handoff artifact
- exact next-skill prompt

Drop Context:
- unrelated READY items
- old DONE history
- broad backlog narrative
```

## Validator

When checking Backlog structure after edits, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-backlog-handoff\scripts\validate_backlog.py C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md
```
