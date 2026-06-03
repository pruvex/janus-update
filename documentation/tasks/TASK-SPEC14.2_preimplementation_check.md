PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC14.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC14_gemini_cost_attribution_and_deepdive_forensics.md
Spec: documentation/SPEC/14_gemini_cost_attribution_and_deepdive_forensics.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- TASK-SPEC14.1 is complete and provides the required attribution schema plus migration-safe persistence contract that this integration task depends on.
- The bound task is atomic: normalize Gemini-side `create_cost_entry()` call sites, attach shared request attribution metadata across base generation and Gemini websearch/grounding subcomponents, and expose explicit attribution-gap states without changing OpenAI behavior.
- Affected files and tests are concrete: Gemini gateway, websearch persistence wrapper, Gemini websearch service/provider paths, and the two existing Gemini/websearch regression modules.
- Implementation risk is HIGH because shared provider cost tracking is touched in multiple live call paths, so a git checkpoint should be recommended through janus-git-governance before Skill 4.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile backend/llm_providers/gemini/gateway.py backend/tool_registry.py backend/services/websearch/websearch.py backend/services/websearch/gemini_provider.py
- python -m pytest backend/tests/tools/test_websearch.py -q
- python -m pytest backend/tests/llm_providers/test_gemini_service.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, touched files, and next-step routing.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The Gemini attribution integration step is implementation-ready, bounded to named provider and websearch files, and the evidence gates are explicit for persistence plus regression safety.
User Action: Say `ok` to start Skill 4 on TASK-SPEC14.2 here, or ask for janus-git-governance first if you want a checkpoint recommendation before the multi-file provider integration.
