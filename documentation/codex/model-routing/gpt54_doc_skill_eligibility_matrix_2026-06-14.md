# GPT-5.4 Documentation Skill OR Eligibility Matrix - 2026-06-14

Status: PLANNING ONLY / NO LIVE EVALS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

Identify which documentation-skill rows that currently require `5.4` or may escalate to `5.4 medium` can safely enter a future OpenRouter candidate comparison phase.

This matrix is separate from the completed `5.4 mini` replacement work. It does not change the seven-skill mini matrix, the fixed-model mini Auto-sparsam path, or the canonical documentation-skill routing table.

## Eligibility Rules

- `5.4` truth, reconciliation, policy, contradiction, audit, and local-state tasks stay Codex/local-only.
- OR can only be tested on sanitized, non-binding assist slices.
- OR output cannot be the final authoritative documentation update for local state, audit outcomes, release readiness, backlog priority, capability claims, or policy assignments.
- Any future live OR call requires a separate explicit approval gate.

## Matrix

| skill_id | skill_name | current_5_4_relevance | eligibility | allowed_or_slice | local_only_boundary | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `DOC-SKILL-002` | Summarize model scoring report | `5.4 medium` if policy nuance rises | `OR_ASSIST_CANDIDATE_CONDITIONAL` | sanitized summary of scoring evidence, preserving HOLD/UNKNOWN/disabled states | no policy override, routing approval, or production-readiness claim | already covered by mini fixed OR for low-risk summaries; only enter 5.4 phase when nuance exceeds mini scope |
| `DOC-SKILL-004` | Draft CURRENT_STATE update | required `5.4 medium` | `LOCAL_ONLY` | none | final rolling state must be written from local bound facts and checks | OR-authored final state is blocked |
| `DOC-SKILL-005` | Reconcile CURRENT_STATE with user-reported local state | required `5.4 medium`; `5.5` if contradiction risk rises | `LOCAL_ONLY` | none, except possible future sanitized commentary after local fact extraction | local evidence comparison, contradiction handling, and final state correction | too truth-sensitive for OR replacement |
| `DOC-SKILL-006` | Format Markdown documentation | `5.4 low/medium` for real repo docs | `OR_ASSIST_CANDIDATE_CONDITIONAL` | sanitized Markdown cleanup draft that preserves meaning | repo-write delegation and semantic/policy rewrites remain local | mini fixed OR already covers safe mechanical formatting; 5.4 phase can test harder formatting fixtures |
| `DOC-SKILL-007` | Detect contradictions between documentation artifacts | required `5.4 medium`; `5.5` for release/audit/security contradictions | `LOCAL_ONLY_WITH_ADVISORY_EXCERPT_OPTION` | possible sanitized excerpt comparison only after local scoping | contradiction decision, severity, and final documentation change | not a replacement candidate |
| `DOC-SKILL-008` | Write changelog-style summary | `5.4 medium` for real changelog work | `OR_ASSIST_CANDIDATE_CONDITIONAL` | sanitized changelog draft from validated facts | final changelog edit, release implication, and readiness language remain local | mini fixed OR covers low-risk draft; 5.4 phase should test release-adjacent wording controls carefully |
| `DOC-SKILL-011` | Record completed final-audit result in documentation | `5.4 medium` after completed audit | `BLOCKED_POST_AUDIT_ONLY` | none | audit result recording after `janus-final-audit`; no audit decision or OR route | remains NOT RUN unless explicitly approved via final-audit path |
| `DOC-SKILL-012` | Split backlog documentation maintenance from backlog/product decisions | safe subparts `5.4 medium` | `SPLIT_SAFE_LOCAL_FIRST` | sanitized wording assist only after backlog/product decisions are fixed locally | priority, recommendation, scope, DONE status, routing, product decisions | do not start live testing until an approved safe maintenance fixture exists |
| `DOC-SKILL-014` | Documentation closeout checklist validation | required `5.4 medium` | `LOCAL_ONLY` | none | marker-scoped validation and exact blocker reporting | OR cannot validate local closeout truth |
| `DOC-SKILL-015` | Test pipeline documentation completion | required `5.4 medium` | `LOCAL_ONLY` | none | record PASS only from bound evidence | OR cannot author completion status |
| `DOC-SKILL-016` | WHAT_I_LEARNED pattern proposal | required `5.4 medium`; `5.5` for high-risk root causes | `LOCAL_ONLY_WITH_BRAINSTORM_OPTION` | sanitized brainstorm only, no append authority | duplicate search, validated root cause, hardening evidence, final append | not a replacement candidate |
| `DOC-SKILL-017` | Split capability documentation maintenance from capability/UX claim decisions | safe subparts `5.4 medium` | `SPLIT_SAFE_LOCAL_FIRST` | sanitized wording assist only after claim scope is fixed and validated locally | capability claims, UX behavior, privacy/security guarantees, support level | do not start live testing until an approved safe maintenance fixture exists |
| `DOC-SKILL-018` | Documentation skill inventory and model-assignment planning | current policy pass `5.5 medium`; future `5.4 medium` after stabilization | `LOCAL_POLICY_ONLY` | possible sanitized fixture text, not assignment decisions | policy inventory, assignment registry, routing recommendations | this current artifact is a local planning task |

## Initial Candidate Set For Future Fixture Work

Only these rows should be considered first, and only with sanitized fixture inputs:

- `DOC-SKILL-002`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-012` safe maintenance subpart only
- `DOC-SKILL-017` safe maintenance subpart only

## Explicit Exclusions

- `DOC-SKILL-004`, `DOC-SKILL-005`, `DOC-SKILL-014`, `DOC-SKILL-015`, and final-output `DOC-SKILL-016` stay local.
- `DOC-SKILL-007` is not a replacement candidate; at most it can receive later advisory excerpt tests.
- `DOC-SKILL-011` remains blocked behind completed final-audit evidence.
- `DOC-SKILL-018` remains local policy planning and cannot delegate assignment authority to OR.
