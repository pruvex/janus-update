# GPT-5.4 DOC-SKILL-002 `openai/gpt-oss-120b` Rerun Result - 2026-06-14

Status: ONE APPROVED LIVE CALL / FILE-FIRST CAPTURE / NON-PRODUCTION / LOCAL POSTCHECK ENFORCED

## Scope

- skill: `DOC-SKILL-002`
- model: `openai/gpt-oss-120b`
- call count: `1`
- workflow: `GPT54-DOC-SKILL-002-OPENAI-GPT-OSS-120B-RERUN-001`

## Capture Summary

- `generation_id`: `gen-1781388947-TkJxvTx12dkYVFoqwGic`
- `finish_reason`: `stop`
- `actual_or_cost`: `0.00014514`
- `estimated_or_cost`: `0.000241077`
- `estimation_error_percent`: `-39.8`
- per-call cap `0.0020`: PASS

## Wrapper Artifacts

- `request_body.json`: present
- `response_body.json`: present
- `response_headers.txt`: present
- `response_summary.json`: present
- `stdout.log`: present
- `stderr.log`: present
- `exit_code.txt`: `0`

Run directory:

- `documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-OPENAI-GPT-OSS-120B-RERUN-001/openai-gpt-oss-120b/`

## Local Postcheck

Using `documentation/codex/model-routing/scripts/gpt54_doc_skill_batch_postcheck.py` against the saved wrapper artifacts:

- `postcheck_validation_result`: `FAIL`
- `accepted_for_local_batch_use`: `false`

Postcheck detail:

- capture checks: PASS
- required status labels: PASS
- required boundary phrase `no production routing is approved`: PASS
- required boundary phrase `no canonical routing-table update is made`: FAIL
- required boundary phrase `no global openrouter approval exists`: FAIL
- `price metadata is not quality evidence`: PASS
- `authority_violation_free`: PASS

## Interpretation

This rerun is cheaper than the pre-call estimate and stays fully within the cost cap, but it still does not satisfy the hardened local acceptance rule for `DOC-SKILL-002`.

The saved output contains:

- no production routing approval
- preserved `HOLD`, `UNKNOWN`, `EXPERIMENT_ONLY`, and `CANDIDATE_NOT_APPROVED`
- safe next-step language

But it does not include the two exact boundary phrases required by the current local postcheck:

- `no canonical routing-table update is made`
- `no global openrouter approval exists`

Therefore the rerun is recorded as:

- `validation_result=FAIL`
- `recommendation_signal=MANUAL_REVIEW`
- `final_outcome=FIXED_OR_CAPTURED_BUT_POSTCHECK_FAILED`

## Healthcheck

Using `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo . --or-telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_openai_gpt_oss_120b_rerun_2026-06-14.jsonl`:

- `record_count`: `1`
- `actual_cost_total`: `0.00014514`
- `validation_result_counts`: `{'FAIL': 1}`
- `recommendation_signal_counts`: `{'MANUAL_REVIEW': 1}`

## Boundaries

- no production routing enabled
- no canonical routing-table update
- no global OR approval
