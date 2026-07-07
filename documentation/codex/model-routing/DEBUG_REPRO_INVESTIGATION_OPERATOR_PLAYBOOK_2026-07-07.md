# Debug Repro Investigation Operator Playbook - 2026-07-07

## Purpose

This playbook turns `TASK-DBG-002` / `debug_repro_investigation` into a repeatable everyday operator pattern for:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

with `2 = Cursor` as the default recommendation for bounded repro, artifact comparison, and smallest-scope debug fixes.

Use this when the lane is already known to be a good fit and the remaining problem is packaging the task cleanly and consistently.

## Current Recommendation

For everyday use of `TASK-DBG-002`:

- prefer `2 = Cursor`
- keep Codex as reviewer, validation owner, and final acceptance owner
- do not treat OpenRouter as the primary path for this lane

This is a bounded debug-worker lane. It is not broad product debugging, not final release-readiness authority, and not a substitute for Codex-owned acceptance.

## When To Use This Lane

Use `debug_repro_investigation` when all of these are true:

- the failure slice is already narrowed
- the worker needs bounded file or tool work
- the editable surface is tiny and explicit
- a focused validation command is obvious up front

Do not use it when:

- only hypothesis ranking is needed
- the task touches security or privacy-sensitive material
- the scope is broad, product-facing, or still ambiguous
- the worker would need authority outside the explicit allowlist

## Required Inputs

The shared gate expects three small artifacts:

1. input package json
2. worker package json
3. allowlist file

Start from these templates:

- `documentation/codex/model-routing/debug-review-fixtures/debug_repro_investigation_cursor_input_template_2026-07-07.json`
- `documentation/codex/model-routing/debug-review-fixtures/debug_repro_investigation_cursor_worker_package_template_2026-07-07.json`
- `documentation/codex/model-routing/debug-review-fixtures/allowlists/debug_repro_investigation_allowlist_template_2026-07-07.txt`

## Packaging Rules

Keep the package shape narrow and explicit:

- one bounded failure code or mismatch description
- one tiny allowlist
- one focused pytest or equivalent check
- one explicit worker prompt
- no product source edits unless the task is explicitly bound that way

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
- `failure_code`
- token-savings estimates
- short `cursor_prompt_contract`

## Recommended Workflow

1. Copy the three templates.
2. Rename them to a task-specific file set.
3. Narrow the allowlist first.
4. Write the worker package against that exact allowlist.
5. Point the input package at the worker package and allowlist.
6. Keep the failure code and prompt tightly aligned to one bounded mismatch.
7. Run the shared gate in prompt mode.
8. Run the shared gate with `2 = Cursor` only after the package is contract-clean.
9. Re-run local validation in Codex.

## Canonical Commands

Prompt gate:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane debug_repro_investigation --task-id TASK-DBG-002 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json <input-package.json> --allowlist-file <allowlist.txt> --estimated-codex-saved-tokens 25000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 8000
```

Live Cursor execution:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane debug_repro_investigation --task-id TASK-DBG-002 --workflow-id <WORKFLOW-ID> --operator-choice 2 --input-package-json <input-package.json> --allowlist-file <allowlist.txt> --estimated-codex-saved-tokens 25000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 8000 --execute-live-cursor
```

## Proven Reference Packages

Current proven shadow example:

- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/input_package.json`
- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/worker_package.json`
- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/allowlist.txt`

These are the best examples to copy when a new bounded debug slice should feel as similar as possible to the already proven path.

## Common Failure Shape

The most likely avoidable failure is package drift:

- the failure slice is described too broadly
- allowlist and `allowed_edit_paths` stop matching
- the debug task quietly widens into product debugging or architecture work

If the gate blocks before invocation, check package shape and scope discipline first before tuning prompts or models.

## Current Decision

Treat this playbook as the everyday packaging standard for real `TASK-DBG-002` Cursor-first bounded debug work.
