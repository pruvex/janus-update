# DOC-SKILL-001 Task Model Decision

Status: TASK_DECISION_RECORDED

## Scope

This is a task-level documentation-skill decision for DOC-SKILL-001 - Summarize benchmark JSON.

It does not update production routing, does not update the canonical routing table, does not mark any model production-approved, does not create a canonical external model recommendation outside this task, and does not start DOC-SKILL-002.

## Decision

- Internal default: GPT-5.4 mini low
- Selected external OpenRouter candidate: `openai/gpt-oss-20b`
- Selected external candidate status in evidence: PASS

## Backups

1. `openai/gpt-oss-120b`
2. `qwen/qwen3.5-flash-02-23`
3. `deepseek/deepseek-v4-flash`

## Evidence Basis

- Live-evaluation fixture: `DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001`
- Evidence summary: `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/evaluation_summary.md`
- Structured evidence: `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/evaluation_results.json`
- Result counts: 9 PASS / 3 HOLD / 0 FAIL

The selected model `openai/gpt-oss-20b` is one of the PASS models in the completed DOC-SKILL-001 live evaluation.

## HOLD Models

These models remain HOLD:

- `openai/gpt-5-nano`
- `qwen/qwen3-235b-a22b-thinking-2507`
- `stepfun/step-3.7-flash`

## Boundaries

- Task-level documentation-skill decision only.
- No production routing activation.
- No canonical routing-table update.
- No model is production-approved.
- No DOC-SKILL-002 or later task is started.
- No new OpenRouter calls were run while recording this decision.
