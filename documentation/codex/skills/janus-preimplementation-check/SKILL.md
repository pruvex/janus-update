---
name: janus-preimplementation-check
description: Verify exactly one Janus task before implementation and produce a strict execution handoff. Use before code changes, when a Backlog handoff or task file is ready, when the user asks to start implementation, or when Codex must validate scope, artifacts, model, tests, and evidence gates before using janus-executioner.
---

# Janus Preimplementation Check

## Overview

This is a pure gate before implementation. It decides only `PRE-CHECK PASSED`, `PRE-CHECK FAILED`, `PRE-CHECK BLOCKED`, or `MODEL SWITCH REQUIRED`. Do not edit product code, generate TestPlans, run TestRuns, or expand scope.

## Source References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\.windsurf\workflows\SKILL 3 – PRE-IMPLEMENTATION VERIFICATION.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`
- `C:\KI\Janus-Projekt\AGENTS.md`

## Required Input

Require:

```text
Target Task: <task id>
Task: documentation/tasks/<task_file>.md
Spec: <spec path | N/A WITH REASON>
Backlog Item: <BACKLOG-XXX | N/A>
Mode: SINGLE_TASK_PRECHECK
Assigned Model: <5.3 codex | 5.4 mini | 5.5 | other explicit model>
```

If a task file contains multiple tasks, `Target Task` is mandatory.

## Validation Gates

Verify:

- task file exists and is readable
- target task is unique
- Spec exists or `N/A WITH REASON` is plausible
- Backlog ID matches task content and `BACKLOG.md` Handoff path if present
- assigned model is clear
- scope is atomic
- in-scope and out-of-scope are clear
- acceptance criteria are measurable
- risk is LOW, MEDIUM, or HIGH
- affected files/artifacts are named or deterministically derivable
- no open product/architecture decisions
- no provider fallback, architecture drift, or scope expansion
- required tests/evidence are explicit
- Git checkpoint is recommended for risky work via `janus-git-governance`

Block with `PRE-CHECK BLOCKED: ARTIFACT_IDENTITY_MISMATCH` if Backlog ID, Target Task, Task path, or Handoff path do not match.

## TestSpec and TestRun Boundary

For TestSpec, TestPlan, Test-Oracle, assertion, `containsAny`, `mustNotContain`, response-format, or TestRun-finding tasks:

- identify the source-of-truth TestSpec under `documentation/TEST_SPEC/`
- Skill 4 may edit only the source-of-truth TestSpec/Oracle file
- Skill 4 must not manually patch old `documentation/test-runs/*_plan.json`
- Skill 4 must not manually create `documentation/test-results/*`
- after TestSpec edit, route to `janus-test-pipeline`
- if no source-of-truth TestSpec can be determined, block with `PRE-CHECK BLOCKED: TESTSPEC_SOURCE_OF_TRUTH_MISSING`

For Live E2E/TestRun execution-only subtasks, route to `janus-test-pipeline` instead of implementation unless a small handoff artifact must first be written.

## Required PASS Literals

A valid PASS output must contain these literal lines:

```text
PRE-CHECK RESULT
PRE-CHECK PASSED
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

The Skill-4 copyblock must be a single fenced `text` code block.

## Forbidden PASS Content

Do not output PASS if the handoff contains:

- `PRE-CHECK RESULT: PASSED`
- `Pre-Check Decision:`
- `Skill 4 Handover`
- `BEGIN COPY FOR @[/SKILL 4`
- `Manual Janus Validation Gate`
- `Stop at Manual Janus Validation Gate`
- `Execution Model:` instead of `Assigned Model:`
- `Changed Files:`
- TestPlan/TestResult artifacts as already created by precheck
- optionalized generator/validator/Playwright wording like `sofern`, `alternativ`, or `nur wenn`
- product-code or scope-expansion clauses for Test-Oracle tasks

If the copyblock cannot be produced exactly, output:

```text
PRE-CHECK BLOCKED: SKILL-4-HANDOVER-INCOMPLETE
```

## PASS Output Template

Use:

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

```text
BEGIN COPY FOR SKILL 4
@[/SKILL 4 – EXECUTIONER]
Target Task: <task id>
Target Subtask: <subtask id | N/A>
Task: <task path>
Spec: <spec path | N/A WITH REASON>
Backlog Item: <BACKLOG-XXX | N/A>
Assigned Model: <model>
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- <concise scope/evidence summary>
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- <unit/integration/build command>
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
END COPY FOR SKILL 4
```
```

## Validator

When a precheck output is saved, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py <path-to-precheck-output.md>
```

