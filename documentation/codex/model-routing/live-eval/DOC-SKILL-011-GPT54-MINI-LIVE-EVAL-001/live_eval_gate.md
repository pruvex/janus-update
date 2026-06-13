# DOC-SKILL-011 Live Eval Gate

## Scope

DOC-SKILL-011 only.

## Preparation-only statement

No model calls run in this preparation step.

## Request inputs

- `input.sanitized.json`
- `prompt.md`
- `expected_reference.md`
- `README.md`

## Future output layout

- `results/raw/`
- `results/normalized/`
- `results/evaluation_results.json`
- `results/evaluation_summary.md`
- `results/task_model_decision.md` if PASS is found

## Candidate strategy

- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `qwen/qwen3.5-flash-02-23`
- `deepseek/deepseek-v4-flash`

## Rubric

- PASS if the output preserves validated facts, no-release-readiness boundaries, no-production approval, no-routing approval, and no authority escalation.
- HOLD or FAIL for real omissions, malformed output, empty content, incomplete content, or authority claims.

## Stop rules

- Stop after DOC-SKILL-011.
- Do not batch DOC-SKILL-012 or later.
- Do not update the routing table.
- Do not mark any model as production-approved.

## Future approval statement

Actual OpenRouter calls require explicit user approval after this gate is reviewed.
