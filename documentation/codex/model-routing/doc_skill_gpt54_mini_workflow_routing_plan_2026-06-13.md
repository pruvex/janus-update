# GPT-5.4 Mini Workflow Routing Plan - 2026-06-13

Status: WORKFLOW-READY PLANNING / NO MODEL CALLS / NO LIVE EVALS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

Define how the completed `5.4 mini` OR replacement phase can be used as a workflow-ready planning layer for documentation workflows before any separate `5.4` candidate work continues.

## Mini Scope Lock

This workflow plan applies only to the completed mini matrix scope:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

Preserved matrix counts remain:

- `OR_CONFIRMED=7`
- `NEEDS_STRONGER_TEST=0`
- `OR_REJECTED=0`

`DOC-SKILL-011` remains `NOT RUN` unless explicitly approved in a separate step.

The separate `5.4` candidate phase remains paused and planning-only.

## Supported Modes

### 1. Codex-only

Use only local Codex execution, local scripts, and local validation.

Use when:

- the task is marked `CODEX_ONLY`, `SCRIPT_ONLY`, `LOCAL_BASELINE_ONLY`, `POST_AUDIT_DOC_SYNC_ONLY`, or otherwise outside mini OR scope
- sanitized OR assistance is not needed
- governance, release, routing, or repo-truth boundaries are close

### 2. Auto-sparsam

Default low-cost workflow mode for mini-scope documentation tasks that already have `OR_CONFIRMED` in the mini matrix.

Use when all are true:

- the task is one of `DOC-SKILL-001/002/003/006/008/009/010`
- the mini matrix marks the task `OR_CONFIRMED`
- the work stays inside sanitized, non-binding, non-authoritative boundaries from the routing table
- local Codex will still validate and finalize the result

### 3. Manual-review

Human-guided review mode when sanitized OR output may still help, but automatic continuation would be too risky or ambiguous.

Use when:

- a task is in mini scope but local validation is non-trivial
- wording or boundary preservation needs a deliberate human gate
- the workflow hit a stop condition and needs inspection before any retry or fallback

## Startup Prompt Shown Once Per Doku Workflow

Use this once at workflow start:

```text
DOC WORKFLOW STARTUP
- Mode: Codex-only | Auto-sparsam | Manual-review
- Bound task: DOC-SKILL-XXX
- Mini matrix scope check: PASS | FAIL
- Routing-table boundary check: PASS | FAIL
- OR status requirement: OR_CONFIRMED required for Auto-sparsam
- Local validation remains mandatory before any repo-facing use
- Non-goals: no production routing, no canonical routing-table update, no 5.4 candidate continuation, no live evals
```

## Auto-sparsam Behavior

For `OR_CONFIRMED` mini skills, Auto-sparsam may use the selected OR option from the mini matrix as the first sanitized assist path:

- `DOC-SKILL-001` -> `openai/gpt-oss-20b`
- `DOC-SKILL-002` -> `openai/gpt-oss-20b`
- `DOC-SKILL-003` -> `openai/gpt-oss-20b`
- `DOC-SKILL-006` -> `openai/gpt-oss-120b`
- `DOC-SKILL-008` -> `qwen/qwen3.5-flash-02-23`
- `DOC-SKILL-009` -> `qwen/qwen3.5-flash-02-23`
- `DOC-SKILL-010` -> `qwen/qwen3.5-flash-02-23`

Automatic use in Auto-sparsam means only:

- sanitized assist may be prepared or referenced as the first low-cost drafting path
- Codex stays the local authority for final validation, final wording, script execution, and repo-facing output
- the workflow must stop immediately if any stop condition triggers

## Work That Remains Codex Or Local-Only

These categories remain local even while the mini workflow plan exists:

- any task outside the seven mini-scope rows
- any `CODEX_ONLY`, `SCRIPT_ONLY`, `LOCAL_BASELINE_ONLY`, `POST_AUDIT_DOC_SYNC_ONLY`, or upstream-blocked routing-table row
- repo writes, final documentation truth, local-state reconciliation, and exact CURRENT_STATE authority
- release, production routing, Git governance, commit authority, push authority, and canonical routing policy
- any `5.4` candidate-list planning or later `5.4` candidate evaluation work

## Stop Conditions

Stop Auto-sparsam or Manual-review continuation immediately when any of these happens:

1. `validation failure`
2. `missing OR confirmation`
3. `state contradiction`
4. `cost limit exceeded`
5. `production routing / release / git governance boundary`

Interpretation:

- `validation failure`: local checks, structure checks, or boundary checks fail
- `missing OR confirmation`: the requested task is not one of the seven `OR_CONFIRMED` mini rows
- `state contradiction`: CURRENT_STATE, matrix scope, routing table, or task framing disagree
- `cost limit exceeded`: the workflow leaves the intended low-cost assist path or would require expanded evaluation
- `production routing / release / git governance boundary`: the request drifts toward activation authority, release flow, commit/push authority, or other governed actions

## Validation Flow After OR Output

After any OR assist output, the workflow remains local-first:

1. Confirm the task is still inside the seven-row mini scope.
2. Confirm the matrix row is still `OR_CONFIRMED`.
3. Re-check routing-table `safe_scope` and `blocked_scope`.
4. Validate that no authority language, production activation language, or routing-policy drift was introduced.
5. If the task is script-first, run the local script path and treat OR text as advisory only.
6. Finalize or reject the result locally in Codex.

## Fallback Behavior From OR To Codex

If Auto-sparsam stops or OR output is unusable:

- fall back to `Codex-only`
- preserve the same bound task and artifact scope
- do not escalate into live evals
- do not continue into the separate `5.4` candidate phase
- document the stop reason in the active state or validation notes if the work block is substantial

## Explicit Non-Goals

- no production routing activation
- no canonical routing-table update
- no `5.4` candidate-list continuation
- no live evals

## Operational Notes

- This plan is workflow-ready planning only.
- It does not create a global OR approval.
- It does not change the routing table.
- It does not authorize `DOC-SKILL-011`.
