# Documentation Skill Codex Reasoning Baseline Matrix

Date: 2026-06-12

Baseline context: conceptual check against the currently selected local `5.4 mini low` reasoning level.

Scope: documentation-skill tasks only, using synthetic/sanitized task checks and no OpenRouter calls.

Follow-up context: the nine low-fail tasks below were re-evaluated conceptually against local `5.4 mini medium`.

High follow-up context: the three medium-fail tasks below were then re-evaluated conceptually against local `5.4 mini high`.

## Summary

- Total tasks assessed: 18
- PASS on low: 9
- FAIL on low: 9
- PASS on medium for previously failed tasks: 6
- FAIL on medium for previously failed tasks: 3
- PASS on high for previously medium-failed tasks: 0
- FAIL on high for previously medium-failed tasks: 3

## Matrix

| task_id | task_name | assignment_class | low_result | low_reason | medium_result | medium_reason | high_result | high_reason | next_required_reasoning_if_failed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DOC-SKILL-001 | Summarize benchmark JSON | OR_ASSIST_CANDIDATE | PASS | Sanitized field extraction and HOLD/PASS wording are compact and deterministic at low reasoning. | not retested | n/a | not retested | n/a | n/a |
| DOC-SKILL-002 | Summarize model scoring report | OR_ASSIST_CANDIDATE | PASS | Advisory summary from a sanitized excerpt is straightforward if the task stays non-binding. | not retested | n/a | not retested | n/a | n/a |
| DOC-SKILL-003 | Draft Codex handoff | OR_ASSIST_CANDIDATE | PASS | Template-driven handoff drafting with explicit exclusions fits low reasoning when the scope is bounded. | not retested | n/a | not retested | n/a | n/a |
| DOC-SKILL-004 | Draft CURRENT_STATE update | CODEX_ONLY | FAIL | This is binding state synchronization and needs truthful synthesis of local facts, not a low-level rewrite pass. | PASS | Medium can reconcile local state, changed files, and validation evidence into a truthful rolling snapshot. | not retested | n/a | n/a |
| DOC-SKILL-005 | Reconcile CURRENT_STATE with user-reported local state | CODEX_ONLY | FAIL | Reconciling state against repository evidence requires judgment about truth and freshness beyond low reasoning. | PASS | Medium can compare local evidence with the user report and call out stale or conflicting state explicitly. | not retested | n/a | n/a |
| DOC-SKILL-006 | Format Markdown documentation | OR_ASSIST_CANDIDATE | PASS | Pure Markdown cleanup for sanitized text is a good low-reasoning mechanical task. | not retested | n/a | not retested | n/a | n/a |
| DOC-SKILL-007 | Detect contradictions between documentation artifacts | CODEX_ONLY | FAIL | Contradiction detection across artifacts is comparison-heavy and can affect binding docs, so low is too weak. | PASS | Medium is sufficient to compare two sanitized documentation artifacts and list exact contradictions. | not retested | n/a | n/a |
| DOC-SKILL-008 | Write changelog-style summary | OR_ASSIST_CANDIDATE | PASS | Changelog wording from sanitized change notes is manageable at low reasoning if release claims stay forbidden. | not retested | n/a | not retested | n/a | n/a |
| DOC-SKILL-009 | Update SKILL_USAGE_LOG summary | SCRIPT_ONLY | PASS | Counting, summarizing, or appending a synthetic row is mechanically safe at low reasoning. | not retested | n/a | not retested | n/a | n/a |
| DOC-SKILL-010 | Prepare non-binding review notes | OR_ASSIST_CANDIDATE | PASS | Advisory notes over sanitized text are a low-risk language task when authority language is banned. | not retested | n/a | not retested | n/a | n/a |
| DOC-SKILL-011 | Record completed final-audit result in documentation | POST_AUDIT_DOC_SYNC_ONLY | FAIL | This task must not perform final audit; it may only sync an already completed `PASS` or `PASS WITH FIXES` result after `janus-final-audit`. | FAIL | Medium does not change the boundary: audit execution belongs to `janus-final-audit`, and documentation may only follow a completed audit result. | FAIL | High still does not convert this into a normal documentation-routing task; it remains post-audit documentation sync only. | `janus-final-audit -> janus-documentation-update` |
| DOC-SKILL-012 | Prepare backlog or product-scope documentation | BLOCKED_FOR_OR | FAIL | Backlog and scope docs encode product decisions, so low reasoning is not enough for safe authorship. | FAIL | Medium still leaves too much product-scope judgment unresolved for safe backlog-style wording. | FAIL | High still leaves product-scope authority too exposed for safe documentation. | n/a |
| DOC-SKILL-013 | Raw JSON schema validation | SCRIPT_ONLY | PASS | Deterministic schema validation is script-first and only needs low-level Codex review. | not retested | n/a | not retested | n/a | n/a |
| DOC-SKILL-014 | Documentation closeout checklist validation | LOCAL_BASELINE_ONLY | PASS | Marker-only checklist validation is mechanical enough for low reasoning when inputs are tightly bounded. | not retested | n/a | not retested | n/a | n/a |
| DOC-SKILL-015 | Test pipeline documentation completion | CODEX_ONLY | FAIL | Test-pipeline closeout binds validation status, so it needs stronger evidence handling than low reasoning. | PASS | Medium can integrate the artifact set and document pipeline completion or an exact blocked handoff. | not retested | n/a | n/a |
| DOC-SKILL-016 | WHAT_I_LEARNED pattern proposal | CODEX_ONLY | FAIL | Pattern proposals need root-cause judgment and long-term memory discipline, which low reasoning cannot safely cover. | PASS | Medium is enough to draft a pattern proposal from validated evidence while keeping append authority with Codex. | not retested | n/a | n/a |
| DOC-SKILL-017 | Capability registry or UX capability documentation | BLOCKED_FOR_OR | FAIL | Capability docs are product-facing claims and must not be inferred at low reasoning from sanitized snippets alone. | FAIL | Medium still does not provide enough safety for product-facing capability wording without stronger governance review. | FAIL | High still lacks enough safety for product-facing capability wording. | n/a |
| DOC-SKILL-018 | Documentation skill inventory and model-assignment planning | CODEX_ONLY | FAIL | The planning artifact itself sets policy boundaries, so low reasoning is too shallow for final assignment decisions. | PASS | Medium can handle the policy-mapped inventory follow-up and preserve the local no-OR decision boundary. | not retested | n/a | n/a |

## Failed Tasks for Next Medium Run

Recommended next run at `5.5 high` for the remaining fails:

- DOC-SKILL-011
- DOC-SKILL-012
- DOC-SKILL-017

Medium follow-up pass set:

- DOC-SKILL-004
- DOC-SKILL-005
- DOC-SKILL-007
- DOC-SKILL-015
- DOC-SKILL-016
- DOC-SKILL-018

High follow-up pass count: 0
High follow-up fail count: 3
Remaining failed task ids after high follow-up:

- DOC-SKILL-011
- DOC-SKILL-012
- DOC-SKILL-017

## DOC-SKILL-011 Boundary

- Correct classification: `POST_AUDIT_DOC_SYNC_ONLY`
- Prerequisite: existing final audit result `PASS` or `PASS WITH FIXES`
- Final required path: `janus-final-audit -> janus-documentation-update`
- Not eligible for OR or normal documentation model routing

## Notes

- `PASS` here means the task is conceptually safe for the currently selected `5.4 mini low` reasoning level under a sanitized, synthetic check.
- `FAIL` means the task should be reserved for a stronger reasoning level or a more authoritative Codex path before any binding output.
- No OpenRouter calls, benchmark JSON generation, Git actions, or production routing decisions were used in this matrix.
