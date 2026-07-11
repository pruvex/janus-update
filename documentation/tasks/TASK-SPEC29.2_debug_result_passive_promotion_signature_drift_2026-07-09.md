SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 4
Progress-Validierung: Failure Code SPEC29_2_PASSIVE_PROMOTION_SIGNATURE_DRIFT; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- The visible Gemini loop is now fixed in production. The `19:55` live run executed exactly two successful tools without the old loop-breaker text.
- Live log for chat `4239` shows a clean mixed path:
  - `force_tool_name=None`
  - two successful tool calls only: `calendar.list_events` and `system.routing`
  - normal combined assistant answer
- Despite that, no passive promotion text was appended.
- Live DB explains why: Janus created a third active candidate instead of promoting the earlier one.
- The new candidate from chat `4239` has fingerprint `c79f934b...` with step order `calendar.list_events -> system.routing`, while the earlier clean candidate from chat `4235` has fingerprint `7493f2f2...` with step order `system.routing -> calendar.list_events` and slightly different argument shape (`end_date` present there, absent here).
- So the remaining blocker is no longer routing or loop handling. Passive promotion currently depends on a stricter workflow signature than the real Gemini/OpenAI mixed-turn behavior provides across runs.
Fix Summary:
- No new product-code fix was applied in this block.
- Verified that the latest dispatcher fix removed the late routing force override in the live app.
- Confirmed the remaining acceptance gap is signature drift / normalization drift between otherwise equivalent mixed two-skill traces.
- This is a new bounded debug slice and a strong Cursor-first candidate because the failure is now narrowly about routine-signature equivalence and promotion matching.
Auto-Verification:
- Status: PASS
- Evidence:
  - targeted live log review PASS around `2026-07-09 19:55:15` to `19:55:25`
  - live mixed-turn dispatcher evidence PASS: `force_tool_name=None`, no loop-breaker text
  - live tool execution PASS: only `calendar.list_events` and `system.routing`
  - live DB inspection PASS: `user_routine_candidates = 3`, `user_routines = 1`
  - new candidate row PASS: chat `4239`, fingerprint `c79f934b1abd9bab64c77823fb869a3be4917a596558f554c3e34b989db9d781`
  - prior clean candidate still active PASS: chat `4235`, fingerprint `7493f2f266fe30719f61f7bd607f30c5e3c770ff84a56289aeb96b728489471c`
Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- documentation/tasks/TASK-SPEC29.2_debug_result_passive_promotion_signature_drift_2026-07-09.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29.2_execution_result.md
- documentation/tasks/TASK-SPEC29.2_debug_result_gemini_force_override_2026-07-09.md
- documentation/tasks/TASK-SPEC29.2_debug_result_passive_promotion_signature_drift_2026-07-09.md
Evidence Paths:
- documentation/logs/janus_backend.log
- C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db
- backend/services/workflow/workflow_offer_service.py
- backend/services/workflow/routine_store.py
Failure Code:
- SPEC29_2_PASSIVE_PROMOTION_SIGNATURE_DRIFT
Changed Files:
- documentation/tasks/TASK-SPEC29.2_debug_result_passive_promotion_signature_drift_2026-07-09.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Decision:
- Treat the visible mixed-turn path as fixed and open a new bounded debug slice for passive-promotion signature normalization.
Reason:
- The feature is now failing one layer later than before: not in dispatch or loop handling, but in deciding that two semantically equivalent mixed turns count as the same learned routine.
Recommended Model: 5.4
Recommended Intelligence: high
Next User Action:
- If we continue immediately, package a Cursor-first bounded debug slice for candidate signature normalization and promotion matching instead of rerunning the same live prompt again first.
