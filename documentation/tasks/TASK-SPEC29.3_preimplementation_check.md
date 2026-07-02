PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC29.3
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it adds regression hardening, operator guidance, and exactly one bounded live-dev pilot for the already sealed worker gateway slices.
- Artifact identity is consistent across approved Spec 29, generated TASK-SPEC29, the sealed prior slices `TASK-SPEC29.1` and `TASK-SPEC29.2`, the released target-task handoff `TASK-SPEC29.3`, and this precheck artifact.
- The affected file cluster is concrete and bounded to worker-gateway tests, one operator-guidance doc, one live-dev evidence directory, and the existing worker scripts only where regression or pilot evidence requires it.
- Risk is HIGH because this is the first slice that may execute one real bounded live-dev worker run. Skill 4 must preserve the hard boundary: no OpenCode/OpenHands backend, no delegated product change outside a harmless bounded target, no commit/push/release/publish/dependency authority, and no acceptance without normalized artifacts, diff, and checks review.
- The live-dev pilot must stay a small internal Dev-/Docs-/Test task with explicit allowlist and clear fallback. If the local prerequisites are missing, the slice may complete with a documented blocker instead of forcing an unsafe run.
Affected Files:
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py
- documentation/codex/model-routing/janus_worker_gateway_profiles.md
- development/openrouter-skill-tests/janus-worker-gateway-live/
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests -q -k "janus_worker or isolated_aider"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- git diff --check -- documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/tests/test_janus_worker_contract.py documentation/codex/model-routing/tests/test_janus_worker_gateway.py documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py documentation/codex/model-routing/janus_worker_gateway_profiles.md documentation/tasks/TASK-SPEC29.3_preimplementation_check.md
- one bounded live-dev pilot result package or one documented blocker under development/openrouter-skill-tests/janus-worker-gateway-live/
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests -q -k "janus_worker or isolated_aider"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29.3_task_breakdown.md
- sealed TASK-SPEC29.1 and TASK-SPEC29.2 artifacts only as contract and runner context
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
Drop Context:
- earlier broad OR rollout history
- release prep, git-governance, changelog work
- product-runtime bug history unrelated to the worker gateway
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The final worker-gateway MVP slice is implementation-ready and tightly bounded to regression hardening, operator guidance, and one controlled live-dev pilot.
User Action: Say `ok` to start implementation of `TASK-SPEC29.3` with the bound scope and evidence gate above.
