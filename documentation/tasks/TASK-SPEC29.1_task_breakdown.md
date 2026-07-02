TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- Task File: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- Target Task: TASK-SPEC29.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 29 plus generated TASK-SPEC29 artifact; the first released slice is the normalized worker task/result contract only, and must not widen into real Aider/OpenRouter execution, live model calls, copy-back of worker changes, or OpenCode/OpenHands support that belong outside TASK-SPEC29.1
- Files: documentation/codex/model-routing/scripts/janus_worker_contract.py, documentation/codex/model-routing/scripts/janus_worker_gateway.py, documentation/codex/model-routing/tests/test_janus_worker_contract.py, documentation/codex/model-routing/tests/test_janus_worker_gateway.py, documentation/codex/model-routing/strong-or-fixtures/
- Acceptance Criteria: valid task packages and result directories are deterministically accepted; missing required fields, forbidden actions, empty allowlists, or missing result artifacts are deterministically rejected; `success` is only possible when status, diff, changed files, checks, and cost/usage metadata are contract-consistent; the contract grants the worker no Git, release, publish, dependency, security, privacy, or architecture authority
- Tests: add focused contract fixtures for valid success, blocked, failed, scope drift, missing artifact, forbidden action, and empty allowlist cases; run `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q`; run `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "contract or result or fail_closed"`; run `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py`; run `git diff --check` on touched scripts, tests, fixtures, and task artifacts
- Execution Model: 5.4
- Readiness: Scope is bounded to schema, validators, fixture contract, and fail-closed classification. This target task must not run Aider, must not call OpenRouter, must not alter copied-back repo files from a worker, and must not add broader skill integration. The output should make TASK-SPEC29.2 implementation possible by defining the contract it must satisfy.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

@janus-preimplementation-check
Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Task: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Backlog Item: N/A
Target Task: TASK-SPEC29.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
