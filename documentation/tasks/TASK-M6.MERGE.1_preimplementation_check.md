PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6.MERGE.1
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_MASTER_INTEGRATION.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The failed merge is one reproducible integration slice between current master and the final-audited M6 feature branch. M6 aggregate audit and Cursor external review are PASS; master integration alone is unresolved.
- Resolve each hunk against merge base, master, and M6 sides. Preserve newer master behavior and all M6 transport contracts; no global ours/theirs selection is allowed.
Affected Files:
- CHANGELOG.md
- PROJECT_STATE.md
- WHAT_I_LEARNED.md
- backend/data/schemas_intent.py
- backend/tests/test_agent_factory_runtime.py
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- documentation/codex/model-routing/cursor_delegation_log.jsonl
Evidence Focus:
- python -m pytest backend/tests/test_agent_factory_runtime.py -q
- python -m pytest backend/tests/test_provider_parity.py backend/tests/test_tool_call_adapter.py backend/tests/test_response_postprocessors.py backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_transport_layer_gemini_gateway.py backend/tests/test_transport_layer_ollama_gateway.py backend/tests/tools/test_websearch.py -q
- python -m py_compile backend/data/schemas_intent.py
- git diff --check
- git grep -n -E '^(<<<<<<<|=======|>>>>>>>)' -- CHANGELOG.md PROJECT_STATE.md WHAT_I_LEARNED.md backend/data/schemas_intent.py backend/tests/test_agent_factory_runtime.py "documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md" documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md documentation/codex/model-routing/cursor_delegation_log.jsonl
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no C3 deletion, no release/version change, no unrelated Ollama worktree modification, and no scope expansion.
Automated Evidence Gate:
- Run the bound Python compile and pytest matrix after conflict resolution.
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test --list --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound M6 task/spec identity
- nine-file conflict allowlist
- master, merge-base, and M6 feature sides
- regression commands
Drop Context:
- unrelated Ollama worktree changes
- closed M6 slice implementation chatter
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Integration execution result, executed checks, changed files, and next-skill handoff.
legacy handoff end
```

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
User Action: approve bounded conflict-resolution execution before any merge hunk is edited.
