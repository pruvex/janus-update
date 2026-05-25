---
name: janus-debug
description: Debug failed Janus execution, tests, provider/runtime behavior, E2E infrastructure, or final-audit blockers with bounded iterations and evidence. Use after janus-executioner fails, janus-final-audit blocks, Playwright/TestRun evidence fails, provider/runtime evidence is required, or the user reports a reproducible Janus mismatch after implementation.
---

# Janus Debug

## Overview

Perform bounded debug inside the bound task/spec/backlog scope. Do not add new features, expand scope, bypass generated test evidence, expose secrets, or claim `FIXED` without validation.

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

## Model Gate

Default: `5.3 codex`, high.

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

## Verification Chain

After a fix touching chat, frontend, backend, provider, tool, memory, stream, or runtime:

1. Mini Auto-Verification or valid N/A.
2. Artifact Identity Check for plan, runner, executed path.
3. Final Feature Suite PASS, or explicit valid N/A. If no suite is definable, do not say `FIXED`.
4. Handoff to `janus-final-audit` or `janus-test-pipeline`.

Manual checks can supplement evidence but cannot replace generated/automated evidence.

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

## Fixed Criteria

`SKILL 5 DEBUG RESULT: FIXED` requires all:

- Auto-Verification `PASS`
- Final Feature Suite `PASS` or valid N/A
- changed files or explicit no-code debug correction
- `NEXT_SKILL_HANDOFF`
- target skill is `janus-final-audit` or `janus-test-pipeline`

For TestRun findings, prefer `janus-test-pipeline` retest before final audit.

## Escalation

On iteration 5, stagnation, or non-deterministic root cause:

- create compact escalation package under `.windsurf/tmp/skill5_escalation_<task>_<YYYYMMDD-HHMM>.md`
- no raw secrets or full logs
- include evidence paths, failure codes, attempted fixes, changed files, and exact ask for `5.5`
- output `SKILL 5 ESCALATION REQUIRED`

## Output Skeleton

```text
SKILL 5 DEBUG RESULT: FIXED | NEEDS RETEST | ESCALATION REQUIRED | BLOCKED | OUT OF SCOPE

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

## Validator

When a debug result is saved, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-debug\scripts\validate_debug_result.py <path-to-debug-result.md>
```

