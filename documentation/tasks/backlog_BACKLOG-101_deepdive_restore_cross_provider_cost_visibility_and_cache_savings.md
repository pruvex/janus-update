TASK-BACKLOG-101
- Source Spec: `documentation/SPEC/backlog_BACKLOG-101_deepdive_restore_cross_provider_cost_visibility_and_cache_savings.md`
- Backlog Item: `BACKLOG-101`
- Feature: DeepDive Restore Cross-Provider Cost Visibility And Cache Savings
- Generated At: 2026-06-04

## Generated Tasks

### TASK-BACKLOG-101.1 Restore cross-provider DeepDive aggregation for GPT/OpenAI, model-level visibility, and cache/savings data
- Ziel:
  - Re-establish the backend/API data contract so DeepDive can show GPT/OpenAI alongside Gemini, grouped by provider and model, including available cache/savings values.
- Scope:
  - Extend or reconnect the existing cost aggregation/read paths so the DeepDive payload exposes the previously expected cross-provider totals, model splits, and cache/savings fields without dropping Spec-14 Gemini attribution details.
- Files:
  - `backend/data/crud.py`
  - `backend/api/routers/system.py`
  - `backend/services/cost_service.py`
  - `backend/tests/test_cost_token_tracking_completeness.py`
  - `backend/services/chat_orchestrator.py` (only if existing cache/savings context must be re-read from current persisted usage patterns)
- Steps:
  1. Inspect the current `/api/costs/deep-dive` payload in `crud.get_monthly_gemini_cost_deep_dive()` and identify which formerly visible GPT/OpenAI, model, and cache/savings fields are no longer surfaced.
  2. Extend the aggregation layer so the DeepDive response is no longer Gemini-only by provider scope and instead exposes provider-level and model-level groupings for at least Gemini and GPT/OpenAI.
  3. Re-surface cache/savings values using the existing token/cost persistence fields and explicitly mark unsupported sections instead of fabricating savings values.
  4. Preserve Spec-14 Gemini forensics fields such as attribution status, component split, residuals, anomaly flags, and request drilldown in the same payload shape.
- Acceptance Criteria:
  - `/api/costs/deep-dive` returns cross-provider visibility for at least Gemini and GPT/OpenAI instead of a Gemini-only provider scope.
  - Model-level cost visibility is available in the response wherever persisted model data exists.
  - Cache/savings values are present where existing persisted token/cost data supports them and explicitly absent where not supported.
  - Existing Gemini attribution/anomaly fields remain available and are not flattened away.
- Tests:
  - `python -m py_compile backend/data/crud.py backend/api/routers/system.py backend/services/cost_service.py`
  - `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q`
- Model: 5.4
- Reason:
  - Shared aggregation/API contract change with medium-high cross-system impact, but still standard Janus implementation work.

### TASK-BACKLOG-101.2 Rebuild the DeepDive modal so cross-provider totals, per-model breakdowns, cache savings, and Gemini forensics coexist cleanly
- Ziel:
  - Update the existing DeepDive UI so the restored GPT/OpenAI, model, and cache/savings views appear together with the Spec-14 Gemini forensic drilldown.
- Scope:
  - Modify the current DeepDive modal only; no new dashboard or parallel billing surface.
- Files:
  - `frontend/js/cost-visualizer.js`
  - `frontend/index.html`
  - `frontend/src/styles.css`
- Steps:
  1. Update the DeepDive layout/state so users can see cross-provider totals and model breakdowns without losing anomaly-first Gemini drilldown.
  2. Reintroduce cache/savings visibility in a form that is understandable alongside gross/net/provider/model numbers.
  3. Ensure unavailable data is shown honestly rather than hidden or implied.
  4. Keep the existing `#cost-summary-widget` entry point and Spec-14 Gemini residual/anomaly surfaces intact.
- Acceptance Criteria:
  - The DeepDive modal visibly includes Gemini and GPT/OpenAI in one coherent cost view.
  - Per-model visibility is shown where available.
  - Cache/savings information is visible again where supported.
  - Gemini anomaly/residual/request-detail drilldown remains usable.
- Tests:
  - `node --check frontend/js/cost-visualizer.js`
  - `npx playwright test <runner> --headed --workers=1 --reporter=list`
- Model: 5.4
- Reason:
  - Existing frontend surface update with meaningful state/render changes, but bounded to one modal and its supporting styles.

### TASK-BACKLOG-101.3 Add focused regression coverage for the restored cross-provider DeepDive contract
- Ziel:
  - Lock in the restored behavior so future DeepDive changes do not silently drop GPT/OpenAI, model, or cache/savings visibility again.
- Scope:
  - Add or extend the smallest focused test coverage needed across backend and frontend DeepDive contract surfaces.
- Files:
  - `backend/tests/test_cost_token_tracking_completeness.py`
  - `frontend/tests/*` (exact runner or spec to be confirmed during task breakdown)
  - `tests/e2e/*` (only if a minimal DeepDive smoke path is the established local pattern)
- Steps:
  1. Add assertions for cross-provider presence, model-level visibility, and cache/savings fields in the backend DeepDive contract tests.
  2. Add focused UI coverage for the restored DeepDive display if an existing frontend or Playwright path already fits.
  3. Keep the tests narrow and tied to the actual regression, not a broad dashboard rewrite.
- Acceptance Criteria:
  - A regression test fails if GPT/OpenAI disappears again from DeepDive.
  - A regression test fails if model-level visibility or cache/savings display disappears where expected.
  - Existing Gemini forensics checks remain green.
- Tests:
  - `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q`
  - `npx playwright test <runner> --headed --workers=1 --reporter=list`
- Model: 5.4
- Reason:
  - Focused regression guard task after behavior is restored; still normal 5.4 work.
