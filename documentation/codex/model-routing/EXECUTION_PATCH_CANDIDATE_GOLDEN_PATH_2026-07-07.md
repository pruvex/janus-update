# Execution Patch Candidate Golden Path - 2026-07-07

## Goal

Make `TASK-EX-001` / `execution_patch_candidate` the reference everyday example for:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

with Cursor as the recommended bounded worker for proposal-first execution work.

## Canonical Task

- Task ID: `TASK-EX-001`
- Skill: `janus-executioner`
- Lane: `execution_patch_candidate`
- Recommended backend: `2 = Cursor`
- Recommended model: `composer-2.5`

This lane is for one bounded patch proposal under an explicit allowlist. Codex remains reviewer, accept/reject owner, validation owner, and completion owner.

## Why This Is The Golden Path

`execution_patch_candidate` is the clearest production-shaped version of the delegated coding-worker story:

1. Codex frames one bounded implementation slice.
2. Cursor edits only the allowlisted file set.
3. Cursor works toward the smallest real patch instead of a broad rewrite.
4. Codex reviews the result and decides accept, reject, or local repair.
5. Any apply/validation/final completion stays Codex-owned.

Unlike `TASK-EX-002`, this lane is not deterministic apply. Unlike larger debug or feature work, the scope can stay tiny, explicit, and cheap enough to use as real bounded labor.

## Boundaries

- only the exact allowlisted execution target files may change
- no Git actions
- no release or audit authority
- no delegated final validation or completion claim
- proposal-first remains the safety posture even when the worker is strong

Representative bounded live harness allowlist:

- `development/openrouter-skill-tests/execution_patch_candidate_live_harness/math_utils.py`

Representative validation commands:

```powershell
python -m pytest development/openrouter-skill-tests/execution_patch_candidate_live_harness/test_math_utils.py -q
python -m py_compile development/openrouter-skill-tests/execution_patch_candidate_live_harness/math_utils.py development/openrouter-skill-tests/execution_patch_candidate_live_harness/test_math_utils.py
```

## Operator Entry

Prompt gate:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --task-id TASK-EX-001 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json <input-package.json> --allowlist-file <allowlist.txt> --estimated-codex-saved-tokens 30000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 10000
```

Expected operator choice:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Recommended:

- `2 = Cursor`

OpenRouter remains available as option `3`, but it is not the primary everyday path for this lane.

## Reference Evidence

Primary live proofs:

- `WF-CURSOR-SHADOW-EXEC-PROPOSAL-LIVE-001`
- `WF-CURSOR-SHADOW-EXEC-PROPOSAL-LIVE-002`

Supporting comparison evidence:

- `WF-OPENROUTER-SHADOW-EXEC-PROPOSAL-LIVE-001`
- `WF-OPENROUTER-SHADOW-EXEC-PROPOSAL-LIVE-002`

Evidence these runs established:

- bounded Cursor proposal runs can complete inside the allowlist
- Cursor can return a real useful patch candidate for this lane
- OpenRouter remains viable as option `3`, but current bounded evidence is weaker and less reliable than Cursor for the same lane
- Codex still needs to review and own the final acceptance decision

Representative run artifacts:

- `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-SHADOW-EXEC-PROPOSAL-LIVE-001/dispatcher_result.json`
- `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-SHADOW-EXEC-PROPOSAL-LIVE-002/dispatcher_result.json`
- `documentation/codex/model-routing/execution-direct-or-runs/WF-OPENROUTER-SHADOW-EXEC-PROPOSAL-LIVE-001/validation_summary.json`
- `documentation/codex/model-routing/execution-direct-or-runs/WF-OPENROUTER-SHADOW-EXEC-PROPOSAL-LIVE-002/patch_candidate_result.json`

Everyday packaging references:

- `documentation/codex/model-routing/EXECUTION_PATCH_CANDIDATE_OPERATOR_PLAYBOOK_2026-07-07.md`
- `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_cursor_input_template_2026-07-07.json`
- `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_cursor_worker_package_template_2026-07-07.json`
- `documentation/codex/model-routing/execution-review-fixtures/allowlists/execution_patch_candidate_allowlist_template_2026-07-07.txt`

## Recommended Everyday Use

Use `execution_patch_candidate` when:

- the requested change is one bounded implementation slice
- the editable file set is tiny and explicit
- Codex wants a cheaper worker to draft the coding leg before local review
- the validation surface is still clearly Codex-owned

Do not use it when:

- the slice is too small to beat orchestration overhead
- the task needs broad product reasoning or multi-step architecture work
- the worker would need Git/release/final-accept authority
- the next step is deterministic apply instead of proposal work

## Current Decision

Treat `execution_patch_candidate` as the primary reference lane for `2 = Cursor` in bounded execution work, with OpenRouter preserved as option `3` rather than removed.
