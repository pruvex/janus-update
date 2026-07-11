# Quickchange Direct OR Qwen Live Retry After Schema Fix - 2026-06-19

SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 3
Progress-Validierung: Failure Code `DIRECT_OR_SCHEMA_ENVELOPE_VARIANT_DRIFT`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- The narrow first compatibility fix was correct for the original saved Qwen live response shape:
  - `file`
  - `diff` as unified diff string
  - nested `summary`
- The new real live retry did not return that same shape.
- Instead, `qwen/qwen3-coder-flash` produced a second bounded but non-canonical envelope:
  - `summary` as plain string
  - `diff` as structured array with `filename` and `lines`
- Transport, usage capture, finish reason, actual cost, and healthcheck ingestion all passed again.
- The remaining failure is therefore still an envelope-compatibility problem, but now confirmed as multi-variant drift rather than a single fixed adapter seam.

Fix Summary:
- No second compatibility expansion was applied in this step.
- The purpose of this retry was to verify whether the first narrow schema coercion was sufficient under a fresh live call.
- The answer is no: Qwen remains semantically aligned but schema-unstable on the quickchange lane.

Auto-Verification:
- Status: PASS
- Evidence:
  - real live retry workflow `DIRECT-OR-QWEN-QUICKCHANGE-LIVE-002`
  - `response_summary.json` shows `generation_id`, `usage`, `finish_reason=stop`, and `actual_or_cost=0.00018681`
  - `healthcheck_summary.json`: PASS
  - `validation_summary.json` shows bounded validation FAIL on schema fields only

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
- This is bounded OR runner/debug evidence, not a product feature change.
- The retry intentionally exercised the same small quickchange lane only.

Changed Files:
- `documentation/codex/model-routing/quickchange_direct_or_qwen_live_retry_after_schema_fix_2026-06-19.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/codex/model-routing/quickchange_direct_or_qwen_coder_flash_result_2026-06-19.md`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_schema_compatibility_fix_2026-06-19.md`
- `documentation/codex/model-routing/quickchange_direct_or_qwen_live_retry_after_schema_fix_2026-06-19.md`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-002/response_body.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-002/validation_summary.json`
Evidence Paths:
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-002/response_summary.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-002/patch_proposal.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-002/validation_summary.json`
- `documentation/codex/model-routing/direct-or-runs/DIRECT-OR-QWEN-QUICKCHANGE-LIVE-002/healthcheck_summary.json`
Failure Code:
- `DIRECT_OR_SCHEMA_ENVELOPE_VARIANT_DRIFT`
Changed Files:
- `documentation/codex/model-routing/quickchange_direct_or_qwen_live_retry_after_schema_fix_2026-06-19.md`
Decision:
- Qwen is still not accepted on the bounded quickchange lane.
- The family remains semantically promising but operationally schema-unstable for this Janus contract.
Reason:
- A fresh real live retry produced a different non-canonical envelope than the first live response, so one narrow adapter fix was not enough to stabilize acceptance.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- Decide whether to keep investing in Qwen-specific schema adaptation or to prioritize already stable families such as `deepseek/deepseek-v4-flash` for workhorse rollout.
