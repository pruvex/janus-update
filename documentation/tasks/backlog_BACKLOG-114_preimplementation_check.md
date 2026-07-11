PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-114
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-114_installierte_janus_skill_arbeitskopien_uebernehmen_spec26_alltagsgates.md
Spec: documentation/SPEC/26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md
Backlog Item: BACKLOG-114
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it rolls the repo-versioned Spec-26 existing-skill operator gates into the installed `C:\Users\pruve\.codex\skills\janus-*` working copies and captures one small real workflow verification.
- Artifact identity is consistent across `BACKLOG-114`, its selected handoff artifact, the implemented Spec-26 chain, and the installed skill-copy rollout target. This slice is not allowed to invent new OR lanes, relax hidden-lane boundaries, or reopen broader OR architecture questions.
- The affected file cluster is concrete and bounded to the five repo-versioned skill sources, the five installed skill working copies, and the small execution-result evidence surface. No Janus product code, provider logic, or production routing artifact is in scope.
- Risk is MEDIUM because the slice touches active installed skill working copies that affect real operator behavior. Skill 4 must keep the work strictly to repo-vs-installed skill alignment plus one bounded workflow check: no product implementation, no routing-table activation, no new lane enablement, and no broad installed-skill rewrite beyond the bound file cluster.
- The implementation may discover that some installed skill copies are already aligned. In that case the slice may limit edits to the missing copies and still complete with an honest live workflow verification, but it must not widen scope just to manufacture more changes.
Affected Files:
- documentation/codex/skills/janus-executioner/SKILL.md
- documentation/codex/skills/janus-debug/SKILL.md
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/skills/janus-quickchange/SKILL.md
- documentation/codex/skills/janus-documentation-update/SKILL.md
- C:\Users\pruve\.codex\skills\janus-executioner\SKILL.md
- C:\Users\pruve\.codex\skills\janus-debug\SKILL.md
- C:\Users\pruve\.codex\skills\janus-test-pipeline\SKILL.md
- C:\Users\pruve\.codex\skills\janus-quickchange\SKILL.md
- C:\Users\pruve\.codex\skills\janus-documentation-update\SKILL.md
- documentation/ai/CURRENT_STATE.md
Evidence Focus:
- one repo-vs-installed diff or parity check for each bound skill copy
- one bounded real workflow verification showing a visible approved lane still offers `1 = Codex` / `2 = OR`
- one bounded real workflow verification showing `generator_review` or `execution_write_apply_candidate` stays local-only and does not appear as a normal everyday OR choice
- git diff --check -- documentation/tasks/backlog_BACKLOG-114_preimplementation_check.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- one repo-vs-installed diff or parity check for each bound skill copy
- one bounded real workflow verification for a visible lane and one hidden lane
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md
- documentation/tasks/backlog_BACKLOG-114_installierte_janus_skill_arbeitskopien_uebernehmen_spec26_alltagsgates.md
- documentation/SPEC/26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md
- documentation/tasks/TASK-SPEC26.3_execution_result.md
- the five repo skill sources and the five installed skill working copies
- the current central lane inventory and operator registry summary
Drop Context:
- older Dev-workhorse rollout history beyond BACKLOG-113 as identity context
- unrelated Janus product backlog items
- broader OR pilot, release, and dashboard planning history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: BACKLOG-114 is now a bounded execution slice: align installed skill copies to the repo-versioned Spec-26 gates and prove one visible lane plus one hidden lane in the real workflow.
User Action: Say `ok` to start implementation of `BACKLOG-114` with the bound scope and evidence gate above.
