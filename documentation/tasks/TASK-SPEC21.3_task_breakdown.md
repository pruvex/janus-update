TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
- Task File: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
- Target Task: TASK-SPEC21.3
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 21 plus generated TASK-SPEC21 artifact; the sealed `TASK-SPEC21.1` eligibility/redaction boundary and the sealed `TASK-SPEC21.2` visible operator gate must be reused unchanged, while consumer-runner integration remains deferred to `TASK-SPEC21.4`
- Files: documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1, documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py, documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py, documentation/codex/skills/janus-health-check/scripts/health_snapshot.py, documentation/codex/model-routing/tests/
- Acceptance Criteria: an accepted or rejected bounded pilot run produces reviewable file-first capture artifacts plus exactly one bounded telemetry row; the shared outcome path can surface actual OR cost after completion when provider usage exists or emit a documented fallback state when usage is incomplete; `health_snapshot.py` can ingest the bounded OR telemetry without changing existing non-OR healthcheck behavior; incomplete capture, missing usage, or validatorically unsafe result states cannot be reported as accepted success
- Tests: add fixture-driven automated coverage for complete file-first capture and bounded telemetry generation; add negative coverage for missing usage or incomplete capture so the run becomes reject or fallback instead of accepted success; add healthcheck-ingestion coverage against bounded OR telemetry summaries for accepted and rejected pilot runs; add regression coverage that `health_snapshot.py` keeps its existing behavior when no OR telemetry input is supplied; run the focused telemetry and healthcheck test modules plus scoped `git diff --check` on the touched dispatcher, wrapper, outcome, healthcheck, and test artifacts
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to file-first capture, post-run cost and outcome normalization, bounded telemetry, and local healthcheck ingestion for the two already approved pilot classes. This task must not widen OR eligibility, rewrite the visible operator gate, add other Janus-skill consumers, enable production routing, or treat consumer-runner integration as part of the same slice.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

@janus-preimplementation-check
Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Target Task: TASK-SPEC21.3
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
