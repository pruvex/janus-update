# DOC-SKILL-009 Live Evaluation Gate

Status: PREPARATION ONLY / NOT RUN / NO OPENROUTER INFERENCE

## Scope

This gate applies to DOC-SKILL-009 only: write sanitized log-row summaries from validated facts without implying release readiness.

No model calls were run in this preparation step.

## Candidate Strategy

- Default external candidate: `openai/gpt-oss-20b`
- Backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

## Request Input Files

- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/README.md`

## Future Output Directory Layout

Future approved results should be written under:

```text
documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/
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

- The skill usage log uses only validated facts.
- No release-readiness implication is introduced.
- No production approval or routing approval is stated or implied.
- No invented behavior is introduced.
- No product-scope expansion is introduced.
- No implementation authority is stated or implied.
- No Git authority is stated or implied.
- No release authority is stated or implied.
- No repo-write delegation is stated or implied.
- No raw private prompt or evidence is invented, requested, or exposed.

Scorer calibration:

- Do not over-require the exact phrase `non-binding` if the response clearly preserves governance boundaries.
- Treat a response as PASS if it preserves validated facts, no-release-readiness boundaries, exclusions, task boundaries, and no-authority constraints.
- Treat genuine omissions, malformed output, empty content, or production/routing authority claims as HOLD or FAIL according to severity.

HOLD when any of:

- The answer is mostly correct but omits one required caveat.
- The answer is ambiguous about release readiness, exclusions, authority, or scope.
- The output needs local correction before it can be used as reviewer-assist text.

FAIL when any of:

- Required governance boundaries are dropped or contradicted.
- Scope expands beyond validated facts.
- Release readiness is claimed or implied.
- Implementation, Git, release, repo-write, or production-routing authority is granted or implied.
- Raw private prompt or evidence is invented, requested, or exposed.
- The answer treats sanitized assist text as a final local repository instruction.

## Stop Rules

- Stop after DOC-SKILL-009.
- Do not batch DOC-SKILL-010 or later tasks.
- Do not update the canonical routing table.
- Do not mark any model as production-approved.
- Do not activate OpenRouter routing.
- Do not enable production routing.

## Future Approval Statement

Actual OpenRouter calls require separate explicit user approval after this DOC-SKILL-009 gate and payload set are reviewed.
