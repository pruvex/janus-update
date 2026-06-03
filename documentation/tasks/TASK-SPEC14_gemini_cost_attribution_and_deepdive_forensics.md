# TASK FILE - TASK-SPEC14

TASK-SPEC14
- Source Spec: documentation/SPEC/14_gemini_cost_attribution_and_deepdive_forensics.md
- Backlog Item: N/A
- Feature: Gemini Cost Attribution and DeepDive Forensics
- Generated At: 2026-06-02

## Generated Tasks

### TASK-SPEC14.1 Extend Gemini cost evidence schema and persistence contract
- Ziel:
  Persist a provider-neutral attribution record for every external Gemini call so DeepDive can group by month, session/test run, and request without storing full prompts or responses.
- Scope:
  Extend the existing `Cost` persistence path with structured attribution metadata for Gemini-only scope, add SQLite drift protection for existing installs, and keep current OpenAI cost flows backward compatible.
- Files:
  - backend/data/models.py
  - backend/data/database.py
  - backend/services/cost_service.py
  - backend/tests/test_cost_token_tracking_completeness.py
- Steps:
  1. Extend the `Cost` model with the structured metadata required by the spec for Gemini forensic drilldown, including grouping identifiers, attribution state, override markers, and component context.
  2. Add matching SQLite auto-migration coverage in `_ensure_sqlite_schema_migrations()` for existing databases.
  3. Refactor `create_cost_entry()` so callers can persist structured attribution metadata without breaking legacy call sites.
  4. Preserve the storage boundary from the spec: metadata and compact cause context only, no full prompt/response payloads.
- Acceptance Criteria:
  - [ ] The `Cost` model can store the metadata required for month -> session/test run -> request drilldown.
  - [ ] Existing SQLite databases auto-migrate on startup without manual DB reset.
  - [ ] Legacy cost writers that do not provide new Gemini metadata continue to work.
  - [ ] Stored attribution data excludes full prompt/response text by default.
- Tests:
  - `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q`
  - Add or update regression coverage for schema defaults and migration-safe persistence.
- Model: 5.4
- Reason:
  Shared backend schema change with migration and persistence risk, but still a normal Janus implementation task.

### TASK-SPEC14.2 Instrument Gemini provider calls, grounding, and websearch cost evidence
- Ziel:
  Ensure every external Gemini call, including Gemini grounding and native websearch, writes a persistent attribution record linked to the same request context.
- Scope:
  Wire Gemini gateway and Gemini websearch cost writers to the new persistence contract, capture component split inside one request context, and surface explicit attribution gaps instead of silently dropping cost evidence.
- Files:
  - backend/llm_providers/gemini/gateway.py
  - backend/tool_registry.py
  - backend/services/websearch/websearch.py
  - backend/services/websearch/gemini_provider.py
  - backend/tests/tools/test_websearch.py
  - backend/tests/llm_providers/test_gemini_service.py
- Steps:
  1. Audit all Gemini-side `create_cost_entry()` call sites and normalize them onto the structured attribution contract from `TASK-SPEC14.1`.
  2. Link base Gemini generation cost and Gemini grounding/websearch subcomponents to one shared request-level attribution trail.
  3. Persist explicit attribution-state markers when a Gemini call succeeds but evidence persistence is partial or failed.
  4. Keep OpenAI behavior unchanged except for non-regression of shared cost paths.
- Acceptance Criteria:
  - [ ] Every external Gemini provider call writes or explicitly fails an attribution record.
  - [ ] Gemini grounding/websearch component costs remain attached to the same request context as the parent request.
  - [ ] Partial attribution or write failures are visible as explicit states, not invisible drops.
  - [ ] Existing non-Gemini provider flows remain behaviorally unchanged.
- Tests:
  - `python -m pytest backend/tests/tools/test_websearch.py -q`
  - Add or update Gemini gateway/provider tests for grouped attribution metadata and persistence-failure signaling.
- Model: 5.4
- Reason:
  Multi-file Gemini integration work with concrete provider paths and regression-sensitive cost capture.

### TASK-SPEC14.3 Build backend forensic aggregation, anomaly summary, and May 2026 reconciliation
- Ziel:
  Produce DeepDive-ready backend summaries for anomaly-first entry, request drilldown, deviation states, and visible unattributed residuals, including historical May 2026 reconstruction.
- Scope:
  Extend aggregation and API responses so DeepDive can show anomaly blocks, month/test run/session/request grouping, intern-attributed vs not-clearly-attributed vs external-billing totals, and a historical reconciliation path for May 2026.
- Files:
  - backend/data/crud.py
  - backend/api/routers/system.py
  - backend/services/cost_service.py
  - backend/tests/test_cost_token_tracking_completeness.py
  - backend/tests/tools/test_websearch.py
- Steps:
  1. Extend monthly cost aggregation beyond the current model/context table to expose anomaly-oriented summaries and hierarchical drilldown keys.
  2. Add backend response fields for attribution states, deviation warnings, avoidable Pro signals, and visible residual buckets.
  3. Implement the historical reconciliation logic for May 2026 using persisted metadata and explicit residual handling when full attribution is impossible.
  4. Expose the DeepDive data through existing system cost endpoints or adjacent cost endpoints without creating a separate billing surface.
- Acceptance Criteria:
  - [ ] Backend responses expose anomaly overview data before the detailed drilldown table.
  - [ ] DeepDive data can drill from month to session/test run to single request.
  - [ ] Internal totals, unattributed residual, and external billing total can be shown side by side.
  - [ ] Historical May 2026 reconciliation leaves visible residuals when exact mapping is impossible.
- Tests:
  - `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q`
  - Add aggregation tests covering anomaly blocks, deviation states, and May 2026 residual handling.
- Model: 5.4
- Reason:
  Backend-heavy aggregation task with historical reconciliation logic but still within the reviewed spec's defined surface.

### TASK-SPEC14.4 Upgrade the existing DeepDive modal for anomaly-first forensic navigation
- Ziel:
  Turn the existing cost DeepDive modal into the spec-defined analysis surface with anomaly entry, grouped drilldown, component split, and visible attribution gaps.
- Scope:
  Rework the existing frontend cost modal only; do not create a new dashboard or separate billing UI. Consume the backend forensic payload and render anomaly-first navigation, grouped request breakdowns, and deviation messaging.
- Files:
  - frontend/index.html
  - frontend/js/cost-visualizer.js
  - frontend/src/styles.css
- Steps:
  1. Replace the current model-centric table-first DeepDive rendering with an anomaly-first overview and explicit drilldown states.
  2. Add grouped navigation for month -> session/test run -> request using the backend payload from `TASK-SPEC14.3`.
  3. Render Gemini grounding/websearch component split, unattributed residuals, external billing comparison, and avoidable Pro indicators.
  4. Preserve the existing modal entry point from `#cost-summary-widget` and keep budget controls working unless the new payload requires relocation inside the same modal.
- Acceptance Criteria:
  - [ ] DeepDive opens into an anomaly overview instead of only a flat model table.
  - [ ] Users can drill from grouped cost blocks down to single-request evidence.
  - [ ] Attribution gaps and billing deviations are visibly labeled rather than hidden in totals.
  - [ ] The implementation stays inside the existing DeepDive modal surface.
- Tests:
  - `node --check frontend/js/cost-visualizer.js`
  - Manual DeepDive smoke check against the updated modal payload and existing budget controls.
- Model: 5.4
- Reason:
  Existing frontend surface enhancement with moderate UI complexity and tight coupling to the backend payload.

### TASK-SPEC14.5 Enforce Flash-by-default Gemini grounding/websearch policy and mark avoidable Pro usage
- Ziel:
  Enforce the product rule that Gemini grounding/websearch uses Flash by default and only reaches Pro through explicit user choice or visible manual override.
- Scope:
  Lock the Gemini websearch/grounding model path to Flash by default, make override paths explicit, and emit enough evidence for DeepDive to flag avoidable Pro spend.
- Files:
  - backend/tool_registry.py
  - backend/services/websearch/websearch.py
  - backend/services/websearch/gemini_provider.py
  - backend/llm_providers/gemini/gateway.py
  - backend/tests/tools/test_websearch.py
  - backend/tests/test_smallest_viable_model_escalation_discipline.py
- Steps:
  1. Audit where Gemini websearch/grounding model selection is coerced or defaulted today.
  2. Enforce Flash as the default path for Gemini grounding/websearch in the first scope.
  3. Require an explicit override signal before Pro is used, and persist that signal into the attribution trail from `TASK-SPEC14.1`.
  4. Mark probable avoidable Pro consumption in the backend data exposed to DeepDive.
- Acceptance Criteria:
  - [ ] Gemini grounding/websearch defaults to Flash in the absence of an explicit override.
  - [ ] Pro usage on these paths is only possible through an explicit visible override path.
  - [ ] DeepDive data can distinguish manual Pro usage from avoidable or policy-breaking Pro usage.
  - [ ] Existing Gemini websearch regressions remain covered by automated tests.
- Tests:
  - `python -m pytest backend/tests/tools/test_websearch.py -q`
  - `python -m pytest backend/tests/test_smallest_viable_model_escalation_discipline.py -q`
- Model: 5.4
- Reason:
  Provider-policy enforcement with regression-sensitive routing behavior and explicit cost-governance impact.

## Task Breakdown Release

- Target Task: TASK-SPEC14.1
- Target Subtask: N/A
- Breakdown Decision: TASK DESIGN COMPLETE
- Readiness: READY FOR SINGLE TASK PRECHECK
- Execution Model: 5.4
- Breakdown Focus:
  Introduce the Gemini attribution evidence schema and migration-safe persistence contract first, because every later task depends on this storage shape.
