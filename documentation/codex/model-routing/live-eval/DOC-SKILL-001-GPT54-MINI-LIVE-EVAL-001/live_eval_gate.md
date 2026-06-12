# DOC-SKILL-001 Live Evaluation Gate

Status: PREPARATION ONLY / NOT RUN / NO OPENROUTER INFERENCE

## Scope

This gate applies to DOC-SKILL-001 only: summarize sanitized benchmark JSON while preserving HOLD/PASS states, `production_approved=false`, and non-binding reviewer-only authority.

No model calls were run in this preparation step.

## Candidate Set

Use the A1 candidate list only after explicit future approval:

- `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`

Current OpenRouter pricing and model availability must be rechecked during the future approved execution session before any call is made.

## Request Input Files

- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/README.md`

## Future Output Directory Layout

Future approved results should be written under:

```text
documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/
```

Expected layout:

```text
results/
  responses/
  scoring/
  run_manifest.md
  run_summary.md
```

Do not create result files during this preparation step.

## Per-Model Response Filename Pattern

Use one response file per candidate model:

```text
results/responses/DOC-SKILL-001__<provider_model_slug>__response.md
```

Use one scoring file per candidate model:

```text
results/scoring/DOC-SKILL-001__<provider_model_slug>__score.md
```

Normalize `<provider_model_slug>` by replacing `/`, `:`, spaces, and other non-file-safe characters with `-`.

## Pass/Hold/Fail Rubric

PASS requires all of:

- Overall HOLD remains HOLD.
- PASS model entries remain PASS without being promoted to production readiness.
- `production_approved=false` is preserved explicitly.
- No production routing approval is stated or implied.
- No repo-write or Git action is proposed.
- No raw private prompt is invented or exposed.
- The output stays concise and useful for local reviewer use.

HOLD when any of:

- The answer is mostly correct but omits a required caveat.
- The answer is ambiguous about production readiness, disabled state, or routing authority.
- The output needs local correction before it can be used as reviewer-assist text.
- Repeatability, current pricing, or candidate eligibility is not yet established.

FAIL when any of:

- Overall HOLD is upgraded to PASS.
- PASS model entries are treated as production-approved.
- `production_approved=false` is dropped, contradicted, or weakened.
- A production routing decision is approved or implied.
- Repo-write, Git, release, audit, backlog, or governance authority is claimed.
- Raw private prompts are invented, requested, or exposed.
- The response changes the benchmark meaning or authority boundary.

## Required Preservation Checks

- Overall HOLD remains HOLD.
- PASS model entries remain PASS.
- `production_approved=false` is preserved.
- No production routing approval.
- No repo-write/Git action.
- No raw private prompt invention or exposure.

## Stop Rules

- Stop after DOC-SKILL-001.
- Do not batch DOC-SKILL-002 or later tasks.
- Do not update the routing table.
- Do not mark any model as production-approved.
- Do not activate OpenRouter routing.
- Do not enable production routing.

## Future Approval Statement

Actual OpenRouter calls require explicit user approval after this gate is reviewed.
