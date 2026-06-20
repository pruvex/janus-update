TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
- Task File: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
- Target Task: TASK-SPEC21.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 21 plus generated TASK-SPEC21 artifact; the sealed `TASK-SPEC21.1` pilot eligibility/redaction boundary is already fixed and must be reused unchanged, while telemetry, actual-cost capture, healthcheck ingestion, and consumer-runner integration remain deferred to `TASK-SPEC21.3` and `TASK-SPEC21.4`
- Files: documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py, documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py, documentation/codex/skills/janus-debug/SKILL.md, documentation/codex/skills/janus-test-pipeline/SKILL.md, documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py, documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- Acceptance Criteria: both approved pilot classes expose the same visible operator choice style `1 = Codex` and `2 = OR-Arbeitspferd`; the gate is only shown when the current skill is `janus-debug` or `janus-test-pipeline` and the `TASK-SPEC21.1` eligibility gate already returned an allowed pilot class; the gate must include the selected OR model, an estimated OR cost, and a confidence or reliability value before the operator can choose `2`; missing model, cost, or confidence fields suppress the OR gate deterministically and leave the path in Codex-only or reviewable no-gate fallback; the versioned skill instructions for `janus-debug` and `janus-test-pipeline` are aligned to the same bounded operator-gate wording without implying production routing, autonomous OR authority, or broader skill rollout
- Tests: add focused automated coverage for gate prompt generation with visible `1 = Codex` / `2 = OR-Arbeitspferd`, selected model, estimated cost, and confidence fields; add negative coverage for missing estimated cost and missing confidence so the gate is suppressed into a reviewable Codex-only result; add regression coverage that a non-eligible or missing-field case does not present a normal OR choice; run the bounded gate-prompt test module plus any touched eligibility regression module; run `git diff --check` on the touched gate, dispatcher, skill, and test artifacts
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to the user-facing operator gate and its mandatory prompt fields. This task must not add live OR capture, actual-cost reporting after completion, healthcheck ingestion, consumer-runner integration, or any expansion beyond the two already approved pilot classes. It may reuse the existing `TASK-SPEC21.1` eligibility boundary, but it must not reopen or relax that boundary while adding the visible gate.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

@janus-preimplementation-check
Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Target Task: TASK-SPEC21.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
