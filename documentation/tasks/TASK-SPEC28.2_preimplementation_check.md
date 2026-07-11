PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC28.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
Spec: documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
Backlog Item: BACKLOG-118
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it defines the bounded local live-retest worker/auth/evidence contract that comes after the already-audited visible `LIVE_TEST_EXECUTION` gate in TASK-SPEC28.1.
- Artifact identity is consistent across BACKLOG-118, approved Spec 28, generated TASK-SPEC28, completed TASK-SPEC28.1, and the released target-task handoff `documentation/tasks/TASK-SPEC28.2_task_breakdown.md`.
- The implementation surface is bounded to repo-owned OR/test-pipeline infrastructure: the `janus-test-pipeline` skill text, the live-test sidecar runner, the isolated worker runner integration surface, the bounded delegation dispatcher touchpoint if needed, focused runner tests, and a fixture/package contract under `documentation/codex/model-routing/strong-or-fixtures/` or an adjacent scoped fixture path.
- Risk is HIGH because this slice touches local auth/header boundaries and the first practical worker/evidence contract for real OR live-retest work. Skill 4 must preserve the hard boundary: no versioned secrets, no broad shell authority, no generic live-test delegation, no real live retest run as part of this slice, no final PASS/release/Git/routing authority for OR, and no TASK-SPEC28.3 accept/reject registry hardening.
- The expected implementation result is a reviewable package/contract shape and deterministic fixture validation, not a production live-run acceptance decision.
Affected Files:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/strong-or-fixtures/
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
- documentation/tasks/TASK-SPEC28.2_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Evidence Focus:
- Validate that a bounded local live-retest worker contract exists for only allowed local health, chat creation, bound prompt execution, and evidence collection steps.
- Validate that local auth/header support is represented as a bounded runtime/local-context requirement and never serialized as real secret values in versioned fixtures, packages, prompts, summaries, or evidence.
- Validate that returned worker artifacts are reviewable by Codex and do not claim final PASS, release, Git, routing, or task-completion authority.
- Validate that the worker package cannot be reused as broad shell delegation or generic live-test delegation.
- Preserve the TASK-SPEC28.1 gate behavior: eligible `local_bounded_retest` may expose `2 = OR`, while non-eligible scopes remain Codex-only.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q
- python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q -k "live"
- python -m py_compile documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- fixture/package validation command for the bounded local live-retest package, including secret-redaction and allowlist checks
- git diff --check -- documentation/codex/skills/janus-test-pipeline/SKILL.md documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/strong-or-fixtures/ documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py documentation/tasks/TASK-SPEC28.2_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28.2_task_breakdown.md
- documentation/tasks/TASK-SPEC28.1_final_audit.md
- documentation/tasks/TASK-SPEC28.1_documentation_update.md
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
Drop Context:
- TASK-SPEC28.1 implementation chatter beyond final audit and documentation closeout
- later TASK-SPEC28.3 accept/reject and registry-regression work
- unrelated OR pilots, broad worker experiments, product-runtime bugs, release work, and dirty worktree debris
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, bounded worker/auth/evidence contract artifacts, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: `TASK-SPEC28.2` is implementation-ready as a bounded worker/auth/evidence contract slice after the visible gate passed final audit; the scope is high-risk but concrete and evidence-gated.
User Action: Continue with `janus-executioner` for `TASK-SPEC28.2` in this chat.
