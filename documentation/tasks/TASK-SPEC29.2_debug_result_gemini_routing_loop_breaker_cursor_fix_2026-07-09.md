SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 2
Progress-Validierung: Failure Code SPEC29_2_GEMINI_ROUTING_LOOP_BREAKER_BLOCKS_PROMOTION; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- After the reload, silent candidate creation was already proven live on GPT, so the remaining bounded failure slice was no longer passive learning itself.
- The live Gemini trace for chat `4236` showed repeated `system.routing` calls followed by `[HARD-LOOP-BREAKER] (stream) duplicate blocked: system.routing`, with the user-visible fallback text about stopping a loop.
- Cursor confirmed the narrow root cause in `execution_dispatcher.py`: the `_routing_geo` dispatch block still applied routing-only forcing and routing-only calendar bans even when the same prompt also had a calendar-read intent.
- On Gemini this over-constrained mixed turn behavior could trap the model in routing-only retries instead of allowing the intended `system.routing + calendar.list_events` two-step path that is required for second-hit passive promotion.
Fix Summary:
- Ran the bounded shared delegation gate for `debug_repro_investigation` with a task-specific Cursor package.
- Prompt gate PASS: the lane exposed `3 = Cursor Composer` as the recommended live choice for this slice.
- First live invocation with stale choice `2` failed fast as expected with `CURSOR_LIVE_EXECUTION_REQUIRES_CURSOR_CHOICE`; reran correctly with choice `3`.
- Cursor Composer live run PASS for workflow `WF-SPEC29.2-GEMINI-ROUTING-LOOP-2026-07-09-001`.
- Accepted the bounded worker patch after Codex review:
  - added `_is_calendar_routing_combo(...)`
  - added `_build_routing_turn_skill_ids(...)`
  - updated `_routing_geo` handling so mixed calendar-plus-routing turns preserve both tool paths and drop routing-only force/ban logic
  - preserved routing-only forcing for pure routing turns
- Added focused regression coverage for the exact mixed prompt and helper behavior in `backend/tests/test_calendar_routing_fix.py`.
Auto-Verification:
- Status: PASS
- Evidence:
  - shared prompt gate PASS with positive ROI and Cursor recommended as choice `3`
  - live Cursor worker PASS: `final_outcome = CURSOR_WORKER_READY_FOR_CODEX_REVIEW`
  - Codex diff review PASS: changed files stayed inside allowlist
  - `python -m pytest backend/tests/test_calendar_routing_fix.py -q`: PASS (`42 passed`)
  - `python -m py_compile backend/services/orchestrator/execution_dispatcher.py`: PASS
  - `python -m pytest backend/tests/test_workflow_offer_service.py -q`: PASS (`14 passed`)
  - `python -m pytest backend/tests/test_routine_store.py -q`: FAIL, but only in pre-existing local ToolManager-stub tests unrelated to the current dispatcher slice (`_ToolManagerStub.__init__() takes 1 positional argument but 2 were given`)
Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- backend/services/orchestrator/execution_dispatcher.py
- backend/tests/test_calendar_routing_fix.py
- documentation/tasks/TASK-SPEC29.2_debug_result_gemini_routing_loop_breaker_cursor_fix_2026-07-09.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_routing_loop_breaker_2026-07-09/allowlist.txt
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_routing_loop_breaker_2026-07-09/worker_package.json
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_routing_loop_breaker_2026-07-09/input_package.json

NEXT_STEP
Target Skill: janus-test-pipeline
Canonical State: HANDOFF
Required Artifacts:
- documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29.2_execution_result.md
- documentation/tasks/TASK-SPEC29.2_debug_result_gemini_routing_loop_breaker_2026-07-09.md
- documentation/tasks/TASK-SPEC29.2_debug_result_gemini_routing_loop_breaker_cursor_fix_2026-07-09.md
Evidence Paths:
- documentation/logs/janus_backend.log
- C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db
- documentation/codex/model-routing/cursor-worker-runs/WF-SPEC29.2-GEMINI-ROUTING-LOOP-2026-07-09-001/
- backend/services/orchestrator/execution_dispatcher.py
- backend/tests/test_calendar_routing_fix.py
Failure Code:
- SPEC29_2_GEMINI_ROUTING_LOOP_BREAKER_BLOCKS_PROMOTION
Changed Files:
- backend/services/orchestrator/execution_dispatcher.py
- backend/tests/test_calendar_routing_fix.py
- documentation/tasks/TASK-SPEC29.2_debug_result_gemini_routing_loop_breaker_cursor_fix_2026-07-09.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_routing_loop_breaker_2026-07-09/allowlist.txt
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_routing_loop_breaker_2026-07-09/worker_package.json
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_routing_loop_breaker_2026-07-09/input_package.json
Decision:
- Keep the bounded Cursor-applied dispatcher fix and move to one fresh live Janus retest for the same mixed prompt.
Reason:
- The remaining blocker is now narrow enough that local code review plus focused validation justify a real app retest, but the slice cannot be called fully fixed until Gemini completes the second-hit promotion flow live.
Recommended Model: 5.4
Recommended Intelligence: high
Next User Action:
- Rerun `Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?` in Gemini. Expected result: normal combined calendar-plus-routing answer plus `Ich habe dafuer eine passende Routine gespeichert.`
