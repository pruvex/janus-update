# DOC-SKILL-003 Task Model Decision

Status: TASK_DECISION_RECORDED

## Scope

This is a task-level documentation-skill decision for DOC-SKILL-003 - Draft Codex handoff.

It does not update production routing, does not update the canonical routing table, does not mark any model production-approved, does not create a global documentation-skill winner, and does not start DOC-SKILL-006.

## Decision

- Internal default: GPT-5.4 mini low
- Selected external OpenRouter candidate: `openai/gpt-oss-20b`
- Selected external candidate status in evidence: PASS

## Backups

- `openai/gpt-oss-120b`: PASS extra evidence from the reduced live run; not selected
- `qwen/qwen3.5-flash-02-23`: PASS extra evidence from the reduced live run; not selected
- `deepseek/deepseek-v4-flash`: PASS extra evidence from the reduced live run; not selected

## Evidence Basis

- Live-evaluation fixture: `DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001`
- Evidence summary: `documentation/codex/model-routing/live-eval/DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001/results/evaluation_summary.md`
- Structured evidence: `documentation/codex/model-routing/live-eval/DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001/results/evaluation_results.json`
- Sequential strategy: default candidate first, backups only if needed, stop on PASS
- Calibration note: all four candidates were attempted after an initial evaluator false-HOLD on explicit non-binding wording; calibrated evidence review selects the default candidate and keeps backups as extra evidence.

The selected model `openai/gpt-oss-20b` is PASS in the completed DOC-SKILL-003 reduced live evaluation.

## Boundaries

- Task-level documentation-skill decision only.
- No production routing activation.
- No canonical routing-table update.
- No model is production-approved.
- No DOC-SKILL-006 or later task is started.
