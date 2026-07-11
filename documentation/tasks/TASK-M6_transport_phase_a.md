TASK-M6
- Source Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`
- Backlog Item: `N/A`
- Feature: Epic 4 Provider Transport Refactor, Phase A Consolidation
- Generated At: 2026-07-11

## Generated Tasks

### TASK-M6.1 Unify the model hierarchy as the single MoA source
- Ziel:
  - Make `MOA_MODEL_HIERARCHY` in `backend/llm_providers/shared/moa.py` the only model-tier source and remove the duplicate `ChatOrchestrator.MODEL_HIERARCHY` use.
- Scope:
  - Spec Section 3.4 and Phase A `T-A1` only. Migrate the bound imports and add a drift regression. No transport class, runtime resolver, OAuth, OpenRouter product path, or feature-flag flip.
- Files:
  - `backend/llm_providers/shared/moa.py`
  - `backend/services/chat_orchestrator.py`
  - `backend/llm_providers/gemini/gateway.py`
  - `backend/tests/test_model_hierarchy_single_source.py`
- Steps:
  1. Identify and remove the duplicate hierarchy definition from the orchestrator path.
  2. Migrate the bound consumers to the shared MoA hierarchy without changing tier semantics.
  3. Add a regression that fails if a second runtime model hierarchy is introduced.
- Acceptance Criteria:
  - `MOA_MODEL_HIERARCHY` is the only runtime model-hierarchy source for the bound paths.
  - OpenAI and Gemini bound consumers preserve their existing tier lookup behavior.
  - The new drift test passes.
- Tests:
  - `python -m pytest backend/tests/test_model_hierarchy_single_source.py -q`
  - focused existing hierarchy/gateway regressions selected by precheck
  - `python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py`
- Model: 5.6 Terra
- Reason:
  - The Spec names this as the first bounded Phase-A consolidation seam; it removes drift before shared loop extraction changes behavior.
- Closeout:
  - Final Audit: `PASS WITH FIXES` in `documentation/tasks/TASK-M6.1_final_audit.md`.
  - `MOA_MODEL_HIERARCHY` is now the sole runtime hierarchy source for the bound orchestrator and Gemini gateway paths. The approved OpenAI, Gemini, and Ollama matrix, including `fast`, is covered by focused regressions and manual Gemini websearch evidence.
  - Non-blocking follow-up: correct the obsolete Ollama-no-tier comment in `backend/llm_providers/shared/moa.py` before `TASK-M6.2`.
  - `T-A2` through `T-A5` remain open and are not covered by this task closeout.
  - Changelog skipped: internal provider-routing consolidation with no new user-facing feature or release.

### TASK-M6.2 Introduce the transport-boundary ToolCallAdapter
- Ziel:
  - Add the canonical-to-transport tool-call adapter defined in Spec Section 2.4 and Phase A `T-A2`.
- Scope:
  - Adapter and directly bound tool-definition/service seams only. Keep canonical skill IDs in the ToolManager and normalize provider names only at the transport boundary.
- Files:
  - `backend/llm_providers/shared/tool_call_adapter.py`
  - `backend/services/tool_manager.py`
  - `backend/llm_providers/openai/service.py`
  - `backend/llm_providers/shared/utils.py`
  - focused adapter/tool-call tests
- Steps:
  1. Define canonical outbound and inbound adaptation for skill IDs and LLM names.
  2. Move dot/underscore and Gemini schema normalization into the adapter boundary.
  3. Cover canonical ID preservation and provider-specific conversion with focused tests.
- Acceptance Criteria:
  - ToolManager emits canonical skill IDs.
  - Provider-specific tool naming is confined to the adapter boundary.
  - Inbound calls normalize back to canonical skill IDs.
- Tests:
  - focused adapter and existing prevalidation regressions selected by precheck
  - `python -m py_compile backend/llm_providers/shared/tool_call_adapter.py backend/services/tool_manager.py backend/llm_providers/openai/service.py backend/llm_providers/shared/utils.py`
- Model: 5.6 Terra
- Reason:
  - This is the explicit next Phase-A seam after hierarchy consolidation and stays transport-boundary only.
- Closeout:
  - Final Audit: `PASS WITH FIXES` in `documentation/tasks/TASK-M6.2_final_audit.md`.
  - `ToolManager` now emits canonical dotted skill IDs; `ToolCallAdapter` owns OpenAI/Gemini outbound naming, inbound canonical restoration, and provider-specific schema adaptation.
  - Focused adapter (`12/12`), OpenAI (`2/2`), and Gemini (`12/12`) regressions, syntax, scoped diff, and manual Gemini Berlin-weather evidence passed.
  - Non-blocking follow-up: Cursor Composer proposal-first execution is not autonomous/productive yet because the shared delegate has wrapper-contract defects and the valid direct run timed out without structured output. Track it as a separate Cursor-infrastructure debug slice.
  - `T-A3` through `T-A5` remain open and are not covered by this task closeout.
  - Changelog skipped: internal provider-routing consolidation with no new user-facing feature or release.

### TASK-M6.3 Extract the OpenAI ToolLoopRunner behind a default-off flag
- Ziel:
  - Extract the provider-neutral OpenAI tool loop into `ToolLoopRunner` without changing default production behavior.
- Scope:
  - Spec Section 3.3 and Phase A `T-A3` only. Preserve OpenAI behavior behind `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED=false`; no Gemini migration in this task.
- Files:
  - `backend/llm_providers/shared/tool_loop_runner.py`
  - `backend/llm_providers/openai/gateway.py`
  - focused OpenAI gateway and runner tests
- Steps:
  1. Extract the explicit provider-neutral loop responsibilities named in the Spec.
  2. Keep provider-specific prompt compilation and synthesis outside the runner.
  3. Add default-off and flag-on regression coverage for the OpenAI path.
- Acceptance Criteria:
  - The default flag preserves the existing OpenAI path.
  - The enabled path routes the declared loop responsibilities through `ToolLoopRunner`.
  - Focused OpenAI gateway regressions pass.
- Tests:
  - focused OpenAI gateway/runner regressions selected by precheck
  - `python -m py_compile backend/llm_providers/shared/tool_loop_runner.py backend/llm_providers/openai/gateway.py`
- Model: 5.6 Terra
- Reason:
  - The Spec explicitly stages OpenAI extraction before Gemini migration to keep behavior risk bounded.

### TASK-M6.4 Migrate the Gemini gateway to the shared ToolLoopRunner
- Ziel:
  - Route the Gemini gateway through the shared runner while preserving its native proto, schema, and history behavior.
- Scope:
  - Phase A `T-A4` only, after the OpenAI runner extraction is validated. No transport-layer classes or provider expansion.
- Files:
  - `backend/llm_providers/gemini/gateway.py`
  - `backend/llm_providers/shared/tool_loop_runner.py`
  - focused Gemini gateway and parity regressions
- Steps:
  1. Replace duplicated Gemini loop control with the shared runner integration.
  2. Keep Gemini-specific bridge and schema behavior in its gateway/service boundary.
  3. Add focused parity and regression coverage.
- Acceptance Criteria:
  - Gemini uses `ToolLoopRunner` for the declared loop responsibilities.
  - Gemini-specific proto/history behavior remains intact.
  - Focused Gemini regressions pass.
- Tests:
  - focused Gemini gateway and existing calendar routing regressions selected by precheck
  - `python -m py_compile backend/llm_providers/gemini/gateway.py backend/llm_providers/shared/tool_loop_runner.py`
- Model: 5.6 Terra
- Reason:
  - This follows the explicit Spec migration order and must remain separate from OpenAI extraction for diagnosis.

### TASK-M6.5 Route streaming through the gateway and ToolLoopRunner path
- Ziel:
  - Remove the declared direct streaming bypass from `execution_engine.py` while preserving provider behavior behind the Phase-A flag boundary.
- Scope:
  - Phase A `T-A5` only, after the shared runner is proven for OpenAI and Gemini. No Phase-B transport resolver or websearch decoupling.
- Files:
  - `backend/services/orchestrator/execution_engine.py`
  - bound gateway/runner files as required
  - focused streaming regressions
- Steps:
  1. Identify the direct provider streaming bypass named in the Spec.
  2. Route it through the gateway/runner path without changing the default-off flag behavior.
  3. Cover streaming and non-streaming path consistency.
- Acceptance Criteria:
  - Streaming no longer bypasses the bound gateway/runner path when Phase A is enabled.
  - Default-off behavior remains unchanged.
  - Focused streaming regressions pass.
- Tests:
  - focused streaming and gateway regressions selected by precheck
  - `python -m py_compile backend/services/orchestrator/execution_engine.py`
- Model: 5.6 Terra
- Reason:
  - The Spec explicitly places streaming migration last in Phase A because it depends on the shared runner path.
