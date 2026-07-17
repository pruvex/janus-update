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
