# Test Fixture Worker Golden Path - 2026-07-06

## Goal

Make `TASK-TP-003` / `test_fixture_worker` the reference everyday example for:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

with Cursor as the recommended bounded worker for fixture/test-helper work.

## Canonical Task

- Task ID: `TASK-TP-003`
- Skill: `janus-test-pipeline`
- Lane: `test_fixture_worker`
- Recommended backend: `2 = Cursor`
- Recommended model: `composer-2.5`

This lane is for bounded fixture/helper authoring plus focused allowlisted validation before any live Playwright or provider test execution.

## Why This Is The Golden Path

`test_fixture_worker` is the cleanest proven example of the intended delegated-worker story:

1. Codex frames a bounded task package.
2. Cursor edits only allowlisted test-fixture files.
3. Cursor runs only the focused validation command.
4. Codex reviews the result and remains final acceptance owner.

Unlike `TASK-EX-002`, this lane is a good fit for a tool-capable agent because the work is not deterministic apply. Unlike broader debug lanes, the scope is narrow and repeatable.

## Boundaries

- only the exact allowlisted shadow-eval fixture files may change
- no product source edits
- no Git actions
- no release or audit authority
- no final PASS/release-readiness claim by the worker

Allowlist:

- `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/fixtures/contact_memory_fixture.json`
- `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/tests/test_contact_memory_fixture.py`

Validation command:

```powershell
python -m pytest development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/tests/test_contact_memory_fixture.py -q
```

## Operator Entry

Prompt gate:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane test_fixture_worker --task-id TASK-TP-003 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json documentation/codex/model-routing/fixtures/cursor-shadow-catalog/test_fixture_worker/input_package.json --allowlist-file documentation/codex/model-routing/fixtures/cursor-shadow-catalog/test_fixture_worker/allowlist.txt --estimated-codex-saved-tokens 30000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 8000
```

Expected operator choice:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Recommended:

- `2 = Cursor`

## Reference Evidence

Primary live proofs:

- `WF-CURSOR-LIVE-SMOKE-003`
- `WF-CURSOR-SHADOW-TEST-LIVE-001`
- `WF-CURSOR-SHADOW-TEST-LIVE-002`

Evidence each run confirmed:

- bounded live Cursor path completed
- changed files stayed inside the exact allowlist
- final outcome was `CURSOR_WORKER_READY_FOR_CODEX_REVIEW`
- focused pytest passed after the bounded edit

Representative run artifacts:

- `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-LIVE-SMOKE-003/dispatcher_result.json`
- `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-SHADOW-TEST-LIVE-001/dispatcher_result.json`
- `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-SHADOW-TEST-LIVE-002/dispatcher_result.json`

Everyday packaging references:

- `documentation/codex/model-routing/TEST_FIXTURE_WORKER_OPERATOR_PLAYBOOK_2026-07-07.md`
- `documentation/codex/model-routing/test-fixture-review-fixtures/test_fixture_worker_cursor_input_template_2026-07-07.json`
- `documentation/codex/model-routing/test-fixture-review-fixtures/test_fixture_worker_cursor_worker_package_template_2026-07-07.json`
- `documentation/codex/model-routing/test-fixture-review-fixtures/allowlists/test_fixture_worker_allowlist_template_2026-07-07.txt`

## Recommended Everyday Use

Use `test_fixture_worker` when:

- the requested work is fixture/test-helper scoped
- the file set is small and explicit
- the validation command is focused and cheap
- Codex wants a cheaper worker to do the bounded test-writing leg

Do not use it when:

- the task needs live Playwright/provider execution
- the task drifts into product code or broad refactors
- the scope becomes a debug investigation instead of fixture shaping

## Current Decision

Treat `test_fixture_worker` as the primary reference lane for `2 = Cursor` in the test pipeline.
