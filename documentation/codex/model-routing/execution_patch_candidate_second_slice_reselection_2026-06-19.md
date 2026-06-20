# Execution Patch Candidate Second Slice Reselection - 2026-06-19

Status: RESELECTION NOTE / NO LIVE OR CALL / NO PRODUCTION ROUTING

## Decision

After two negative live DeepSeek runs on `BACKLOG-110`, the preferred next real slice for the missing second accepted direct OR `execution_patch_candidate` evidence point is now:

- `BACKLOG-108`

Bound artifacts:

- `documentation/tasks/backlog_BACKLOG-108_preimplementation_check.md`
- `documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md`

## Why The Selection Changed

`BACKLOG-110` was originally the cleaner first choice, and it was tested twice on purpose.

What we learned from those two live runs:

- transport worked
- file-first capture worked
- `generation_id` and usage were captured
- telemetry JSONL parsing worked
- `health_snapshot.py` ingestion worked
- cost stayed far below the class cap

But both live runs still failed on the same core outcome:

- `finish_reason=length`
- truncated JSON
- no accepted bounded patch candidate

That means `BACKLOG-110` is no longer the best immediate second-slice investment on the current prompt shape.

## Why BACKLOG-108 Is Now The Best Next Slice

`BACKLOG-108` is now the best next candidate because it is:

- already prechecked
- still bounded to one clear existing-contact persistence seam
- broader than `BACKLOG-110`, which is useful because it tests a different larger-class behavior surface
- still reviewable through one explicit backend-centered file cluster and focused regression evidence

Required file cluster:

- `backend/services/chat_orchestrator.py`
- `backend/services/contact_manager.py`
- `backend/services/memory_extractor.py`
- `backend/tools/memory_tools.py`
- `backend/data/crud.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_memory_tools.py`
- `backend/tests/test_memory_write_update_conflict_handling.py`

## Why Not Keep Spending On BACKLOG-110 Immediately

Because we now have two live results on the same slice showing the same failure class.

A third live retry on the same slice would most likely require:

- prompt redesign
- input-shape redesign
- or both

That may still be worth doing later, but it is no longer the fastest way to get the missing second accepted larger-class evidence point.

## Working Recommendation

Use `BACKLOG-108` as the next candidate when we are ready to spend exactly one more bounded larger-class direct OR proposal-first run on the preferred worker family:

- `deepseek/deepseek-v4-flash`

Target purpose of that run:

- obtain the missing second accepted real `execution_patch_candidate` evidence point required before the first `execution_write_apply_candidate` live pilot should even be considered

## Boundaries

- no production routing
- no canonical routing-table update
- no live write activation
- no automatic implementation start
- Codex remains review, validation, and acceptance owner
