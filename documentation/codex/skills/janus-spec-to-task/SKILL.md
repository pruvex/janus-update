---
name: janus-spec-to-task
description: Compile one approved Janus Feature Spec into deterministic execution task artifacts. Use after janus-spec-review when the user asks to create task files, compile a Spec to tasks, prepare Skill 2/task breakdown, or start implementation routing from a Spec.
---

# Janus Spec To Task

## Purpose

Use this skill to transform one reviewed Janus Feature Spec into a deterministic task file under `documentation/tasks/`.

It creates execution-ready task structure for `janus-task-breakdown`. It does not implement code and does not make architecture or product decisions.
This is primarily a ChatGPT-led compilation skill. Codex normally consumes the resulting task artifact handoff rather than leading the compilation decision.

## Inputs

- One `APPROVED` Feature Spec.
- Optional Backlog item identity.

If a Spec file is named, use only that file as source of truth. Ignore chat history and older drafts.
If approval evidence is missing, contradictory, or the Spec is not final, block instead of inferring readiness from surrounding context.

## Hard Rules

- No implementation.
- No code generation.
- No architecture decisions.
- No product decisions from chat context.
- No invented requirements.
- No feature expansion.
- No tasks based only on analysis, design, review, verification, or documentation marking.
- If deterministic decomposition is impossible, stop and route back to `janus-spec-review` with a model escalation recommendation.
- Do not treat a vague `ok` as approval evidence or as a valid handoff substitute.

## Task Eligibility

Every execution task must produce at least one of:

- code change in a concrete file or module
- test change in a concrete test file
- configuration/data change explicitly allowed by the Spec
- documentation change only if documentation is explicit feature scope

Review, analysis, verification, and non-regression work belong inside steps, acceptance criteria, tests, or precheck notes.

Deterministic task artifact means:

- every generated task maps directly to explicit approved Spec scope
- no task depends on hidden product decisions or guessed architecture
- file targets, acceptance intent, and tests are concrete enough for `janus-task-breakdown`
- parallel or later work is separated instead of blended into one ambiguous task

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
- Model: 5.4 | 5.4 mini | 5.5
- Reason:
```

Use `5.4` as the normal Janus workhorse for implementation/refactor/test execution tasks. Use `5.4` low for deterministic single-file text/data/test artifact edits when the `5.4` context is warm or follow-up implementation will return to `5.4`. Use `5.4 mini` only for separated mechanical edits that are still likely cheaper than staying on warm `5.4`. Recommend `5.5` as escalation when decomposition is ambiguous, security-sensitive, architecture-heavy, or high-risk.

Validate task structure when useful:

```powershell
python C:\Users\pruve\.codex\skills\janus-spec-to-task\scripts\validate_task_artifact.py --task <TaskFile>
```

## Handoff

For valid task artifacts, end with model/reasoning above exactly one copyable fenced `text` handoff to `janus-task-breakdown`:

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

If approval evidence is missing or the Spec is still incomplete, route back to `janus-spec-review`.
If the Spec itself needs new or clarified product decisions, route back to `janus-spec-generator`.

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

For valid task artifacts, next skill is `janus-task-breakdown`.
