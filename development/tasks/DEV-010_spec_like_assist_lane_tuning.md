# DEV-010 - Spec-like assist lane tuning from calibration report

- **Parent Item:** DEV-010 - Tune under-estimated spec-like OpenRouter assist lane defaults
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Status:** READY FOR PRECHECK
- **Created:** 2026-07-06
- **Scope Type:** Lean Dev / bounded routing-default tuning slice

## Goal

Apply one tiny evidence-backed follow-up tuning pass for the still under-estimated spec-like OpenRouter assist lanes without widening into execution-path economics, live runs, or skill/governance rewrites.

## Required Outcome

Update the current tri-modal routing manifest only for `spec_generator_review` and `spec_to_task_review`, add focused regression coverage for those tuned defaults, and rerender the calibration report to confirm the new baseline.

## In Scope

- raise the `spec_generator_review` OpenRouter cost default to the bounded report's evidence-backed level
- raise the `spec_to_task_review` OpenRouter cost default to the bounded report's evidence-backed level
- add one focused regression test for those two tuned defaults
- rerender the local calibration report after the changes

## Out Of Scope

- execution-lane default tuning
- `spec_review` tuning
- skill prose rewrites
- live Cursor or OpenRouter calls
- automatic routing activation
- production routing claims
- new backend or lane additions

## Evidence Paths

- `development/openrouter-skill-tests/delegation_routing_calibration_report_2026-07-06.json`
- `development/openrouter-skill-tests/delegation_routing_calibration_report_2026-07-06.md`
- `documentation/codex/model-routing/config/delegation_routing_manifest.json`
- `documentation/codex/model-routing/tests/test_delegation_routing.py`

## Suggested Target Artifacts

- `documentation/codex/model-routing/config/delegation_routing_manifest.json`
- `documentation/codex/model-routing/tests/test_delegation_routing.py`
- `development/openrouter-skill-tests/delegation_routing_calibration_report_2026-07-06.json`
- `development/openrouter-skill-tests/delegation_routing_calibration_report_2026-07-06.md`

## Validation Expectation

- manifest remains valid
- tuned defaults are covered by one focused regression test
- rerendered calibration report reflects the new defaults
- no production routing, live call, or authority change is introduced

HANDOFF_SCOPE:
- Backlog Item: DEV-010
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: `development/tasks/DEV-010_spec_like_assist_lane_tuning.md`
- Required Next Skill: `janus-preimplementation-check`
- Evidence Paths: `development/openrouter-skill-tests/delegation_routing_calibration_report_2026-07-06.json`; `development/openrouter-skill-tests/delegation_routing_calibration_report_2026-07-06.md`; `documentation/codex/model-routing/config/delegation_routing_manifest.json`; `documentation/codex/model-routing/tests/test_delegation_routing.py`
- Dropped Context: broad OR rollout history; execution-lane transport experiments; unrelated product backlog items
