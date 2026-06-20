# GPT-5.4 Documentation Skill Fixed OR Comparison Plan - 2026-06-13

Status: PREPARATION ONLY / NOT RUN / NO LIVE EVALS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This plan applies only to:

- `DOC-SKILL-002`
- `DOC-SKILL-006`
- `DOC-SKILL-008`

These are the first three `5.4` documentation-skill fixtures with local baseline review artifacts already prepared.

This plan does not:

- run any OpenRouter call
- approve any model
- replace the completed mini fixed-model path
- activate Auto Router
- update the routing table

## Local Baseline Prerequisite

Use the existing local review baselines as the comparison reference:

- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/local_baseline_result_2026-06-13.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-LIVE-EVAL-001/local_baseline_result_2026-06-13.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-008-GPT54-LIVE-EVAL-001/local_baseline_result_2026-06-13.md`

These are accepted as working planning references only. They are not verified runtime identity captures.

## Candidate Pool

First bounded fixed-model comparison pool:

- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `inclusionai/ling-2.6-flash`
- `mistralai/mistral-nemo`
- `ibm-granite/granite-4.1-8b`

Rationale:

- keeps the set small
- includes low-cost structured candidates
- includes OpenAI-family continuity candidates
- avoids repeating broad Auto Router breadth testing

## Per-Skill Comparison Mapping

| skill_id | fixture_dir | comparison_mode | initial_model_order | special_gate |
| --- | --- | --- | --- | --- |
| `DOC-SKILL-002` | `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/` | sanitized scoring-summary assist only | `openai/gpt-oss-20b`, `inclusionai/ling-2.6-flash`, `mistralai/mistral-nemo`, `ibm-granite/granite-4.1-8b`, `openai/gpt-oss-120b` | exact preservation of `HOLD`, `UNKNOWN`, `EXPERIMENT_ONLY`, and `CANDIDATE_NOT_APPROVED` |
| `DOC-SKILL-006` | `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-LIVE-EVAL-001/` | sanitized formatting assist only | `openai/gpt-oss-20b`, `mistralai/mistral-nemo`, `inclusionai/ling-2.6-flash`, `ibm-granite/granite-4.1-8b`, `openai/gpt-oss-120b` | no semantic expansion and no new permissions |
| `DOC-SKILL-008` | `documentation/codex/model-routing/live-eval/DOC-SKILL-008-GPT54-LIVE-EVAL-001/` | sanitized changelog-draft assist only | `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `mistralai/mistral-nemo`, `inclusionai/ling-2.6-flash`, `ibm-granite/granite-4.1-8b` | must preserve planning-only caveats and avoid release-readiness language |

## Required Input Files Per Run

For each future approved comparison run, load only:

- `README.md`
- `input.sanitized.json`
- `prompt.md`
- `local_reference_output.md`
- `local_baseline_result_2026-06-13.md`
- `acceptance_criteria.md`
- `blocked_authority_checks.md`

## Proposed Future Output Layout

Do not create these result files in this planning step.

Per fixture:

```text
results/
  responses/
  scoring/
  run_manifest.md
  run_summary.md
```

Per model response filename:

```text
results/responses/<skill_id>__<provider_model_slug>__response.md
```

Per model scoring filename:

```text
results/scoring/<skill_id>__<provider_model_slug>__score.md
```

Normalize `<provider_model_slug>` to a file-safe form by replacing `/`, `:`, spaces, and similar characters with `-`.

## Cost And Safety Gates

Every future live comparison call must satisfy all of:

- refreshed or explicitly accepted price snapshot
- pre-call estimate shown
- confidence/sample-count caveat shown
- bounded per-call cap defined before execution
- file-first capture wrapper used
- response body saved
- `generation_id` captured
- usage and actual cost captured
- telemetry JSONL written only if acceptance gates pass
- `health_snapshot.py --or-telemetry-jsonl` ingestion passes

## Stop Rules

- stop after the explicitly approved skill/model scope
- do not batch all five models automatically without a fresh approval
- abort if estimate exceeds cap
- abort if response body, `generation_id`, or usage is missing
- abort if `finish_reason=length`
- abort if authority boundaries fail
- abort if output invents release, routing, policy, audit, backlog, or repo-write authority

## Pass / Hold / Fail Rules

### PASS

Use `PASS` only if the candidate:

- matches the local baseline on preserved facts
- respects all blocked authority checks
- stays inside sanitized assist scope
- keeps the output useful enough that local Codex editing effort does not increase

### HOLD

Use `HOLD` if the candidate is mostly usable but:

- omits one caveat
- is slightly ambiguous
- needs local cleanup beyond the baseline comfort threshold
- has incomplete repeatability or capture confidence

### FAIL

Use `FAIL` if the candidate:

- violates authority boundaries
- drops required status labels or caveats
- implies routing or production approval
- invents facts
- fails capture or healthcheck ingestion
- costs materially more without clear quality advantage

## Comparison Result Statuses

For the later matrix update, the allowed post-comparison statuses are:

- `OR_ASSIST_CANDIDATE`
- `FURTHER_TEST_CANDIDATE`
- `KEEP_CODEX`
- `OR_REJECTED`

No future comparison result from this plan may directly create:

- production routing activation
- canonical routing-table update
- global OR approval

## Future Approval Phrase

Use an explicit later approval before any live comparison, for example:

```text
APPROVE GPT54 DOC SKILL FIXED OR COMPARISON: DOC-SKILL-002 openai/gpt-oss-20b
```

The approval must name:

- one skill
- one fixed model

If the user wants a broader batch later, that must be approved separately with explicit cost and abort caps.

## Next Decision

After review, choose one:

1. Keep this as planning-only and stop here.
2. Approve one single-skill single-model bounded live comparison.
3. Revise the candidate order before any live call.
