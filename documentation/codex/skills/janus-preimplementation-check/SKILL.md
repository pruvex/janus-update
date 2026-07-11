---
name: janus-preimplementation-check
description: Verify exactly one Janus task before implementation and produce a strict execution handoff. Use before code changes, when a Backlog handoff or task file is ready, when the user asks to start implementation, or when Codex must validate scope, artifacts, model, tests, and evidence gates before using janus-executioner.
---

# Janus Preimplementation Check

## Overview

This is a pure gate before implementation. It decides only `PRE-CHECK PASSED`, `PRE-CHECK FAILED`, `PRE-CHECK BLOCKED`, or `MODEL SWITCH REQUIRED`. Do not edit product code, generate TestPlans, run TestRuns, or expand scope.
This is primarily a Codex execution skill. ChatGPT normally uses its result only when Codex returns `BLOCKED`, `NEEDS_INFO`, `SCOPE_MISMATCH`, or a model-switch escalation.

## Source References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\.windsurf\workflows\SKILL 3 - PRE-IMPLEMENTATION VERIFICATION.md`
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
Assigned Model: <5.6 Terra | 5.6 Luna | 5.6 Sol | 5.5 fallback | legacy fallback | other explicit model>
```

If a task file contains multiple tasks, `Target Task` is mandatory.
Exactly one target task or implementation slice may be checked per run. If the request spans multiple tasks, stop and require a narrower handoff.

Model choice is part of the gate. If the current `5.6 Terra` context is warm and the implementation will continue in `5.6 Terra`, prefer `Assigned Model: 5.6 Terra` with low reasoning for short mechanical work instead of assigning `5.6 Luna`. Assign `5.6 Luna` only when the task is a separated low-risk mechanical block that is still likely cheaper than staying on warm `5.6 Terra`.

## Tri-Modal Rollout Note

Global delegation vocabulary across Janus is now:

- `1 = Codex`
- `2 = OpenRouter`
- `3 = Cursor Composer`
- `4 = Cursor API`

This skill's bounded precheck-review lane is now wired through the shared manifest-backed `documentation/codex/model-routing/scripts/janus_delegate.py` entry. OpenRouter remains the recommended backend for this assist-only review slice; Cursor is visible as option `2` but is not the recommended backend here.

## Bounded Delegation Gate

For a narrowly bounded precheck slice, this skill now has the shared cost-aware operator gate:

- `1 = Codex`
- `2 = OpenRouter`
- `4 = Cursor API`

Use the shared delegate entry first:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane precheck_review --task-id TASK-PC-001 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-preimplementation-check/precheck_input_package.json --estimated-codex-saved-tokens 12000 --estimated-delegation-overhead-tokens 4000
```

For a narrowly bounded precheck slice, this skill may offer one operator-facing delegated choice only when all of the following are true:

- exactly one target task package is bound
- the delegated task is recommendation-only and bounded to precheck review output
- no final precheck decision, execution start, implementation, Git action, or release action is delegated
- Codex remains the final reviewer and local owner of the actual pass/block decision

Binding implementation artifact:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_precheck_review_runner.py`

Current bounded winner for the representative precheck slice:

- `qwen/qwen3-coder-30b-a3b-instruct`

Current lane behavior:

- OpenRouter remains the recommended backend for this bounded assist-only review slice.
- Cursor is visible as option `2`, but not the recommended backend.
- The existing `codex_precheck_review_runner.py` remains the downstream OR helper planned by `janus_delegate.py`.
- Current shared-gate productive evidence shows this lane is both usable and cost-stable for bounded single-task precheck packages.

Gate rules:

- if the user chooses `1`, `local`, or `codex`, stay local in Codex
- if the user chooses `2`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded precheck helper path and hands off to the existing runner
- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, do not imply a live Cursor precheck path unless a later migration artifact explicitly adds one
- use only a bounded precheck input package; do not delegate the final precheck authority
- accepted delegated output remains review material only; Codex must still perform the real precheck decision locally

Forbidden inside this path:

- delegated final precheck decisions
- delegated execution start or implementation
- delegated Git, release, routing-table, or `CURRENT_STATE` writes

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

Use `PRE-CHECK BLOCKED: SCOPE_MISMATCH` when the requested work is not exactly one target task or one implementation slice.

## Context Budget

Precheck is a gate, not a reread of the whole project. Load only:

- the target task file
- the bound Spec or `N/A WITH REASON`
- the matching Backlog handoff if applicable
- the minimum relevant tests or evidence surface

Do not reload prior execution chatter, old audit text, or unrelated task history when artifact identity is already clear.

## TestSpec and TestRun Boundary

For TestSpec, TestPlan, Test-Oracle, assertion, `containsAny`, `mustNotContain`, response-format, or TestRun-finding tasks:

- identify the source-of-truth TestSpec under `documentation/TEST_SPEC/`
- `janus-executioner` may edit only the source-of-truth TestSpec/Oracle file
- `janus-executioner` must not manually patch old `documentation/test-runs/*_plan.json`
- `janus-executioner` must not manually create `documentation/test-results/*`
- after TestSpec edit, route to `janus-test-pipeline`
- if no source-of-truth TestSpec can be determined, block with `PRE-CHECK BLOCKED: TESTSPEC_SOURCE_OF_TRUTH_MISSING`

For Live E2E/TestRun execution-only subtasks, route to `janus-test-pipeline` instead of implementation unless a small handoff artifact must first be written.

## Same-Chat Output Rule

The canonical precheck result belongs in the bound artifact file, not in the conversational reply.

- when continuing in the same chat, write or update the canonical precheck artifact first, then answer with a compact summary only
- the compact summary should name: canonical state, artifact path, next skill, recommended model, and recommended intelligence
- do not paste a full handoff block into chat unless the user explicitly asks for it or a real new-chat handoff is required
- a compact same-chat summary never replaces the canonical artifact; `janus-executioner` should read the bound file when it needs the full literals

## Required PASS Literals

A valid PASS output must contain these literal lines:

```text
PRE-CHECK RESULT
PRE-CHECK PASSED
legacy handoff start
NEXT: janus-executioner
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
Scope-Regel:
Automated Evidence Gate:
npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
Oracle-/TestPlan-Regel:
legacy handoff end
```

The execution handoff is a compact Codex-native artifact.
A bare `ok` or similar acknowledgement is never a valid handoff replacement.

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

If the required native fields cannot be produced exactly, output:

```text
PRE-CHECK BLOCKED: SKILL-4-HANDOVER-INCOMPLETE
```

## PASS Output Template

Use:

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
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
Affected Files:
- <explicit files or deterministic file cluster>
Evidence Focus:
- <exact commands, tests, or validator paths>
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- <unit/integration/build command>
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound task/spec/backlog identity
- affected files
- evidence commands
Drop Context:
- old failed drafts
- unrelated backlog or audit history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end
```
```

If the next step stays inside the same warm Codex context, keep the canonical artifact compact and artifact-bound.

## Non-PASS Handoff Rule

## Codex-Native Result Contract

The active PASS artifact is plain text and must include:

- `NEXT STEP`
- `Recommended Skill: janus-executioner`
- `Recommended Model:`
- `Recommended Intelligence:`
- `User Action:`

If the result is `PRE-CHECK BLOCKED`, `NEEDS_INFO`, `SCOPE_MISMATCH`, or `MODEL SWITCH REQUIRED`, output one compact plain-text handoff for Codex -> ChatGPT.

That handoff must include:

- `NEXT:` with the exact next skill when known
- the blocked target task identity
- the missing, contradictory, or escalation-triggering artifact
- the concrete decision or clarification needed

Do not use bare `ok`, prose-only routing, or broad chat-history recap as a substitute.

## Validator

When a precheck output is saved, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py <path-to-precheck-output.md>
```
