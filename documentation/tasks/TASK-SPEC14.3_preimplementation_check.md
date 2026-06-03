PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC14.3
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC14_gemini_cost_attribution_and_deepdive_forensics.md
Spec: documentation/SPEC/14_gemini_cost_attribution_and_deepdive_forensics.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- TASK-SPEC14.2 is complete and already persists grouped Gemini request evidence, so this task can focus on aggregation, anomaly summaries, deviation states, and historical May 2026 reconciliation on top of the established attribution trail.
- The bound task is still atomic: it stays backend-only, extends the existing monthly summary and cost endpoints, and does not yet touch the DeepDive frontend modal or Flash-default policy enforcement.
- The affected files are concrete and already form the current DeepDive data surface: `backend/data/crud.py` builds the monthly summary, `backend/api/routers/system.py` exposes the cost endpoints, `backend/services/cost_service.py` owns shared cost helpers, and `backend/tests/test_cost_token_tracking_completeness.py` already covers summary semantics that must expand for anomaly and residual handling.
- Implementation risk is HIGH because this task changes the backend payload shape consumed by the existing DeepDive surface and introduces historical reconciliation logic; a git checkpoint should be recommended through janus-git-governance before Skill 4.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile backend/data/crud.py backend/api/routers/system.py backend/services/cost_service.py
- python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q
- python -m pytest backend/tests/tools/test_websearch.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-step handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The backend forensic aggregation task is implementation-ready, uses the now-persisted Gemini attribution evidence as source data, and keeps the next cut strictly on aggregation plus API payloads before the DeepDive UI upgrade.
User Action: Say `ok` to start Skill 4 on TASK-SPEC14.3 here, or ask for janus-git-governance first if you want a checkpoint recommendation before the high-risk aggregation and historical reconciliation step.
