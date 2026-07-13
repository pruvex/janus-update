# TASK-M6 MASTER INTEGRATION

- Source Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`
- Supporting Evidence: `documentation/tasks/TASK-M6_AGGREGATE_FINAL_AUDIT.md`; `documentation/tasks/CURSOR_M6_TOTAL_REVIEW_HANDOFF.md`; `documentation/ai/CURRENT_STATE.md`.
- Backlog Item: `N/A` - delivery integration for approved M6 scope.
- Feature: merge validated M6 transport refactor into current `master` without losing newer master behavior.
- Generated At: 2026-07-13.

## Generated Tasks

### TASK-M6.MERGE.1 - Resolve M6-to-master integration conflicts

- Goal:
  - Integrate `codex/m6-transport-prep` into the current `master` while preserving both the validated M6 transport contracts and the newer master behavior represented by the conflict side.
- Scope:
  - Resolve only the conflict set reported by the failed `git merge --no-ff codex/m6-transport-prep` attempt from `master`.
  - Preserve M6 outcomes: provider-boundary isolation, canonical tool IDs, default-off transport behavior, C1 Websearch boundary, C2 response postprocessors, C4 parity coverage, and C3 as documented debt.
  - Preserve newer master contracts; do not use a global `ours` or `theirs` resolution and do not discard master-only features.
  - Do not widen into C3 deletion, OpenRouter/Codex rollout, new provider behavior, release/version changes, or the unrelated Ollama worktree branch.
- Files:
  - `CHANGELOG.md`
  - `PROJECT_STATE.md`
  - `WHAT_I_LEARNED.md`
  - `backend/data/schemas_intent.py`
  - `backend/tests/test_agent_factory_runtime.py`
  - `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`
  - `documentation/ai/CURRENT_STATE.md`
  - `documentation/codex/SKILL_USAGE_LOG.md`
  - `documentation/codex/model-routing/cursor_delegation_log.jsonl`
- Steps:
  1. Reproduce the merge in a clean integration worktree or temporary branch and inspect each conflict hunk against merge base, current master, and M6 feature sides.
  2. Resolve documentation conflicts by retaining newer master entries and appending or merging the M6 closure evidence without duplicate or contradictory status claims.
  3. Resolve `schemas_intent.py` and `test_agent_factory_runtime.py` hunk-by-hunk so master intent/runtime contracts and M6 imports/tests remain valid.
  4. Resolve the M6 source Spec conflict without altering approved M6 scope or claiming C3 deletion.
  5. Run the bound regression matrix and a scoped diff review before accepting the merge result.
- Acceptance Criteria:
  - A merge of current `master` and `codex/m6-transport-prep` completes without conflict markers.
  - No conflict file uses a global side-selection shortcut; both relevant contracts are represented or an explicit evidence-backed rejection is recorded.
  - All M6 aggregate evidence remains accurate: Phase-B `63 passed`, C1 `111 passed, 6 deselected`, C2 `24 passed`, C4 `14 passed`, Cursor re-review PASS.
  - `schemas_intent.py` imports and `test_agent_factory_runtime.py` execute under the merged tree.
  - `CURRENT_STATE`, registry-facing documentation, changelog, and skill/delegation logs contain no contradictory duplicate closure claims.
  - Root checkout is updated only after its unrelated `feature/ollama-dev-workhorse` work is cleanly preserved or explicitly handled outside this task.
- Tests:
  - `python -m pytest backend/tests/test_agent_factory_runtime.py -q`
  - M6 focused matrix: `backend/tests/test_provider_parity.py`, `backend/tests/test_tool_call_adapter.py`, `backend/tests/test_response_postprocessors.py`, `backend/tests/test_transport_layer_openai_gateway.py`, `backend/tests/test_transport_layer_gemini_gateway.py`, `backend/tests/test_transport_layer_ollama_gateway.py`, and `backend/tests/tools/test_websearch.py` with selections preserved by precheck.
  - `python -m py_compile backend/data/schemas_intent.py`
  - `git diff --check` and conflict-marker scan over the nine-file conflict set.
- Execution Model: 5.6 Terra/high.
- Reason:
  - M6 is final-audited and externally reviewed PASS, but the delivery merge is blocked by a concrete, reproducible master divergence. This task is integration-only and preserves, rather than extends, approved behavior.
