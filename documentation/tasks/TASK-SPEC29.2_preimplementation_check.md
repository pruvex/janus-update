PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC29.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it wires the existing isolated Aider/OpenRouter runner into the validated `janus-worker` gateway contract and makes every backend outcome emit the normalized result package.
- Artifact identity is consistent across approved Spec 29, generated TASK-SPEC29, the released target-task handoff `TASK-SPEC29.2`, the completed prior contract slice `TASK-SPEC29.1`, and this precheck artifact.
- The affected file cluster is concrete and bounded to the existing isolated runner, the new gateway/contract files from TASK-SPEC29.1, and focused tests for successful artifact emission, blocked/local outcomes, invalid profile or missing key, scope drift rejection, and repo-root side-effect rejection.
- Risk is HIGH because this slice is the first real bounded Aider/OpenRouter backend wiring for the new gateway. Skill 4 must preserve the hard boundary: no OpenCode/OpenHands support, no broad Janus skill activation, no commit/push/release/publish/dependency authority, no product-runtime changes, and no first bounded live-dev pilot yet.
- This slice may wire normalized result emission and copy-back gating into the isolated runner, but it must not yet add operator guidance docs or claim the gateway is ready for everyday live use before TASK-SPEC29.3.
Affected Files:
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q
- python -m py_compile documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py
- git diff --check -- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py documentation/codex/model-routing/tests/test_janus_worker_gateway.py documentation/tasks/TASK-SPEC29.2_preimplementation_check.md
- focused negative-path checks for missing `OPENROUTER_API_KEY`, invalid profile, scope drift, missing required result artifacts, operator-local fallback, and repo-root side effects
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q
- python -m py_compile documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29.1_execution_result.md
- documentation/tasks/TASK-SPEC29.2_task_breakdown.md
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
Drop Context:
- completed TASK-SPEC29.1 audit and documentation-sync detail beyond the contract behavior it established
- later TASK-SPEC29.3 operator guidance and live-dev pilot
- OpenCode, OpenHands, broad OR routing, release, Git governance, and product-runtime history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The first real backend wiring slice is implementation-ready and tightly bounded to isolated Aider/OpenRouter integration plus normalized artifact emission.
User Action: Say `ok` to start implementation of `TASK-SPEC29.2` with the bound scope and evidence gate above.
