# Quickchange Direct OR Transport Result - 2026-06-19

Status: PASS / DIRECT OR TRANSPORT FIXTURE-VALIDATED / NO LIVE OR CALL

## Purpose

This note records the corrected Diamond-standard worker transport after the first `janus-quickchange` OpenRouter attempt exposed a model-access boundary in the ChatGPT-account-backed Codex sidecar surface.

## Root Cause

The previous live attempt did not fail because OpenRouter is unsuitable for Janus work. It failed because the bounded worker was launched through the Codex CLI model-selection surface:

```text
The 'openai/gpt-oss-20b' model is not supported when using Codex with a ChatGPT account.
```

That surface rejects OpenRouter model slugs before a delegated patch result can exist.

## Decision

Use direct OpenRouter transport for OpenRouter workers:

- Codex App remains the orchestrator, reviewer, validator, and final acceptance owner.
- OpenRouter receives a bounded, redacted task package.
- OpenRouter returns a structured patch proposal only.
- Local file writes remain Codex-owned until a separate accepted apply step.
- The file-first capture wrapper persists request body, response body, headers, summary, stdout, stderr, and exit code.
- Healthcheck telemetry records cost, usage, latency, validation result, fallback, and recommendation signal.

## Implemented Changes

- Added `documentation/codex/model-routing/scripts/openrouter_direct_quickchange_patch_runner.py`.
- Patched `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py` so `quickchange_patch_review` with an OpenRouter model slug uses the direct OpenRouter runner.
- Patched `documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1` to emit the documented `X-OpenRouter-Title` header.
- Added a local fixture response at `documentation/codex/model-routing/sidecar-fixtures/direct_or_quickchange_fixture_response_2026-06-19.json`.

## Validation

Direct runner fixture validation:

```powershell
python documentation\codex\model-routing\scripts\openrouter_direct_quickchange_patch_runner.py --task-label "Fixture direct OR quickchange" --normal-target-model "5.4/medium" --model openai/gpt-oss-20b --prompt-path documentation\codex\model-routing\sidecar-fixtures\quickchange_or_live_prompt_2026-06-19.md --editable-path frontend/index.html --max-touched-files 1 --workflow-id DIRECT-OR-QUICKCHANGE-FIXTURE-001 --estimated-prompt-tokens 500 --estimated-completion-tokens 150 --estimated-or-cost 0.000250000 --cost-estimate-confidence-percent 15 --cost-estimate-sample-count 1 --use-local-fixture --local-fixture-response-path documentation\codex\model-routing\sidecar-fixtures\direct_or_quickchange_fixture_response_2026-06-19.json
```

Result:

- `validation_result`: `PASS`
- `final_outcome`: `DIRECT_OR_PATCH_PROPOSAL_READY_FOR_CODEX_REVIEW`
- `actual_or_cost`: `0.000051500`
- `healthcheck_status`: `PASS`

Dispatcher fixture validation:

```powershell
python documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py --task-class quickchange_patch_review --task-label "Fixture dispatcher direct OR quickchange" --normal-target-model "5.4/medium" --operator-choice delegated --workflow-id DIRECT-OR-DISPATCH-FIXTURE-001 --selected-or-model openai/gpt-oss-20b --estimated-or-cost 0.000250000 --cost-estimate-confidence-percent 15 --estimated-prompt-tokens 500 --estimated-completion-tokens 150 --cost-estimate-sample-count 1 --prompt-path documentation\codex\model-routing\sidecar-fixtures\quickchange_or_live_prompt_2026-06-19.md --editable-path frontend/index.html --max-touched-files 1 --use-local-or-fixture --or-local-fixture-response-path documentation\codex\model-routing\sidecar-fixtures\direct_or_quickchange_fixture_response_2026-06-19.json
```

Result:

- `validation_result`: `PASS`
- `final_outcome`: `DIRECT_OR_PATCH_PROPOSAL_READY_FOR_CODEX_REVIEW`
- `codex_owned_outcome_status`: `CODEX_REVIEW_REQUIRED`
- `healthcheck_status`: `PASS`

Syntax validation:

```powershell
python -m py_compile documentation\codex\model-routing\scripts\openrouter_direct_quickchange_patch_runner.py documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py
```

Result: PASS

## Boundaries

- No live OR call was made in this fix.
- No production routing was enabled.
- No canonical routing-table update was made.
- No global OR approval is implied.
- No Git, release, backlog, registry, or `CURRENT_STATE` authority is delegated to OR.

## Next Step

Run exactly one live direct-OR quickchange patch proposal through the dispatcher with `--execute-direct-or` after explicit user approval. If that passes, wire the same direct transport pattern into the next bounded task class.
