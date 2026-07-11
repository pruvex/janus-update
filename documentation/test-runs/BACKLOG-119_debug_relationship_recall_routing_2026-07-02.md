SKILL 5 DEBUG RESULT: FIXED

Iteration: 2
Progress-Validierung: Failure Code `RELATIONSHIP_RECALL_ROUTED_AWAY_FROM_CONTACT_MEMORY`; Evidence geaendert ggue. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- The remaining live BACKLOG-119 failure was no longer persistence. Nathan's contact card already stored `Freundin heisst Elena`, but fresh recall prompts like `wer ist nathans freundin?` were still classified and dispatched down the wrong runtime path.
- `backend/services/orchestrator/intent_engine.py` did not reliably classify possessive relationship recall prompts as `personal_recall`.
- `backend/services/orchestrator/execution_dispatcher.py` did not force the corrected recall slice onto `memory.read`, so the live run could still drift into `system.wikipedia_summary`.
- `backend/services/tool_executor.py` and `backend/tools/memory_tools.py` still had legacy-shape and subject-scope seams that made cross-provider write/retrieval less deterministic for relationship facts.

Fix Summary:
- Extended `backend/services/orchestrator/intent_engine.py` so possessive prompts such as `wer ist nathans freundin?` and `wie heisst nathans freundin?` classify as `personal_recall`.
- Added a deterministic relationship-recall forcing rule in `backend/services/orchestrator/execution_dispatcher.py` so this slice executes through `memory.read`.
- Hardened `backend/services/tool_executor.py` to normalize legacy `memory.write` arguments before schema validation, including top-level `query` / `text` / `value`, `priority`, and legacy `key`-derived `subject_name` / `category`.
- Extended `backend/tools/memory_tools.py` possessive subject filtering so queries like `wer ist timos freundin?` or `wer ist korbinians freundin?` stay bound to the correct subject and do not leak older unrelated relationship facts.
- Added focused regressions for routing, legacy `memory.write` normalization, and possessive relationship recall filtering.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_calendar_routing_fix.py -q -k "relationship_contact or contact_knowledge_question_bypasses_external_and_ambiguity"`: PASS
  - `python -m pytest backend/tests/test_tool_executor_memory_write_normalization.py -q`: PASS
  - `python -m pytest backend/tests/test_memory_tools.py -q -k "filters_relationship_recall_to_matching_possessive_subject or filters_contact_recall_to_matching_subject"`: PASS
  - ad-hoc intent sanity check: `wer ist nathans freundin?` and `wie heisst nathans freundin?` now classify as `personal_recall`, while `wer ist nikola tesla?` still routes to the public-knowledge path

Artifact Identity Check: PASS
Final Feature Suite: PASS
Changed Files:
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/orchestrator/execution_dispatcher.py`
- `backend/services/tool_executor.py`
- `backend/tools/memory_tools.py`
- `backend/tests/test_calendar_routing_fix.py`
- `backend/tests/test_memory_tools.py`
- `backend/tests/test_tool_executor_memory_write_normalization.py`
- `documentation/test-runs/BACKLOG-119_debug_relationship_recall_routing_2026-07-02.md`

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts:
- `documentation/tasks/backlog_BACKLOG-119_execution_result.md`
- `documentation/test-runs/BACKLOG-119_debug_relationship_persistence_2026-07-02.md`
- `documentation/test-runs/BACKLOG-119_debug_relationship_recall_routing_2026-07-02.md`
- `documentation/test-results/BACKLOG-119-live-retest-after-routing-fix-2026-07-02/BACKLOG-119_live_retest_after_routing_fix_api_evidence.json`
- `documentation/test-results/BACKLOG-119-live-retest-after-routing-fix-2026-07-02/BACKLOG-119_live_retest_after_routing_fix_api_summary.md`
Evidence Paths:
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/orchestrator/execution_dispatcher.py`
- `backend/services/tool_executor.py`
- `backend/tools/memory_tools.py`
- `backend/tests/test_calendar_routing_fix.py`
- `backend/tests/test_memory_tools.py`
- `backend/tests/test_tool_executor_memory_write_normalization.py`
- `documentation/logs/janus_backend.log`
- `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`
Failure Code:
- `RELATIONSHIP_RECALL_ROUTED_AWAY_FROM_CONTACT_MEMORY`
Changed Files:
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/orchestrator/execution_dispatcher.py`
- `backend/services/tool_executor.py`
- `backend/tools/memory_tools.py`
- `backend/tests/test_calendar_routing_fix.py`
- `backend/tests/test_memory_tools.py`
- `backend/tests/test_tool_executor_memory_write_normalization.py`
- `documentation/test-runs/BACKLOG-119_debug_relationship_recall_routing_2026-07-02.md`
Decision:
- move to `janus-final-audit`; the narrowed routing slice is now fixed, regression-covered, and backed by a fresh live cross-provider recall pass
Reason:
- the live Korbinian/Ylvie retest proves the full provider/chat path now persists the relationship into the contact card and answers the relationship from `memory.read` in a fresh GPT chat
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Run `janus-final-audit` on the combined execution, debug, and live PASS evidence bundle for `BACKLOG-119`.
