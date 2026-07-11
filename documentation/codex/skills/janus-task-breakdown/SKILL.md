---
name: janus-task-breakdown
description: Refine one Janus task artifact against its source Spec and release exactly one target task for preimplementation check. Use after janus-spec-to-task or backlog handoff when tasks need validation, source-of-truth checks, test enrichment, model confirmation, or a single-task handoff to janus-preimplementation-check.
---

# Janus Task Breakdown

## Purpose

Use this skill to refine Skill-1 task artifacts into exactly one implementation-ready target task for `janus-preimplementation-check`.

It validates scope, files, tests, source of truth, and execution model. It does not implement code.
This is a shared refinement skill. ChatGPT may shape the slice and frame the handoff, while Codex may refine the artifact inside a warm context, but neither actor may implement, run precheck, or fill product gaps here.

## Inputs

- One task file under `documentation/tasks/`.
- One source Spec file.
- Optional Backlog item.
- Optional target task or subtask.

When artifacts are named, they are the only requirements sources.
Accept either one compiled task artifact or one clear backlog handoff that already identifies the artifact path and intended slice. If the input points to multiple plausible task artifacts or lacks source identity, block instead of guessing.

## Hard Rules

- No implementation.
- No test execution.
- No precheck execution.
- No code generation.
- No new requirements.
- No product decisions from chat context.
- No architecture decisions.
- No full chain auto-release.
- Release exactly one target task.
- Later tasks require a separate handoff.
- If multiple target tasks remain plausible, stop and route back for narrowing instead of selecting one implicitly.
- Do not treat a vague `ok` as a valid handoff substitute.

## Tri-Modal Rollout Note

Global delegation vocabulary across Janus is now:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

This skill's bounded single-target refinement lane is now wired through the shared manifest-backed `documentation/codex/model-routing/scripts/janus_delegate.py` entry. OpenRouter remains the recommended backend for this assist-only review slice; Cursor is visible as option `2` but is not the recommended backend here.

## Bounded Delegation Gate

For a narrowly bounded single-target refinement slice, this skill now has the shared tri-modal operator gate:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Use the shared delegate entry first:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane task_breakdown_review --task-id TASK-TB-001 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-task-breakdown/task_breakdown_input_package.json --estimated-codex-saved-tokens 12000 --estimated-delegation-overhead-tokens 4000
```

For a narrowly bounded single-target refinement slice, this skill may offer one operator-facing delegated choice only when all of the following are true:

- exactly one source Spec and one task artifact are bound
- the delegated task is recommendation-only and bounded to releasing exactly one target task for precheck
- no authoritative handoff write, precheck execution, implementation, Git action, or product decision is delegated
- Codex remains the final reviewer and local writer of any accepted task-breakdown handoff

Binding implementation artifact:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_task_breakdown_runner.py`

Current bounded winner for the representative Spec-21 refinement slice:

- `qwen/qwen3-coder-30b-a3b-instruct`

Current lane behavior:

- OpenRouter remains the recommended backend for this bounded assist-only review slice.
- Cursor is visible as option `2`, but not the recommended backend.
- The existing `codex_task_breakdown_runner.py` remains the downstream OR helper planned by `janus_delegate.py`.

Gate rules:

- if the user chooses `1`, `local`, or `codex`, stay local in Codex
- if the user chooses `2`, `cursor`, or `Cursor`, do not imply a live Cursor task-breakdown path unless a later migration artifact explicitly adds one
- if the user chooses `3`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded task-breakdown helper path and hands off to the existing runner
- use only a bounded single-target input package; do not delegate the authoritative handoff write
- accepted delegated output remains review material only; Codex must still perform any real handoff write locally

Forbidden inside this path:

- delegated authoritative handoff writes
- delegated implementation or precheck execution
- delegated release of multiple target tasks
- delegated Git, release, routing-table, or `CURRENT_STATE` writes

## Validation Gates

For each candidate task, check:

- goal is clear
- scope is bounded
- files are concrete or deliberately scoped
- acceptance criteria are binary
- tests are appropriate
- execution model is valid
- no verify-only, review-only, analysis-only, or design-only standalone task is forwarded

Precheck-ready target task means:

- exactly one selected target task is named
- scope is atomic enough for one preimplementation check run
- required files or file cluster are concrete or deliberately bounded
- tests and acceptance criteria are explicit enough for precheck
- no missing product decision or source-of-truth contradiction remains

If a task affects TestSpec, test oracle, assertions, `containsAny`, `mustNotContain`, response format, or expected output, enforce source of truth:

- `documentation/TEST_SPEC/*.md` is primary.
- `documentation/test-runs/*_plan.json` is generated evidence only.
- A test-plan-only oracle patch is blocked.
- After TestSpec changes, route to `janus-test-pipeline`.

## Model Routing

- `5.6 Terra`: normal task refinement and risk judgment.
- `5.6 Luna`: separated mechanical task artifact validation only when likely cheaper than staying on warm `5.6 Terra`.
- `5.6 Terra` low: short mechanical validation when current `5.6 Terra` context is warm or the next step returns to `5.6 Terra`.
- `5.6 Sol`: escalation for ambiguous, security-sensitive, or architecture-heavy tasks.

## Validation Script

Use when useful:

```powershell
python C:\Users\pruve\.codex\skills\janus-task-breakdown\scripts\validate_task_handoff.py --task <TaskFile> --target <TASK-ID>
```

## Handoff

End with exactly one compact copyable fenced `text` handoff:

```text
@janus-preimplementation-check
Spec: <source spec file>
Task: <task file>
Backlog Item: <BACKLOG-XXX | N/A>
Target Task: <TASK-XXX.Y>
Target Subtask: <SUBTASK-XXX-YY | N/A>
Mode: SINGLE_TASK_PRECHECK
Execution Model: <5.6 Terra | 5.6 Luna | 5.6 Sol | 5.5 fallback | legacy fallback>
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```

If the task artifact is unclear, routes conflict, or multiple target tasks remain plausible, route back to `janus-spec-to-task` or `janus-backlog-handoff` with one compact fenced `text` block instead of releasing an implicit choice.

## Decisions

Return one:

- `TASK DESIGN COMPLETE`: exactly one target task is ready for precheck.
- `TASK DESIGN BLOCKED`: source of truth, files, tests, or scope are unsafe.
- `TASK AMBIGUOUS`: Spec or task needs clarification.
- `MODEL SWITCH REQUIRED`: use `5.6 Sol` for high-risk ambiguity.

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
