TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- Task File: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- Target Task: TASK-SPEC25.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 25 plus generated TASK-SPEC25 artifact; the sealed `TASK-SPEC25.1` contract for the dedicated productive class/model boundary must be reused unchanged, while `TASK-SPEC25.2` is limited to the visible productive operator gate, the fixed recommended OR model display, and the pre-call cost-basis display only
- Files: documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py, documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py, documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py, documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json, documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- Acceptance Criteria: the dedicated productive gate path shows the fixed recommended OR model for each allowed work class from the already sealed `TASK-SPEC25.1` contract; the visible gate shows the pre-call cost basis together with the required estimate and confidence fields before any wrapper or dispatcher path can start; missing fixed model mapping, missing cost basis, missing estimate, missing confidence, or other failed gate prerequisites must abort before wrapper or dispatcher invocation and leave a deterministic Codex-only or reviewable no-gate outcome; the runbook must describe only this dedicated productive gate standard and must not imply productive runtime execution, broad OR activation, production routing, or free manual model choice
- Tests: add focused automated coverage for prompt-mode and operator-facing gate output through `codex_dev_workhorse_runner.py` with visible `1 = Codex` / `2 = OR-Arbeitspferd`, fixed recommended OR model, pre-call cost basis, estimated cost, and confidence fields; add negative coverage for missing fixed model mapping, missing cost basis, missing estimated cost, and missing confidence so the runner aborts before wrapper or dispatcher invocation; add regression coverage that choosing `1` yields a local Codex-only result without delegating and that the sealed `TASK-SPEC25.1` class boundary remains unchanged; run the dedicated runner test module plus any directly touched eligibility or gate-helper regression module; run scoped `git diff --check` on the touched runner, gate helper, budget-profile config, runbook, and test artifacts
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to the visible operator-invoked gate slice for the dedicated productive Dev-workhorse path. This task must not add delegated runtime execution, accepted write handling, file-first capture, telemetry persistence, actual-cost closeout, healthcheck ingestion, or any expansion beyond the already sealed class/model contract from `TASK-SPEC25.1`.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

@janus-preimplementation-check
Spec: documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Task: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Backlog Item: N/A
Target Task: TASK-SPEC25.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
