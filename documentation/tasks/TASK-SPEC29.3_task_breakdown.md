TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- Task File: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- Target Task: TASK-SPEC29.3
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 29 plus generated TASK-SPEC29 artifact; the third released slice adds regression hardening, operator guidance, and one bounded live-dev pilot only, and must not widen into new backend families, release prep, broad Janus skill activation, or unbounded delegated product work
- Files: documentation/codex/model-routing/scripts/janus_worker_gateway.py, documentation/codex/model-routing/tests/test_janus_worker_contract.py, documentation/codex/model-routing/tests/test_janus_worker_gateway.py, documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py, documentation/codex/model-routing/janus_worker_gateway_profiles.md, development/openrouter-skill-tests/janus-worker-gateway-live/, documentation/tasks/TASK-SPEC29.3_execution_result.md
- Acceptance Criteria: regression coverage clearly separates successful and fail-closed worker outcomes; operator guidance documents Aider/OpenRouter as the MVP backend and keeps OpenCode/OpenHands explicitly out of MVP scope; one bounded live-dev pilot produces a normalized result package or a documented blocker; Codex does not accept any worker outcome without diff, checks, and artifact review
- Tests: extend focused regression coverage for success, missing key, invalid profile, forbidden file, red checks, missing artifacts, and local fallback paths; run `python -m pytest documentation/codex/model-routing/tests -q -k "janus_worker or isolated_aider"`; run `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`; execute one bounded live-dev pilot under `development/openrouter-skill-tests/janus-worker-gateway-live/` or document a concrete blocker
- Execution Model: 5.4
- Readiness: Scope is bounded to hardening and proof. This target task may add regression tests, write profile/operator guidance, and run exactly one small isolated live-dev worker pilot, but it must not add OpenCode/OpenHands, broad delegated product execution, release/Git authority, or re-open the already sealed TASK-SPEC29.1/TASK-SPEC29.2 slices except where regression evidence requires it.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

@janus-preimplementation-check
Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Task: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Backlog Item: N/A
Target Task: TASK-SPEC29.3
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
