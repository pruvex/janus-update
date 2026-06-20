TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
- Task File: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
- Target Task: TASK-SPEC21.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 21 plus generated TASK-SPEC21 artifact; existing wider bounded OR worker infrastructure, historical quickchange or execution classes, and prior documentation-skill evidence are implementation context only and must not widen the first pilot slice beyond `debug_hypothesis_review` and `test_result_triage_review`
- Files: documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py, documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py, documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py, documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json, documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- Acceptance Criteria: only `janus-debug` with `debug_hypothesis_review` and `janus-test-pipeline` with `test_result_triage_review` can become OR-eligible in this first rollout; a package containing non-allowlisted or unredacted fields is blocked before any OR request is emitted; all other Janus skills and dispatcher task classes fall back deterministically to Codex-only at the eligibility gate; the eligibility output exposes reviewable `OR_ALLOWED`, `OR_NOT_ELIGIBLE`, or `OR_CONTEXT_REDACTION_REQUIRED` style outcomes without implying production routing
- Tests: extend `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py` with positive coverage for the two allowed pilot classes and negative coverage for out-of-scope task classes; add one fixture or unit-level check that a package with forbidden or unredacted fields is rejected before request dispatch; run the bounded eligibility test module; run `git diff --check` on the touched eligibility/config/test artifacts
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to the pre-request eligibility and context-redaction boundary only. This task must not add the user-facing cost/confidence gate, must not add telemetry or healthcheck ingestion, must not integrate new consumer classes, and must not preserve the current broader dispatcher eligibility set just because that infrastructure already exists. The goal is to hard-close the first rollout boundary and make the redaction rule locally testable before any later OR gate or live runner path is touched.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

@janus-preimplementation-check
Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Target Task: TASK-SPEC21.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
