# AUDIT_PACKAGE

Generated: 2026-07-17 17:02:31 UTC

## Goal

Re-audit Task .5 authoritative OpenRouter telemetry persistence and DeepDive rendering after stream-handoff and router-boundary repairs

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md (feature remains partial until Task .6)
- Task File: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_task_breakdown.md
- Backlog Item: N/A WITH REASON - compiled Feature Spec task
- Pre-Implementation Check: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_precheck.md
- Manual Janus Evidence: N/A WITH REASON - deterministic headed Playwright covers the bounded UI; live provider is excluded
- Pipeline Completion Status: Task .5 repair complete and fully retested; Task .6 remains outside this audit

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
# TASK BREAKDOWN - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5

## Source Identity

- **Spec:** `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- **Task File:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.md`
- **Backlog Item:** N/A WITH REASON - compiled Feature Spec task
- **Prior Gates:** Tasks `.1` through `.4` Final Audit PASS; parent feature remains `PARTIAL IMPLEMENTATION (4/6)`; production certification registry remains intentionally empty

## Selected Target

- **Target Task:** `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5`
- **Target Subtask:** N/A
- **Mode:** `SINGLE_TASK_PRECHECK`
- **Goal:** Persist and render only authoritative OpenRouter response-model, token, cache, reasoning, charged-credit, and upstream-inference-cost telemetry per Janus turn, while preserving missing-versus-zero truth and preventing any cross-unit aggregation or local estimate.

## Source Of Truth

- The bound Feature Spec field map is authoritative:
  - `response.model` -> exact concrete model identity
  - `usage.prompt_tokens` -> input tokens
  - `usage.completion_tokens` -> output tokens
  - `usage.total_tokens` -> total tokens
  - `usage.prompt_tokens_details.cached_tokens` -> cache-read tokens
  - `usage.prompt_tokens_details.cache_write_tokens` -> cache-write tokens
  - `usage.completion_tokens_details.reasoning_tokens` -> reasoning tokens
  - `usage.cost` -> actually charged OpenRouter credits
  - `usage.cost_details.upstream_inference_cost` -> actual upstream inference cost
- `OpenRouterServiceProvider` remains the provider-response boundary. It may normalize only those exact fields and must preserve each missing field as absent/`None`, not synthesize it.
- The existing `Cost` persistence and `get_costs_deep_dive_summary()` remain the storage and DeepDive authority. Task `.5` extends them; it does not create a second telemetry store or billing surface.
- The existing Janus request/trace context is the source for one stable per-turn attribution identity. All OpenRouter response rounds belonging to the same Janus turn must carry the same turn identity without using `chat_id` alone as a supposedly unique turn ID.
- Existing shared `total_cost` and cross-provider totals retain their current currency semantics. OpenRouter credits and upstream inference cost use separate nullable fields and separately labelled aggregations; values with different units must never be summed.

## Scope

- Add one narrow OpenRouter telemetry normalizer at the provider boundary. It copies only finite numeric values from the exact Spec paths, preserves a numeric `0`, preserves a missing or non-numeric field as `None`, and carries the already verified exact response model.
- Preserve the normalized payload through non-streaming responses, tool-loop final responses, and terminally successful streaming usage events. Missing usage must never convert a successful response into a provider error.
- Bind every persisted OpenRouter telemetry row to:
  - provider `openrouter`
  - exact verified `response.model`
  - one stable Janus-turn/request identity
  - an optional per-round/component identity when a tool loop produces multiple authoritative upstream responses
- Extend the existing `Cost` model and startup migration with nullable OpenRouter-specific columns for prompt, completion, total, cached, cache-write, and reasoning tokens, charged credits, and upstream inference cost. Historical rows must receive `NULL`, never a default `0`.
- Extend `create_cost_entry()` or one bounded OpenRouter-specific wrapper on that existing persistence seam so nullable values remain nullable. Do not pass OpenRouter credits through the shared EUR calculation/conversion path, `_calculate_cost_saved()`, model price tables, or a fallback estimate.
- Persist at most once per authoritative OpenRouter response/usage record. The existing stream-final and post-response cost paths must not duplicate the same OpenRouter telemetry.
- Extend DeepDive with a separate OpenRouter truth section at turn/request and exact-model granularity:
  - show each token field independently
  - show charged OpenRouter credits and upstream inference cost independently
  - render a real numeric `0` as `0`
  - render a missing field as `nicht verfügbar`
  - never sum OpenRouter credits or upstream costs into EUR totals or across incompatible units
- Preserve current OpenAI, Gemini, Ollama, websearch, cross-provider, caching, savings, and Gemini-forensic behavior.

## Files

- `backend/llm_providers/openrouter/service.py`
- `backend/llm_providers/openrouter/gateway.py`
- `backend/llm_providers/shared/response_postprocessors.py`
- `backend/services/chat_orchestrator.py`
- `backend/services/orchestrator/chat_request_workflow_state.py`
- `backend/services/orchestrator/execution_engine.py`
- `backend/services/cost_service.py`
- `backend/data/models.py`
- `backend/data/database.py`
- `backend/data/crud.py`
- `frontend/js/cost-visualizer.js`
- `backend/tests/test_cost_token_tracking_completeness.py`
- `backend/tests/test_openrouter_provider.py`
- `backend/tests/test_openrouter_telemetry.py` (new)
- `tests/functional/chat-core.spec.js`
- `tests/e2e/openrouter-deep-dive.spec.js` (new focused DeepDive UI evidence)

`backend/llm_providers/openrouter/gateway.py`, `backend/tests/test_openrouter_provider.py`, and the focused DeepDive E2E file refine the compiled file list only to prove exact-model propagation, tool-loop/stream preservation, and UI missing-versus-zero behavior at the existing seams. They do not add a new provider or product surface.

## Explicit Exclusions

- No OpenRouter key lifecycle, key validation, eligibility, selector, retained-selection, send-gate, credential invalidation, retry, fallback, or certification-registry changes.
- No candidate certification, real model activation, real credential, live OpenRouter request, price lookup, local rate table, EUR/USD conversion, currency assumption, or estimated cost.
- No replacement of the existing `Cost` table, DeepDive, cross-provider summary, Gemini forensics, or cost-debug log.
- No aggregation of charged OpenRouter credits with upstream inference cost or with another provider's currency totals.
- No reinterpretation of historical zero/default values as delivered OpenRouter telemetry.
- No telemetry completeness requirement for chat success. Only the existing exact-response-model mismatch remains a provider failure.
- No Task `.6` conformance battery, release, build, commit, push, sync, publish, or production activation.

## Acceptance Criteria

1. A complete mocked OpenRouter response persists the exact verified response model and every mapped token/cost field without calculation, conversion, rounding-before-storage, or substitution.
2. A partially populated successful response remains successful; each missing mapped field persists as `NULL`/unavailable and appears in DeepDive as `nicht verfügbar`.
3. A delivered numeric `0` remains distinguishable from missing in the database, API payload, aggregation, and UI.
4. Every persisted OpenRouter telemetry row is bound to provider `openrouter`, exact `response.model`, and a stable Janus-turn/request identity. Multi-round tool-loop rows share the turn identity and remain individually attributable.
5. Charged OpenRouter credits and upstream inference cost are stored and displayed in separate nullable fields with explicit labels. They are not summed together and are never included in EUR or incompatible cross-provider totals.
6. Prompt, completion, total, cache-read, cache-write, and reasoning tokens are stored and displayed independently. Missing totals are not reconstructed from other token fields.
7. Existing non-streaming, tool-loop, and successful stream paths persist each authoritative OpenRouter usage record at most once. Error, incomplete-stream, and model-mismatch paths persist no successful telemetry.
8. Startup migration adds nullable columns without non-null defaults, preserves historical rows as unavailable, and remains idempotent on repeated startup.
9. OpenAI, Gemini, Ollama, websearch, shared cost/savings aggregation, Gemini forensics, and existing DeepDive UI remain unchanged.
10. The packaged empty certification registry remains empty; Task `.5` creates no live provider activity or production-selectable model.

## Tests

- `backend/tests/test_openrouter_telemetry.py`:
  - exact complete field mapping
  - partial fields
  - explicit zero versus missing
  - finite-number validation
  - exact response-model propagation
  - per-turn/provider/model and multi-round attribution
  - no persistence on provider/model/stream failure
  - no duplicate persistence across response and stream-final seams
  - charged credits versus upstream cost separation
- `backend/tests/test_cost_token_tracking_completeness.py`:
  - startup migration from a legacy `costs` schema produces nullable OpenRouter columns
  - migration is idempotent
  - historical rows remain `NULL`
  - DeepDive exposes separate OpenRouter per-field/per-turn values
  - OpenRouter amounts do not enter shared EUR totals
  - existing cross-provider/cache/savings/Gemini-forensic assertions remain green
- `backend/tests/test_openrouter_provider.py`: successful non-stream, tool-loop, and stream usage preserves the authoritative normalized telemetry after exact-model validation; failure paths remain fail-closed.
- `tests/functional/chat-core.spec.js`: response telemetry does not alter chat success/error behavior or existing provider submission.
- `tests/e2e/openrouter-deep-dive.spec.js`: mocked complete, partial, and zero telemetry renders exact labels and `nicht verfügbar` without local conversion; existing user-first overview remains intact.
- Existing permanent DeepDive UI regressions:
  - `tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js`
  - `tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js`
- Python compilation for all changed Python files, JavaScript syntax checks, scoped telemetry/secret-shape scans, and scoped `git diff --check`.

Required automated gate:

```powershell
python -m pytest -q backend/tests/test_openrouter_telemetry.py backend/tests/test_openrouter_provider.py backend/tests/test_cost_token_tracking_completeness.py
node --check frontend/js/cost-visualizer.js
npx playwright test tests/functional/chat-core.spec.js --workers=1 --reporter=list
npx playwright test tests/e2e/openrouter-deep-dive.spec.js tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js --headed --workers=1 --reporter=list
git diff --check -- backend/llm_providers/openrouter/service.py backend/llm_providers/openrouter/gateway.py backend/llm_providers/shared/response_postprocessors.py backend/services/chat_orchestrator.py backend/services/orchestrator/chat_request_workflow_state.py backend/services/orchestrator/execution_engine.py backend/services/cost_service.py backend/data/models.py backend/data/database.py backend/data/crud.py frontend/js/cost-visualizer.js backend/tests/test_cost_token_tracking_completeness.py backend/tests/test_openrouter_provider.py backend/tests/test_openrouter_telemetry.py tests/functional/chat-core.spec.js tests/e2e/openrouter-deep-dive.spec.js
```

## Risks And Precheck Gates

- Verify the exact OpenRouter SDK/runtime response shape preserves `usage.cost` and nested `cost_details`/token-detail fields. Block implementation if the current `model_dump()` path drops extras or cannot distinguish absent from `None`.
- Verify one stable per-turn identity is already available or can be generated once at the chat-request boundary and propagated without using `chat_id` as a unique turn surrogate.
- Verify shared cost callers and aggregators cannot silently coerce OpenRouter `None` fields through `or 0`, reconstruct `total_tokens`, calculate savings, or mix units.
- Verify the database migration uses nullable columns with no server default and leaves existing rows `NULL`.
- Verify non-stream, tool-loop, stream, and gateway-handoff seams have one
```

## Pre-Implementation Check

```text
# PRE-IMPLEMENTATION CHECK - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5

PRE-CHECK RESULT
PRE-CHECK PASSED

## Pre-Check Identity

- Target Task: `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5`
- Target Subtask: N/A
- Task: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_task_breakdown.md`
- Spec: `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- Backlog Item: N/A WITH REASON - compiled Feature Spec task
- Mode: `SINGLE_TASK_PRECHECK`
- Assigned Model: `5.6 Terra`
- Assigned Intelligence: high
- Risk: HIGH
- Artifact Identity Check: PASS - exactly one compiled Feature-Spec task, its source Spec, and its Task `.5` breakdown are bound.
- Implementation Started: NO
- Product Tests Executed: NO
- Live Provider/Credential Action: NO
- Git Action: NO

## Gate Review

- Scope and field map: PASS - the Spec fixes every response-model, token-detail, charged-credit, and upstream-inference-cost source path. No price lookup, conversion, or estimation decision remains.
- SDK preservation: PASS - the installed OpenAI SDK `2.20.0` uses `extra=allow` for `CompletionUsage`; a local contract inspection confirmed `model_dump()` preserves `cost`, `cost_details.upstream_inference_cost`, `prompt_tokens_details.cache_write_tokens`, explicit zero values, and the standard token-detail fields.
- Exact model identity: PASS - Task `.3` already rejects a mismatched or missing `response.model` before a response/stream can complete. Task `.5` consumes the verified identity and does not weaken the fail-closed gate.
- Provider response seam: PASS - `OpenRouterServiceProvider` already owns non-stream and stream usage extraction. It can normalize the exact fields once and emit the existing `usage` plus an additive authoritative cost/telemetry payload.
- Tool-loop round preservation: PASS - `ToolLoopRunner.run()` already exposes `on_round_response`. `OpenRouterGateway` can collect each authoritative round in a local closure and attach the bounded records to the final response without changing the shared runner or mixing OpenRouter values into its EUR-oriented counters.
- Streaming completion: PASS - the OpenRouter stream already requires exact model identity and a completion marker before `finish`/`done`. `execution_engine` can buffer the last normalized usage record and persist only after that terminal proof instead of at the early usage-event branch.
- Duplicate-persistence ownership: PASS - OpenRouter is already excluded from the generic stream-final shared-cost path. The task can assign exactly one OpenRouter persistence owner to non-stream/tool-loop result records and one terminal-success owner to streamed records, with direct no-duplicate tests.
- Stable turn identity: PASS - `ChatRequestWorkflowState` is created once per `handle_chat_request`. A single UUID field can be initialized at `_classify_request`, propagated through gateway kwargs, and reused as `attribution_request_id`; `chat_id` remains only the session/group context and is not misrepresented as a unique turn ID.
- Nullable storage: PASS - the `Cost` table is the existing authority and the startup migration already uses idempotent column inspection. New OpenRouter-specific token and cost columns can be nullable with no defaults, preserving historical rows as `NULL`.
- Unit isolation: PASS - existing `total_cost`, savings, budget, provider/model summaries, and `formatCurrency()` are EUR-oriented. The task binds separate nullable OpenRouter-credit and upstream-cost columns/API sections and explicitly excludes them from those shared totals.
- Missing versus zero: PASS - new provider-specific nullable columns avoid the legacy shared token columns' `DEFAULT 0` semantics. Task `.5` forbids `or 0`, reconstruction, or `Number(value ?? 0)` on these fields.
- DeepDive extension: PASS - `get_costs_deep_dive_summary()` already owns provider/model/request grouping and the frontend has a single existing DeepDive renderer. An additive OpenRouter truth section can reuse request identity without creating a second surface.
- Existing-provider preservation: PASS - shared EUR totals and Gemini forensics remain unchanged; permanent BACKLOG-101 and BACKLOG-103 UI smokes plus the cost-token suite are bound as regressions.
- Production safety: PASS - no certification registry or credential action is in scope. The packaged registry remains empty and all positive telemetry evidence uses controlled provider responses.
- Open product decisions: NONE.
- Open architecture decisions: NONE. Exact helper and column names remain bounded implementation details as long as they satisfy the nullable, unit-isolated, single-owner contracts above.

## Required Storage Contract

- Provider: exact lowercase `openrouter` in persistence; user-facing label may remain `OpenRouter`.
- Model: verified exact `response.model` in the existing `model` column.
- Turn: one generated-per-request UUID in `attribution_request_id`; chat/session context may use existing attribution metadata/group fields.
- Round: one component/round marker per authoritative upstream response when a tool loop has multiple rounds.
- Nullable OpenRouter fields: prompt, completion, total, cached, cache-write, reasoning tokens, charged credits, and upstream inference cost.
- Historical rows: all new fields remain `NULL`.
- Shared EUR fields: no OpenRouter credit/upstream amount is written to `total_cost`, `cost_saved`, budget totals, or EUR provider/model summaries.

## Execution Risk Controls

- Do not read, save, print, or validate a real API key and do not make a live OpenRouter request.
- Accept only finite `int`/`float` values; reject booleans and non-numeric strings as unavailable. Preserve numeric zero.
- Do not derive total tokens from prompt plus completion tokens and do not derive any missing cache, reasoning, charged-credit, or upstream value.
- Do not persist stream telemetry until exact model identity and completion marker are both proven.
- Do not persist model-mismatch, incomplete-stream, authentication, provider, or malformed-response attempts as successful telemetry.
- Do not let generic tool-loop EUR counters, `_calculate_cost_saved()`, price tables, `formatCurrency()`, or cross-provider totals consume OpenRouter credits.
- Use the existing `on_round_response` seam rather than modifying shared tool-loop semantics unless execution proves the seam insufficient; any required shared-runner change must stop and reroute as scope expansion.
- Preserve unrelated dirty and untracked operator files.

## Validation

- Task/Spec identity and single-target scope: PASS
- Exact Spec field map: PASS
- Installed SDK extra-field/zero preservation: PASS
- Existing exact-response-model gate: PASS
- Non-stream/tool-loop round capture seam: PASS
- Terminal stream persistence seam: PASS
- Stable per-turn workflow identity seam: PASS
- Nullable idempotent migration seam: PASS
- Unit-isolated DeepDive/API/UI seam: PASS
- Existing-provider regression surface: PASS
- Required backend, migration, functional, headed, syntax, leak, and diff evidence: PASS
- Product tests during precheck: NOT RUN by rule

## Execution Handoff

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5
Target Subtask: N/A
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_task_breakdown.md
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Persist only exact verified OpenRouter response-model and authoritative token/cost fields with missing-versus-zero preservation, stable per-turn attribution, separate units, and one persistence owner per response path.
- Keep successful partial-telemetry turns successful; keep production disabled and existing providers unchanged.
Affected Files:
- backend/llm_providers/openrouter/service.py
- backend/llm_providers/openrouter/gateway.py
- backend/llm_providers/shared/response_postprocessors.py
- backend/services/chat_orchestrator.py
- backend/services/orchestrator/chat_request_workflow_state.py
- backend/services/orchestrator/execution_engine.py
- backend/services/cost_service.py
- backend/data/models.py
- backend/data/database.py
- backend/data/crud.py
- frontend/js/cost-visualizer.js
- backend/tests/test_cost_token_tracking_completeness.py
- backend/tests/test_openrouter_provider.py
- backend/tests/test_openrouter_telemetry.py
- tests/functional/chat-core.spec.js
- tests/e2e/openrouter-deep-dive.spec.js
Evidence Focus:
- Exact complete/partial/zero provider field mapping and exact response-model preservation.
- Nullable legacy migration, stable turn and multi-round attribution, terminal stream persistence, and no duplicate records.
- Separate OpenRouter credits/upstream cost with no EUR conversion or incompatible aggregation.
- DeepDive per-field `nicht verfügbar` behavior and unchanged cross-provider/Gemini/user-first surfaces.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not change credentials, eligibility, selectors, certification, retry/fallback, Task .6, release, or production activation.
Automated Evidence Gate:
- python -m pytest -q backend/tests/test_openrouter_telemetry.py backend/tests/test_openrouter_provider.py backend/tests/test_cost_token_tracking_completeness.py
- node --check frontend/js/cost-visualizer.js
- npx playwright test tests/functional/chat-core.spec.js --workers=1 --reporter=list
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/openrouter-deep-dive.spec.js tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js --headed --workers=1 --reporter=list
- git diff --check -- backend/llm_providers/openrouter/service.py backend/llm_providers/openrouter/gateway.py backend/llm_providers/shared/response_postprocessors.py backend/services/chat_orchestrator.py backend/services/orchestrator/chat_request_workflow_state.py backend/services/orchestrator/execution_engine.py backend/services/cost_service.py backend/data/models.py backend/data/database.py backend/data/crud.py frontend/js/cost-visualizer.js backend/tests/test_cost_token_tracking_completeness.py backend/tests/test_openrouter_provider.py backend/tests/test_openrouter_telemetry.py tests/functional/chat-core.spec.js tests/e2e/openrouter-deep-dive.spec.js
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_task_breakdown.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_precheck.md
- named affected files and evidence commands only
Drop Context:
- Tasks .1 through .4 implementation history
- Task .6, unrelated backlog, audit, release, and Git history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths. Stop before final audit, documentation closeout, Git, release, or production activation.
Expected Output:
- Implementation result, executed checks, affected files, residual risks, and exact next-skill handoff.
legacy handoff end
```

## NEXT STEP

Recommended Skill: janus-executioner

Recommended Model: `5.6 Terra`

Recommended Intelligence: high

User Action: Continue in the current warm Codex context with exactly Task `.5`; no additional approval is required before the bounded non-Git implementation.
```

## Changed Files

```text
warning: could not open directory 'backend/llm_providers/openrouter/service.py,backend/llm_providers/openrouter/gateway.py,backend/services/chat_orchestrator.py,backend/services/orchestrator/execution_engine.py,backend/services/cost_service.py,backend/data/models.py,backend/data/database.py,backend/data/crud.py,frontend/js/cost-visualizer.js,backend/tests/test_openrouter_telemetry.py,backend/tests/test_openrouter_provider.py,backend/tests/test_cost_token_tracking_completeness.py,backend/tests/test_streaming_tool_loop_runner.py,tests/e2e/openrouter-deep-dive.spec.js,tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js,tests/e2e/generated/': Filename too long
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_debug_result_stream_handoff_telemetry.md (3257 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_debug_result_router_round_forwarding.md (2702 bytes)
```

## Diff Summary

```text
No diff stat available.
```

## Validation

```text
# TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5 Execution Result

Canonical State: PASS

## Result

Task .5 now preserves authoritative OpenRouter response telemetry across non-stream, multi-round tool-loop, and terminally successful stream paths; persists it with stable turn/round attribution; and renders it in the existing DeepDive without mixing OpenRouter credits or upstream inference cost into Janus EUR totals.

Explicit numeric zero remains zero. Missing, non-numeric, boolean, non-finite, or fractional token fields remain unavailable. Repeated persistence for the same turn/model/round is idempotent.

## Implementation

- Provider boundary normalizes only the approved response model, token details, charged OpenRouter credits, and upstream inference cost.
- Gateway carries each tool-loop round with one stable turn identity.
- Orchestrator persistence writes non-stream/tool-loop data once and stream data only after exact-model and completion proof.
- Nullable database fields preserve historical missing data as `NULL`.
- DeepDive exposes a separate, explicitly labelled OpenRouter section with no currency conversion or estimation.
- Existing EUR totals, budget, savings, OpenAI/Gemini/Ollama behavior, and Gemini forensics remain separate.
- Two stale permanent DeepDive smoke oracles were aligned to the already approved localized two-stage UI; no product behavior changed for that repair.
- Final Audit findings exposed the combined stream-tool/gateway-continuation path and its central-router boundary. The continuation now persists its attached telemetry with a global round offset forwarded through the established `current_round` seam, preventing idempotency collisions with earlier streamed rounds.

## Changed Files

- `backend/llm_providers/openrouter/service.py`
- `backend/llm_providers/openrouter/gateway.py`
- `backend/services/chat_orchestrator.py`
- `backend/services/orchestrator/execution_engine.py`
- `backend/services/cost_service.py`
- `backend/data/models.py`
- `backend/data/database.py`
- `backend/data/crud.py`
- `frontend/js/cost-visualizer.js`
- `backend/tests/test_openrouter_telemetry.py`
- `backend/tests/test_openrouter_provider.py`
- `backend/tests/test_cost_token_tracking_completeness.py`
- `backend/tests/test_streaming_tool_loop_runner.py`
- `tests/e2e/openrouter-deep-dive.spec.js`
- `tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js`
- `tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_task_breakdown.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_precheck.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_debug_result_stale_deep_dive_smokes.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_debug_result_stream_handoff_telemetry.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_debug_result_router_round_forwarding.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_test_oracle_precheck.md`
- `development/openrouter-skill-tests/janus-executioner/task5_execution_input_package_2026-07-17.json`
- `development/openrouter-skill-tests/janus-executioner/task5_execution_allowlist_2026-07-17.txt`

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest -q backend/tests/test_openrouter_telemetry.py backend/tests/test_openrouter_provider.py backend/tests/test_cost_token_tracking_completeness.py backend/tests/test_streaming_tool_loop_runner.py` -> 44 passed.
  - Focused combined stream-tool/gateway-continuation regression was red before repair and passed after repair.
  - The same regression exercises the real central gateway router and proves the OpenRouter continuation receives its completed-round offset.
  - `npx playwright test tests/functional/chat-core.spec.js --workers=1 --reporter=list` -> 1 passed.
  - `npx playwright test tests/e2e/openrouter-deep-dive.spec.js tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js --headed --workers=1 --reporter=list` -> 3 passed.
  - Focused BACKLOG-101 headed retest -> 1 passed.
  - Python compilation for all changed Python files -> PASS.
  - JavaScript syntax checks for the renderer and all three DeepDive runners -> PASS.
  - Scoped `git diff --check` -> PASS.
  - Scoped credential/authorization pattern scan -> PASS.
  - Debug result validator -> PASS.
  - Test-oracle precheck validator -> PASS.

Manual Janus Validation Gate:
- Status: N/A WITH REASON
- Test Example: Open the DeepDive against the controlled Task .5 payload and inspect complete, zero, and missing OpenRouter fields.
- Expected Result: Exact model and turn are visible; zero renders as `0`; missing renders as `nicht verfügbar`; credits/upstream cost remain separately labelled without EUR conversion.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit
- Reason: The required UI behavior was executed headed through Playwright with a deterministic controlled OpenRouter payload. A live OpenRouter request is explicitly excluded because production certification and credentials remain out of scope.

## Known Limits

- No live OpenRouter provider request was made.
- The production certification registry remains empty and OpenRouter remains unavailable for production chat.
- Existing unrelated vector/vision dependency warnings appeared during Janus startup but did not block the bound Chat-Core or DeepDive suites.

## NEXT_STEP

- Target Skill: janus-final-audit
- Canonical State: HANDOFF
- Required Artifacts:
  - Task .5 breakdown and precheck
  - This execution result
  - Closed stale-oracle debug result
  - Changed implementation and test files listed above
- Evidence Paths:
  - `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_execution_result.md`
  - `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_debug_result_stale_deep_dive_smokes.md`
  - `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_debug_result_stream_handoff_telemetry.md`
  - `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_debug_result_router_round_forwarding.md`
  - `tests/e2e/openrouter-deep-dive.spec.js`
- Failure Code: NONE
- Changed Files: implementation, tests, and bound Task .5 artifacts listed in this result
- Decision: Audit Task .5 against the approved Spec and precheck.
- Reason: All bound automated gates pass and the live-provider exclusion is explicit.
- Recommended Model: 5.6 Sol
- Recommended Intelligence: high
- Next User Action: None; Codex continues to the final audit in the current task.
```

## Notes

# Debug Result — TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5

SKILL 5 DEBUG RESULT: FIXED

Iteration: 2

## Failure

- Failure Code: `OPENROUTER_ROUTER_DROPS_ROUND_OFFSET`
- The first stream-handoff repair used a new keyword that the central gateway
  router retained only in `**kwargs` and did not forward to the OpenRouter
  silo.
- The initial regression mocked the router function itself, so it could not
  detect the dropped value.

## Root Cause

The provider router has an explicit silo-argument allowlist. It already
forwards `current_round`, but not task-specific keyword names.

## Repair

- The stream handoff sets `current_round` only when its current provider is
  OpenRouter; it represents the count of completed streamed rounds.
- `OpenRouterGateway` uses that router-forwarded value as the continuation
  offset when emitting authoritative telemetry records.
- The regression now invokes the real central router with a captured OpenRouter
  silo and proves that round `1` reaches the silo before the record for round
  `2` is persisted.

Progress-Validierung:
- Before repair: real-router regression failed with `KeyError: current_round`.
- After repair: real-router stream-handoff regression and OpenRouter gateway
  multi-round offset test passed.

Auto-Verification:
- Status: PASS
- Evidence:
  - `backend/tests/test_streaming_tool_loop_runner.py::test_openrouter_stream_handoff_persists_attached_telemetry_with_global_round`
  - `backend/tests/test_openrouter_provider.py::test_exact_model_stays_pinned_across_tool_and_synthesis_rounds`

Final Feature Suite: N/A WITH REASON

The full Task `.5` Python and UI suites are the following re-audit gate and are
not represented by this focused debug pass.

## NEXT_STEP

- Target Skill: janus-final-audit
- Canonical State: HANDOFF
- Required Artifacts: repaired stream handoff, router-boundary regression, both Task `.5` debug results, refreshed execution result and audit package
- Evidence Paths: `backend/services/orchestrator/execution_engine.py`, `backend/llm_providers/openrouter/gateway.py`, `backend/services/llm_gateway.py`, `backend/tests/test_streaming_tool_loop_runner.py`
- Failure Code: NONE
- Changed Files: `backend/services/orchestrator/execution_engine.py`, `backend/llm_providers/openrouter/gateway.py`, `backend/tests/test_streaming_tool_loop_runner.py`, `backend/tests/test_openrouter_provider.py`, this debug result
- Decision: run the complete bound Task `.5` validation and re-audit
- Reason: the global round survives the real central router and has focused regression evidence
- Recommended Model: 5.6 Terra
- Recommended Intelligence: high
- Next User Action: none; Codex continues validation in the current task

## Risks

No live provider request; production certification remains empty; unrelated vector/vision startup warnings remain outside scope.

## Open Issues

None inside Task .5 after both focused repairs; Task .6 remains outside this audit.

## Re-Audit Delta

Primary blocker: OPENROUTER_ROUTER_DROPS_ROUND_OFFSET
Prior audit/package: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_FINAL_AUDIT.md

The real central router now forwards the existing current_round seam for OpenRouter stream handoffs; the gateway applies it as the global telemetry-round offset, with a red-before/green-after real-router SQLite regression.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
