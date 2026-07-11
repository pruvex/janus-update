# DOC-SKILL-002-GPT54-LIVE-EVAL-001

Status: FIXTURE PREPARED / NOT RUN / NO LIVE EVALS / NO PRODUCTION ROUTING

## Task

`DOC-SKILL-002` - Summarize model scoring report.

## Purpose

Prepare a `5.4`-level documentation-skill fixture for summarizing a nuanced scoring report where HOLD, UNKNOWN, disabled, and experiment-only states must be preserved exactly.

## Scope

Allowed:

- summarize sanitized scoring evidence
- preserve model status labels exactly
- distinguish price metadata from quality evidence
- state that production routing remains disabled

Blocked:

- routing approval
- policy override
- production activation
- global OR approval
- private evidence interpretation

## Candidate Pool For Later Approval

First no-live comparison set:

- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `inclusionai/ling-2.6-flash`
- `mistralai/mistral-nemo`
- `ibm-granite/granite-4.1-8b`

## Required Baseline

Local `5.4` / medium baseline must be recorded before any OR call.

## Files

- `input.sanitized.json`
- `prompt.md`
- `local_reference_output.md`
- `acceptance_criteria.md`
- `blocked_authority_checks.md`

## Notes

This fixture is separate from the completed mini fixed-OR evidence. It does not update the canonical routing table and does not approve any model.
