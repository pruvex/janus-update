TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/20_separate_dev_or_infrastructure_governance.md
- Task File: documentation/tasks/TASK-SPEC20_separate_dev_or_infrastructure_governance.md
- Target Task: TASK-SPEC20.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Spec 20 plus the generated TASK-SPEC20 artifact; TASK-SPEC20.2 and TASK-SPEC20.3 are later slices only and must not be pulled forward into backlog migration, AGENTS updates, workflow-playbook hardening, or any Janus backlog rewrites in this task
- Files: development/README.md, development/DEV_STATE.md, development/DEV_BACKLOG.md
- Acceptance Criteria: the new `development/` area exists outside `documentation/`; `development/README.md` clearly states the boundary between Janus product work and Dev-OR infrastructure work; `development/DEV_STATE.md` and `development/DEV_BACKLOG.md` exist as canonical starting artifacts; the new Dev area explicitly avoids claiming Janus product, Git, release, or production-routing authority
- Tests: create the three bounded files only under `development/`; run `git diff --check` for the new Dev artifacts; run one focused consistency check that README, DEV_STATE, and DEV_BACKLOG use the same source-of-truth and non-authority rules
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to creating the separate top-level Dev governance home and nothing else. This task must not migrate existing Janus backlog entries, edit `AGENTS.md`, edit `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`, change `documentation/backlog/BACKLOG.md`, or solve any active backend or OR runtime issue. The slice is documentation and governance only, but it is still implementation-eligible because it creates the concrete new Dev source-of-truth artifacts defined by the spec.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

@janus-preimplementation-check
Spec: documentation/SPEC/20_separate_dev_or_infrastructure_governance.md
Task: documentation/tasks/TASK-SPEC20_separate_dev_or_infrastructure_governance.md
Backlog Item: N/A
Target Task: TASK-SPEC20.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
