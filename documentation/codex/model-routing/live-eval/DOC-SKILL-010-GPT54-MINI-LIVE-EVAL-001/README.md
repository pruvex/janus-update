# DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001

## Task

DOC-SKILL-010 - Prepare Non-Binding Review Notes

## Scope

Evaluate whether the reduced candidate set can draft sanitized review notes from validated facts while preserving:

- no release-readiness implication
- no invented behavior
- no product-scope expansion
- no production approval
- no routing approval
- no repo-write delegation

## Candidate Strategy

- Default external candidate: `openai/gpt-oss-20b`
- Backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

## Required Baseline

GPT-5.4 mini low for sanitized draft; GPT-5.4 medium for real review notes work.

## Status

NOT RUN

## Notes

This fixture prepares DOC-SKILL-010 only.
Do not run OpenRouter inference/model tests until explicitly approved.
Do not batch with DOC-SKILL-011 or later tasks.
Do not update production routing, mark any model production-approved, or update the canonical routing table.
