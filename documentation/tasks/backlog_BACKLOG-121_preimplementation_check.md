PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: BACKLOG-121
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
Spec: N/A WITH REASON - Lean-Dev routing-hardening slice on existing shared delegation infrastructure; no separate product Spec governs this bounded policy repair.
Backlog Item: BACKLOG-121
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: repair the shared delegation visibility policy for bounded external options so technically eligible Cursor alternatives can remain visible for capacity reasons even when pure Codex-token ROI is slightly negative.
- Scope is restricted to the existing shared routing infrastructure around `execution_patch_candidate`, especially manifest policy, `delegation_routing.py`, `janus_delegate.py`, the operator-facing task-list wording, and the focused regression tests that currently enforce the old hide-on-negative-ROI behavior.
- The slice must stay fail-closed. It may refine recommendation-versus-visibility logic, but it must not open unvalidated lanes, remove lane-specific eligibility checks, change accepted-source apply behavior, or broaden into new delegation architecture.
- Risk is MEDIUM because the change affects operator-facing gating semantics across shared bounded lanes, but it remains a Lean-Dev governance slice with a concrete file cluster and no Janus product feature logic.
Affected Files:
- documentation/codex/model-routing/config/delegation_routing_manifest.json
- documentation/codex/model-routing/scripts/delegation_routing.py
- documentation/codex/model-routing/scripts/janus_delegate.py
- documentation/codex/model-routing/tests/test_delegation_routing.py
- documentation/codex/model-routing/tests/test_janus_delegate.py
- documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md
- documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
- documentation/tasks/backlog_BACKLOG-121_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests/test_delegation_routing.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_delegate.py -q
- python -m py_compile documentation/codex/model-routing/scripts/delegation_routing.py documentation/codex/model-routing/scripts/janus_delegate.py
- git diff --check -- documentation/codex/model-routing/config/delegation_routing_manifest.json documentation/codex/model-routing/scripts/delegation_routing.py documentation/codex/model-routing/scripts/janus_delegate.py documentation/codex/model-routing/tests/test_delegation_routing.py documentation/codex/model-routing/tests/test_janus_delegate.py documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md documentation/tasks/backlog_BACKLOG-121_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not create new delegation backends, do not remove OpenRouter or Cursor choices globally, do not change deterministic apply semantics for `TASK-EX-002`, and do not widen into dashboard quota polling, billing telemetry services, or general release/governance work.
- Cursor-first should be checked again at execution time for this bounded write-capable slice when the shared execution gate exposes a sensible lane; Codex remains owner of review, validation, and final state.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_delegation_routing.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_delegate.py -q
- python -m py_compile documentation/codex/model-routing/scripts/delegation_routing.py documentation/codex/model-routing/scripts/janus_delegate.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md
- documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
- documentation/tasks/backlog_BACKLOG-121_preimplementation_check.md
- documentation/codex/model-routing/config/delegation_routing_manifest.json
- documentation/codex/model-routing/scripts/delegation_routing.py
- documentation/codex/model-routing/scripts/janus_delegate.py
- documentation/codex/model-routing/tests/test_delegation_routing.py
- documentation/codex/model-routing/tests/test_janus_delegate.py
- documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md
- the real gate evidence `WF-EXEC-SPEC29-1-2026-07-09-002`
Drop Context:
- Spec-29 routine-learning implementation details beyond the one execution-gate repro
- old OR/Cursor rollout history that does not affect the current visibility-policy repair
- unrelated backlog items, final audits, release work, and provider/product debugging
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: BACKLOG-121 is now a bounded Lean-Dev routing-hardening slice with explicit files, regression tests, and a clear fail-closed scope.
User Action: Continue with janus-executioner for `BACKLOG-121`, and probe the shared execution gate for a sensible Cursor-first write-capable lane before local implementation.
