PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6.5
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_a.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only the confirmed streaming boundary: StreamEvent protocol, auth isolation, forced-tool start, delta normalization, and stream-final cost remain in execution_engine.
- Flag-on may route only non-streaming tool-round handoff through existing gateway/runner seams; flag-off remains unchanged.
- OpenRouter review is planned-only; Codex owns the final precheck decision.
Affected Files:
- backend/services/orchestrator/execution_engine.py
- backend/tests/test_streaming_tool_loop_runner.py
Evidence Focus:
- focused streaming flag-off/flag-on regression
- provider stream regression selected during execution
- python -m py_compile backend/services/orchestrator/execution_engine.py
Scope-Regel:
- Implement only TASK-M6.5. No StreamEvent rewrite, delta parser migration, auth-isolation change, forced-tool policy change, Gemini grounding-policy change, transport classes, resolver, OAuth, or Phase-B work.
Automated Evidence Gate:
- focused streaming regression
- python -m py_compile backend/services/orchestrator/execution_engine.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and task-breakdown handoff verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- M6.5 task, Spec Section 3.3.3, execution_engine streaming loop, gateway/runner boundaries.
Drop Context:
- completed M6.1 through M6.4 implementation history and Phase-B work.
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: M6.5 has an explicit stream ownership boundary and no remaining architecture decision.
User Action: Execution proceeds in this approved M6 chain.
