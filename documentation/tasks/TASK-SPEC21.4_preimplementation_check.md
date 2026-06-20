PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC21.4
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it wires the already sealed shared OR foundation into exactly two approved everyday consumer paths, `janus-debug/debug_hypothesis_review` and `janus-test-pipeline/test_result_triage_review`, without widening pilot scope or changing the sealed foundation layers.
- Artifact identity is consistent across Spec 21, the generated TASK-SPEC21 artifact, the released handoff `documentation/tasks/TASK-SPEC21.4_task_breakdown.md`, and target task `TASK-SPEC21.4`.
- The affected file cluster is concrete and bounded to the two approved consumer runners, their shared dispatcher seam, the versioned `janus-debug` and `janus-test-pipeline` skill instructions, and focused consumer integration regression tests.
- Implementation risk is HIGH because this slice reaches the first real bounded everyday consumer integration seam. Skill 4 must reuse the sealed `TASK-SPEC21.1` eligibility boundary, the sealed `TASK-SPEC21.2` visible cost and confidence gate, and the sealed `TASK-SPEC21.3` file-first capture plus truthful telemetry finalization unchanged. It must not widen rollout beyond `debug_hypothesis_review` and `test_result_triage_review`, and it must not imply production routing, canonical routing-table changes, or autonomous OR repo-write authority. A git checkpoint is recommended through `janus-git-governance` before Skill 4 if the broader worktree remains mixed.
- This slice establishes only bounded consumer wiring, local fallback semantics, and Codex-owned final outcome behavior inside the two approved pilot consumers. Any broader skill rollout remains out of scope.
Affected Files:
- documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
- documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/skills/janus-debug/SKILL.md
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/tests/
Evidence Focus:
- focused positive automated coverage for `debug_hypothesis_review` using the visible bounded gate plus Codex-owned final outcome
- focused positive automated coverage for `test_result_triage_review` using the visible bounded gate plus Codex-owned final outcome
- focused negative coverage that non-approved debug or test-pipeline modes stay Codex-only before any OR runner path starts
- focused regression coverage that sealed eligibility, visible gate, file-first capture, truthful telemetry finalization, and local healthcheck ingestion remain unchanged for the two pilot classes
- python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation/tasks/TASK-SPEC21.4_preimplementation_check.md
- git diff --check -- documentation/tasks/TASK-SPEC21.4_preimplementation_check.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- focused consumer integration, eligibility, gate, and telemetry regression test modules for the touched runner, dispatcher, skill-doc, and test file cluster
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC21.4_task_breakdown.md
- the exact bounded runner, dispatcher, skill-doc, and test file cluster listed above
Drop Context:
- sealed implementation details from `TASK-SPEC21.1`, `TASK-SPEC21.2`, and `TASK-SPEC21.3` beyond the reused foundation boundaries
- unrelated quickchange, sidecar write, direct OR, or documentation-skill OR rollout history
- any broader all-skill OR rollout ideas outside the two approved pilot consumers
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The final Spec-21 slice is implementation-ready, tightly scoped to consumer integration for exactly two approved pilot paths while reusing the sealed eligibility, gate, capture, telemetry, and healthcheck foundations unchanged.
User Action: Say `ok` to start implementation of `TASK-SPEC21.4` with the bound scope and evidence gate above.
