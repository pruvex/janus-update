PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC26.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md
Spec: documentation/SPEC/26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it establishes one shared fail-closed visibility contract that decides whether existing Janus skills may show the visible `1 = Codex / 2 = OR` gate at all.
- Artifact identity is consistent across reviewed Spec 26, the generated `TASK-SPEC26` artifact, and released target task `TASK-SPEC26.1`. No product-facing dashboard idea, no later skill-entry integration slice, and no later cross-skill regression slice is the source of truth for this execution block.
- The affected file cluster is concrete and bounded to the shared OR eligibility config, the shared visibility and gate prompt helpers, and the focused eligibility/gate regression tests.
- Risk is HIGH because this slice defines the shared visibility boundary for several existing skills at once. Skill 4 must keep the work strictly on the shared contract layer only: no skill-SKILL.md rewiring, no runner entry integration, no runtime execution changes, no production-routing activation, and no exposure of experimental or partial OR candidates.
- This slice is contract-only for visibility. It may decide which already approved bounded OR-Lanes can surface the normal operator gate, but it must not yet wire that gate into the individual existing skill entries and must not yet add the later cross-skill registry-sync fence from `TASK-SPEC26.3`.
Affected Files:
- documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt
- python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py
- git diff --check -- documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py documentation/tasks/TASK-SPEC26.1_preimplementation_check.md
- one focused negative-path check that experimental, partial, or unhealthy OR candidates do not surface the normal operator gate
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_gate_prompt
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md
- documentation/tasks/TASK-SPEC26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md
- documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py
Drop Context:
- later `TASK-SPEC26.2` skill-entry rewiring across existing skills
- later `TASK-SPEC26.3` cross-skill regression and registry-sync fence work
- unrelated historical OR pilot, sidecar, direct-execution, or dashboard planning history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The first Spec-26 slice is implementation-ready and tightly scoped to the shared fail-closed visibility contract, shared gate prompt behavior, and focused regression coverage only.
User Action: Say `ok` to start implementation of `TASK-SPEC26.1` with the bound scope and evidence gate above.
