# GPT-5.4 DOC-SKILL-002 `openai/gpt-oss-120b` Run Prep - 2026-06-14

Status: PREPARED / NOT RUN / EXPLICIT LIVE APPROVAL REQUIRED / NON-PRODUCTION

## Scope

- skill: `DOC-SKILL-002`
- model: `openai/gpt-oss-120b`
- mode: one narrow fixed-model follow-up only
- no production routing
- no canonical routing-table update
- no global OR approval

## Bound Inputs

- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/local_baseline_result_2026-06-13.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/acceptance_criteria.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/blocked_authority_checks.md`
- `documentation/codex/model-routing/scripts/gpt54_doc_skill_response_evaluator.py`
- `documentation/codex/model-routing/scripts/gpt54_doc_skill_batch_postcheck.py`

## Historical Reference

Most recent bounded `DOC-SKILL-002` `openai/gpt-oss-120b` row from `GPT54-FIXED-OR-COMPARISON-BATCH-001`:

- estimated_or_cost: `0.000241077`
- actual_or_cost: `0.00012904`
- validation_result: `HOLD`
- recommendation_signal: `MANUAL_REVIEW`
- reason_for_escalation: `no_prod`

Interpretation:

- the model stayed well below the normal `0.0020` per-call cap
- the old batch evaluator was still pre-hardening and should not be treated as the final acceptance reference
- the next run must be judged with the saved-artifact postcheck helper, not only raw telemetry

## Proposed Gates For The Next Approved Live Run

- pre-call estimate must be shown before execution
- pre-call estimate must stay below `0.0020`
- file-first wrapper only
- save `request_body.json`, `response_body.json`, `response_headers.txt`, `response_summary.json`, `stdout.log`, `stderr.log`, `exit_code.txt`
- capture `generation_id`, `usage`, `actual_or_cost`, and `finish_reason`
- abort acceptance if `finish_reason=length`
- run `health_snapshot.py --or-telemetry-jsonl` after capture
- run `gpt54_doc_skill_batch_postcheck.py` on saved artifacts before any result note calls the row acceptable

## Required Local Acceptance Rule

The row counts as locally acceptable only if:

- wrapper capture checks pass
- `gpt54_doc_skill_batch_postcheck.py` returns:
  - `postcheck_validation_result=PASS`
  - `accepted_for_local_batch_use=true`

If the raw telemetry and the local postcheck disagree, the local postcheck wins for the candidate note.

## Explicit Not-Doing List

- no live call in this prep step
- no production routing activation
- no routing-table update
- no Auto Router
- no broad multi-model batch
- no `DOC-SKILL-006` or `DOC-SKILL-008` continuation in this prep artifact

## Next Approval Phrase

Use an explicit later approval before any live run:

```text
APPROVE GPT54 DOC SKILL FIXED OR COMPARISON: DOC-SKILL-002 openai/gpt-oss-120b
```
