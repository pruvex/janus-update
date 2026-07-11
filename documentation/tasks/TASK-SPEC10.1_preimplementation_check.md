PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC10.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC10_contact_memory_reconciliation.md
Spec: documentation/SPEC/10_contact_memory_reconciliation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: harden trusted contact fact sync on new memory writes without expanding into recall reconciliation or conflict dialog behavior from later tasks.
- Artifact identity is consistent across the approved Spec `documentation/SPEC/10_contact_memory_reconciliation.md`, the generated task artifact `documentation/tasks/TASK-SPEC10_contact_memory_reconciliation.md`, and the selected target task `TASK-SPEC10.1`.
- Scope stays inside the existing backend contact-memory write path: trust classification for sync-eligible contact facts, strict allowed-field enforcement, and dietary/besonderheiten classification.
- Implementation risk is MEDIUM because the task touches write semantics between memory ingestion and contact persistence, but the affected files and regression surface are concrete.
Affected Files:
- backend/tools/memory_tools.py
- backend/services/contact_manager.py
- backend/services/tool_executor.py
- backend/tests/test_contact_manager.py
- backend/tests/test_memory_tools.py
Evidence Focus:
- python -m pytest backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py -q
- python -m py_compile backend/tools/memory_tools.py backend/services/contact_manager.py backend/services/tool_executor.py
- Add or update focused regression coverage for trusted contact fact sync, blocked model-generated/imported memory sync, and dietary facts landing under Besonderheiten/Details.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py -q
- python -m py_compile backend/tools/memory_tools.py backend/services/contact_manager.py backend/services/tool_executor.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/10_contact_memory_reconciliation.md
- documentation/tasks/TASK-SPEC10_contact_memory_reconciliation.md
- backend/tools/memory_tools.py
- backend/services/contact_manager.py
- backend/services/tool_executor.py
- backend/tests/test_contact_manager.py
- backend/tests/test_memory_tools.py
Drop Context:
- later TASK-SPEC10.2 and TASK-SPEC10.3 work
- old backlog execution history not needed for this target task
- unrelated address book UI or dashboard context
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The task is implementation-ready on the current warm backend context and needs careful but bounded reasoning across memory write, trust classification, and contact persistence.
User Action: Say `ok` to start implementation of `TASK-SPEC10.1` with the bound scope and evidence gate above.
