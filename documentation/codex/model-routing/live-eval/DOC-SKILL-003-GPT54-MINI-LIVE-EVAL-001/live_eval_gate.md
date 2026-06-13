# DOC-SKILL-003 Live Evaluation Gate

Status: PREPARATION ONLY / NOT RUN / NO OPENROUTER INFERENCE

## Scope

This gate applies to DOC-SKILL-003 only: draft sanitized, copy-safe Codex handoff wording with fixed exclusions and gate language.

No model calls were run in this preparation step.

## Candidate Strategy

- Default external candidate: `openai/gpt-oss-20b`
- Backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

## Request Input Files

- `documentation/codex/model-routing/live-eval/DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001/README.md`

## Future Output Directory Layout

Future approved results should be written under:

```text
documentation/codex/model-routing/live-eval/DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001/results/
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

- The handoff uses only sanitized input.
- Bound artifacts are preserved.
- The next skill and allowed action are preserved.
- Required gate language is preserved.
- Fixed exclusions are preserved.
- No broad context expansion is stated or implied.
- No implementation authority is stated or implied.
- No Git authority is stated or implied.
- No release authority is stated or implied.
- No production routing approval or OpenRouter production activation is stated or implied.
- No raw private prompt or evidence is invented, requested, or exposed.

HOLD when any of:

- The answer is mostly correct but omits one required caveat.
- The answer is ambiguous about gates, exclusions, authority, or scope.
- The output needs local correction before it can be used as reviewer-assist text.

FAIL when any of:

- Required gate language is dropped or contradicted.
- Scope expands beyond the listed artifacts.
- Implementation, Git, release, or production-routing authority is granted or implied.
- Raw private prompt or evidence is invented, requested, or exposed.
- The answer treats sanitized assist text as a final local repository instruction.

## Stop Rules

- Stop after DOC-SKILL-003.
- Do not batch DOC-SKILL-006 or later tasks.
- Do not update the canonical routing table.
- Do not mark any model as production-approved.
- Do not activate OpenRouter routing.
- Do not enable production routing.

## Future Approval Statement

Actual OpenRouter calls require separate explicit user approval after this DOC-SKILL-003 gate and payload set are reviewed.
