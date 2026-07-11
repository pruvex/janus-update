TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- Task File: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- Target Task: TASK-SPEC25.3
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 25 plus generated TASK-SPEC25 artifact; the sealed `TASK-SPEC25.1` productive class/model contract and the sealed `TASK-SPEC25.2` visible operator gate must both be reused unchanged, while `TASK-SPEC25.3` is limited to bounded write/apply runtime wiring, file-first result persistence, local validation, and an explicit Codex-owned final outcome only
- Files: documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py, documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py, documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py, documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py, documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
- Acceptance Criteria: the dedicated `codex_dev_workhorse_runner.py` can route exactly the two allowlisted productive classes `execution_patch_candidate` and `execution_write_apply_candidate` from the already sealed visible gate into the existing bounded execution runners without widening any other workflow entry; delegated results end in explicit Codex-owned statuses such as `accept`, `reject`, `fallback`, or `manual review` instead of being treated as self-authenticating success; file-first artifacts and local validation remain visible for accepted and non-accepted runs; unsupported classes, scope escapes, validation failures, or weak delegated outcomes do not gain implicit success and do not reopen any mixed review or assist-only path
- Tests: add focused automated coverage proving the dedicated runner can route `execution_patch_candidate` and `execution_write_apply_candidate` into the intended bounded runtime path after the sealed gate; add negative coverage for unsupported classes, scope-escaping or cap-violating delegated outcomes, and local-validation or weak-result failure paths so the final result is deterministic `fallback`, `reject`, or `manual review`; run the dedicated runner test module plus any directly touched bounded dispatcher or candidate-runner regression modules; run `git diff --check` on the touched runtime files and tests
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to the productive bounded runtime and explicit Codex-owned acceptance seam that `TASK-SPEC25.2` deliberately left open. This task must not change the already sealed fixed-model mapping, visible cost-basis gate, production-routing semantics, canonical routing-table state, broad OR activation, or any out-of-path Janus workflow entry.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

@janus-preimplementation-check
Spec: documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Task: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Backlog Item: N/A
Target Task: TASK-SPEC25.3
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
