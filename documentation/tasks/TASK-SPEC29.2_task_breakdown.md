TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- Task File: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- Target Task: TASK-SPEC29.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 29 plus generated TASK-SPEC29 artifact; the second released slice wires the existing isolated Aider/OpenRouter runner into the validated gateway contract, and must not widen into OpenCode/OpenHands support, broad skill activation, release or Git authority, or the later operator guidance and live-dev pilot work that belong outside TASK-SPEC29.2
- Files: documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py, documentation/codex/model-routing/scripts/janus_worker_contract.py, documentation/codex/model-routing/scripts/janus_worker_gateway.py, documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py, documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- Acceptance Criteria: a successful isolated Aider/OpenRouter run emits the normalized result package and is reviewable by Codex; missing `OPENROUTER_API_KEY`, invalid profile, red checks, scope drift, or missing artifacts do not produce `success`; the runner remains isolated from repo-root `.aider*` and `.gitignore` side effects; the worker gains no commit, push, release, publish, or dependency authority
- Tests: add focused runner coverage for successful normalized artifact emission, missing key, invalid profile, blocked and local operator outcomes, scope drift rejection, missing artifact rejection, and repo-root side-effect rejection; run `python -m pytest documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py -q`; run `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q`; run `python -m py_compile documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py`; run `git diff --check` on the touched scripts, tests, and task artifacts
- Execution Model: 5.4
- Readiness: Scope is bounded to the first real backend integration only. This target task may wire the existing isolated Aider/OpenRouter runner into the gateway contract and produce normalized result packages, but it must not add OpenCode/OpenHands, broad Janus skill entry activation, final operator guidance, changelog/release behavior, or the first live-dev pilot that belongs to TASK-SPEC29.3.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

@janus-preimplementation-check
Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Task: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Backlog Item: N/A
Target Task: TASK-SPEC29.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
