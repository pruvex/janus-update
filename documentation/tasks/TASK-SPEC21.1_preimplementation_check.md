PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC21.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Assigned Model: 5.4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it narrows the shared bounded OR eligibility layer to the first approved pilot classes only and adds a locally testable request redaction/allowlist gate before any OR request can be emitted.
- Artifact identity is consistent across Spec 21, the generated TASK-SPEC21 artifact, the released handoff `documentation/tasks/TASK-SPEC21.1_task_breakdown.md`, and target task `TASK-SPEC21.1`.
- The affected file cluster is concrete and bounded to the shared eligibility helper, dispatcher entry gate, request builder seam, one existing eligibility config file, and the existing bounded eligibility test module.
- Implementation risk is MEDIUM because the current shared eligibility configuration is broader than the new Spec 21 pilot scope. Skill 4 must actively narrow the rollout to `debug_hypothesis_review` and `test_result_triage_review` and must not inherit wider historical task classes just because they already exist in infrastructure. A git checkpoint is recommended through `janus-git-governance` before Skill 4 if the broader worktree remains mixed.
- This first slice only establishes the enforceable pre-request boundary. User-facing cost/confidence display, OR telemetry capture, actual-cost reporting, and weekly-healthcheck optimization summaries belong to later slices and must not be pulled forward here.
Affected Files:
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py
- documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility
- git diff --check -- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- one focused negative-path check that a request package with forbidden or unredacted fields is rejected before dispatch
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC21.1_task_breakdown.md
- the exact bounded eligibility/config/request-builder/test file cluster listed above
Drop Context:
- later gate-display slice `TASK-SPEC21.2`
- later telemetry and healthcheck slice `TASK-SPEC21.3`
- later consumer integration slice `TASK-SPEC21.4`
- older quickchange, execution, and documentation-skill OR history outside the new pilot boundary
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The first slice is implementation-ready, tightly bounded to eligibility, allowlist, and redaction narrowing, and gives Skill 4 a concrete test gate without pulling forward UI gate, telemetry, or broader consumer work.
User Action: Say `ok` to start implementation of `TASK-SPEC21.1` with the bound scope and evidence gate above.
