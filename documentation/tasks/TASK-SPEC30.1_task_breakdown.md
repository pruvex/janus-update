TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
- Task File: documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
- Target Task: TASK-SPEC30.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 30 plus generated TASK-SPEC30 artifact; the first released slice is only the bounded shadow-task packaging and fixed comparison-config layer, and must not widen into live shadow-run execution, final consumer recommendation, real product-code delegation, or any repo writeback outside the isolated evaluation sandbox
- Files: development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/, documentation/codex/model-routing/scripts/janus_worker_gateway.py, documentation/codex/model-routing/scripts/janus_worker_contract.py, documentation/codex/model-routing/tests/test_janus_worker_gateway.py, documentation/codex/model-routing/tests/test_janus_worker_contract.py
- Acceptance Criteria: exactly two shadow work classes are defined and no third implicit class appears; each class has one normalized bounded task package with isolated allowlist, forbidden actions, acceptance criteria, and check commands; each class binds exactly two fixed worker models for the same comparison path; the configuration grants no product-code writeback, no skill/Git/release authority, and no already-approved real consumer activation
- Tests: add focused contract and gateway coverage for shadow-evaluation task packaging, isolated allowlist enforcement, forbidden action rejection, fixed two-model comparison config, and fail-closed sandbox boundaries; run `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q -k "shadow or evaluation or allowlist"`; run `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "shadow or evaluation or sandbox"`; run `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py`; run `git diff --check` on touched scripts, tests, shadow-eval fixtures, and task artifacts
- Execution Model: 5.4
- Readiness: Scope is bounded to defining the two shadow work classes, their local packages, and the fixed comparison structure only. This target task must not start real model runs, must not build the final recommendation package, must not activate any real consumer, and must not expand into broader backend or routing policy beyond the isolated evaluation surface needed by later TASK-SPEC30.2 and TASK-SPEC30.3 slices.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

@janus-preimplementation-check
Spec: documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Task: documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Backlog Item: N/A
Target Task: TASK-SPEC30.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
