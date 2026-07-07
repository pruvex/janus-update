# Debug Repro Investigation Golden Path - 2026-07-07

## Goal

Make `TASK-DBG-002` / `debug_repro_investigation` the reference everyday example for:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

with Cursor as the recommended bounded worker for repro, artifact comparison, and smallest-scope debug fixes.

## Canonical Task

- Task ID: `TASK-DBG-002`
- Skill: `janus-debug`
- Lane: `debug_repro_investigation`
- Recommended backend: `2 = Cursor`
- Recommended model: `composer-2.5`

This lane is for one bounded debug slice that needs tool/file work under an explicit allowlist.

## Why This Is The Golden Path

`debug_repro_investigation` is the cleanest proven example of the intended delegated debug-worker story:

1. Codex frames one bounded failure slice.
2. Cursor reproduces the mismatch inside allowlisted shadow files only.
3. Cursor makes the smallest bounded correction when needed.
4. Cursor runs the focused validation command.
5. Codex reviews the result and remains final acceptance owner.

Unlike `debug_hypothesis_review`, this lane is allowed to do bounded tool/file work. Unlike broader product debugging, the surface stays fully shadowed and repeatable.

## Boundaries

- only the exact allowlisted shadow debug files may change
- no product source edits
- no Git actions
- no release or audit authority
- no final FIXED/release-readiness claim by the worker

Allowlist:

- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/sandbox/runner_plan_shadow.json`
- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/sandbox/executed_runner_shadow.json`
- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/sandbox/test_debug_repro_shadow.py`

Validation command:

```powershell
python -m pytest documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/sandbox/test_debug_repro_shadow.py -q
```

## Operator Entry

Prompt gate:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane debug_repro_investigation --task-id TASK-DBG-002 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/input_package.json --allowlist-file documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/allowlist.txt --estimated-codex-saved-tokens 25000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 8000
```

Expected operator choice:

- `1 = Codex`
- `2 = Cursor`

Recommended:

- `2 = Cursor`

OpenRouter is not the primary everyday path for this lane; use the shared Cursor-first route for bounded repro work.

## Reference Evidence

Primary live proofs:

- `WF-CURSOR-SHADOW-DEBUG-LIVE-001`
- `WF-CURSOR-SHADOW-DEBUG-LIVE-002`

Supporting readiness proof:

- `development/openrouter-skill-tests/debug_repro_shadow_readiness_2026-07-06.md`

Evidence these runs confirmed:

- bounded live Cursor path completed
- allowlist remained intact
- one run performed the bounded fix
- the later rerun confirmed the mismatch was already resolved
- focused pytest passed after the bounded work

Representative run artifacts:

- `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-SHADOW-DEBUG-LIVE-001/dispatcher_result.json`
- `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-SHADOW-DEBUG-LIVE-002/dispatcher_result.json`
- `development/openrouter-skill-tests/debug_repro_live_smoke_2026-07-06.md`

Everyday packaging references:

- `documentation/codex/model-routing/DEBUG_REPRO_INVESTIGATION_OPERATOR_PLAYBOOK_2026-07-07.md`
- `documentation/codex/model-routing/debug-review-fixtures/debug_repro_investigation_cursor_input_template_2026-07-07.json`
- `documentation/codex/model-routing/debug-review-fixtures/debug_repro_investigation_cursor_worker_package_template_2026-07-07.json`
- `documentation/codex/model-routing/debug-review-fixtures/allowlists/debug_repro_investigation_allowlist_template_2026-07-07.txt`

## Recommended Everyday Use

Use `debug_repro_investigation` when:

- the failure slice is already narrowed
- the worker needs file/tool work, not only hypothesis ranking
- the editable/debuggable surface is tiny and explicit
- Codex wants a bounded cheaper worker to do the repro/fix leg before local review

Do not use it when:

- only hypothesis ranking is needed
- the slice touches security/privacy-sensitive material
- the scope is broad, product-facing, or iteration-5 ambiguous

## Current Decision

Treat `debug_repro_investigation` as the primary reference lane for `2 = Cursor` in bounded debug work.
