# FINAL AUDIT - BACKLOG-108 contact fact routing debug delta

FINAL AUDIT RESULT: BLOCKED

Audit Model To Use: 5.5/high

Canonical State: BLOCKED

## Audit Scope

- Spec: N/A WITH REASON: Backlog bugfix/debug scope, no Feature Spec bound.
- Task: `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md`
- Backlog Item: BACKLOG-108
- TestSpec/TestRun: `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md`
- Audit Package: `documentation/test-runs/BACKLOG-108_AUDIT_PACKAGE.md`
- Changed Files:
  - `backend/services/contact_manager.py`
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/services/chat/context_builder.py`
  - `backend/services/orchestrator/execution_dispatcher.py`
  - `backend/services/memory_extractor.py`
  - `backend/tests/test_contact_manager.py`
  - `backend/tests/test_calendar_routing_fix.py`
  - `documentation/codex/SKILL_USAGE_LOG.md`

## Testmatrix

- `python -m pytest backend/tests/test_contact_manager.py -q`: PASS per bound debug artifact
- `python -m pytest backend/tests/test_calendar_routing_fix.py -q`: PASS per bound debug artifact
- `python -m py_compile backend/services/contact_manager.py backend/services/orchestrator/intent_engine.py backend/services/chat/context_builder.py backend/services/orchestrator/execution_dispatcher.py backend/services/memory_extractor.py backend/tests/test_contact_manager.py backend/tests/test_calendar_routing_fix.py`: PASS per bound debug artifact
- `python C:\Users\pruve\.codex\skills\janus-debug\scripts\validate_debug_result.py documentation\test-runs\BACKLOG-108_contact_fact_routing_debug.md`: PASS
- `python C:\Users\pruve\.codex\skills\codex-health-check\scripts\weekly_healthcheck.py`: WARN, non-blocking for Janus code; personal Codex skills validated, recommendation only

## Findings

- BLOCKER: `_suppress_identity_for_address_book_contact_recall()` is called with `wf.final_system_prompt`, not a verified address-book hit. Since `wf.final_system_prompt` is normally non-empty, any query matching contact-recall wording can suppress the user identity directive even when no concrete `**Adressbuch:**` contact context is present. This can regress legitimate user-profile recall such as `was weisst du ueber mich?` or other personal-recall turns by removing identity anchoring too broadly.

## Blocked By

- The identity/contact separation fix is under-scoped in tests and over-broad in execution: it proves suppression for an address-book contact hit, but does not prove suppression stays disabled when the final prompt lacks concrete `**Adressbuch:**` contact data.

## Re-Audit Trigger

- Update the suppressor or call site so identity suppression is gated by an actual address-book contact section, not merely by a non-empty final system prompt.
- Add regression evidence for both sides:
  - Contact recall with `**Adressbuch:**` contact hit suppresses the user identity directive.
  - User/self recall or contact-recall wording without a concrete address-book hit does not suppress the user identity directive.

## Audit Package Delta Required

- Update `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md` with the blocker delta, root cause, fix summary, and new validation commands.
- Refresh `documentation/test-runs/BACKLOG-108_AUDIT_PACKAGE.md` or add a compact re-audit delta section referencing this final audit.

## NEXT_STEP

Target Skill: janus-debug

Canonical State: HANDOFF

Required Artifacts: `documentation/test-runs/BACKLOG-108_contact_fact_routing_final_audit.md`, `documentation/test-runs/BACKLOG-108_AUDIT_PACKAGE.md`, `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md`

Evidence Paths: `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_calendar_routing_fix.py`

Failure Code: CONTACT_RECALL_IDENTITY_SUPPRESSION_TOO_BROAD

Changed Files: `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_calendar_routing_fix.py`, `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md`, `documentation/test-runs/BACKLOG-108_AUDIT_PACKAGE.md`

Decision: HANDOFF

Reason: FINAL AUDIT RESULT BLOCKED; identity suppression must be narrowed before documentation sync or git checkpoint.

Recommended Model: 5.5

Recommended Intelligence: hoch

Next Action: Run `janus-debug` on `CONTACT_RECALL_IDENTITY_SUPPRESSION_TOO_BROAD`, then rerun scoped tests and re-audit this same BACKLOG-108 delta.

Next User Action: Say `ok` to start `janus-debug` for `CONTACT_RECALL_IDENTITY_SUPPRESSION_TOO_BROAD`.
