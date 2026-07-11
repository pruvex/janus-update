TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
- Task File: documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
- Target Task: TASK-SPEC30.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 30 plus generated TASK-SPEC30 artifact; the second released slice is only the comparable shadow-run and result-pipeline layer, and must not widen into final consumer recommendation, real product-code delegation, repo writeback outside the isolated shadow sandbox, or any global worker-release decision
- Files: documentation/codex/model-routing/scripts/janus_worker_gateway.py, documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py, documentation/codex/model-routing/tests/test_janus_worker_gateway.py, documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py, development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/shadow_evaluation_manifest.json, development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/docs_fleissarbeit/, development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/
- Acceptance Criteria: each of the two required shadow work classes runs exactly the fixed model pair `openrouter/qwen/qwen3-coder-30b-a3b-instruct` and `openrouter/moonshotai/kimi-k2.5` on the same bounded task package or records a fail-closed blocker instead of silently skipping; each individual run emits normalized result artifacts for content outcome, changed files, executed checks, usage or cost hints, and scope-discipline status; each class produces one local side-by-side class summary that compares the two fixed runs against the same acceptance markers; missing artifacts, red checks, scope drift, missing usage data, or any attempted writeback outside the sandbox are not treated as reviewable success
- Tests: add focused runner and gateway coverage for fixed-pair comparison execution, normalized shadow result capture, class-summary generation, missing-artifact fail-closed behavior, red-check rejection, missing-usage rejection, and sandbox writeback rejection; run `python -m pytest documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py -q -k "shadow or evaluation"`; run `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "comparison or result or fail_closed"`; run `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`; run `git diff --check` on touched scripts, tests, shadow-eval run artifacts, and task artifacts
- Execution Model: 5.4
- Readiness: Scope is bounded to executing and capturing the first comparable shadow runs only. This target task may run the already-fixed `qwen` versus `kimi` pair across the two seeded shadow classes and write normalized local result artifacts, but it must not issue the final first-consumer recommendation, must not activate any real worker consumer, and must not expand into broader routing policy, Git/release authority, or non-sandbox product edits that belong outside TASK-SPEC30.2.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

@janus-preimplementation-check
Spec: documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Task: documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Backlog Item: N/A
Target Task: TASK-SPEC30.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
