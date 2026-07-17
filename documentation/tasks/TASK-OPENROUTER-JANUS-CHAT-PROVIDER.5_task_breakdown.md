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
- Verify non-stream, tool-loop, stream, and gateway-handoff seams have one explicit persistence owner each. Block any design that can persist the same usage twice.
- Verify streaming persistence occurs only after exact model identity and a completion marker are proven; incomplete or failed streams must not write successful telemetry.
- Verify the DeepDive API contract can expose unavailable values and unit metadata without changing current EUR totals or Gemini forensic contracts.
- Verify UI formatters do not use `Number(value ?? 0)` for the new nullable fields and do not append `€`, `$`, or a converted currency to OpenRouter credits.
- Preserve all unrelated dirty and untracked operator files.

## Execution Model

- **Model:** `5.6 Terra`
- **Intelligence:** high
- **Reason:** This is a cross-layer persistence and data-truthfulness change with unit isolation, migration, multi-round attribution, and duplicate-persistence risks, but the product field map and provider boundaries are already fixed.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_task_breakdown.md
Backlog Item: N/A
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```

## Completion Update

- **Status:** DONE - Task-scoped Final Audit PASS WITH FIXES on 2026-07-17.
- **Evidence:** telemetry/provider/cost/stream-handoff Python matrix `44 passed`; Chat-Core `1 passed`; headed DeepDive suite `3 passed`; compile, JavaScript syntax, scoped diff, and scoped credential scan PASS.
- **Audit Repairs:** the stream-to-gateway persistence owner and the router-preserved global round identity are both directly regression-tested.
- **Remaining Feature Work:** Task `.6` only; production remains disabled and the packaged certification registry remains empty.
