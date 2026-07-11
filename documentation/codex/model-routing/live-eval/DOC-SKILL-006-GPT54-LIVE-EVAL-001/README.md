# DOC-SKILL-006-GPT54-LIVE-EVAL-001

Status: FIXTURE PREPARED / NOT RUN / NO LIVE EVALS / NO PRODUCTION ROUTING

## Task

`DOC-SKILL-006` - Format Markdown documentation.

## Purpose

Prepare a `5.4`-level Markdown formatting fixture that is harder than the mini mechanical cleanup path because it includes nested governance language that must be preserved exactly.

## Scope

Allowed:

- reorganize headings
- normalize bullets and code spans
- preserve meaning and authority boundaries
- improve readability without semantic rewrite

Blocked:

- repo-write delegation
- policy rewrite
- production approval
- release-readiness implication
- changing blocked scope into allowed scope

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
