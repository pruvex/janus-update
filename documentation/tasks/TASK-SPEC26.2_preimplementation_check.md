PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC26.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md
Spec: documentation/SPEC/26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it wires the already approved existing skill entries to the shared fail-closed visibility contract from `TASK-SPEC26.1`, so visible delegated choice appears automatically only where a released bounded lane already exists.
- Artifact identity is consistent across reviewed Spec 26, the generated `TASK-SPEC26` artifact, the new `TASK-SPEC26.2` task-breakdown handoff, and released target task `TASK-SPEC26.2`. No dashboard expansion, no global routing change, and no later cross-skill regression fence is the source of truth for this execution block.
- The affected file cluster is concrete and bounded to the repo-versioned skill entry texts plus the directly corresponding runner entrypoints for `janus-executioner`, `janus-debug`, `janus-test-pipeline`, `janus-quickchange`, and the fixed documentation path.
- Risk is HIGH because this slice changes several existing skill entry surfaces at once. Skill 4 must keep the work strictly on already approved bounded lanes only: no new lane creation, no visibility for experimental or partial candidates, no production-routing activation, no canonical routing-table update, and no delegated authority expansion.
- This slice is integration-only. It may connect existing skill entrances to the shared visibility contract and align their visible operator wording, but it must not yet add the later cross-skill registry-sync fence from `TASK-SPEC26.3`.
Affected Files:
- documentation/codex/skills/janus-executioner/SKILL.md
- documentation/codex/skills/janus-debug/SKILL.md
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/skills/janus-quickchange/SKILL.md
- documentation/codex/skills/janus-documentation-update/SKILL.md
- documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
- documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
- documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
- documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py
- documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
- documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py
- documentation/codex/model-routing/tests/test_quickchange_write_apply_runner.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner
- python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration
- python -m unittest documentation.codex.model-routing.tests.test_quickchange_write_apply_runner
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt
- python -m py_compile documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
- git diff --check -- documentation/codex/skills/janus-executioner/SKILL.md documentation/codex/skills/janus-debug/SKILL.md documentation/codex/skills/janus-test-pipeline/SKILL.md documentation/codex/skills/janus-quickchange/SKILL.md documentation/codex/skills/janus-documentation-update/SKILL.md documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py documentation/codex/model-routing/tests/test_quickchange_write_apply_runner.py documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py documentation/tasks/TASK-SPEC26.2_preimplementation_check.md
- one focused negative-path check that a hidden or partial lane such as execution_write_apply_candidate does not emit a normal visible delegated choice through an existing skill entry
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m unittest documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner
- python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_consumer_integration
- python -m unittest documentation.codex.model-routing.tests.test_quickchange_write_apply_runner
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound task/spec identity for Spec 26 and TASK-SPEC26.2
- the shared visibility-contract result from TASK-SPEC26.1
- affected skill entry files, runner entrypoints, and focused tests
- evidence commands listed above
Drop Context:
- old failed drafts
- unrelated backlog or audit history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The existing-skill integration slice is implementation-ready, tightly bounded to already approved skill-entry gates and their directly corresponding runners, while the later cross-skill regression fence remains explicitly deferred.
User Action: Say `ok` to start implementation of `TASK-SPEC26.2` with the bound scope and evidence gate above.
