# Execution Patch Candidate Second Slice Selection - 2026-06-19

Status: SELECTION NOTE / NO LIVE OR CALL / NO PRODUCTION ROUTING

## Decision

The preferred next real slice for the second accepted direct OR `execution_patch_candidate` evidence run is:

- `BACKLOG-110`

Bound artifact:

- `documentation/tasks/backlog_BACKLOG-110_preimplementation_check.md`

## Why This Slice Is Preferred

`BACKLOG-110` is the strongest current candidate because it is:

- already prechecked
- narrow and backend-first by default
- low-risk compared with broader persistence or orchestration seams
- bounded to a small, reviewable file cluster
- supported by direct local regression checks without requiring a broad UI/runtime chain

Current required file cluster:

- `backend/services/contact_manager.py`
- `backend/data/crud.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_contact_card_normalization.py`

Optional only if needed:

- `backend/data/contact_schemas.py`
- a tiny address-book UI presentation follow-up only if backend normalization alone does not surface correctly

This is a better second proposal-first proof point than a larger orchestration seam because it stays close to:

- one explicit mapping bug
- one explicit cleanup rule
- one explicit regression surface

## Why Not BACKLOG-108

`BACKLOG-108` is real and prechecked, but it is a weaker second proof point for this purpose.

Reasons:

- it spans chat orchestration, memory extraction, contact persistence, and conflict handling
- it touches more files
- it has higher ambiguity around persistence-versus-proposal semantics
- it is more likely to need broader Codex judgment even if the patch stays bounded

That makes it a worse candidate for the next proposal-first OR evidence step.

It may still become useful later, but not as the cleanest second acceptance slice.

## Why Not BACKLOG-102

`BACKLOG-102` is already completed and audited.

So it is not a valid next slice for new proposal-first evidence.

## Working Recommendation

Use `BACKLOG-110` as the next candidate when we are ready to spend exactly one more bounded larger-class direct OR proposal-first run on the preferred worker family:

- `deepseek/deepseek-v4-flash`

Target purpose of that run:

- obtain the second accepted real `execution_patch_candidate` evidence point required before the first `execution_write_apply_candidate` live pilot should even be considered

## Boundaries

- no production routing
- no canonical routing-table update
- no live write activation
- no automatic implementation start
- Codex remains review, validation, and acceptance owner
