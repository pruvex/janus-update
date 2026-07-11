SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 5
Progress-Validierung: Failure Code SPEC29_2_PASSIVE_PROMOTION_SIGNATURE_DRIFT; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- The visible Gemini mixed-turn failure is already fixed in production, but passive promotion still depended on an exact workflow fingerprint.
- Cursor worker evidence and local review confirmed the real seam: `get_active_candidate_by_fingerprint(...)` only matched exact step-order plus arg-key fingerprints.
- Equivalent mixed `calendar.list_events + system.routing` traces could therefore diverge when the tool order flipped or when harmless arg-shape drift appeared, such as:
  - calendar using `start_date` plus `end_date` in one run and `range=today` in the next
  - routing using `from_city` / `to_city` in one run and `origin` / `destination` in the next
- The first Cursor patch proved the bounded direction, but its raw skill-set equivalence was too broad because it could have merged distinct routes or different calendar scopes into one candidate.
Fix Summary:
- Built and executed a Cursor-first bounded worker slice:
  - `WF-SPEC29.2-PASSIVE-PROMOTION-SIGNATURE-DRIFT-2026-07-09-001`
  - live Cursor Composer run PASS with review artifacts returned
- Reviewed the returned patch locally and kept the bounded equivalence approach, but narrowed it before acceptance:
  - exact fingerprint matching still stays first
  - passive candidate promotion now has a conservative equivalence fallback for the specific mixed `calendar.list_events + system.routing` family
  - the fallback only matches when both runs resolve to the same normalized day meaning and the same normalized routing endpoints and mode
  - different routes remain separate candidates even if they use the same two skills
- Added focused regression coverage proving both:
  - equivalent order/arg drift promotes correctly
  - distinct route requests do not collapse into one candidate
Auto-Verification:
- Status: PASS
- Evidence:
  - live Cursor worker PASS: `documentation/codex/model-routing/cursor-worker-runs/WF-SPEC29.2-PASSIVE-PROMOTION-SIGNATURE-DRIFT-2026-07-09-001/`
  - Cursor response review PASS: returned bounded patch and focused pytest success
  - `python -m pytest backend/tests/test_workflow_offer_service.py -q`: PASS (`16 passed`)
  - `python -m py_compile backend/services/workflow/routine_schema.py backend/services/workflow/routine_store.py backend/services/workflow/workflow_detector.py backend/services/workflow/workflow_offer_service.py`: PASS
Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- backend/services/workflow/routine_schema.py
- backend/services/workflow/routine_store.py
- backend/services/workflow/workflow_detector.py
- backend/services/workflow/workflow_offer_service.py
- backend/tests/test_workflow_offer_service.py
- documentation/tasks/TASK-SPEC29.2_debug_result_passive_promotion_signature_drift_cursor_fix_2026-07-09.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_passive_promotion_signature_drift_2026-07-09/allowlist.txt
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_passive_promotion_signature_drift_2026-07-09/input_package.json
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_passive_promotion_signature_drift_2026-07-09/worker_package.json

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29.2_execution_result.md
- documentation/tasks/TASK-SPEC29.2_debug_result_passive_promotion_signature_drift_2026-07-09.md
- documentation/tasks/TASK-SPEC29.2_debug_result_passive_promotion_signature_drift_cursor_fix_2026-07-09.md
Evidence Paths:
- documentation/logs/janus_backend.log
- C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db
- documentation/codex/model-routing/cursor-worker-runs/WF-SPEC29.2-PASSIVE-PROMOTION-SIGNATURE-DRIFT-2026-07-09-001/
- backend/services/workflow/routine_schema.py
- backend/services/workflow/routine_store.py
- backend/services/workflow/workflow_detector.py
- backend/services/workflow/workflow_offer_service.py
- backend/tests/test_workflow_offer_service.py
Failure Code:
- SPEC29_2_PASSIVE_PROMOTION_SIGNATURE_DRIFT
Changed Files:
- backend/services/workflow/routine_schema.py
- backend/services/workflow/routine_store.py
- backend/services/workflow/workflow_detector.py
- backend/services/workflow/workflow_offer_service.py
- backend/tests/test_workflow_offer_service.py
- documentation/tasks/TASK-SPEC29.2_debug_result_passive_promotion_signature_drift_cursor_fix_2026-07-09.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_passive_promotion_signature_drift_2026-07-09/allowlist.txt
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_passive_promotion_signature_drift_2026-07-09/input_package.json
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_passive_promotion_signature_drift_2026-07-09/worker_package.json
Decision:
- Keep the narrowed passive-promotion equivalence fix and move to one fresh live Gemini/GPT retest of the same mixed prompt.
Reason:
- We now have both Cursor worker evidence and local regression proof for the exact signature-normalization seam, but we still need one live product retest to confirm Janus promotes the existing candidate instead of creating another one.
Recommended Model: 5.4
Recommended Intelligence: high
Next User Action:
- Rerun `Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?` once in the live app after the updated backend is active. Expected result: normal combined answer plus `Ich habe dafuer eine passende Routine gespeichert.`
