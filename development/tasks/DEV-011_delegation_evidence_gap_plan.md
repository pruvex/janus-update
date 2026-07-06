# DEV-011 - Delegation evidence gap plan

- **Parent Item:** DEV-011 - Add a bounded evidence-gap plan for remaining delegation lanes
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Status:** READY FOR PRECHECK
- **Created:** 2026-07-06
- **Scope Type:** Lean Dev / bounded routing-evidence planning slice

## Goal

Create one deterministic local review surface that turns the existing delegation routing calibration report into a prioritized next-evidence plan for remaining `NO_EVIDENCE` and high-variance lanes.

## Required Outcome

Add a local helper and focused tests that rank remaining delegation evidence gaps without calling Cursor, OpenRouter, or changing routing defaults automatically.

## In Scope

- read the existing local calibration report
- combine it with the current manifest and task list
- produce `delegation_evidence_gap_plan_2026-07-06.json`
- produce `delegation_evidence_gap_plan_2026-07-06.md`
- prioritize Cursor `NO_EVIDENCE` worker lanes before lower-value review gaps
- keep `live_test_execution` and `diamond_retest_audit` Codex-owned
- preserve explicit language that live Cursor/OpenRouter calls require fresh approval

## Out Of Scope

- live Cursor calls
- live OpenRouter calls
- manifest default tuning
- production routing activation
- skill prose rewrites
- execution-lane authority changes
- Git commit or push

## Evidence Paths

- `development/openrouter-skill-tests/delegation_routing_calibration_report_2026-07-06.json`
- `development/openrouter-skill-tests/delegation_routing_calibration_report_2026-07-06.md`
- `documentation/codex/model-routing/config/delegation_routing_manifest.json`
- `documentation/codex/model-routing/config/delegation_task_list_2026-07-05.json`

## Suggested Target Artifacts

- `documentation/codex/model-routing/scripts/delegation_evidence_gap_plan.py`
- `documentation/codex/model-routing/tests/test_delegation_evidence_gap_plan.py`
- `development/openrouter-skill-tests/delegation_evidence_gap_plan_2026-07-06.json`
- `development/openrouter-skill-tests/delegation_evidence_gap_plan_2026-07-06.md`
- `development/DEV_BACKLOG.md`
- `development/DEV_STATE.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Validation Expectation

- focused pytest passes
- the helper renders the plan from the current calibration report
- the rendered plan contains no live-call authorization
- no manifest, production routing, live-run, or backend-authority change is introduced

HANDOFF_SCOPE:
- Backlog Item: DEV-011
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: `development/tasks/DEV-011_delegation_evidence_gap_plan.md`
- Required Next Skill: `janus-preimplementation-check`
- Evidence Paths: `development/openrouter-skill-tests/delegation_routing_calibration_report_2026-07-06.json`; `documentation/codex/model-routing/config/delegation_routing_manifest.json`; `documentation/codex/model-routing/config/delegation_task_list_2026-07-05.json`
- Dropped Context: broad OR rollout history; old transport mismatch experiments; unrelated Janus product backlog items
