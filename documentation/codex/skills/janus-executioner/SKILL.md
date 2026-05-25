---
name: janus-executioner
description: Execute exactly one Janus target task from bound artifacts after a valid preimplementation check. Use when the user asks to implement, fix, edit code, run task execution, continue a selected Backlog/Spec task, or apply changes after janus-preimplementation-check has passed.
---

# Janus Executioner

## Overview

Implement exactly one target task. Use bound artifacts only: task, Spec, Backlog item, precheck, and validation plan. Do not plan new features, expand scope, bypass evidence, or change provider/architecture boundaries unless the task explicitly requires it.

## Source References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\.windsurf\workflows\SKILL 4 – EXECUTIONER.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`
- `C:\KI\Janus-Projekt\AGENTS.md`

## Required Input

Require:

```text
Target Task:
Assigned Model:
Task:
Spec: <path | N/A WITH REASON>
Backlog Item: <BACKLOG-XXX | N/A>
Pre-Check: PRE-CHECK PASSED
```

If a precheck is claimed, validate the handoff literals from `janus-preimplementation-check`. Block if invalid.

## Model Gate

Default execution model is `5.3 codex`, medium/high.

Recommend `5.5` only for high-risk security/privacy/provider/memory architecture fixes or when the precheck requires strongest reasoning. Recommend `5.4 mini` only for deterministic low-risk docs/config edits.

## Golden Path

1. Load bound artifacts and isolate the target task.
2. Validate precheck/handoff before any edits.
3. Output a command-first Mini-TestPlan or N/A plan before product edits.
4. Implement only in target scope.
5. Run specified tests or the smallest meaningful test set.
6. Run Playwright/generator validation unless N/A is explicitly valid.
7. Fix verification failures only inside task scope, max two focused attempts.
8. End in exactly one canonical state: `PASS`, `BLOCKED`, `NEEDS_INFO`, `FAILED`, or `HANDOFF`.

## Command-First Rule

Before edits, state:

```text
MINI TEST PLAN
- Target Task:
- Scope:
- Files Expected:
- Unit/Integration Checks:
- Playwright/E2E Check:
- N/A Reason: <only if valid>
```

Playwright N/A is valid only for pure `.md`, `.yml`, or `.css` changes with no logic, chat, backend, provider, stream, tool, memory, or frontend runtime path.

## Precheck Handoff Gate

Valid precheck must contain:

```text
BEGIN COPY FOR SKILL 4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
Scope-Regel:
Automated Evidence Gate:
npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
Oracle-/TestPlan-Regel:
END COPY FOR SKILL 4
```

If missing:

```text
BLOCKED: INVALID_SKILL3_HANDOVER
Reason: Skill-3 handoff lacks complete V3.2 copyblock.
Required Fix: Run janus-preimplementation-check again.
```

## Provider Isolation

For provider-specific tasks:

- no cross-provider fallback
- no model switch as fake fix
- validate the original provider/test case
- if provider is not testable, output credential check without secrets
- if runtime evidence is missing, hand off to `janus-debug`

## TestSpec and TestRun Boundaries

For TestSpec/TestPlan/Oracle/Assertion tasks:

- edit source-of-truth TestSpec/Oracle only
- never patch old generated TestPlan manually
- never create fake TestResult evidence
- end with `IMPLEMENTATION COMPLETE - VALIDATION REQUIRED`
- hand off to `janus-test-pipeline`

For TestRun-finding product fixes:

- local implementation may complete
- do not mark Backlog DONE
- do not route to final audit until focused or full retest evidence exists
- hand off to `janus-test-pipeline`

## Failure Management

If validation fails:

- record exact failure command, code, evidence path, and excerpt
- make at most two focused fixes in scope
- if still failing or out of scope, hand off to `janus-debug`
- never proceed to final audit on unresolved failure

## Completion Rules

`TASK COMPLETE` or `ALL TASKS COMPLETE` requires an immediately preceding block:

```text
Auto-Verification:
- Status: PASS
```

If Auto-Verification is N/A, do not say `TASK COMPLETE`; use `N/A-SCOPE CLOSURE` with reason and next gate.

For final task completion, hand off to `janus-final-audit`; otherwise hand off to the next task/precheck.

## Output Skeleton

```text
TASK EXECUTION RESULT
Canonical State: PASS | BLOCKED | FAILED | HANDOFF | NEEDS_INFO
Target Task:
Changed Files:
Executed Checks:
Auto-Verification:
- Status: PASS | FAIL | N/A
- Evidence:

NEXT_SKILL_HANDOFF
Target Skill: janus-final-audit | janus-debug | janus-test-pipeline | janus-preimplementation-check
Canonical State: HANDOFF | BLOCKED
Required Artifacts:
Evidence Paths:
Failure Code:
Changed Files:
Decision:
Reason:
Copy Prompt:
```

## Validator

When an execution result is saved, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py <path-to-execution-result.md>
```

