# DOC-SKILL-006 Task Model Decision

Status: TASK_DECISION_RECORDED

## Scope

This is a task-level documentation-skill decision for DOC-SKILL-006 - Format Markdown Documentation.

It does not update production routing, does not update the canonical routing table, does not mark any model production-approved, does not create a global documentation-skill winner, and does not start DOC-SKILL-008.

## Decision

- Internal default: GPT-5.4 mini low
- Selected external OpenRouter candidate: `openai/gpt-oss-120b`
- Selected external candidate status in evidence: PASS

## Backups

- `openai/gpt-oss-120b`: NOT RUN / not needed
- `qwen/qwen3.5-flash-02-23`: NOT RUN / not needed
- `deepseek/deepseek-v4-flash`: NOT RUN / not needed

## Evidence Basis

- Live-evaluation fixture: `DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001`
- Evidence summary: `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001/results/evaluation_summary.md`
- Structured evidence: `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001/results/evaluation_results.json`
- Sequential strategy: default candidate first, backups only if needed, stop on PASS
- Calibration note: pass responses when artifacts, gates, exclusions, task boundaries, and no-authority constraints are preserved without over-requiring the exact word `non-binding`.

The selected model `openai/gpt-oss-120b` is PASS in the completed DOC-SKILL-006 reduced live evaluation.

## Boundaries

- Task-level documentation-skill decision only.
- No production routing activation.
- No canonical routing-table update.
- No model is production-approved.
- No DOC-SKILL-008 or later task is started.
