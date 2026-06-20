# Direct OR Execution Patch Candidate Live Retry Result - 2026-06-19

Status: FAIL / LIVE RESPONSE CAPTURED / NOT ACCEPTED

## Summary

The second bounded live `execution_patch_candidate` attempt completed transport successfully after timeout hardening, but the returned result was not acceptable under the bounded contract.

- Workflow: `DIRECT-OR-EXECUTION-DISPATCH-LIVE-002`
- Live call attempts in this note: `1`
- OR model: `openai/gpt-oss-20b`
- HTTP status: `200`
- Generation id: `gen-1781822646-fTYm2Ifric2XQPqCl5g4`
- Finish reason: `error`
- Budget profile: `execution_patch_candidate`
- Estimated cost: `0.020000000`
- Reported actual OR cost field: `0.000000000`
- Upstream inference cost details: `0.0003555`
- Healthcheck ingestion: `PASS`

## What Worked

- The direct OpenRouter transport returned without hanging.
- File-first response artifacts were captured:
  - `response_body.json`
  - `response_headers.txt`
  - `response_summary.json`
- `generation_id` and `usage` were captured.
- Telemetry JSONL parsed and `health_snapshot.py` ingestion passed.

## Why It Failed

The provider returned `finish_reason=error` and no usable assistant content.

OpenRouter response error:

```text
Upstream error from Groq: Failed to generate JSON. Please adjust your prompt.
```

The returned body contains internal reasoning text about trying to construct the bounded JSON result, but no valid JSON payload matching the required execution patch candidate schema was produced.

Because of that:

- `patch_text` was unavailable
- `changed_files` stayed empty
- `suggested_validation_steps` were unavailable
- bounded validation failed

## Validation Failure

`validation_summary.json` recorded:

- `patch_text must be unified diff text`
- `suggested_validation_steps must be a non-empty list`

Final outcome:

- `DIRECT_OR_REJECT_AND_FALLBACK`
- `recommendation_signal=CODEX_PREFERRED`

## Interpretation

This result is important because it separates two different questions:

1. Transport reliability:
   - now improved enough to capture the live response
2. Model/provider fit for this larger structured class:
   - not yet proven with `openai/gpt-oss-20b` on this provider path

So this is no longer a transport blocker. It is now a bounded model-output reliability mismatch for the larger `execution_patch_candidate` class.

## Next Safe Step

Do not infer broad failure of the Direct OR architecture from this one result.

The next safe options are:

1. keep `execution_patch_candidate` canonical on Codex for now
2. test one stronger OR candidate for this class under the same bounded contract
3. relax the response format strategy for this class only if we explicitly decide that proposal parsing can be made more fault-tolerant without weakening review safety
