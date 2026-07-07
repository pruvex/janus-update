# Test Fixture Worker Operator Playbook - 2026-07-07

## Purpose

This playbook turns `TASK-TP-003` / `test_fixture_worker` into a repeatable everyday operator pattern for:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

with `2 = Cursor` as the default recommendation for bounded fixture/test-helper work.

Use this when the lane is already known to be a good fit and the remaining problem is packaging the task cleanly and consistently.

## Current Recommendation

For everyday use of `TASK-TP-003`:

- prefer `2 = Cursor`
- keep `3 = OpenRouter` available but secondary
- keep Codex as reviewer, validation owner, and final acceptance owner

This is a bounded worker lane for fixture/test-helper shaping. It is not live Playwright authority, not provider execution authority, and not final release-readiness delegation.

## When To Use This Lane

Use `test_fixture_worker` when all of these are true:

- the requested work is fixture or test-helper scoped
- the editable file set is tiny and explicit
- a focused validation command is obvious up front
- Codex review after the worker run is still the intended trust boundary

Do not use it when:

- the task is really a broader debug investigation
- the worker would need to touch product code
- the task depends on live provider or Playwright execution
- the scope is large enough that fixture authoring stops being the real unit of work

## Required Inputs

The shared gate expects three small artifacts:

1. input package json
2. worker package json
3. allowlist file

Start from these templates:

- `documentation/codex/model-routing/test-fixture-review-fixtures/test_fixture_worker_cursor_input_template_2026-07-07.json`
- `documentation/codex/model-routing/test-fixture-review-fixtures/test_fixture_worker_cursor_worker_package_template_2026-07-07.json`
- `documentation/codex/model-routing/test-fixture-review-fixtures/allowlists/test_fixture_worker_allowlist_template_2026-07-07.txt`

## Packaging Rules

Keep the package shape narrow and explicit:

- one or two fixture/test files
- one focused pytest command when possible
- one explicit worker prompt
- one allowlist that exactly matches `allowed_edit_paths`
- no product source changes
- no Git, release, auth, or architecture authority

The worker package should carry the real edit contract:

- `task_label`
- `worker_profile`
- `allowed_edit_paths`
- `acceptance_criteria`
- `checks`
- `forbidden_actions`
- `requested_actions`
- `task_prompt`

The thin input package should point to the worker package and carry the lane-facing metadata:

- `task_id`
- `lane_id`
- `bound_skill_context`
- `worker_package_json`
- `allowlist_file`
- token-savings estimates
- short `cursor_prompt_contract`

## Recommended Workflow

1. Copy the three templates.
2. Rename them to a task-specific file set.
3. Narrow the allowlist first.
4. Write the worker package against that exact allowlist.
5. Point the input package at the worker package and allowlist.
6. Confirm that the task is still fixture/test-helper scoped and not drifting into product code.
7. Run the shared gate in prompt mode.
8. Run the shared gate with `2 = Cursor` only after the package is contract-clean.
9. Re-run local validation in Codex.

## Canonical Commands

Prompt gate:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane test_fixture_worker --task-id TASK-TP-003 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json <input-package.json> --allowlist-file <allowlist.txt> --estimated-codex-saved-tokens 30000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 8000
```

Live Cursor execution:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane test_fixture_worker --task-id TASK-TP-003 --workflow-id <WORKFLOW-ID> --operator-choice 2 --input-package-json <input-package.json> --allowlist-file <allowlist.txt> --estimated-codex-saved-tokens 30000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 8000 --execute-live-cursor
```

## Proven Reference Packages

Current proven shadow-eval example:

- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/test_fixture_worker/input_package.json`
- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/test_fixture_worker/worker_package.json`
- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/test_fixture_worker/allowlist.txt`

These are the best examples to copy when a new bounded fixture/test-helper task should feel as similar as possible to the already proven path.

## Common Failure Shape

The most likely avoidable failure is package drift:

- allowlist and `allowed_edit_paths` stop matching
- fixture work drifts into product code
- the worker package becomes too vague about checks and scope

If the gate blocks before invocation, check package shape and scope discipline first before tuning prompts or models.

## Current Decision

Treat this playbook as the everyday packaging standard for real `TASK-TP-003` Cursor-first fixture/test-helper delegation work.
