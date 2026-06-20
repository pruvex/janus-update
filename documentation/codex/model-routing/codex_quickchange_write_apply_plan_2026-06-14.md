# Codex Quickchange Write Apply Plan - 2026-06-14

Status: THIRD CLASS PLAN / FIRST WRITE-CAPABLE CLASS AFTER TWO ASSIST-ONLY CLASSES

## Purpose

This artifact defines the next bounded delegation expansion class after:

- `documentation_draft`
- `quickchange_patch_review`
- `generator_review`
- `debug_hypothesis_review`
- `test_result_triage_review`

The new class is:

- `quickchange_write_apply`

Its goal is to let the operator choose whether one tiny bounded quickchange should stay in Codex or use the already proven bounded workspace-write path under strict allowlist and validation control.

## Scope

Owning skill:

- `janus-quickchange`

Allowed delegation mode:

- `SIDECAR_WRITE_CANDIDATE`

This class is not broad write authority. It is the controlled reuse of the already accepted tiny workspace-write quickchange pattern.

## Operator Choice Model

The operator-facing choice stays aligned with the shared bounded model:

- `1 = Codex`
- `2 = Delegated`

Offer the operator choice only when all are true:

- one tiny quickchange brief exists
- one file cluster is bound
- exact editable-path allowlist is declared
- touched-file cap is declared
- acceptance is obvious and narrow
- Codex still owns validation and final acceptance

Do not offer delegated mode when any are true:

- product behavior is ambiguous
- backend, persistence, routing, auth, provider, or release scope is involved
- more than one small file cluster is likely
- runtime validation is broad or unclear
- a normal Backlog or precheck path is more appropriate

## Required Input Package

The delegated quickchange write path should receive only a compact apply package:

- workflow or task label
- bound skill context
- request summary
- quickchange brief
- mini test plan
- exact editable paths
- max touched files
- diff-size expectation
- validation expectation

## Required Safety Gates

Every delegated write must preserve these gates:

- exact editable-path allowlist
- exact touched-file cap
- delete/rename/move tripwire
- diff capture
- local validation capture
- Codex-owned final accept or reject decision

## Delegated Output Contract

The delegated write result should be normalized into this bounded structure:

```text
QUICKCHANGE_WRITE_APPLY
Status: PASS | BLOCKED | FAILED
Changed Files:
Touched File Count:
Allowlist Check: PASS | FAIL
Touched File Cap Check: PASS | FAIL
Delete/Rename/Move Check: PASS | FAIL
Validation Check: PASS | FAIL
Git Diff Path:
Validation Summary Path:
Notes:
```

Rules:

- no auto-apply beyond the bounded sidecar write itself
- no Git, release, routing, registry, or backlog claims
- Codex still decides whether the result is accepted as final quickchange evidence

## Codex Validation Flow

After a delegated write returns:

1. Verify summary and validation artifacts exist.
2. Reject immediately if allowlist, file-cap, or delete/rename/move checks fail.
3. Review the captured diff against the bound quickchange brief.
4. Review the declared local validation result.
5. Select one of:
   - `ACCEPT_FOR_LOCAL_QUICKCHANGE_CLOSEOUT`
   - `ACCEPT_WITH_MANUAL_REVIEW`
   - `REJECT_AND_FALLBACK_TO_CODEX`

## Fallback Rules

Fallback to Codex-only immediately when:

- changed files drift outside the allowlist
- touched-file cap is exceeded
- delete, rename, or move appears
- validation is missing or failed
- the diff expands beyond the quickchange brief

Fallback outcome:

- keep the delegated artifacts as evidence
- do not accept the delegated edit as final
- continue locally in Codex or reroute out of quickchange

## Minimal Artifact Plan

The first implementation slice for this class should create:

- one class-specific apply helper or dispatcher branch
- one operator summary artifact
- one accepted-source validation path based on the already proven bounded live quickchange package

Suggested run artifact family:

- `documentation/codex/model-routing/quickchange-apply-runs/<WORKFLOW_ID>/`

Suggested core files:

- `source_validation.json`
- `operator_summary.json`

## Evidence Requirements Before Everyday Use

Required acceptance evidence:

- existing accepted live bounded quickchange write package
- 1 helper-level accepted-source validation run
- 1 dispatcher-level accepted-source validation run
- 0 allowlist escapes
- 0 delete/rename/move escapes

## Non-Goals

- no production routing
- no canonical routing-table update
- no broad sidecar code-writing authority
- no debug/executioner write approval
- no delegated Git or release authority

## Recommended Next Build Step

Implement a bounded dispatcher/helper path for `quickchange_write_apply` that validates and operationalizes the already accepted live quickchange write evidence as a reusable operator-facing class.
