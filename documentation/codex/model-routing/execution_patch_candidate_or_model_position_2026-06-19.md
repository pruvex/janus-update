# Execution Patch Candidate OR Model Position - 2026-06-19

Status: WORKING POSITION / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Decision

For the bounded `execution_patch_candidate` class, the current preferred OR worker candidate is:

- `deepseek/deepseek-v4-flash`

The current Qwen result for the same class is:

- `qwen/qwen3-coder-flash` = not accepted on the present live contract

## Why DeepSeek Is The Preferred Candidate

Accepted bounded evidence already exists for DeepSeek on this class.

Binding evidence:

- `documentation/codex/model-routing/direct_or_execution_patch_candidate_deepseek_v4_flash_reclassification_2026-06-19.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_direct_or_execution_patch_2026-06-19_DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002.jsonl`

What matters operationally:

- live capture worked
- usage and cost were captured
- healthcheck ingestion passed
- the accepted larger-class run survived later validator seam review
- Codex review/apply ownership remained intact

DeepSeek therefore currently satisfies the real need for this class:

- one reliable bounded OR candidate that can draft a multi-file execution patch proposal under Codex review

## Why Qwen Is Not The Current Candidate For This Class

Qwen now has real live evidence on the same class, and that evidence is negative for the present contract.

Binding evidence:

- `documentation/codex/model-routing/qwen_execution_patch_candidate_live_debug_result_2026-06-19.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_qwen_responses_execution_patch_candidate_2026-06-19_DIRECT-OR-QWEN-EXECUTION-LIVE-001.jsonl`

Observed live problems:

- 10 `openrouter:apply_patch` output items instead of one final bounded proposal
- noisy diff preambles such as `#@ title=...`
- one context-mismatched hunk
- actual cost `0.005427825` USD versus estimated `0.00045` USD

This means Qwen is not rejected globally.

It means only:

- Qwen is not accepted for the current bounded `execution_patch_candidate` contract

## Scope Clarification

This position applies only to:

- `execution_patch_candidate`

It does not change the separate smaller-class result:

- Qwen remains a separate accepted option for the bounded `quickchange_patch_review` lane

## Working Recommendation

For everyday bounded larger-class OR usage planning:

1. treat `deepseek/deepseek-v4-flash` as the current preferred OR candidate for `execution_patch_candidate`
2. do not spend another Qwen live call on this class unless we first make a deliberate Qwen-specific contract hardening pass
3. keep Codex as final review, validation, and local apply/reject owner

## What This Does Not Mean

- no production routing
- no canonical routing-table update
- no global DeepSeek approval
- no global Qwen rejection
- no removal of Codex ownership
