PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC21.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Spec: documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Assigned Model: 5.4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it adds the first visible operator gate for the already approved Spec-21 pilot classes and requires the shared prompt to show `1 = Codex` and `2 = OR-Arbeitspferd` together with selected model, estimated cost, and confidence before any OR choice can be taken.
- Artifact identity is consistent across Spec 21, the generated TASK-SPEC21 artifact, the released handoff `documentation/tasks/TASK-SPEC21.2_task_breakdown.md`, and target task `TASK-SPEC21.2`.
- The affected file cluster is concrete and bounded to the shared gate-prompt helper, the dispatcher seam that must suppress missing-field OR gates into Codex-only outcomes, the versioned `janus-debug` and `janus-test-pipeline` skill instructions, and the focused gate-prompt plus eligibility regression tests.
- Implementation risk is MEDIUM because the visible gate sits directly on the boundary between safe operator UX and accidental scope drift. Skill 4 must reuse the sealed `TASK-SPEC21.1` pilot eligibility gate unchanged, must not widen rollout beyond `debug_hypothesis_review` and `test_result_triage_review`, and must not pull forward telemetry, actual-cost capture, healthcheck ingestion, or consumer-runner integration from later slices. A git checkpoint is recommended through `janus-git-governance` before Skill 4 if the broader worktree remains mixed.
- This slice establishes only the visible pre-run choice and mandatory prompt data. Post-run actual-cost display belongs to `TASK-SPEC21.3`, and everyday runner integration belongs to `TASK-SPEC21.4`.
Affected Files:
- documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/skills/janus-debug/SKILL.md
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility
- git diff --check -- documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/skills/janus-debug/SKILL.md documentation/codex/skills/janus-test-pipeline/SKILL.md documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- one focused negative-path check that missing estimated cost or missing confidence suppresses the OR gate into a reviewable Codex-only result
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/21_assisted_or_workhorse_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
- documentation/tasks/TASK-SPEC21.2_task_breakdown.md
- the exact bounded gate-prompt, dispatcher, skill, and test file cluster listed above
Drop Context:
- sealed eligibility/redaction implementation details beyond the reused pilot boundary from `TASK-SPEC21.1`
- later telemetry and healthcheck slice `TASK-SPEC21.3`
- later consumer integration slice `TASK-SPEC21.4`
- unrelated quickchange, direct OR, or sidecar write history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The visible operator-gate slice is implementation-ready, tightly bounded to prompt fields, gate suppression behavior, and skill wording, and it intentionally defers telemetry plus consumer-runner integration to later Spec-21 tasks.
User Action: Say `ok` to start implementation of `TASK-SPEC21.2` with the bound scope and evidence gate above.
