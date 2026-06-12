# Documentation Skill Model Assignment Registry - 2026-06-12

Status: PROPOSED / REVIEW REQUIRED / NO PRODUCTION ROUTING

This registry condenses the documentation-skill inventory into a model-assignment plan. It is a design artifact only. It does not activate OpenRouter, rerun benchmarks, generate benchmark JSON, update production routing, or approve any Git/release/backlog/final-audit action.

## Baseline Policy

- Local `5.4 mini` low remains the clean mini baseline for small sanitized documentation assist tasks.
- `5.4` remains the normal Janus workhorse for binding documentation updates, marker validation, backlog/spec/test documentation sync, and real repo edits.
- `5.5` remains appropriate for final audit, release, security/privacy, provider-risk, or policy-sensitive documentation planning.
- Scripts should be used before models when the task is deterministic: JSON parse, schema validation, marker search, append-only log rows, version checks, duplicate detection, and dashboard/backlog validators.
- OpenRouter is not approved for routing decisions. It may be benchmarked later only on public/sanitized, non-binding documentation assist fixtures with `production_approved=false`.

## Registry

| task_id | assignment_class | primary local assignment | OR status | notes |
| --- | --- | --- | --- | --- |
| DOC-SKILL-001 | `OR_ASSIST_CANDIDATE` | `5.4 mini` low baseline; script extracts fields first when possible | Safe first fixture candidate | Benchmark JSON summary may be assisted only from sanitized result fields. |
| DOC-SKILL-002 | `OR_ASSIST_CANDIDATE` | `5.4 mini` low baseline; `5.4` medium for nuanced policy | Safe first fixture candidate | Must preserve all HOLD/UNKNOWN/no-production states. |
| DOC-SKILL-003 | `OR_ASSIST_CANDIDATE` | `5.4 mini` low for sanitized handoff wording; Codex finalizes | Safe first fixture candidate | Handoff draft cannot skip gates or expand context. |
| DOC-SKILL-004 | `CODEX_ONLY` | `5.4` medium or `5.5` medium | Blocked for OR final output | Final `CURRENT_STATE` update is local truth and must be Codex-reviewed. |
| DOC-SKILL-005 | `CODEX_ONLY` | `5.4` medium; `5.5` for risky contradiction | Blocked for OR | Reconciliation depends on local repo/user truth. |
| DOC-SKILL-006 | `OR_ASSIST_CANDIDATE` | `5.4 mini` low for sanitized text; Codex for repo edit | Safe first fixture candidate | Sanitized Markdown cleanup only; no repo-write delegation. |
| DOC-SKILL-007 | `CODEX_ONLY` | `5.4` medium; `5.5` high for release/audit/security contradiction | OR only for sanitized excerpt notes later | Private repo-state contradiction analysis stays local. |
| DOC-SKILL-008 | `OR_ASSIST_CANDIDATE` | `5.4 mini` low for sanitized draft; `5.4` medium for real changelog | Safe first fixture candidate | Draft only; no release/readiness or product-scope invention. |
| DOC-SKILL-009 | `SCRIPT_ONLY` | `record_skill_usage.py`; `summarize_skill_usage.py`; Codex review | Later sanitized assist candidate for synthetic summary only | Real append operations remain script/Codex-owned. |
| DOC-SKILL-010 | `OR_ASSIST_CANDIDATE` | `5.4 mini` low | Later fixture candidate | Non-binding review notes from sanitized excerpts only. |
| DOC-SKILL-011 | `POST_AUDIT_DOC_SYNC_ONLY` | No normal documentation routing before audit; after `PASS` or `PASS WITH FIXES`, use `janus-documentation-update` for bounded sync only | Blocked | This task must not perform final audit. Final required path is `janus-final-audit -> janus-documentation-update`. |
| DOC-SKILL-012 | `BLOCKED_FOR_OR` | `5.4` medium/high; `5.5` high if product/security risk | Blocked | Backlog/product-scope docs are decision-adjacent. |
| DOC-SKILL-013 | `SCRIPT_ONLY` | Local JSON/schema validators, then Codex review | Blocked | Deterministic validation should not be delegated. |
| DOC-SKILL-014 | `LOCAL_BASELINE_ONLY` | `5.4` medium with validator/search support; isolated `5.4 mini` low marker checks only | Blocked for now | Checklist truth depends on local markers. |
| DOC-SKILL-015 | `CODEX_ONLY` | `5.4` medium | Blocked | Test pipeline completion is binding validation documentation. |
| DOC-SKILL-016 | `CODEX_ONLY` | `5.4` medium; `5.5` high for security/release/provider root cause | Blocked for final append | Long-term memory writes need validated root cause and duplicate search. |
| DOC-SKILL-017 | `BLOCKED_FOR_OR` | `5.4` medium; `5.5` high for sensitive capability claims | Blocked | Product-facing capability registry changes are not assist-safe. |
| DOC-SKILL-018 | `CODEX_ONLY` | `5.5` medium for this policy pass; future `5.4` medium after stabilization | Blocked for policy decision | OR may later assist with sanitized fixture text, not assignment policy. |

## Counts

| assignment_class | count | task_ids |
| --- | ---: | --- |
| `CODEX_ONLY` | 6 | DOC-SKILL-004, DOC-SKILL-005, DOC-SKILL-007, DOC-SKILL-015, DOC-SKILL-016, DOC-SKILL-018 |
| `LOCAL_BASELINE_ONLY` | 1 | DOC-SKILL-014 |
| `OR_ASSIST_CANDIDATE` | 6 | DOC-SKILL-001, DOC-SKILL-002, DOC-SKILL-003, DOC-SKILL-006, DOC-SKILL-008, DOC-SKILL-010 |
| `OR_EXECUTION_CANDIDATE` | 0 | none |
| `SCRIPT_ONLY` | 2 | DOC-SKILL-009, DOC-SKILL-013 |
| `POST_AUDIT_DOC_SYNC_ONLY` | 1 | DOC-SKILL-011 |
| `BLOCKED_FOR_OR` | 2 | DOC-SKILL-012, DOC-SKILL-017 |

Total inventoried documentation tasks: 18.

## DOC-SKILL-011 Gate

- `DOC-SKILL-011` is not a final-audit execution task.
- Prerequisite: an existing final audit result of `PASS` or `PASS WITH FIXES`.
- Final required path: `janus-final-audit -> janus-documentation-update`.
- Do not assign `DOC-SKILL-011` to OpenRouter or normal documentation model routing.

## Activation Rules

Before any OR-assist activation for documentation tasks:

1. The fixture must be fully sanitized and committed to a no-live plan.
2. `production_approved` must remain `false`.
3. Codex must run or review the local `5.4 mini` baseline for the same fixture.
4. Exactly one OR candidate may be benchmarked after explicit user approval.
5. The OR output must be schema-checked or rubric-scored locally.
6. Codex must decide whether the output is useful; OR cannot decide routing, policy, backlog, product scope, final audit, release, or Git actions.
7. Any fallback must be local Codex, not another external live model, unless separately approved.

## Recommended First Benchmark

Recommended first OR-assist fixture to benchmark after review: `DOC-FIX-001`, the benchmark JSON summary fixture.

Reason: it is the most mechanical safe assist task, can use synthetic/sanitized result fields, has clear pass/fail criteria, and maps directly to current evidence without giving OR any authority over routing decisions.
