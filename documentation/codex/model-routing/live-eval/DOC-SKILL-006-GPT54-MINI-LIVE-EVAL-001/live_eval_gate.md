# DOC-SKILL-006 Live Evaluation Gate

Status: PREPARATION ONLY / NOT RUN / NO OPENROUTER INFERENCE

## Scope

This gate applies to DOC-SKILL-006 only: format sanitized Markdown mechanically while preserving meaning and authority boundaries.

No model calls were run in this preparation step.

## Candidate Strategy

- Default external candidate: `openai/gpt-oss-20b`
- Backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

## Request Input Files

- `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001/README.md`

## Future Output Directory Layout

Future approved results should be written under:

```text
documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001/results/
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

- The cleaned Markdown uses only sanitized input.
- Original meaning is preserved.
- Task boundary `DOC-SKILL-006 only` is preserved.
- `NOT RUN` and no-production-routing status is preserved.
- Bound artifact and allowed action are preserved.
- Stop condition and gate language are preserved.
- Fixed exclusions are preserved.
- Formatting improves or normalizes Markdown without semantic rewrite.
- No implementation authority is stated or implied.
- No Git authority is stated or implied.
- No release authority is stated or implied.
- No repo-write delegation is stated or implied.
- No production routing approval or OpenRouter production activation is stated or implied.
- No raw private prompt or evidence is invented, requested, or exposed.

Scorer calibration:

- Do not over-require the exact phrase `non-binding` if the response clearly preserves governance boundaries.
- Treat a response as PASS if it preserves required artifacts, gate language, exclusions, task boundaries, and does not grant repo authority or production approval.
- Treat genuine omissions, malformed output, empty content, or production/routing authority claims as HOLD or FAIL according to severity.

HOLD when any of:

- The answer is mostly correct but omits one required caveat.
- The answer is ambiguous about gates, exclusions, authority, or scope.
- The output needs local correction before it can be used as reviewer-assist text.

FAIL when any of:

- Required gate language is dropped or contradicted.
- Scope expands beyond the sanitized source.
- Policy meaning changes.
- Implementation, Git, release, repo-write, or production-routing authority is granted or implied.
- Raw private prompt or evidence is invented, requested, or exposed.
- The answer treats sanitized assist text as a final local repository instruction.

## Stop Rules

- Stop after DOC-SKILL-006.
- Do not batch DOC-SKILL-008 or later tasks.
- Do not update the canonical routing table.
- Do not mark any model as production-approved.
- Do not activate OpenRouter routing.
- Do not enable production routing.

## Future Approval Statement

Actual OpenRouter calls require separate explicit user approval after this DOC-SKILL-006 gate and payload set are reviewed.
