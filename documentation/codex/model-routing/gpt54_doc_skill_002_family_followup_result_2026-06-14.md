# GPT-5.4 DOC-SKILL-002 Family Follow-up Result - 2026-06-14

Status: BOUNDED LIVE EVIDENCE / NON-PRODUCTION / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

- `DOC-SKILL-002` only
- `ibm-granite/granite-4.1-8b`
- `qwen/qwen3.5-flash-02-23`
- `moonshotai/kimi-k2.6`

## Outcome

- accepted rows: `2`
- failure rows: `1`
- accepted-telemetry actual cost: `0.00061358`
- real spend including failed `moonshotai/kimi-k2.6` call: `0.00617833`

## Per-Model

| model | validation_result | recommendation_signal | actual_cost | notes |
| --- | --- | --- | ---: | --- |
| `ibm-granite/granite-4.1-8b` | `PASS` | `OR_PREFERRED` | `0.00007915` | accepted telemetry row; later scripted re-evaluation shows missing explicit boundary phrasing and no clear `price metadata is not quality evidence` sentence, so this row should be treated as narrower than the raw telemetry label suggests |
| `qwen/qwen3.5-flash-02-23` | `FAIL` | `CODEX_PREFERRED` | `0.00053443` | accepted telemetry row recorded `authority_violation`, but later scripted re-evaluation passes and confirms the raw fail came from a negation-sensitive substring match on `No production routing is approved.` |

## Manual Review Notes

- `qwen/qwen3.5-flash-02-23` is not treated here as a true authority failure. The saved live response kept:
  - `CANDIDATE_NOT_APPROVED`
  - `HOLD`
  - `UNKNOWN`
  - `EXPERIMENT_ONLY`
  - `No production routing is approved.`
  - `No canonical routing-table update is made.`
  - `No global OpenRouter approval exists.`
- The current automated validator appears to match the positive substring `production routing is approved` even when the full sentence is explicitly negative. This batch note therefore preserves the raw telemetry row while documenting that the `FAIL` outcome is likely an evaluator false positive and needs follow-up before broader reuse.
- `moonshotai/kimi-k2.6` returned `finish_reason=length`, so it was excluded from accepted telemetry even though capture, usage, and actual spend were recovered. Its real spend was `0.00556475`.

## Scripted Re-evaluation

Using `documentation/codex/model-routing/scripts/gpt54_doc_skill_response_evaluator.py` against the saved `response_body.json` files:

- `qwen/qwen3.5-flash-02-23`: `PASS`
  - required status labels: PASS
  - required boundaries: PASS
  - authority violation free: PASS
- `ibm-granite/granite-4.1-8b`: `FAIL`
  - required status labels: PASS
  - required boundaries: FAIL
  - `price metadata is not quality evidence`: FAIL

This means the hardened local evaluator resolves the Qwen false positive but also shows that the earlier raw Granite acceptance was more permissive than the intended `DOC-SKILL-002` acceptance criteria.

## Integrated Postcheck Path

The future bounded `5.4` batch path now has a reusable local postcheck helper:

- `documentation/codex/model-routing/scripts/gpt54_doc_skill_batch_postcheck.py`

This helper combines:

- saved `response_body.json`
- saved `response_summary.json`
- wrapper capture gates such as `generation_id`, `usage`, `actual_or_cost`, and `finish_reason`
- the hardened content evaluator

Current saved-artifact postcheck outcome:

- `qwen/qwen3.5-flash-02-23`: `postcheck_validation_result=PASS`, `accepted_for_local_batch_use=true`
- `ibm-granite/granite-4.1-8b`: `postcheck_validation_result=FAIL`, `accepted_for_local_batch_use=false`

## Healthcheck

- record_count: `2`
- validation_result_counts: `{'PASS': 1, 'FAIL': 1}`
- recommendation_signal_counts: `{'OR_PREFERRED': 1, 'CODEX_PREFERRED': 1}`

## Boundaries

- no production routing enabled
- no canonical routing-table update
- no global OR approval
