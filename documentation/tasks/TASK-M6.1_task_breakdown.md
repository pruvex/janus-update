# TASK BREAKDOWN - TASK-M6.1

## Binding Sources
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Section 3.4, Phase A `T-A1`)
- Parent Task: `documentation/tasks/TASK-M6_transport_phase_a.md`
- Backlog Item: `N/A` - roadmap/spec-driven infrastructure slice
- Source Import: byte-identical local import from the prior worktree, SHA-256 `ED7CC8B9C198629B6E6E1839D5109C97DAADEF6A8AE000338AA2B64B6C370CB4`

## Released Target
- Target Task: `TASK-M6.1`
- Title: Unify the model hierarchy as the single MoA source
- Execution Model: `5.6 Terra`, `medium`
- Readiness: `PRECHECK_READY`

## Atomic Scope
- Make `MOA_MODEL_HIERARCHY` in `backend/llm_providers/shared/moa.py` the sole runtime model-tier source for the bound paths.
- Remove or migrate the duplicate hierarchy use in `backend/services/chat_orchestrator.py`.
- Migrate the bound Gemini gateway consumer in `backend/llm_providers/gemini/gateway.py` without tier-semantic drift.
- Add `backend/tests/test_model_hierarchy_single_source.py` to guard against a second runtime model hierarchy.

## Explicit Exclusions
- No `ToolCallAdapter`, `ToolLoopRunner`, gateway loop extraction, streaming migration, transport classes, runtime resolver, OAuth, OpenRouter, websearch refactor, or feature-flag flip.
- No Phase-A task beyond `T-A1`; `TASK-M6.2` through `TASK-M6.5` require separate prechecks.
- No architecture changes beyond the binding Spec decision that `MOA_MODEL_HIERARCHY` is the single source.

## Acceptance And Tests
- The bound OpenAI and Gemini consumers resolve tiers from `MOA_MODEL_HIERARCHY`.
- No duplicate runtime hierarchy remains in the bound orchestrator path.
- The new drift regression passes.
- Precheck must select focused existing hierarchy/gateway regressions and confirm flag/default behavior is unaffected.
- Required baseline commands:
  - `python -m pytest backend/tests/test_model_hierarchy_single_source.py -q`
  - focused existing hierarchy/gateway regressions selected by precheck
  - `python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py`

## Risks
- Model-tier drift can silently alter provider selection or fallback behavior.
- The precheck must inspect every bound hierarchy consumer before implementation and block if another source-of-truth remains outside this scope.

## Next Skill
`janus-preimplementation-check`
