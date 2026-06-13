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

TASK_DECISION_RECORDED

## Reduced Live Evaluation Result

- Attempted models: 2
- Completed normalized responses: 2
- Selected external candidate: `openai/gpt-oss-20b`
- Backup evidence: `openai/gpt-oss-120b` PASS but not selected
- Remaining backups: NOT RUN / not needed
- Calibration note: the initial scorer over-flagged the default candidate's disabled-state wording; calibrated evidence review marks the default candidate PASS.

## Notes

This fixture records DOC-SKILL-002 only.
Do not batch with DOC-SKILL-003 or later tasks.
Do not update production routing, mark any model production-approved, or update the canonical routing table.
