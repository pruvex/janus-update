---
name: janus-task-breakdown
description: Refine one Janus task artifact against its source Spec and release exactly one target task for preimplementation check. Use after janus-spec-to-task or backlog handoff when tasks need validation, source-of-truth checks, test enrichment, model confirmation, or a single-task handoff to janus-preimplementation-check.
---

# Janus Task Breakdown

## Purpose

Use this skill to refine Skill-1 task artifacts into exactly one implementation-ready target task for `janus-preimplementation-check`.

It validates scope, files, tests, source of truth, and execution model. It does not implement code.

## Inputs

- One task file under `documentation/tasks/`.
- One source Spec file.
- Optional Backlog item.
- Optional target task or subtask.

When artifacts are named, they are the only requirements sources.

## Hard Rules

- No implementation.
- No code generation.
- No new requirements.
- No architecture decisions.
- No full chain auto-release.
- Release exactly one target task.
- Later tasks require a separate handoff.

## Validation Gates

For each task, check:

- goal is clear
- scope is bounded
- files are concrete or deliberately scoped
- acceptance criteria are binary
- tests are appropriate
- execution model is valid
- no verify-only, review-only, analysis-only, or design-only standalone task is forwarded

If a task affects TestSpec, test oracle, assertions, `containsAny`, `mustNotContain`, response format, or expected output, enforce source of truth:

- `documentation/TEST_SPEC/*.md` is primary.
- `documentation/test-runs/*_plan.json` is generated evidence only.
- A test-plan-only oracle patch is blocked.
- After TestSpec changes, route to `janus-test-pipeline`.

## Model Routing

- `5.4`: normal task refinement and risk judgment.
- `5.4 mini`: mechanical task artifact validation.
- `5.3 codex`: later implementation, not this skill.
- `5.5`: escalation for ambiguous, security-sensitive, or architecture-heavy tasks.

## Validation Script

Use when useful:

```powershell
python C:\Users\pruve\.codex\skills\janus-task-breakdown\scripts\validate_task_handoff.py --task <TaskFile> --target <TASK-ID>
```

## Handoff

End with exactly one copyable handoff:

```text
@janus-preimplementation-check
Spec: <source spec file>
Task: <task file>
Backlog Item: <BACKLOG-XXX | N/A>
Target Task: <TASK-XXX.Y>
Target Subtask: <SUBTASK-XXX-YY | N/A>
Mode: SINGLE_TASK_PRECHECK
Execution Model: <5.3 codex | 5.4 mini>
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```

## Decisions

Return one:

- `TASK DESIGN COMPLETE`: exactly one target task is ready for precheck.
- `TASK DESIGN BLOCKED`: source of truth, files, tests, or scope are unsafe.
- `TASK AMBIGUOUS`: Spec or task needs clarification.
- `MODEL SWITCH REQUIRED`: use `5.5` for high-risk ambiguity.

## Output

Use:

```text
TASK BREAKDOWN RESULT
- Spec:
- Task File:
- Target Task:
- Decision:
- Source Of Truth:
- Files:
- Tests:
- Execution Model:
- Readiness:
- Next Skill:
- Model Recommendation:
```
