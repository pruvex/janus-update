TASK EXECUTION RESULT
Canonical State: NEEDS_INFO
Target Task: TASK-MEM-M1.1
Changed Files:
- backend/services/memory/retrieval_service.py
- backend/services/memory_budget.py
- backend/services/memory_observability.py
- backend/services/chat_orchestrator.py
- backend/tests/test_memory_hot_layer_cap.py
- backend/tests/test_memory_on_demand_injection.py
- documentation/tasks/TASK-MEM-M1.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Executed Checks:
- `python -m py_compile backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py`
- `python -m pytest backend/tests/test_memory_hot_layer_cap.py -v`
- `python -m pytest backend/tests/test_memory_on_demand_injection.py -v`
- `python -m pytest backend/tests/test_memory_hot_layer_cap.py -v backend/tests/test_memory_on_demand_injection.py -v backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py -q`
- `git diff --check -- backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py backend/tests/test_memory_hot_layer_cap.py backend/tests/test_memory_on_demand_injection.py backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md`
Auto-Verification:
- Status: PASS
- Evidence:
  - `retrieve_diamond_slots()` now supports a bounded `include_general_memory=False` path so generic/external queries can skip general retrieval while the health injector still runs.
  - `should_inject_memory(...)` now keeps personal-scope queries such as `wo ich wohne` eligible for retrieval while blocking generic weather/external-context requests.
  - High-priority memory slots are now tiered more explicitly (`core_always` vs. `core_identity`) so the bounded hot-layer cap can run on the always-on core slice instead of the full memory pool.
  - `select_slots_by_budget()` now applies the Phase-A hot-layer cap behind `MEMORY_HOT_LAYER_CAP_ENABLED`, preserves protected `health`/`medical` slots, and records `slots_dropped_core_cap`.
  - `format_memory_context()` now renders `health_mandatory` slots explicitly instead of letting that safety tier disappear from the formatted context block.
  - Focused new suites passed for protected core-cap behavior, weather-vs-personal gating, and health-only retrieval without query-embedding dependency; the bound legacy memory regression block stayed green (`68 passed`).
Manual Janus Validation Gate:
- Status: PASS
- Test Example: Starte Janus normal und teste nacheinander im Chat `Wie wird das Wetter in Berlin, wo ich wohne?` und danach `Ich habe eine Nussallergie, was soll ich beim Essen beachten?`
- Expected Result: Beim Wetter-Prompt darf Janus weiterhin den Wohnortbezug sinnvoll nutzen, statt die persönliche Memory-Schicht komplett zu verlieren. Beim Allergie-Prompt muss Janus weiterhin die Gesundheits-/Allergie-Information sicher berücksichtigen und darf sie nicht wegen On-Demand-Gating unterschlagen.
- Recorded Result: PASS am `2026-07-08` auf GPT und Gemini. Wetter mit Wohnortbezug blieb sinnvoll (`Wie wird das Wetter in Köln, wo ich wohne?`), und die Allergie-Antwort blieb sicher und alltagstauglich (`Ich habe eine Nussallergie, was soll ich beim Essen beachten?`) ohne erkennbaren Verlust der Health-/Medical-Schutzlogik.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts:
- documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
- documentation/tasks/TASK-MEM-M1.1_task_breakdown.md
- documentation/tasks/TASK-MEM-M1.1_preimplementation_check.md
- documentation/tasks/TASK-MEM-M1.1_execution_result.md
Audit Package:
- N/A until the Manual Janus Validation Gate is confirmed PASS
Evidence Paths:
- backend/services/memory/retrieval_service.py
- backend/services/memory_budget.py
- backend/services/memory_observability.py
- backend/services/chat_orchestrator.py
- backend/tests/test_memory_hot_layer_cap.py
- backend/tests/test_memory_on_demand_injection.py
Failure Code: N/A
Changed Files:
- backend/services/memory/retrieval_service.py
- backend/services/memory_budget.py
- backend/services/memory_observability.py
- backend/services/chat_orchestrator.py
- backend/tests/test_memory_hot_layer_cap.py
- backend/tests/test_memory_on_demand_injection.py
- documentation/tasks/TASK-MEM-M1.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Decision: HANDOFF
Reason: The bounded Memory A+B slice is code-complete, locally green, and the required Manual Janus Validation Gate now passed on both GPT and Gemini.
Recommended Model: 5.4
Recommended Intelligence: medium
New Chat: no
Next User Action: Run the two manual Janus prompts above; if both behave as expected, route this artifact set to `janus-final-audit`.
