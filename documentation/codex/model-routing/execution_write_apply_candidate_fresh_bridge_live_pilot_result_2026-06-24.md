# execution_write_apply_candidate Fresh Bridge Live Pilot Result - 2026-06-24

Canonical state: `HANDOFF`
Workflow: `EXEC-WRITE-APPLY-LIVE-PILOT-002`
Target task: `BACKLOG-108`

## Summary

One real bounded `execution_write_apply_candidate` live pilot was run against fresh accepted-source bridge `EXEC-WRITE-APPLY-SOURCE-BRIDGE-002`.

The sidecar run itself completed and reported:

- `Apply succeeded`
- changed file: `backend/services/contact_manager.py`
- blocker: none

But the bounded runner still classified the pilot as:

- `validation_result`: `FAIL`
- `final_outcome`: `EXECUTION_WRITE_APPLY_LIVE_WRITE_REJECT_AND_FALLBACK`

## What Passed

- accepted-source validation: `PASS`
- source snapshots: `PASS`
- escalated sidecar launch: `PASS`
- sidecar process exit code: `0`
- sidecar summary status: `PASS`
- allowlist check: `PASS`
- touched-file-cap check: `PASS`
- delete/rename/move check: `PASS`
- last message present: `PASS`

## Why The Pilot Still Failed

The bounded live validation failed on three validator seams:

1. `artifact_success` in sidecar `summary.json` remained `false` even though the sidecar status was `PASS` and the last message reported `Apply succeeded`.
2. `touched_files` was emitted as a single string (`backend/services/contact_manager.py`) instead of the list shape expected by the live validator.
3. `pre_run_status` and `post_run_status` were both `M backend/services/contact_manager.py`, so the validator treated the run as unchanged even though this was a pre-dirtied working-tree file and the sidecar still reported a successful bounded apply.

## Interpretation

This is not evidence that fresh bridge `002` is stale.

This is also not evidence of an allowlist escape or broad write failure.

The failure seam is the bounded live validator contract for already-dirty files and sidecar artifact normalization, not the accepted-source bridge itself.

## Key Artifacts

- runner summary:
  - `documentation/codex/model-routing/execution-write-apply-runs/EXEC-WRITE-APPLY-LIVE-PILOT-002/operator_summary.json`
- live validation:
  - `documentation/codex/model-routing/execution-write-apply-runs/EXEC-WRITE-APPLY-LIVE-PILOT-002/live_validation_summary.json`
- sidecar summary:
  - `documentation/codex/model-routing/execution-write-apply-runs/EXEC-WRITE-APPLY-LIVE-PILOT-002/sidecar_run/summary.json`
- sidecar validation:
  - `documentation/codex/model-routing/execution-write-apply-runs/EXEC-WRITE-APPLY-LIVE-PILOT-002/sidecar_run/validation_summary.json`
- sidecar last message:
  - `documentation/codex/model-routing/execution-write-apply-runs/EXEC-WRITE-APPLY-LIVE-PILOT-002/sidecar_run/last_message.md`

## Cost Note

This path ran through `Codex CLI sidecar / gpt-5.4`.

- actual OR cost: `N/A`
- generation id: `N/A`

The pilot does not produce OpenRouter usage/cost telemetry because this derivative write lane is currently executed through the Codex sidecar runtime, not a direct OR API call.

## Next Recommended Step

Route to `janus-debug` for one tight validator-contract repair:

- normalize sidecar `touched_files` into list form before comparison
- treat already-dirty target files as valid when bounded apply evidence exists
- align `artifact_success` with successful bounded apply on the live write lane

Do not retry another live write pilot until this validator seam is repaired.
