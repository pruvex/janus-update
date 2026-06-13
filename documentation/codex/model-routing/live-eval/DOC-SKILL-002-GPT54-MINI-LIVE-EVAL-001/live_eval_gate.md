# DOC-SKILL-002 Live Evaluation Gate

Status: PREPARATION ONLY / NOT RUN / NO OPENROUTER INFERENCE

## Scope

This gate applies to DOC-SKILL-002 only: summarize sanitized model-scoring evidence while preserving HOLD, UNKNOWN, and disabled states.

No model calls were run in this preparation step.

## Candidate Strategy

- Default external candidate: `openai/gpt-oss-20b`
- Backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

## Request Input Files

- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/README.md`

## Future Output Directory Layout

Future approved results should be written under:

```text
documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/
```

Expected layout:

```text
results/
  raw/
  normalized/
  evaluation_summary.md
  evaluation_results.json
```

Do not create result files during this preparation step.

## Pass/Hold/Fail Rubric

PASS requires all of:

- Overall HOLD remains HOLD.
- UNKNOWN entries remain UNKNOWN.
- Disabled entries remain disabled.
- `production_approved=false` is preserved.
- `routing_approved=false` is preserved.
- No routing approval is stated or implied.
- No policy override is stated or implied.
- No production activation is stated or implied.
- No private evidence is interpreted or invented.

HOLD when any of:

- The answer is mostly correct but omits a required caveat.
- The answer is ambiguous about disabled, UNKNOWN, HOLD, routing, or production state.
- The output needs local correction before it can be used as reviewer-assist text.

FAIL when any of:

- HOLD is upgraded to PASS at the overall level.
- UNKNOWN or disabled entries are converted to PASS.
- Disabled state is dropped or contradicted.
- Routing approval, policy override, or production activation is approved or implied.
- Private evidence is interpreted, invented, requested, or exposed.

## Stop Rules

- Stop after DOC-SKILL-002.
- Do not batch DOC-SKILL-003 or later tasks.
- Do not update the canonical routing table.
- Do not mark any model as production-approved.
- Do not activate OpenRouter routing.
- Do not enable production routing.

## Future Approval Statement

Actual OpenRouter calls require separate explicit user approval after this DOC-SKILL-002 gate and payload set are reviewed.
