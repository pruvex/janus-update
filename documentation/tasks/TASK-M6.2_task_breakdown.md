# TASK BREAKDOWN - TASK-M6.2

## Binding Sources
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Section 2.4, Section 3.1, Phase A `T-A2`)
- Parent Task: `documentation/tasks/TASK-M6_transport_phase_a.md`
- Backlog Item: `N/A` - roadmap/spec-driven infrastructure slice
- Prior Slice: `TASK-M6.1` completed and checkpointed; its MoA hierarchy decision is unchanged.

## Released Target
- Target Task: `TASK-M6.2`
- Title: Introduce the transport-boundary ToolCallAdapter
- Execution Model: `5.6 Terra`, `medium`
- Readiness: `PRECHECK_READY`

## Atomic Scope
- Add `backend/llm_providers/shared/tool_call_adapter.py` as the single owner of canonical-to-provider tool-name adaptation and inbound provider-name normalization.
- Change `backend/services/tool_manager.py` so `get_tool_definitions()` emits canonical skill IDs rather than applying Gemini-safe name rewriting globally.
- Move the existing OpenAI dot-to-underscore conversion and forced-tool name handling in `backend/llm_providers/openai/service.py` behind the adapter boundary.
- Move Gemini tool-name sanitization, inbound name restoration, and adapter-bound schema conversion in `backend/llm_providers/gemini/service.py` behind the adapter boundary.
- Integrate only directly necessary prevalidation normalization in `backend/llm_providers/shared/utils.py`.
- Add focused adapter coverage and retain existing executor alias fallback coverage as a compatibility regression.

## Files
- `backend/llm_providers/shared/tool_call_adapter.py` (new)
- `backend/services/tool_manager.py`
- `backend/llm_providers/openai/service.py`
- `backend/llm_providers/gemini/service.py`
- `backend/llm_providers/shared/utils.py`
- `backend/tests/test_tool_call_adapter.py` (new)
- `backend/tests/test_tool_name_aliasing.py`
- `backend/tests/llm_providers/test_openai_service.py`
- `backend/tests/llm_providers/test_gemini_service.py`

## Explicit Exclusions
- No `ToolLoopRunner`, transport classes, runtime resolver, gateway-loop extraction, streaming migration, OAuth, OpenRouter path, websearch policy change, feature flag, or MoA hierarchy change.
- No removal of existing executor alias fallback in `backend/services/tool_executor.py`; it remains a backward-compatibility guard.
- No new provider policy or new tool schema semantics beyond moving the existing provider-specific handling to the adapter boundary.
- No Phase-A task beyond `T-A2`; `TASK-M6.3` through `TASK-M6.5` require separate task breakdown and precheck artifacts.

## Acceptance Criteria
- `ToolManager.get_tool_definitions()` exposes canonical skill IDs such as `system.websearch` and does not apply provider-specific dot/underscore conversion.
- The adapter emits provider-safe outbound names for OpenAI and Gemini without changing the canonical internal `skill_id`.
- Inbound OpenAI/Gemini provider names normalize back to canonical Janus skill IDs before shared execution or prevalidation consumes them.
- Existing OpenAI forced-tool behavior and Gemini history/function-call behavior remain compatible after their name conversions route through the adapter.
- Existing executor dot/underscore alias fallback remains covered and unchanged.
- Provider-specific schema cleaning stays behaviorally unchanged and is invoked only from the adapter boundary where required by the bound services.

## Tests
- `python -m pytest backend/tests/test_tool_call_adapter.py -q`
- `python -m pytest backend/tests/test_tool_name_aliasing.py -q`
- `python -m pytest backend/tests/llm_providers/test_openai_service.py -q`
- `python -m pytest backend/tests/llm_providers/test_gemini_service.py -q`
- focused prevalidation regression selected by precheck for `backend/llm_providers/shared/utils.py`
- `python -m py_compile backend/llm_providers/shared/tool_call_adapter.py backend/services/tool_manager.py backend/llm_providers/openai/service.py backend/llm_providers/gemini/service.py backend/llm_providers/shared/utils.py`

## Risks
- A name conversion moved at the wrong boundary can make forced tools unavailable or cause provider function calls to miss canonical execution routing.
- Gemini function-call history and provider-specific schema restrictions are compatibility-sensitive; the precheck must bind their existing regressions before implementation.
- The local ChromaDB SQLite panic can block normal pytest collection, so precheck must determine whether the focused suites can run with `--noconftest` or require an environment repair handoff.

## Next Skill
`janus-preimplementation-check`
