---
name: janus-quickchange
description: Execute a trivial low-risk Janus quick change such as copy replacement, label rename, percentage display, or tightly bounded local polish without sending the request through the full Backlog-to-Spec pipeline. Use only when scope is tiny, acceptance is obvious, and a Mini-TestPlan plus validation evidence can be produced before and after the edit.
---

# Janus Quickchange

## Overview

Use this skill for one tiny bounded change on an existing Janus surface. It is a guarded express lane for edits that would be wasteful in the full pipeline, not a loophole for skipping scope control, evidence, or rerouting.

Default execution model is `5.4`, low/medium. Stay on warm `5.4` when possible. Escalate to `janus-backlog-intake`, `janus-feature-design`, or `janus-preimplementation-check` as soon as the change stops being trivial.

## Allowed Scope

Typical fits:

- copy replacement, German/English wording cleanup, tooltip or label rename
- percentage, unit, icon, spacing, or small presentation fix
- tiny local UI polish in one component cluster
- deterministic docs or config touch tied to the same bounded intent

All of these must stay true:

- one user-visible intent
- likely one to three touched files in one file cluster
- no new product decision
- no persistence, routing, API, provider, auth, security, privacy, migration, or release-boundary change
- targeted validation is known before editing

## Do Not Use

Stop and reroute when any of these apply:

- a Backlog item should exist for visibility, prioritization, or follow-up tracking
- multiple plausible implementations or product decisions exist
- the change may affect saved state, data shape, backend contracts, or several surfaces
- verification needs a broad test matrix, unclear manual exploration, or a normal precheck
- the user asked for a feature, refactor, test expansion, or architecture change

## Required Input

Start only when you can state this brief up front:

```text
QUICKCHANGE BRIEF
- Request:
- Scope:
- Expected Files:
- Acceptance:
- Why Quickchange:
- Reroute Trigger:
```

If any line is unclear, do not guess broadly. Route out.

## Workflow

1. Read only the directly affected files and the smallest binding context.
2. Emit `QUICKCHANGE BRIEF`.
3. Emit a command-first `MINI TEST PLAN` before edits.
4. Make the smallest possible change set.
5. Run the targeted checks from the plan.
6. If checks fail, fix only inside the brief. Make at most two focused attempts.
7. If scope expands, stop and reroute instead of growing the quickchange.
8. End in exactly one canonical state from the pipeline contract.

## Mini Test Plan

Before edits, state:

```text
MINI TEST PLAN
- Scope:
- Files Expected:
- Checks:
- Visual Check:
- N/A Reason:
```

`N/A Reason` is allowed only when the omitted check truly does not apply.

## Validation

Prefer the cheapest real evidence that still proves the change:

- targeted unit test or existing focused test command
- narrow build, lint, or typecheck command
- screenshot, Browser check, or documented manual visual confirmation for local UI-only tweaks
- exact file diff review when the change is pure text/config and runtime validation is genuinely unnecessary

Never claim completion without executed evidence or an explicit documented blocker.

## Reroute Rules

Reroute to:

- `janus-backlog-intake` when the issue deserves tracking or stops being tiny
- `janus-feature-design` when product decisions appear
- `janus-preimplementation-check` when implementation scope is real but still bounded
- `janus-debug` when validation fails for reasons outside the brief

## Output Skeleton

```text
QUICKCHANGE RESULT
Canonical State: PASS | BLOCKED | FAILED | HANDOFF | NEEDS_INFO
Request:
Changed Files:
Executed Checks:
Evidence Paths:
Notes:

NEXT_SKILL_HANDOFF
Target Skill: janus-git-governance | janus-backlog-intake | janus-feature-design | janus-preimplementation-check | janus-debug | none
Canonical State: PASS | HANDOFF | BLOCKED | FAILED | NEEDS_INFO
Required Artifacts:
Evidence Paths:
Changed Files:
Decision:
Reason:
Recommended Model:
Recommended Intelligence:
New Chat: yes | no
```

Use `Target Skill: none` only when the quickchange is fully validated and no additional Janus gate is required yet.
