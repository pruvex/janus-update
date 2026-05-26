---
name: janus-spec-to-task
description: Compile one approved Janus Feature Spec into deterministic execution task artifacts. Use after janus-spec-review when the user asks to create task files, compile a Spec to tasks, prepare Skill 2/task breakdown, or start implementation routing from a Spec.
---

# Janus Spec To Task

## Purpose

Use this skill to transform one reviewed Janus Feature Spec into a deterministic task file under `documentation/tasks/`.

It creates execution-ready task structure for `janus-task-breakdown`. It does not implement code and does not make architecture or product decisions.

## Inputs

- One reviewed Feature Spec.
- Optional Backlog item identity.

If a Spec file is named, use only that file as source of truth. Ignore chat history and older drafts.

## Hard Rules

- No implementation.
- No code generation.
- No architecture decisions.
- No feature expansion.
- No tasks based only on analysis, design, review, verification, or documentation marking.
- If deterministic decomposition is impossible, stop and route back to `janus-spec-review` with a model escalation recommendation.

## Task Eligibility

Every execution task must produce at least one of:

- code change in a concrete file or module
- test change in a concrete test file
- configuration/data change explicitly allowed by the Spec
- documentation change only if documentation is explicit feature scope

Review, analysis, verification, and non-regression work belong inside steps, acceptance criteria, tests, or precheck notes.

## Task File Contract

Create or update one task file under `documentation/tasks/` with:

```text
TASK-XXX
- Source Spec:
- Backlog Item:
- Feature:
- Generated At:

## Generated Tasks

### TASK-XXX.1 <title>
- Ziel:
- Scope:
- Files:
- Steps:
- Acceptance Criteria:
- Tests:
- Model: 5.3 codex | 5.4 mini
- Reason:
```

Use `5.3 codex` for implementation/refactor/test execution tasks. Use `5.4 mini` only for deterministic single-file text/data/test artifact edits. Recommend `5.4` or `5.5` as escalation, not as normal execution, when decomposition is ambiguous or high-risk.

Validate task structure when useful:

```powershell
python C:\Users\pruve\.codex\skills\janus-spec-to-task\scripts\validate_task_artifact.py --task <TaskFile>
```

## Handoff

End with exactly one copyable handoff to `janus-task-breakdown`:

```text
@janus-task-breakdown
Spec: <source spec file>
Task: <generated task file>
Backlog Item: <BACKLOG-XXX | N/A>
Target Task: <first generated task id>
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
```

## Output

Use:

```text
SPEC COMPILATION RESULT
- Spec:
- Task File:
- Generated Tasks:
- Execution Models:
- Validation:
- Next Skill:
- Model Recommendation:
```
