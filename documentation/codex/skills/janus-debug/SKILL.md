---
name: janus-debug
description: Debug failed Janus execution, tests, provider/runtime behavior, E2E infrastructure, or final-audit blockers with bounded iterations and evidence. Use after janus-executioner fails, janus-final-audit blocks, Playwright/TestRun evidence fails, provider/runtime evidence is required, or the user reports a reproducible Janus mismatch after implementation.
---

# Janus Debug

## Overview

Perform bounded debug inside the bound task/spec/backlog scope. Do not add new features, expand scope, bypass generated test evidence, expose secrets, or claim `FIXED` without validation.
This is primarily a Codex-led debug skill. ChatGPT should take over only when evidence is unclear, risk escalates, a product decision is required, or an actor/chat boundary needs one compact handoff.

## Source References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\.windsurf\workflows\SKILL 5 – FEATURE DEBUG.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`
- `C:\KI\Janus-Projekt\AGENTS.md`

## Required Debug Package

Require:

- feature/task/spec/backlog context
- failed command or audit finding
- expected vs actual behavior
- evidence paths
- changed files
- logs or reason logs are unavailable
- current iteration number
- previous failure code/evidence summary when iteration > 1

If missing, return `SKILL 5 DEBUG RESULT: BLOCKED` with `Reason: DEBUG PACKAGE INCOMPLETE`.
Bind exactly one failure slice per run. If the package mixes multiple unrelated bugs, failure chains, or fix goals, block and require a narrower debug package instead of batching them together.

Do not reconstruct scope from broad chat history when the debug package, failure code, and evidence paths are already sufficient to isolate the slice.

## WHAT_I_LEARNED Lookup

Before iteration 1 for a non-trivial failure, search targeted terms from the failure code, exact error text, affected subsystem, and evidence file names:

```powershell
python documentation\codex\scripts\search_what_i_learned.py --query "<failure-code exact-error subsystem>"
```

Do not load the full file. Apply a learned pattern only if it directly matches the current root cause or tripwire. If a fix produces a new reusable root-cause pattern, route it to `janus-documentation-update` for append-only learning capture.

## Model Gate

Default: `5.4`, high.

Recommend `5.5`, high/very high, when:

- root cause is non-deterministic
- multiple plausible causes remain
- security/privacy/provider/memory/release risk is high
- iteration 5 is reached
- stagnation guard triggers

## Iteration Rules

- Max 5 iterations per same failure chain.
- Each iteration needs new or updated evidence.
- From iteration 2 onward, compare failure code and evidence with previous iteration.
- Before iteration 5, stop and escalate if there are 3 unchanged transitions or 4 identical failure snapshots.
- After iteration 5 without valid fix, escalate to `5.5`.
- If evidence becomes contradictory, stale, or no longer points to one failure slice, stop with `BLOCKED` instead of widening scope.

## Verification Chain

After a fix touching chat, frontend, backend, provider, tool, memory, stream, or runtime:

1. Mini Auto-Verification or valid N/A.
2. Artifact Identity Check for plan, runner, executed path.
3. Final Feature Suite PASS, or explicit valid N/A. If no suite is definable, do not say `FIXED`.
4. Handoff to `janus-final-audit` or `janus-test-pipeline`.

Manual checks can supplement evidence but cannot replace generated/automated evidence.
Do not make product decisions, architecture changes, or scope additions inside debug. Route those decisions back to the caller or the appropriate upstream planning skill.

## Generator and Runner Gate

Classify generator/runner failures exactly:

- `GENERATOR_PLAN_INVALID`
- `GENERATOR_RUNNER_FAILED`
- `RUNNER_VALIDATION_FAILED`
- `RUNNER_ARTIFACT_MISMATCH`
- `ASSERTION_ORACLE_TOO_NARROW`
- `STALE_RUNNER_EXECUTED`

Do not use a handwritten Playwright runner as final evidence for `FIXED`.

## Secret Redaction Gate

Never output secrets, bearer tokens, JWTs, cookies, API keys, internal keys, config values, or complete Authorization headers.

Allowed: paths, key names, presence/length checks, non-reconstructable fingerprints if needed.

If a secret would appear, block with:

```text
SKILL 5 OUTPUT BLOCKED: SECRET_REDACTION_REQUIRED
```

## Bounded Delegation Gate

This skill now has one bounded assist-only delegation class:

- `debug_hypothesis_review`

Use it only when the current debug slice is asking for bounded hypothesis review rather than a live fix.

Offer the operator choice only when all are true:

- one bounded debug package exists
- evidence can be safely redacted
- Codex still owns reproduction, validation, and the next debug action
- no local command execution needs to be delegated
- the productive gate confirms this is exactly `debug_hypothesis_review` and the pre-call estimate stays within the bounded debug budget

Operator wording:

- `1 = Codex`
- `2 = OR-Arbeitspferd`

Current delegated meaning:

- bounded assist-only hypothesis review
- no delegated local command execution
- no delegated test execution
- no delegated final fix claim
- Codex remains validation and acceptance owner

Bounded helper path:

```powershell
python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class debug_hypothesis_review ...
```

Consumer integration path for everyday `janus-debug` work:

- build one redacted package with `codex_debug_hypothesis_review_runner.build_consumer_input_package(...)`
- enter the operator gate through `codex_debug_hypothesis_review_runner.run_consumer_flow(...)`
- keep the visible everyday operator wording aligned with the productive Dev-workhorse convention: `1 = Codex`, `2 = OR-Arbeitspferd`
- if the productive gate rejects the slice, do not show an OR choice; keep the step deterministically Codex-only
- for the released `TASK-SPEC23.2` rollout, the OR branch may execute exactly one bounded hypothesis-review run with file-first capture or fixture validation; the delegated branch must resolve to exactly one runtime mode before dispatch
- if no bounded runtime mode is present, or if capture, usage, validation, or healthcheck gates fail, fall back directly to a visible Codex-only continuation

Do not treat this as production routing, broad sidecar debug authority, or a replacement for the normal `janus-debug` evidence chain.

## Fixed Criteria

`SKILL 5 DEBUG RESULT: FIXED` requires all:

- Auto-Verification `PASS`
- Final Feature Suite `PASS` or valid N/A
- changed files or explicit no-code debug correction
- `NEXT_SKILL_HANDOFF`
- target skill is `janus-final-audit` or `janus-test-pipeline`

For TestRun findings, prefer `janus-test-pipeline` retest before final audit.

Use these canonical meanings:

- `FIXED`: one bounded failure slice is resolved and validated
- `BLOCKED`: required evidence is missing, contradictory, redaction-limited, or unsafe to continue
- `NEEDS_INFO`: one specific clarification or artifact is missing from the bound slice
- `REROUTE`: the slice belongs in `janus-test-pipeline`, `janus-executioner`, `janus-final-audit`, or caller review instead of more debug

A bare `ok` or similar acknowledgement is never a valid handoff replacement.

## Escalation

On iteration 5, stagnation, or non-deterministic root cause:

- create compact escalation package under `.windsurf/tmp/skill5_escalation_<task>_<YYYYMMDD-HHMM>.md`
- no raw secrets or full logs
- include evidence paths, failure codes, attempted fixes, changed files, and exact ask for `5.5`
- output `SKILL 5 ESCALATION REQUIRED`

## Output Skeleton

```text
SKILL 5 DEBUG RESULT: FIXED | BLOCKED | NEEDS_INFO | REROUTE | ESCALATION REQUIRED

Iteration: <1-5>
Progress-Validierung: Failure Code <code>; Evidence geaendert ggü. N-1: JA | NEIN | N/A; Stagnationszaehler: <n>; Stopp-Regel ausgeloest: JA | NEIN
Root Cause:
Fix Summary:
Auto-Verification:
- Status: PASS | FAIL | N/A
- Evidence:
Artifact Identity Check: PASS | FAIL | N/A
Final Feature Suite: PASS | FAIL | N/A WITH REASON
Changed Files:

NEXT_SKILL_HANDOFF
Target Skill: janus-final-audit | janus-test-pipeline | janus-debug | janus-backlog-handoff
Canonical State: HANDOFF | ESCALATED | BLOCKED
Required Artifacts:
Evidence Paths:
Failure Code:
Changed Files:
Decision:
Reason:
Copy Prompt:
```

If control moves across an actor or chat boundary, emit exactly one compact fenced `text` block with:

- `NEXT:` and the exact next skill when known
- the bound failure slice identity
- the primary blocker or fix state
- the minimum evidence or action needed next

## Validator

When a debug result is saved, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-debug\scripts\validate_debug_result.py <path-to-debug-result.md>
```
