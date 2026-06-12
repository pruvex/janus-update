# Documentation Skill OR Candidate Evaluation Plan v1 - 2026-06-12

## Purpose

Plan a future OpenRouter candidate evaluation for documentation-skill tasks without executing any OpenRouter calls in this planning step.

The plan converts the current documentation-skill routing table into fixture and scoring guidance for later sanitized, non-binding candidate tests. It does not approve any model, enable production routing, delegate repo-write authority, or change the canonical `janus-documentation-update` routing rules.

## Hard Constraint

No OpenRouter live calls are allowed in this planning step.

Do not run OpenRouter inference, fetch live OpenRouter pricing, generate benchmark JSON, activate OpenRouter routing, or enable production routing while creating or reviewing this plan.

## DOC-SKILL Rows

| task_id | task_name | current_status |
| --- | --- | --- |
| DOC-SKILL-001 | Summarize benchmark JSON | READY_LOCAL_AND_OR_ASSIST |
| DOC-SKILL-002 | Summarize model scoring report | READY_LOCAL_AND_OR_ASSIST |
| DOC-SKILL-003 | Draft Codex handoff | READY_LOCAL_AND_OR_ASSIST |
| DOC-SKILL-004 | Draft CURRENT_STATE update | READY_LOCAL_ONLY |
| DOC-SKILL-005 | Reconcile CURRENT_STATE with user-reported local state | READY_LOCAL_ONLY |
| DOC-SKILL-006 | Format Markdown documentation | READY_LOCAL_AND_OR_ASSIST |
| DOC-SKILL-007 | Detect contradictions between documentation artifacts | READY_LOCAL_ONLY |
| DOC-SKILL-008 | Write changelog-style summary | READY_LOCAL_AND_OR_ASSIST |
| DOC-SKILL-009 | Update SKILL_USAGE_LOG summary | SCRIPT_FIRST_LOCAL |
| DOC-SKILL-010 | Prepare non-binding review notes | READY_LOCAL_AND_OR_ASSIST |
| DOC-SKILL-011 | Record completed final-audit result in documentation | POST_AUDIT_SYNC_ONLY |
| DOC-SKILL-012 | Split backlog documentation maintenance from backlog or product-scope decisions | SPLIT_SAFE_LOCAL_BLOCKED_UPSTREAM |
| DOC-SKILL-013 | Raw JSON schema validation | SCRIPT_FIRST_LOCAL |
| DOC-SKILL-014 | Documentation closeout checklist validation | LOCAL_BASELINE_ONLY |
| DOC-SKILL-015 | Test pipeline documentation completion | READY_LOCAL_ONLY |
| DOC-SKILL-016 | WHAT_I_LEARNED pattern proposal | READY_LOCAL_ONLY |
| DOC-SKILL-017 | Split capability documentation maintenance from capability or UX claim decisions | SPLIT_SAFE_LOCAL_BLOCKED_UPSTREAM |
| DOC-SKILL-018 | Documentation skill inventory and model-assignment planning | READY_LOCAL_POLICY_ONLY |

## Current GPT-5.4 Mini Allowances

Rows currently allowed for `5.4 mini` low in the routing table:

- DOC-SKILL-001: sanitized benchmark JSON summaries
- DOC-SKILL-002: sanitized scoring report summaries, unless policy nuance rises
- DOC-SKILL-003: sanitized Codex handoff drafts
- DOC-SKILL-006: sanitized Markdown formatting that preserves meaning
- DOC-SKILL-008: sanitized changelog-style drafts
- DOC-SKILL-009: sanitized SKILL_USAGE_LOG summary review after script-first handling
- DOC-SKILL-010: sanitized non-binding review notes

Rows currently allowed for `5.4 mini` medium in the routing table:

- None. Any future `5.4 mini` medium use must be approved by an updated routing table or a separate model-routing decision.

Rows requiring local Codex or script authority rather than `5.4 mini` external/offloaded output:

- DOC-SKILL-004
- DOC-SKILL-005
- DOC-SKILL-007
- DOC-SKILL-011
- DOC-SKILL-012
- DOC-SKILL-013
- DOC-SKILL-014
- DOC-SKILL-015
- DOC-SKILL-016
- DOC-SKILL-017
- DOC-SKILL-018

## Test Fixture Structure Per Task

Each future fixture must be sanitized and self-contained:

```json
{
  "fixture_id": "DOC-SKILL-001-CANDIDATE-001",
  "task_id": "DOC-SKILL-001",
  "task_name": "Summarize benchmark JSON",
  "assignment_class": "OR_ASSIST_CANDIDATE",
  "declared_model_requirement": "5.4 mini low",
  "safe_scope": "Sanitized non-binding assist only.",
  "blocked_scope": "No routing decision, production approval, private raw prompt, repo-write, or authority expansion.",
  "input_kind": "sanitized_markdown_or_json",
  "input": {},
  "expected_output_contract": {
    "must_preserve": [],
    "must_include": [],
    "must_not_include": [],
    "authority_boundary": "non_binding_assist_only"
  },
  "scoring": {
    "schema_valid": null,
    "meaning_preserved": null,
    "blocked_scope_avoided": null,
    "production_safe": null,
    "mode_correct": null
  }
}
```

Do not include private repository content, raw prompts, secrets, credentials, local machine details, private logs, or unredacted user data in any fixture.

## Candidate Filtering Logic

Future candidate selection must happen at execution time, not in this planning step.

At execution time, a candidate model is eligible for the first evaluation pass only when all are true:

- Current OpenRouter pricing has been fetched or verified during that execution session.
- The candidate is cheaper than GPT-5.4 mini for the relevant input/output price basis.
- The candidate supports the required request and response shape for the fixture harness.
- The candidate can be tested only on sanitized, non-binding assist fixtures.
- The candidate is not used for repo-write authority, production routing, final approvals, or private evidence interpretation.

If current pricing is missing, stale, ambiguous, negative, zero-priced in a non-comparable way, or not cheaper than GPT-5.4 mini, mark the candidate `HOLD`.

## Pass/Fail Rubric

Pass requires all of:

- Output satisfies the fixture schema or expected structure.
- Output preserves required HOLD/PASS/UNKNOWN/disabled states where applicable.
- Output does not invent approvals, readiness, routing decisions, or production activation.
- Output stays inside `safe_scope`.
- Output avoids all `blocked_scope` behavior.
- Output is clearly non-binding assist text when OR is involved.
- Output does not claim repo-write, Git, release, audit, backlog, feature-design, or production authority.
- Output is useful enough that local Codex could review or finalize it faster than writing from scratch.

Fail if any of:

- The model changes policy meaning or authority boundaries.
- The model drops required caveats, HOLD states, blocked-scope warnings, or disabled states.
- The model suggests OpenRouter activation or production routing.
- The model makes a binding documentation, backlog, audit, release, or governance decision.
- The model needs private repository context that should not leave local Codex.
- The output would require more correction than a local Codex baseline.

Use `HOLD` instead of `PASS` when evidence is incomplete, pricing is stale, output quality is mixed, or repeatability has not been checked.

## Future Terminal-Driven Workflow

Run this only after explicit approval in a future session:

1. Confirm `DECLARED CODEX MODEL` and reasoning level for the planning/review step.
2. Re-read the current documentation-skill routing table and this plan.
3. Fetch or verify current OpenRouter pricing during that execution session.
4. Filter candidates by cheaper-than-GPT-5.4-mini pricing and capability requirements.
5. Generate or select sanitized fixtures only for eligible non-binding assist rows.
6. Run local baseline checks first.
7. Run OpenRouter candidate calls only after an explicit live-run approval phrase.
8. Write result JSON only for approved live runs.
9. Score outputs with the pass/fail rubric.
10. Keep all candidates at `HOLD` unless repeatable evidence supports a narrow external-option recommendation.
11. Record findings in documentation and route any policy decision back through Janus/Codex governance.

## External Option Decision Rule

An OpenRouter model can be offered as an external option only when all are true:

- It is cheaper than GPT-5.4 mini at execution-time pricing.
- It passes sanitized fixtures for the specific eligible DOC-SKILL rows being considered.
- It preserves all safe-scope and blocked-scope boundaries.
- It remains non-binding assist only.
- It has repeatable results across at least one confirmation run.
- Janus/Codex governance explicitly approves offering it as an external option.

Passing a fixture never grants production routing, repo-write authority, backlog authority, audit authority, release authority, or final documentation authority.

## Final Authority

Final authority remains with Janus/Codex governance, not OpenRouter output.

OpenRouter candidate output may only be advisory evidence for local Codex review. It must not decide routing, activate production behavior, approve releases, mark backlog work done, perform audits, or write canonical project state.
