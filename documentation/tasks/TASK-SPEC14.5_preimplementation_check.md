PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC14.5
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC14_gemini_cost_attribution_and_deepdive_forensics.md
Spec: documentation/SPEC/14_gemini_cost_attribution_and_deepdive_forensics.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- TASK-SPEC14.4 is complete and the DeepDive surface already consumes the Gemini forensic payload, so this task can stay strictly on provider-policy enforcement and evidence tagging rather than UI or aggregation work.
- The bound task is atomic: enforce Flash as the default Gemini grounding/websearch model path, require an explicit visible override before Pro is allowed, and propagate that override evidence into the existing attribution trail.
- The affected files are concrete and already own the policy path: `backend/tool_registry.py` handles Gemini websearch routing and cost persistence, `backend/services/websearch/websearch.py` owns provider dispatch, `backend/services/websearch/gemini_provider.py` owns Gemini-native search prompts and grounding metadata, `backend/llm_providers/gemini/gateway.py` owns Gemini tool-loop orchestration, and the two listed tests cover regression-sensitive policy behavior.
- Acceptance is measurable from the existing surface: Gemini grounding/websearch defaults to Flash, Pro is only reachable via explicit override, and the data written for DeepDive can distinguish manual Pro use from avoidable or policy-breaking Pro usage.
- Implementation risk is MEDIUM-HIGH because this task changes live provider-selection behavior and cost attribution evidence, so a git checkpoint should be recommended through janus-git-governance before Skill 4.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/tools/test_websearch.py -q
- python -m pytest backend/tests/test_smallest_viable_model_escalation_discipline.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The Gemini Flash-default policy task is implementation-ready, bounded to provider-policy and regression tests, and fits the warm 5.4 workflow without a model upgrade.
User Action: Say `ok` to start Skill 4 on TASK-SPEC14.5 here, or ask for janus-git-governance first if you want a checkpoint recommendation before the provider-policy change.
