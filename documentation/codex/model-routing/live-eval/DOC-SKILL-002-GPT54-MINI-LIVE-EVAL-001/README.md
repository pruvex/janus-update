# DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001

## Task

DOC-SKILL-002 - Summarize model scoring report

## Scope

Evaluate whether the reduced candidate set can summarize sanitized model-scoring evidence while preserving:

- HOLD states
- UNKNOWN states
- disabled states
- no routing approval
- no policy override
- no production activation
- no private evidence interpretation

## Candidate Strategy

- Default external candidate: `openai/gpt-oss-20b`
- Backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

## Required baseline

GPT-5.4 mini low; GPT-5.4 medium if policy nuance rises.

## Status

NOT RUN

## Notes

This fixture prepares DOC-SKILL-002 only.
Do not run OpenRouter inference/model tests until explicitly approved.
Do not batch with DOC-SKILL-003 or later tasks.
Do not update production routing, mark any model production-approved, or update the canonical routing table.
