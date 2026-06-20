# Direct OR Execution Patch Candidate Prompt Hardening - 2026-06-19

Status: PROMPT/CONTRACT HARDENING COMPLETE / NO LIVE OR CALL IN THIS STEP

## Why This Hardening Was Needed

The first larger `deepseek/deepseek-v4-flash` `execution_patch_candidate` live retry failed only on two Janus governance wording fields:

- `manual_validation_note must preserve Codex-owned manual validation`
- `codex_acceptance_rule must preserve Codex apply/reject ownership`

This was not a transport or patch-generation failure. It was a contract-language miss.

## What Changed

Updated:

- `documentation/codex/model-routing/scripts/openrouter_direct_execution_patch_candidate_runner.py`

Hardening added in request construction:

- stronger system instruction that these two fields must explicitly preserve Codex ownership
- exact required sentence for `manual_validation_note`
- exact required sentence for `codex_acceptance_rule`
- explicit `field_contract` block in the user payload

Required ownership phrases now injected into the prompt:

- `Codex must manually validate this patch locally before task completion.`
- `Codex must review and apply or reject locally.`

## Validation

- `python -m py_compile documentation/codex/model-routing/scripts/openrouter_direct_execution_patch_candidate_runner.py`: PASS
- local fixture validation:
  - workflow: `DIRECT-OR-DEEPSEEK-EXECUTION-HARDEN-FIXTURE-001`
  - result: `PASS`
  - healthcheck ingestion: `PASS`

## Interpretation

This does not prove the next live DeepSeek retry will pass, but it does prove:

- the runner remains valid
- the contract hardening is active
- the hardened wording path is compatible with the existing bounded execution fixture

## Next Safe Step

If the user wants to continue, the next clean test is:

- one bounded second live `execution_patch_candidate` retry on `deepseek/deepseek-v4-flash`

with the hardened prompt/contract now in place.
