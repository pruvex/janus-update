# GPT-5.4 Mini Auto-sparsam Implementation Plan - 2026-06-13

Status: IMPLEMENTATION PLAN ONLY / OPERATOR-INVOKED / BOUNDED LOCAL WORKFLOW / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This implementation plan is limited to the seven live-evidenced mini documentation skills only:

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
- any broader `5.4` candidate work
- any production routing activation
- any canonical routing-table update
- any global OR approval

The first `DOC-SKILL-008` smoke-test row remains debug-only and excluded from accepted evidence.

## Operator Invocation Flow

### Step 1: operator starts bounded Auto-sparsam mode

The workflow starts only when the operator explicitly selects:

- routing mode: `Auto-sparsam`
- one in-scope skill from the seven-skill list
- one bounded task instance that stays within documentation-planning or documentation-maintenance scope

Auto-sparsam must not self-start from background routing, automatic repo scanning, or any production workflow hook.

### Step 2: allowed skill detection

Before any OR action, the implementation must verify all of the following:

- `skill_id` is one of `DOC-SKILL-001/002/003/006/008/009/010`
- the mini matrix still records `OR_CONFIRMED` for that skill
- CURRENT_STATE still says the separate `5.4` candidate phase is paused
- the request does not drift into release, approval, governance, routing-table, `DOC-SKILL-011`, or `DOC-SKILL-012` territory

If any check fails, the workflow must stop before wrapper invocation and route to `Codex-only` or `Manual-review`.

### Step 3: model selection per skill

The selected OR model is fixed by the accepted mini evidence layer:

| skill_id | selected_or_model |
| --- | --- |
| `DOC-SKILL-001` | `openai/gpt-oss-20b` |
| `DOC-SKILL-002` | `openai/gpt-oss-20b` |
| `DOC-SKILL-003` | `openai/gpt-oss-20b` |
| `DOC-SKILL-006` | `openai/gpt-oss-120b` |
| `DOC-SKILL-008` | `qwen/qwen3.5-flash-02-23` |
| `DOC-SKILL-009` | `qwen/qwen3.5-flash-02-23` |
| `DOC-SKILL-010` | `qwen/qwen3.5-flash-02-23` |

No dynamic model search, candidate expansion, or model substitution is allowed inside this bounded plan.

### Step 4: pre-call operator display

Before any OR call is even considered, the operator must be shown:

- `workflow_id`
- `skill_id`
- `routing_mode=Auto-sparsam`
- `selected_or_model`
- `estimated_prompt_tokens`
- `estimated_completion_tokens`
- `estimated_or_cost`
- `price_snapshot_source`
- `price_snapshot_timestamp`
- `estimated_codex_effort` if available

Required display line:

- `Estimated OR cost: <estimated_or_cost> | Prompt tokens: <estimated_prompt_tokens> | Completion tokens: <estimated_completion_tokens> | Price source: <price_snapshot_source> @ <price_snapshot_timestamp>`

### Step 5: pre-call confidence display

The operator must also be shown:

- `cost_estimate_confidence_percent`
- `cost_estimate_sample_count`
- `cost_estimate_mean_abs_error_percent`
- `cost_estimate_p50_error_percent`
- `cost_estimate_p90_error_percent`
- `cost_estimate_basis`
- `prompt_template_hash`
- `task_variant`

Required display line:

- `Cost confidence: <cost_estimate_confidence_percent>% | Samples: <cost_estimate_sample_count> | Avg error: <cost_estimate_mean_abs_error_percent>% | P50: <cost_estimate_p50_error_percent>% | P90: <cost_estimate_p90_error_percent>%`

If either the estimate block or the confidence block is incomplete, Auto-sparsam must stop before wrapper invocation.

### Step 6: file-first wrapper invocation

If all gates are still green, the implementation should invoke the existing file-first wrapper path:

- script:
  - `documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1`

The wrapper invocation must be responsible for persisting these artifacts before any operator summary is treated as trustworthy:

- `request_body.json`
- `response_body.json`
- `response_headers.txt`
- `response_summary.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`

### Step 7: telemetry JSONL session file naming

Accepted rows should be written to one session-scoped JSONL file named with a bounded, explicit pattern:

- `documentation/codex/model-routing/or_healthcheck_telemetry_auto_sparsam_session_<YYYY-MM-DD>_<workflow_id>.jsonl`

Recommended rules:

- one JSONL file per bounded operator session
- append one accepted row per successful OR-routed activity
- do not append debug-only or failed-capture rows to the accepted session file

### Step 8: healthcheck ingestion step

After each accepted row, the implementation must run:

```powershell
python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --or-telemetry-jsonl <session_jsonl_path>
```

The summary must remain readable and must expose at least:

- `record_count`
- `models_seen`
- `skills_seen`
- `estimated_cost_total`
- `actual_cost_total`
- `confidence_average`
- `fallback_count`
- `validation_result_counts`
- `recommendation_signal_counts`

## Fallback To Codex-only Behavior

Fallback to `Codex-only` must happen immediately when:

- the requested skill is outside the seven-skill scope
- the selected skill loses `OR_CONFIRMED` status in the mini matrix
- pre-call estimate breaches the per-call or total session cap
- the estimate block or confidence block is missing
- `response_body.json` is missing or not parseable
- `response_summary.json` is missing
- `generation_id` is missing
- usage or actual cost cannot be recovered through the documented path
- healthcheck ingestion fails
- the resulting telemetry row does not validate as `PASS`

Fallback means:

- stop OR handling for the current task
- do not append an accepted telemetry row
- return control to local Codex handling or escalate to `Manual-review`

## Manual-review Triggers

Route to `Manual-review` when:

- confidence is below the operator threshold
- sample count is too low to trust the estimate
- average or p90 error indicates unstable prediction
- the task variant differs from the live-evidenced pattern
- `fallback_used=YES`
- `rework_required=YES`
- `reason_for_escalation` is populated
- quality notes indicate ambiguity or boundary risk
- the task drifts into governance, approval, release, or upstream-owned decision work

## Abort Rules

The bounded Auto-sparsam session must abort immediately when:

- validation fails
- state contradiction is detected between CURRENT_STATE, the mini matrix, the proposal, and this implementation plan
- single-call actual cost exceeds `0.0020`
- cumulative session cost exceeds `0.0060`
- the session would exceed `3` OR-routed calls
- healthcheck ingestion fails after an accepted row attempt
- the work crosses a production routing, release, canonical routing, or git-governance boundary

## Required Operator Summary Format

Each completed Auto-sparsam attempt should end with a compact operator summary containing:

- `workflow_id`
- `skill_id`
- `selected_or_model`
- `selected_path`
- `estimated_or_cost`
- `actual_or_cost`
- `cost_estimate_confidence_percent`
- `latency_ms`
- `validation_result`
- `fallback_used`
- `rework_required`
- `final_outcome`
- `session_jsonl_path`
- `healthcheck_summary_path` or command

Recommended display block:

```text
AUTO-SPARSAM SUMMARY
- Workflow:
- Skill:
- OR Model:
- Selected Path:
- Estimated Cost:
- Actual Cost:
- Confidence:
- Validation:
- Fallback:
- Rework Required:
- Final Outcome:
- Session Telemetry:
- Healthcheck:
```

## Governance Boundaries

This implementation stays inside documentation-workflow planning only:

- operator-invoked only
- bounded to seven named skills
- bounded by per-call and total session caps
- dependent on file-first capture
- dependent on telemetry JSONL acceptance
- dependent on healthcheck ingestion after accepted rows

It must not be treated as:

- production routing
- a global OR approval
- a canonical routing-table decision
- authority to continue `5.4` candidate evaluation

## Forbidden Without Explicit Approval

The following remain forbidden without separate explicit user approval:

- any OR call outside the seven approved skills
- any move into `DOC-SKILL-011`
- any move into `DOC-SKILL-012`
- any continuation of the `5.4` candidate phase
- any production routing activation
- any canonical routing-table update
- any release, merge, tag, or broad git-governance action
- any interpretation of the accepted live evidence as a repo-wide automatic routing permission

## Boundary Reminder

- mini matrix counts remain `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, `OR_REJECTED=0`
- Auto-sparsam remains operator-invoked and bounded
- no OR calls are made by this implementation plan
- no model calls are made by this implementation plan
- no live evals are started by this implementation plan
