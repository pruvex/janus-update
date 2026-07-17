# TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5 Test Oracle Precheck

PRE-CHECK RESULT
PRE-CHECK PASSED

## Binding

- Source Task: `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5`
- Debug Evidence: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_debug_result_stale_deep_dive_smokes.md`
- Target: One stale localization assertion in `tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js`
- Risk: LOW
- Product Logic: unchanged
- Persistence/API/Provider/Auth/Security/Privacy: unchanged

## Evidence

- The current renderer exposes the metric label `Ersparnis` in `frontend/js/cost-visualizer.js`.
- The remaining assertion expects the obsolete English label `Savings`.
- Git blame binds the stale assertion to `d649e7587f` from 2026-06-04, before the localized current UI.
- The same headed retest already proved:
  - BACKLOG-103: PASS
  - OpenRouter DeepDive: PASS
  - BACKLOG-101 interaction reaches `Recherche-Anteil`; only `Savings` remains red.

## Execution Handoff

Pre-Check: PRE-CHECK PASSED

Pre-Check Context:
- Replace exactly one stale string assertion, `Savings` -> `Ersparnis`.
- Preserve the already added privacy-modal setup and staged source/request interaction.
- Do not touch product code or any other test.

Affected Files:
- tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js

Scope-Regel:
- One assertion-only correction. Stop if any product, fixture, payload, or second file must change.

Automated Evidence Gate:
- node --check tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js
- npx playwright test <runner> --headed --workers=1 --reporter=list
- Exact runner: `tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js`
- After focused PASS, rerun the bound three-file DeepDive gate.

Artifact Identity Check:
- Execute the repository file named above and verify the failure line now asserts the current renderer label.

Oracle-/TestPlan-Regel:
- This focused smoke has no generated TestSpec/TestRun bundle according to its final-audit record. Change only the stale assertion; do not alter payload or results.

## NEXT STEP

- Recommended Skill: janus-executioner
- Recommended Model: 5.6 Terra
- Recommended Intelligence: low
- User Action: None; execute the bound assertion correction and retest.
