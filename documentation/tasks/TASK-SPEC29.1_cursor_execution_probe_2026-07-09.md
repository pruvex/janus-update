# TASK-SPEC29.1 Cursor Execution Probe

- Date: `2026-07-09`
- Target Task: `TASK-SPEC29.1`
- Spec: `documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md`
- Task File: `documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md`
- Precheck: `documentation/tasks/TASK-SPEC29.1_preimplementation_check.md`
- Workflow Gate:
  - prompt gate: `WF-SPEC29-1-EXEC-GATE-2026-07-09-001`
  - Cursor API live run: `WF-SPEC29-1-EXEC-GATE-2026-07-09-002`
  - Cursor Composer live run: `WF-SPEC29-1-EXEC-GATE-2026-07-09-003`

## Purpose

Document the real Cursor-first execution evidence for the bounded `TASK-SPEC29.1` slice before any local Codex implementation. This artifact exists so the team can revisit Cursor packaging and timeout behavior later without relying on chat history.

## Gate Summary

- Shared execution gate lane: `execution_patch_candidate`
- Visible operator choices:
  - `1 = Codex`
  - `2 = OpenRouter`
  - `3 = Cursor Composer`
  - `4 = Cursor API`
- Recommendation from gate: `1 = Codex`
- ROI status: `NEGATIVE`
- Visibility policy: `keep_visible_non_recommended`
- Reason visibility still matters: bounded write-capable external options remain visible as fallback capacity and evidence targets even when they are not the cost-optimized recommendation.

## Cursor API Result

- Choice used: `4 = Cursor API`
- Workflow: `WF-SPEC29-1-EXEC-GATE-2026-07-09-002`
- Result: transport/live path worked and returned a session id, but no reviewable patch artifacts were produced.
- Session id: `ebd644f6-bb14-409b-93b7-ad9d76384609`
- Final outcome reported by dispatcher: `CURSOR_WORKER_READY_FOR_CODEX_REVIEW`
- Actual worker message:
  - The worker responded that the real delegated task prompt/instructions were missing and asked for the full prompt to be pasted.
- Artifact reality:
  - expected files such as `RESULT.md`, `DIFF.patch`, and `FILES_CHANGED.txt` were not materialized
  - `changed_files.txt` remained empty
- Interpretation:
  - the shared delegate and Cursor API transport are alive for this slice
  - the current packaging/prompt handoff into the Cursor API worker is not semantically sufficient for productive patch generation on this task

## Cursor Composer Result

- Choice used: `3 = Cursor Composer`
- Workflow: `WF-SPEC29-1-EXEC-GATE-2026-07-09-003`
- Result: timeout at the invocation level
- Exit behavior:
  - the call timed out after about `124` seconds
  - no stable run directory artifacts were materialized under the expected workflow id
- Interpretation:
  - Cursor Composer was not productively usable for this bounded slice in the current run
  - the failure mode is currently a timeout/no-artifact problem, not a patch-quality problem

## Operational Conclusion

- Cursor was tried first in a real bounded execution lane, so the evidence goal for this slice was honored.
- For `TASK-SPEC29.1`, Cursor is currently not productive enough to replace local Codex execution:
  - Cursor API: transport PASS, semantic packaging FAIL
  - Cursor Composer: timeout / no-artifact FAIL
- Recommended follow-up for later hardening:
  - inspect why the worker still perceives the delegated prompt as missing even though the planned command includes a long inline task payload
  - compare this package shape against known successful Cursor Composer runs such as the semantic routine reuse slice
  - decide whether the fix belongs in worker package generation, prompt framing, or timeout policy

## Evidence Paths

- `documentation/codex/model-routing/cursor-worker-runs/WF-SPEC29-1-EXEC-GATE-2026-07-09-002/dispatcher_result.json`
- `documentation/codex/model-routing/cursor-worker-runs/WF-SPEC29-1-EXEC-GATE-2026-07-09-002/cursor_response.json`
- `documentation/codex/model-routing/cursor-worker-runs/WF-SPEC29-1-EXEC-GATE-2026-07-09-002/stdout.log`
- `documentation/codex/model-routing/cursor_delegation_log.jsonl`

## Current Execution Decision

- Keep this artifact as a blocker/evidence note.
- Continue the actual product implementation for `TASK-SPEC29.1` locally in Codex unless a dedicated Cursor-lane debug slice is explicitly chosen next.
