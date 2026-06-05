TASK-BACKLOG-101-R2
- Source Spec: `documentation/SPEC/backlog_BACKLOG-101_deepdive_restore_cross_provider_cost_visibility_and_cache_savings.md`
- Backlog Item: `BACKLOG-101`
- Feature: Clean Cost DeepDive And Cost Tracking Debug Log
- Generated At: 2026-06-05

## Generated Tasks

### TASK-BACKLOG-101-R2.1 Reframe the DeepDive backend contract around user-facing cost understanding and compact truthfulness hints
- Ziel:
  - Reshape the DeepDive payload so the primary contract serves user-facing provider, model, budget, and savings understanding first, while exposing only concise warning signals when cost truth is partially limited.
- Scope:
  - Update the existing DeepDive aggregation and API payload shape only as needed to support a cleaner user surface. Keep at least Gemini and GPT/OpenAI, model-level visibility, and savings context available, but stop treating forensic detail as the primary UI contract.
- Files:
  - `backend/data/crud.py`
  - `backend/api/routers/system.py`
  - `backend/tests/test_cost_token_tracking_completeness.py`
- Steps:
  1. Inspect the current `/api/costs/deep-dive` response and identify which fields are currently optimized for forensic drilldown instead of user-facing cost understanding.
  2. Adjust the aggregation contract so the top-level and summary sections prioritize provider totals, model visibility, savings context, and concise warning states for partially attributable costs.
  3. Preserve only the backend data that the cleaned DeepDive surface still needs, and ensure uncertainty is expressed as compact user-relevant truthfulness signals rather than raw forensic framing.
  4. Keep the payload honest when model or savings data is incomplete instead of fabricating values or hiding missing sections.
- Acceptance Criteria:
  - `/api/costs/deep-dive` still exposes at least Gemini and GPT/OpenAI in one coherent cost view.
  - Model-level visibility and savings values remain available where persisted data supports them.
  - Cost truthfulness gaps are represented as concise user-relevant warning signals rather than requiring the UI to render raw forensic detail by default.
  - Existing payload changes remain bounded to the DeepDive contract and do not expand into a separate billing API.
- Tests:
  - `python -m py_compile backend/data/crud.py backend/api/routers/system.py`
  - `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q`
- Model: 5.4
- Reason:
  - Shared aggregation and API contract work with medium cross-system impact, but still standard Janus implementation scope.

### TASK-BACKLOG-101-R2.2 Add a privacy-safe cost-tracking debug log for dev mode without making DeepDive depend on it
- Ziel:
  - Write structured cost-tracking debug events to `documentation/logs/cost-tracking-debug.jsonl` in dev mode so attribution and persistence quality can be analyzed outside the user UI.
- Scope:
  - Touch only existing cost-persistence and provider attribution paths needed to emit the debug log. The log must contain technical metadata only and must not be required for normal DeepDive rendering.
- Files:
  - `backend/services/orchestrator/execution_engine.py`
  - `backend/llm_providers/gemini/gateway.py`
  - `backend/services/cost_service.py`
  - `backend/tests/test_cost_token_tracking_completeness.py`
- Steps:
  1. Identify the existing persistence points where DeepDive-relevant cost attribution and stream-final usage decisions are currently created.
  2. Add structured debug-log emission for those paths in dev mode, including provider, model, component, attribution status, event type, IDs or hashes, and cost values.
  3. Ensure prompt, response, chat history, and other user content never enter the debug log, including nested metadata sanitization.
  4. Ensure debug-log write failures do not turn the DeepDive user experience into a technical error surface.
- Acceptance Criteria:
  - In dev mode, cost-tracking debug events are written to `documentation/logs/cost-tracking-debug.jsonl`.
  - Debug events contain technical attribution and cost metadata sufficient for later analysis.
  - Debug events contain no prompt, response, chat history, or other user-content payloads.
  - DeepDive does not require the debug log to render normal user-facing cost data.
- Tests:
  - `python -m py_compile backend/services/orchestrator/execution_engine.py backend/llm_providers/gemini/gateway.py backend/services/cost_service.py`
  - `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q`
- Model: 5.4
- Reason:
  - Bounded persistence-path work with privacy constraints, but no architecture escalation if kept inside the existing cost-attribution flow.

### TASK-BACKLOG-101-R2.3 Simplify the DeepDive modal into a user-first cost surface and remove forensic framing from the primary experience
- Ziel:
  - Rebuild the current DeepDive presentation so users primarily see cost understanding and optimization signals rather than developer-oriented forensic analysis.
- Scope:
  - Modify only the existing DeepDive modal and its current supporting styles and render flow. No new dashboard, no separate developer panel, and no installer-specific logging UI.
- Files:
  - `frontend/js/cost-visualizer.js`
  - `frontend/src/styles.css`
  - `frontend/index.html`
- Steps:
  1. Rework the DeepDive heading, summary, and information hierarchy so provider totals, model breakdown, budget context, and savings are the primary first-view content.
  2. Remove or demote forensic-first wording, raw anomaly emphasis, and developer-oriented detail blocks from the default user experience.
  3. Keep only concise warning text when attribution or cost completeness is limited, without surfacing raw internal tracking diagnostics.
  4. Preserve honest empty or partial-data states so the cleaned surface remains truthful.
- Acceptance Criteria:
  - The first DeepDive view reads as a user-facing cost understanding and optimization surface.
  - Gemini and GPT/OpenAI remain visible in one coherent view together with model and savings context where supported.
  - DeepDive no longer presents developer-oriented forensic framing as its primary content.
  - If attribution or savings data is partial, the UI shows a concise user-relevant hint instead of raw diagnostic detail.
- Tests:
  - `node --check frontend/js/cost-visualizer.js`
  - `npx playwright test tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js --headed --workers=1 --reporter=list`
- Model: 5.4
- Reason:
  - Frontend hierarchy and render-state work stays bounded to one existing modal but meaningfully changes what users see first.

### TASK-BACKLOG-101-R2.4 Add focused regression coverage for the user-facing DeepDive contract and the dev-only debug-log boundary
- Ziel:
  - Lock in the new separation so future changes do not reintroduce forensic clutter into DeepDive or leak user content into the debug log.
- Scope:
  - Extend the smallest existing backend and UI smoke coverage that already fits the DeepDive surface and cost-tracking contract.
- Files:
  - `backend/tests/test_cost_token_tracking_completeness.py`
  - `tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js`
- Steps:
  1. Add backend assertions for user-facing provider/model/savings visibility, concise warning behavior, and privacy-safe debug-log contents.
  2. Update the existing DeepDive UI smoke test so it verifies the cleaned user-first presentation and fails if forensic-first wording or layout returns as the primary experience.
  3. Keep the coverage narrow and tied to the new user/developer separation, not a broad dashboard rewrite.
- Acceptance Criteria:
  - A backend regression test fails if debug-log events leak prompt, response, chat history, or other user content.
  - A backend regression test fails if the DeepDive contract loses user-facing provider, model, or savings visibility promised by the Spec.
  - A UI smoke test fails if the DeepDive primary experience regresses back to forensic-first framing.
- Tests:
  - `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q`
  - `npx playwright test tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js --headed --workers=1 --reporter=list`
- Model: 5.4
- Reason:
  - Focused regression guard task using existing test surfaces, still normal 5.4 execution work.
