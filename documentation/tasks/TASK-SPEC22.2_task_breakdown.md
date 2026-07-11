TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
- Task File: documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
- Target Task: TASK-SPEC22.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 22 plus generated TASK-SPEC22 artifact; the sealed `TASK-SPEC22.1` boundary contract for `productive_dev_workhorse_path` is already fixed and must be reused unchanged, while delegated execution wiring, Codex-owned acceptance, actual-cost closeout, and healthcheck visibility remain deferred to `TASK-SPEC22.3` and `TASK-SPEC22.4`
- Files: documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py, documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py, documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py, documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py, documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- Acceptance Criteria: the dedicated `codex_dev_workhorse_runner.py` is the only new productive operator-facing entry for the Spec-22 rollout and is bound to `productive_dev_workhorse_path` only; in-scope calls show a visible operator choice with `1 = Codex` and `2 = OR`, plus selected OR model, estimated OR cost, confidence, and explicit scope hints before any wrapper or dispatcher path can start; missing estimate, missing confidence, missing budget, or failed eligibility data must abort before wrapper or dispatcher invocation and leave a deterministic Codex-only or reviewable no-gate outcome; the runbook must describe only this new dedicated Dev-workhorse entry and must not imply that existing Janus skills already gained a broad productive OR path
- Tests: add focused automated coverage for prompt-mode and operator-facing gate output through `codex_dev_workhorse_runner.py` with visible `1 = Codex` / `2 = OR`, selected model, estimated cost, and confidence fields; add negative coverage for missing estimated cost, missing confidence, and failed eligibility so the runner aborts before wrapper or dispatcher invocation; add regression coverage that choosing `1` yields a local Codex-only result without delegating; run the dedicated runner test module plus any touched eligibility regression module; run `git diff --check` on the touched runner, gate helper, runbook, and tests
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to the visible operator-invoked entry runner and its mandatory pre-dispatch gate fields. This task must not add delegated execution wiring, accepted write handling, telemetry persistence, actual-cost closeout, healthcheck ingestion, or any expansion beyond the already sealed `productive_dev_workhorse_path` contract from `TASK-SPEC22.1`.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

@janus-preimplementation-check
Spec: documentation/SPEC/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Task: documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Backlog Item: N/A
Target Task: TASK-SPEC22.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
