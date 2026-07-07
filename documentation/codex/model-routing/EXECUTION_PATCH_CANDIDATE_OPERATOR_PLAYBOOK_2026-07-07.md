# Execution Patch Candidate Operator Playbook - 2026-07-07

## Purpose

This playbook turns `TASK-EX-001` / `execution_patch_candidate` into a repeatable everyday operator pattern for:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

with `2 = Cursor` as the default recommendation for real bounded coding labor.

Use this when the lane is already known to be a good fit and the remaining problem is packaging the task cleanly and consistently.

## Current Recommendation

For everyday use of `TASK-EX-001`:

- prefer `2 = Cursor`
- keep `3 = OpenRouter` available but secondary
- keep Codex as reviewer, accept/reject owner, validation owner, and completion owner

This is a proposal-first lane. It is not autonomous apply, not Git authority, and not final validation delegation.

## When To Use This Lane

Use `execution_patch_candidate` when all of these are true:

- exactly one bounded implementation slice is in scope
- the editable file set is tiny and explicit
- you can state a focused validation command up front
- Codex review after the worker run is still the intended trust boundary

Do not use it when:

- the scope is still fuzzy
- the worker would need to touch many files
- the task depends on broad architectural judgment
- you actually need deterministic apply rather than proposal work

## Required Inputs

The shared gate expects three small artifacts:

1. input package json
2. worker package json
3. allowlist file

Start from these templates:

- `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_cursor_input_template_2026-07-07.json`
- `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_cursor_worker_package_template_2026-07-07.json`
- `documentation/codex/model-routing/execution-review-fixtures/allowlists/execution_patch_candidate_allowlist_template_2026-07-07.txt`

## Packaging Rules

Keep the package shape boring and strict:

- one target source file when possible, two only when clearly necessary
- one focused pytest or equivalent check
- one explicit worker prompt
- one allowlist that exactly matches `allowed_edit_paths`
- no placeholders that widen authority like Git, release, auth, or architecture changes

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
6. Intentionally confirm the target check is red before live delegation when you are proving a new real harness.
7. Run the shared gate in prompt mode.
8. Run the shared gate with `2 = Cursor` only after the package is contract-clean.
9. Re-run local validation in Codex.

## Canonical Commands

Prompt gate:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --task-id TASK-EX-001 --workflow-id <WORKFLOW-ID> --operator-choice prompt --input-package-json <input-package.json> --allowlist-file <allowlist.txt> --estimated-codex-saved-tokens 25000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 10000
```

Live Cursor execution:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --task-id TASK-EX-001 --workflow-id <WORKFLOW-ID> --operator-choice 2 --input-package-json <input-package.json> --allowlist-file <allowlist.txt> --estimated-codex-saved-tokens 25000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 10000 --execute-live-cursor
```

## Proven Reference Packages

Current proven repo-bound examples:

- clamp harness:
  - `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_live_harness_cursor_input_package_2026-07-07.json`
  - `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_live_harness_cursor_worker_package_2026-07-07.json`
  - `documentation/codex/model-routing/execution-review-fixtures/allowlists/execution_patch_candidate_live_harness_allowlist_2026-07-07.txt`
- text utils harness:
  - `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_text_utils_cursor_input_package_2026-07-07.json`
  - `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_text_utils_cursor_worker_package_2026-07-07.json`
  - `documentation/codex/model-routing/execution-review-fixtures/allowlists/execution_patch_candidate_text_utils_allowlist_2026-07-07.txt`

These are the best examples to copy when a new real bounded execution slice should feel as similar as possible to the already proven path.

## Common Failure Shape

The most likely avoidable failure is not the model itself but package drift:

- legacy execution-style input package
- worker runner expecting the stricter worker package contract
- allowlist and `allowed_edit_paths` no longer matching exactly

If the gate blocks before invocation, check package shape first before tuning prompts or models.

## Current Decision

Treat this playbook as the everyday packaging standard for real `TASK-EX-001` Cursor-first delegation work.
