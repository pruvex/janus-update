# DEBUG RESULT - TASK-CHATGPT-DEVICE-CODE-PROVIDER.3

SKILL 5 DEBUG RESULT: FIXED

Iteration: 5

Progress-Validierung: Failure Code `MANUAL_PROVIDER_SELECTION_EMPTY`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN.

Root Cause:
Two coupled causes produced the empty provider selection seen in the passive manual check. The Task `.3` E2E runner did not isolate `GET`/`PUT /api/last-used-model`, so a mocked ChatGPT selection could be persisted into the operator's local Janus configuration. During a later real startup, `loadModelCatalog()` correctly removed unavailable ChatGPT eligibility, but `loadLastUsedModel()` then blindly restored the stale persisted `chatgpt` provider after catalog loading, leaving the native select with a value for which no option existed.

Fix Summary:
- added an exact in-memory E2E mock for both `GET` and `PUT /api/last-used-model`, preventing any local configuration mutation
- made startup reject only a persisted ChatGPT provider/model pair that is absent from the current verified catalog
- selected an existing non-ChatGPT provider/model fallback instead of leaving the provider select empty
- added a headed regression scenario for stale persisted ChatGPT state under unavailable verification
- retained the prior disjoint route ownership, local-model mock, app-readiness marker, and empty unavailable catalog oracle

Auto-Verification:
- Status: PASS
- Evidence: JavaScript syntax checks PASS; focused stale-start scenario `1 passed`; focused verified/unavailable scenario `1 passed`; backend/hierarchy suite `17 passed`; complete headed E2E spec `10 passed (3.5m)`.

Post-Fix Manual Recheck:
- Status: PASS
- Evidence: After a full Janus restart, the operator confirmed visible providers, masked OpenAI/Gemini keys, safe ChatGPT unavailability, no alternative credential storage, and disabled sign-in without any account action.

Artifact Identity Check: PASS — the executed Task `.3` E2E spec now covers verified availability, exact model visibility, verification loss, fail-closed removal, local last-used-model isolation, and stale-start self-healing.

Final Feature Suite: PASS — `npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --project=janus-chromium --workers=1 --reporter=line` returned exit code 0 with 10 passed.

Changed Files:
- `frontend/js/app.js`
- `tests/e2e/codex-connection-settings.spec.js`
- `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_debug_result_model_catalog_mock.md`
- `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_execution_result.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## NEXT_STEP

Target Skill: janus-executioner

Canonical State: HANDOFF

Required Artifacts:
- this debug result
- `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_execution_result.md`
- `frontend/js/app.js`
- `tests/e2e/codex-connection-settings.spec.js`

Evidence Paths:
- focused stale-start Playwright result: `1 passed`
- focused verified/unavailable Playwright result: `1 passed`
- complete headed Playwright result: `10 passed (3.5m)`
- backend/hierarchy pytest result: `17 passed`

Failure Code: `NONE`

Changed Files: as listed above.

Decision: accept the empty-provider startup defect and local E2E configuration contamination as fixed; require one fresh passive Janus restart check before audit packaging.

Reason: the manual symptom now has a deterministic startup-order root cause, both correction boundaries are covered by automated evidence, and no account or credential action is needed.

Recommended Model: 5.6 Terra

Recommended Intelligence: high

Next User Action: proceed with the compact package-only independent final audit.
