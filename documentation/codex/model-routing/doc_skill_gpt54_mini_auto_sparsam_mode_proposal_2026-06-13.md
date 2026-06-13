# GPT-5.4 Mini Auto-sparsam Mode Proposal - 2026-06-13

Status: PROPOSAL ONLY / BOUNDED LOCAL WORKFLOW MODE / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This proposal is limited to the seven mini documentation skills that now have accepted bounded live OR telemetry evidence:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

Out of scope:

- `DOC-SKILL-011`
- `DOC-SKILL-012`
- the separate `5.4` candidate-list phase
- any global OR approval
- any production routing activation
- any canonical routing-table update

The first `DOC-SKILL-008` smoke-test row remains excluded from accepted evidence because it is debug failure evidence only.

## Selected OR Model Per Skill

| skill_id | skill_name | selected_or_model | live_evidence_status |
| --- | --- | --- | --- |
| `DOC-SKILL-001` | compact documentation-state sync | `openai/gpt-oss-20b` | accepted bounded live telemetry |
| `DOC-SKILL-002` | compact documentation inventory / listing update | `openai/gpt-oss-20b` | accepted bounded live telemetry |
| `DOC-SKILL-003` | compact documentation status normalization | `openai/gpt-oss-20b` | accepted bounded live telemetry |
| `DOC-SKILL-006` | compact documentation comparison / matrix synthesis | `openai/gpt-oss-120b` | accepted bounded live telemetry |
| `DOC-SKILL-008` | compact workflow/telemetry planning note | `qwen/qwen3.5-flash-02-23` | accepted bounded live telemetry via retry row |
| `DOC-SKILL-009` | compact workflow/telemetry follow-up planning note | `qwen/qwen3.5-flash-02-23` | accepted bounded live telemetry |
| `DOC-SKILL-010` | compact workflow/telemetry completion note | `qwen/qwen3.5-flash-02-23` | accepted bounded live telemetry |

## Proposed Auto-sparsam Gates

### Cost caps

- per-call cap: `0.0020`
- total session cap: `0.0060`
- maximum bounded Auto-sparsam session size under this proposal: `3` OR calls

If a workflow would need more than `3` OR-routed calls, the mode must stop and hand off to `Manual-review` before any further OR activity.

### Required pre-call estimate display

Before each OR-routed call, the operator prompt must show:

- `skill_id`
- `selected_or_model`
- `estimated_prompt_tokens`
- `estimated_completion_tokens`
- `estimated_or_cost`
- `price_snapshot_source`
- `price_snapshot_timestamp`
- `estimated_codex_effort` if available

### Required confidence display

Before each OR-routed call, the operator prompt must also show:

- `cost_estimate_confidence_percent`
- `cost_estimate_sample_count`
- `cost_estimate_mean_abs_error_percent`
- `cost_estimate_p50_error_percent`
- `cost_estimate_p90_error_percent`
- `cost_estimate_basis`
- `prompt_template_hash`
- `task_variant`

Display format:

- `Estimated OR cost: <estimated_or_cost> | Confidence: <cost_estimate_confidence_percent>% | Samples: <cost_estimate_sample_count> | Avg error: <cost_estimate_mean_abs_error_percent>%`

### Mandatory file-first telemetry capture

Every Auto-sparsam OR call must persist these artifacts before any operator summary is trusted:

- `request_body.json`
- `response_body.json`
- `response_headers.txt`
- `response_summary.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`

The acceptance gate for `response_summary.json` is:

- response body parseable
- `generation_id` present
- usage block present from response or later recovery path
- actual cost resolvable or explicitly downgraded to documented fallback handling

### Mandatory healthcheck ingestion

Every accepted Auto-sparsam telemetry row must be appended to a JSONL file that can be read by:

```powershell
python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --or-telemetry-jsonl <path>
```

The resulting summary must at minimum expose:

- `record_count`
- `models_seen`
- `skills_seen`
- `estimated_cost_total`
- `actual_cost_total`
- `confidence_average`
- `fallback_count`
- `validation_result_counts`
- `recommendation_signal_counts`

## Fallback And Abort Rules

### Fallback to Codex-only

Auto-sparsam must fall back to `Codex-only` immediately when any of these occurs:

- selected skill is outside the seven-skill scope
- the skill has no accepted live evidence row
- `OR_CONFIRMED` is missing for the skill in the mini matrix
- pre-call estimate already breaches the per-call or session cap
- the confidence display is missing
- `response_body.json` is missing or not parseable
- `generation_id` is missing
- usage is missing and the documented fallback path cannot recover a trustworthy actual cost
- healthcheck ingestion fails
- post-call validation is not `PASS`

### Abort the bounded session

The entire Auto-sparsam session must stop immediately when any of these occurs:

- validation failure
- missing OR confirmation
- state contradiction between CURRENT_STATE, matrix, workflow plan, and telemetry plan
- actual cost exceeds `0.0020` for a single call
- cumulative session cost exceeds `0.0060`
- fallback is triggered twice in one session
- the work touches release, production routing, canonical routing, or broader git governance authority

## Manual-review Triggers

Route to `Manual-review` instead of continuing automatically when:

- `cost_estimate_confidence_percent` is below the operator threshold for the workflow
- `cost_estimate_sample_count` is too low to justify unattended use
- `cost_estimate_mean_abs_error_percent` or `cost_estimate_p90_error_percent` indicates unstable pricing prediction
- the prompt or task variant differs materially from the live-evidenced pattern
- `rework_required=YES`
- `reason_for_escalation` is populated
- `quality_notes` indicate ambiguity, missing nuance, or state-risk wording
- the requested work drifts from planning/documentation upkeep into approval, release, governance, or upstream-owned product decisions

## Forbidden Without Explicit User Approval

Even in Auto-sparsam mode, the following remain forbidden without separate explicit approval:

- any OR call outside `DOC-SKILL-001/002/003/006/008/009/010`
- any OR call after the `3`-call / `0.0060` bounded session limit
- any production routing activation
- any canonical routing-table update
- any interpretation of the seven live-evidenced rows as global OR approval
- any `DOC-SKILL-011` run
- any `DOC-SKILL-012` start
- any continuation of the separate `5.4` candidate phase
- any release, tag, merge, or broad git-governance action

## Why This Is Not Production Routing

This proposal remains non-production because it is:

- limited to seven named documentation skills
- bounded by explicit per-call and per-session cost caps
- dependent on visible pre-call estimate and confidence disclosure
- dependent on mandatory file-first telemetry artifacts
- dependent on mandatory post-call healthcheck ingestion
- designed to fall back to Codex-local handling on capture, cost, validation, or state inconsistencies
- restricted to operator-invoked workflow use, not repo-wide autonomous routing

## What Would Still Be Needed Before Any Canonical Routing-table Update

Before even considering a canonical routing-table update, the project would still need:

- repeated multi-session evidence beyond the current bounded seven-row live layer
- stronger historical confidence baselines for estimate accuracy per skill/model pair
- documented failure-mode handling across more than one prompt/template variant per skill
- explicit review of real-work-equivalence, which currently remains `UNCLEAR`
- an explicit governance decision that planning-only Auto-sparsam behavior is safe to promote
- a separate approved routing-table review task

## Boundary Reminder

- mini matrix counts remain `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, `OR_REJECTED=0`
- the first `DOC-SKILL-008` smoke-test row stays debug-only and excluded
- no OR calls are made by this proposal
- no model calls are made by this proposal
- no live evals are started by this proposal
