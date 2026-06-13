# DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001

## Task

DOC-SKILL-003 - Draft Codex handoff

## Scope

Evaluate whether the reduced candidate set can draft sanitized, copy-safe Codex handoff wording while preserving:

- fixed exclusions
- gate language
- no broad context expansion
- no implementation authority
- no Git authority
- no release authority

## Candidate Strategy

- Default external candidate: `openai/gpt-oss-20b`
- Backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

## Required Baseline

GPT-5.4 mini low.

## Status

TASK_DECISION_RECORDED

## Reduced Live Evaluation Result

- Attempted models: 4
- Completed normalized responses: 4
- Selected external candidate: `openai/gpt-oss-20b`
- Backup evidence: all three backups PASS but not selected
- Calibration note: the initial evaluator over-required explicit non-binding wording; calibrated evidence review marks the default candidate PASS because it preserved artifacts, gates, exclusions, and did not grant repo authority.

## Notes

This fixture records DOC-SKILL-003 only.
Do not batch with DOC-SKILL-006 or later tasks.
Do not update production routing, mark any model production-approved, or update the canonical routing table.
