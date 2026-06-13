# DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001

## Task

DOC-SKILL-006 - Format Markdown Documentation

## Scope

Evaluate whether the reduced candidate set can perform sanitized mechanical Markdown cleanup while preserving:

- original meaning
- task boundaries
- gate language
- fixed exclusions
- no semantic rewrite
- no policy change
- no repo-write delegation
- no production approval

## Candidate Strategy

- Default external candidate: `openai/gpt-oss-20b`
- Backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

## Required Baseline

GPT-5.4 mini low for sanitized text; GPT-5.4 low or medium for repo docs.

## Status

NOT RUN

## Notes

This fixture prepares DOC-SKILL-006 only.
Do not run OpenRouter inference/model tests until explicitly approved.
Do not batch with DOC-SKILL-008 or later tasks.
Do not update production routing, mark any model production-approved, or update the canonical routing table.
