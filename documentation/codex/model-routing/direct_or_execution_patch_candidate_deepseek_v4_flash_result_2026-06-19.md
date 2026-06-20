# Direct OR Execution Patch Candidate DeepSeek V4 Flash Result - 2026-06-19

Status: FAIL / LIVE RESPONSE CAPTURED / STRONGER THAN GPT-OSS-20B BUT NOT ACCEPTED

## Summary

The first larger direct OR `execution_patch_candidate` family-first retry on `deepseek/deepseek-v4-flash` completed cleanly on transport, usage capture, finish reason, bounded file scope, and patch structure, but it still failed the Janus contract on two governance wording fields.

- Workflow: `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-001`
- Task class: `execution_patch_candidate`
- OR model: `deepseek/deepseek-v4-flash`
- Response model field: `deepseek/deepseek-v4-flash-20260423`
- HTTP status: `200`
- Generation id: `gen-1781824327-eIl1CEHwHMUShwQlVfKA`
- Finish reason: `stop`
- Estimated cost: `0.000441000`
- Actual cost: `0.000471744`
- Cost cap: `0.050000000`
- Healthcheck ingestion: `PASS`

## What Passed

- direct OpenRouter capture completed cleanly
- file-first artifacts were written
- `generation_id` and `usage` were captured
- actual cost stayed far below the execution patch cap
- `finish_reason` was `stop`
- changed files stayed exactly inside the five-file allowlist
- changed file count matched the allowed `max_touched_files=5`
- patch structure, risk list, validation steps, and slice scope were all present
- `health_snapshot.py` ingestion passed

## Why It Still Failed

The result missed two Janus-specific review-ownership wording gates:

- `manual_validation_note must preserve Codex-owned manual validation`
- `codex_acceptance_rule must preserve Codex apply/reject ownership`

This is important because the failure is no longer about:

- missing JSON
- provider error
- missing patch text
- missing validation steps
- scope escape

Instead, the remaining mismatch is a narrower governance-contract wording problem.

## Comparison Against The Earlier GPT-OSS-20B Result

### `openai/gpt-oss-20b`

- `finish_reason=error`
- provider JSON-generation failure
- no usable structured patch candidate
- missing `patch_text`
- missing `suggested_validation_steps`
- clear model/provider fit failure for the larger class

### `deepseek/deepseek-v4-flash`

- `finish_reason=stop`
- valid patch candidate object returned
- correct file scope
- correct patch body
- correct validation-step presence
- failed only on two Codex-governance wording fields

## Interpretation

`deepseek/deepseek-v4-flash` is materially stronger than the current `gpt-oss-20b` anchor for `execution_patch_candidate`.

Best classification right now:

- `FURTHER_TEST_CANDIDATE`

Why not `PASS` yet:

- Janus still requires explicit Codex-owned manual validation language
- Janus still requires explicit Codex apply/reject ownership language

Why not `CODEX_ONLY` immediately:

- the model proved it can satisfy the hard technical parts of the larger class much better than the prior anchor
- the remaining gap looks prompt/governance-contract-specific, not broad model incapability

## Recommended Next Safe Step

If we continue on this class, the next best move is not a broad new family sweep.

Instead:

1. keep `deepseek/deepseek-v4-flash` as the current strongest larger-class candidate
2. tighten the execution patch prompt or acceptance wording specifically around:
   - `Codex must manually validate`
   - `Codex must apply or reject locally`
3. run at most one bounded follow-up retry on the same class only after that wording hardening is explicit

## Boundary Reminder

- no production routing is activated
- no canonical routing-table update is made
- no global DeepSeek approval exists
- Codex remains the local apply/reject and validation owner
