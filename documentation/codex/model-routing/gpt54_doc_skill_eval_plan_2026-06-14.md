# GPT-5.4 Documentation Skill OR Evaluation Plan - 2026-06-14

Status: PLANNING ONLY / NO LIVE EVALS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Goal

Create the same disciplined evaluation ladder used for the completed mini work, but adapted for `5.4` documentation skills where many tasks are local truth, policy, audit, or governance work and therefore cannot be replaced by OR.

## Inputs

- `documentation/codex/model-routing/documentation_skill_routing_table_v1_2026-06-12.md`
- `documentation/codex/model-routing/gpt54_doc_skill_eligibility_matrix_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_or_candidate_price_shortlist_2026-06-14.md`
- `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.md`
- completed mini evidence and lessons, including fixed-model mini Auto-sparsam and Auto Router lessons learned

## Phase 0: Boundary Review

Output: confirm the candidate set before fixtures.

Candidate rows:

- `DOC-SKILL-002`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-012` safe maintenance subpart only
- `DOC-SKILL-017` safe maintenance subpart only

Blocked rows stay local unless a later explicit artifact narrows them to sanitized advisory text:

- `DOC-SKILL-004`
- `DOC-SKILL-005`
- `DOC-SKILL-007`
- `DOC-SKILL-011`
- `DOC-SKILL-014`
- `DOC-SKILL-015`
- `DOC-SKILL-016`
- `DOC-SKILL-018`

## Phase 1: Fixture Preparation

For each candidate row, create one sanitized fixture package:

- `README.md`
- `input.sanitized.json`
- `prompt.md`
- `local_reference_output.md`
- `acceptance_criteria.md`
- `blocked_authority_checks.md`

Fixture requirements:

- no private repo facts that require external truth judgment
- no raw secrets, tokens, logs, credentials, or private prompts
- exact forbidden claims listed
- expected local `5.4` behavior documented before any OR comparison

## Phase 2: Local Baseline

Run or record a local Codex baseline for each fixture before OR.

Baseline fields:

- `skill_id`
- `fixture_id`
- `local_model`
- `local_reasoning`
- `local_result_status`
- `local_cost_estimate_if_available`
- `authority_boundary_pass`
- `semantic_preservation_pass`
- `notes`

No OR model can be promoted unless it matches or exceeds the local baseline on authority boundaries and semantic preservation.

## Phase 3: No-Live Candidate Selection

Use the price shortlist to pick at most five candidates for the first comparison batch:

- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `inclusionai/ling-2.6-flash`
- `mistralai/mistral-nemo`
- `ibm-granite/granite-4.1-8b`

Do not use Auto Router in this phase. The mini Auto Router breadth test showed mixed evidence, including cost regression and `finish_reason=length`.

## Phase 4: Bounded OR Fixture Evaluation

Requires explicit user approval before any live call.

Per-call gates:

- fixed model selected from the candidate list
- estimated cost displayed before call
- confidence or sample-count caveat displayed before call
- per-call cost cap defined
- file-first capture wrapper used
- `generation_id`, usage, actual cost, and `finish_reason` captured
- telemetry JSONL row written only if acceptance gates pass
- `health_snapshot.py --or-telemetry-jsonl` ingestion passes

Abort conditions:

- estimate exceeds cap
- response body missing
- `generation_id` missing
- usage or fallback accounting unavailable
- `finish_reason=length`
- validation result is not `PASS`
- authority boundary fails
- output invents release, audit, product, routing, or policy authority

## Phase 5: Replacement Matrix

Only after fixture evaluation, create a `5.4` OR replacement or assist matrix with these statuses:

- `KEEP_CODEX`
- `OR_ASSIST_CANDIDATE`
- `FURTHER_TEST_CANDIDATE`
- `OR_REJECTED`
- `BLOCKED_LOCAL_ONLY`

Promotion rules:

- `OR_ASSIST_CANDIDATE`: OR is cheaper or equivalent, passes authority boundaries, and produces useful sanitized assist output, but local Codex remains final editor.
- `FURTHER_TEST_CANDIDATE`: promising but insufficient repeatability or one unresolved issue.
- `KEEP_CODEX`: OR is costlier, weaker, or less reliable than local `5.4`.
- `OR_REJECTED`: authority violation, repeated validation failure, missing usage/capture, or material semantic drift.
- `BLOCKED_LOCAL_ONLY`: task is inherently local truth, audit, release, policy, or governance work.

## Non-Goals

- no live evals in this planning step
- no OpenRouter Auto Router continuation
- no production routing
- no canonical routing-table update
- no global OR approval
- no `DOC-SKILL-011` run
- no `DOC-SKILL-012` product/backlog decision
- no replacement of the completed fixed-model mini Auto-sparsam path

## Next Concrete Step

Prepare fixture packages for `DOC-SKILL-002`, `DOC-SKILL-006`, and `DOC-SKILL-008` first. Defer `DOC-SKILL-012` and `DOC-SKILL-017` until a safe maintenance subpart is explicitly bound by an upstream decision.
