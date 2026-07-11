SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 3
Progress-Validierung: Failure Code SPEC29_2_GEMINI_LATE_ROUTING_FORCE_OVERRIDE; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- The earlier mixed calendar-plus-routing patch was active in the live app at `2026-07-09 19:46`, so the running Janus process was not stale anymore.
- Live log evidence for chat `4238` shows the exact remaining seam:
  - first `💎 ROUTING-GEO: Mixed calendar+routing turn detected. Preserving combined tool set`
  - then immediately `💎 DIAMOND-CORE-ROUTING-FORCE: Routing intent detected. Forcing tool_choice for system.routing`
  - then repeated Gemini `system_routing` function calls until the hard loop breaker stopped the turn
- This proves the mixed-turn preservation block was later overwritten by a second generic force-tool override in `execution_dispatcher.py`.
- A side-effect of the still-broken live path is already visible in the DB: a second active candidate was created from chat `4237`, but its trace is polluted with two routing steps plus one calendar step instead of the intended clean two-step signature.
Fix Summary:
- Built a second, even narrower Cursor-first package for the exact late override seam:
  - `development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_force_override_2026-07-09/`
- Live Cursor Composer run for workflow `WF-SPEC29.2-GEMINI-FORCE-OVERRIDE-2026-07-09-001` timed out at the bounded `180s` limit without returning artifacts.
- After collecting that routing evidence, applied the smallest local product fix:
  - added `_should_force_routing_tool_choice(...)`
  - changed the late `DIAMOND-CORE-ROUTING-FORCE` block so mixed calendar-read plus routing turns no longer end with `force_tool_name=system.routing`
  - kept forced routing active for pure routing-only turns
- Added focused regression coverage for the exact late-override rule in `backend/tests/test_calendar_routing_fix.py`.
Auto-Verification:
- Status: PASS
- Evidence:
  - targeted live log review PASS around `2026-07-09 19:46:50` to `19:46:55`
  - live DB inspection PASS: `user_routine_candidates = 2`, including the polluted three-step candidate from chat `4237`
  - second bounded Cursor package validation PASS
  - second live Cursor Composer run BLOCKED by `CURSOR_AGENT_TIMEOUT`
  - `python -m pytest backend/tests/test_calendar_routing_fix.py -q`: PASS (`44 passed`)
  - `python -m py_compile backend/services/orchestrator/execution_dispatcher.py`: PASS
Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- backend/services/orchestrator/execution_dispatcher.py
- backend/tests/test_calendar_routing_fix.py
- documentation/tasks/TASK-SPEC29.2_debug_result_gemini_force_override_2026-07-09.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_force_override_2026-07-09/allowlist.txt
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_force_override_2026-07-09/worker_package.json
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_force_override_2026-07-09/input_package.json

NEXT_STEP
Target Skill: janus-test-pipeline
Canonical State: HANDOFF
Required Artifacts:
- documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29.2_execution_result.md
- documentation/tasks/TASK-SPEC29.2_debug_result_gemini_routing_loop_breaker_cursor_fix_2026-07-09.md
- documentation/tasks/TASK-SPEC29.2_debug_result_gemini_force_override_2026-07-09.md
Evidence Paths:
- documentation/logs/janus_backend.log
- C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db
- documentation/codex/model-routing/cursor-worker-runs/WF-SPEC29.2-GEMINI-FORCE-OVERRIDE-2026-07-09-001/
- backend/services/orchestrator/execution_dispatcher.py
- backend/tests/test_calendar_routing_fix.py
Failure Code:
- SPEC29_2_GEMINI_LATE_ROUTING_FORCE_OVERRIDE
Changed Files:
- backend/services/orchestrator/execution_dispatcher.py
- backend/tests/test_calendar_routing_fix.py
- documentation/tasks/TASK-SPEC29.2_debug_result_gemini_force_override_2026-07-09.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_force_override_2026-07-09/allowlist.txt
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_force_override_2026-07-09/worker_package.json
- development/openrouter-skill-tests/janus-debug/workflow_spec29_2_gemini_force_override_2026-07-09/input_package.json
Decision:
- Keep the late-force override fix and move directly to one fresh live Gemini retest.
Reason:
- The current blocker is now isolated to a single late dispatcher condition, and the local regression suite explicitly covers the intended mixed-turn rule.
Recommended Model: 5.4
Recommended Intelligence: high
Next User Action:
- Rerun `Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?` in Gemini once after the updated backend is running. Expected result: no loop-breaker text; instead a normal combined answer plus `Ich habe dafuer eine passende Routine gespeichert.`
