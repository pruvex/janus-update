TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
- Task File: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
- Target Task: TASK-SPEC21.4
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 21 plus generated TASK-SPEC21 artifact; the sealed `TASK-SPEC21.1` eligibility/redaction boundary, the sealed `TASK-SPEC21.2` visible operator gate, and the sealed `TASK-SPEC21.3` file-first capture plus truthful telemetry finalization must be reused unchanged while this slice adds only the bounded consumer wiring for the two already approved pilot classes
- Files: documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py, documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py, documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py, documentation/codex/skills/janus-debug/SKILL.md, documentation/codex/skills/janus-test-pipeline/SKILL.md, documentation/codex/model-routing/tests/
- Acceptance Criteria: `janus-debug` can offer OR only for `debug_hypothesis_review` and otherwise keeps a deterministic Codex-only path; `janus-test-pipeline` can offer OR only for `test_result_triage_review` and otherwise keeps a deterministic Codex-only path; accepted, rejected, and manual-review outcomes for both pilot classes surface a clear Codex-owned completion state with model and cost context from the sealed capture and telemetry path; no other Janus skill, debug mode, or test-pipeline class receives an implicit OR path through this integration slice
- Tests: add focused positive automated coverage for `debug_hypothesis_review` using the visible bounded gate plus Codex-owned final outcome; add focused positive automated coverage for `test_result_triage_review` using the visible bounded gate plus Codex-owned final outcome; add negative coverage that non-approved debug or test-pipeline modes stay Codex-only before any OR runner path starts; add regression coverage that sealed eligibility, visible gate, file-first capture, truthful telemetry finalization, and local healthcheck ingestion continue to behave unchanged for the two pilot classes; run the focused consumer integration test modules plus scoped `git diff --check` on the touched runner, dispatcher, skill-doc, and test artifacts
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to wiring the already sealed shared OR foundation into exactly two approved everyday consumer paths: `janus-debug/debug_hypothesis_review` and `janus-test-pipeline/test_result_triage_review`. This task must not widen the pilot skill list, add other debug or test-pipeline classes, alter the sealed cost or confidence gate semantics, enable production routing, change canonical routing tables, or introduce autonomous OR repo-write authority.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

@janus-preimplementation-check
Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Target Task: TASK-SPEC21.4
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
