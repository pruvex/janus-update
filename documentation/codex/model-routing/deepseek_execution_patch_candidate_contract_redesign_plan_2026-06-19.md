SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 4
Progress-Validierung: Failure Code EXECUTION_PATCH_CANDIDATE_CONTRACT_TOO_HEAVY_FOR_SINGLE_JSON_RETURN; Evidence geaendert gegenueber N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- Two different real prechecked larger-class slices, `BACKLOG-110` and `BACKLOG-108`, both failed with the same outcome: `finish_reason=length`.
- In both cases, transport, capture, `generation_id`, usage, telemetry JSONL, and `health_snapshot.py` ingestion all passed, so the failure is not the wrapper or provider transport path.
- The current larger-class contract asks the model to do too much in one single JSON return:
  - consume a long embedded task brief
  - obey a strict response schema
  - emit a full unified diff
  - emit `changed_files`
  - emit `risk_list`
  - emit `suggested_validation_steps`
  - emit governance wording fields
- The request bodies also inline long `mini_test_plan` arrays and a long `spec_excerpt`, which increases prompt pressure before the model even starts the patch candidate.
- The most likely root cause is therefore the current one-shot prompt/input contract, not a single unlucky slice.

Fix Summary:
- Compared the completed `BACKLOG-110` and `BACKLOG-108` request bodies and their repeated `finish_reason=length` outcomes.
- Identified the main contract-weight drivers: long embedded spec excerpts, long test-plan strings, and the requirement to return the full patch plus all review metadata in one strict JSON object.
- Converted that analysis into one concrete redesign plan before any further larger-class DeepSeek live retry.

Auto-Verification:
- Status: PASS
- Evidence:
  - `documentation/codex/model-routing/execution-direct-or-runs/DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-004/request_body.json`
  - `documentation/codex/model-routing/execution-direct-or-runs/DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-005/request_body.json`
  - `documentation/codex/model-routing/deepseek_execution_patch_candidate_backlog110_retry_result_2026-06-19.md`
  - `documentation/codex/model-routing/deepseek_execution_patch_candidate_backlog108_result_2026-06-19.md`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON planning-only contract redesign; no new live OR call and no product apply happened.
Changed Files:
- `documentation/codex/model-routing/deepseek_execution_patch_candidate_contract_redesign_plan_2026-06-19.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/codex/model-routing/execution-direct-or-runs/DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-004/request_body.json`
- `documentation/codex/model-routing/execution-direct-or-runs/DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-005/request_body.json`
- `documentation/codex/model-routing/deepseek_execution_patch_candidate_backlog110_retry_result_2026-06-19.md`
- `documentation/codex/model-routing/deepseek_execution_patch_candidate_backlog108_result_2026-06-19.md`
Evidence Paths:
- `documentation/codex/model-routing/execution-direct-or-runs/DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-004/response_summary.json`
- `documentation/codex/model-routing/execution-direct-or-runs/DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-005/response_summary.json`
- `documentation/codex/model-routing/execution-direct-or-runs/DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-004/request_body.json`
- `documentation/codex/model-routing/execution-direct-or-runs/DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-005/request_body.json`
Failure Code: EXECUTION_PATCH_CANDIDATE_CONTRACT_TOO_HEAVY_FOR_SINGLE_JSON_RETURN
Changed Files:
- `documentation/codex/model-routing/deepseek_execution_patch_candidate_contract_redesign_plan_2026-06-19.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`
Decision: Redesign the larger-class `execution_patch_candidate` contract before any further DeepSeek live retry.
Reason: The same `length` truncation now reproduced across two different real slices, so further live retries on the same contract would likely waste spend without producing accepted evidence.
Recommended Model: 5.4
Recommended Intelligence: medium
Next User Action: If you want to continue this lane, approve a bounded contract-redesign step before any new larger-class live run.

## Redesign Plan

### 1. Shrink The Input Package

Keep:

- `target_task`
- exact allowlist
- `max_touched_files`
- one short `manual_validation_gate`
- one short `delegation_question`

Reduce:

- replace long `mini_test_plan` arrays with one short summary line plus one `validation_bundle_id`
- replace the long embedded `spec_excerpt` with:
  - one compact goal line
  - one compact acceptance line
  - one compact risk line

### 2. Shrink The Output Contract

Replace the current heavy one-shot JSON object with a smaller first-pass contract:

- `status`
- `target_task`
- `changed_files`
- `patch_text`
- `notes`

Move the rest out of the first-pass requirement:

- derive `changed_files` from `patch_text` locally when possible
- let Codex synthesize `suggested_validation_steps` locally from the known `mini_test_plan`
- let Codex inject the fixed governance wording locally after parse success instead of requiring the model to spend tokens on it
- keep `risk_list` optional or cap it to 3 short strings

### 3. Reduce Patch Payload Size

- ask for one bounded minimal diff only
- forbid explanatory prose outside JSON
- instruct the model to touch only the smallest viable subset of the allowlist
- if needed, prefer backend-first proposals and let Codex decide whether test-file additions are still needed

### 4. Retry Strategy After Redesign

Do not immediately spend another live run on the old contract.

Instead:

1. implement the contract/input shrink locally
2. validate it with fixture mode
3. then approve at most one new bounded DeepSeek larger-class live retry
