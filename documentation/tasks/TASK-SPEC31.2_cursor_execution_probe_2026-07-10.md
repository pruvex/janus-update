# TASK-SPEC31.2 Cursor Execution Probe - 2026-07-10

Canonical State: PASS WITH FALLBACK NOTE
Target Task: TASK-SPEC31.2

## Goal

Collect real Cursor-first execution evidence for the bounded `janus-executioner` hardening slice before Codex-owned review/apply and local validation.

## Bound Package

- Input package: `development/openrouter-skill-tests/janus-executioner/spec31_2_routine_reuse_hardening_2026-07-10/input_package.json`
- Worker package: `development/openrouter-skill-tests/janus-executioner/spec31_2_routine_reuse_hardening_2026-07-10/worker_package.json`
- Allowlist: `development/openrouter-skill-tests/janus-executioner/spec31_2_routine_reuse_hardening_2026-07-10/allowlist.txt`

## Execution Evidence

1. Shared prompt gate PASS
   - Command:
     - `python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --workflow-id WF-SPEC31.2-EXEC-PATCH-2026-07-10-001 --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-executioner/spec31_2_routine_reuse_hardening_2026-07-10/input_package.json --allowlist-file development/openrouter-skill-tests/janus-executioner/spec31_2_routine_reuse_hardening_2026-07-10/allowlist.txt --estimated-codex-saved-tokens 15000 --estimated-delegation-overhead-tokens 4500`
   - Result:
     - positive ROI
     - visible choices: `1 = Codex`, `2 = OpenRouter`, `3 = Cursor Composer`, `4 = Cursor API`
     - recommendation: `3 = Cursor Composer`

2. Cursor Composer live run BLOCKED
   - Command:
     - `python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --workflow-id WF-SPEC31.2-EXEC-PATCH-2026-07-10-001 --operator-choice 3 --input-package-json development/openrouter-skill-tests/janus-executioner/spec31_2_routine_reuse_hardening_2026-07-10/input_package.json --allowlist-file development/openrouter-skill-tests/janus-executioner/spec31_2_routine_reuse_hardening_2026-07-10/allowlist.txt --estimated-codex-saved-tokens 15000 --estimated-delegation-overhead-tokens 4500 --execute-live-cursor`
   - Result:
     - `validation_result = BLOCKED`
     - `final_outcome = CURSOR_AGENT_TIMEOUT`
     - package validation PASS
     - allowlist validation PASS
     - evidence path:
       - `documentation/codex/model-routing/cursor-worker-runs/WF-SPEC31.2-EXEC-PATCH-2026-07-10-001/dispatcher_result.json`

3. Cursor API live fallback exposed runner-output decode failure
   - Command:
     - `python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --workflow-id WF-SPEC31.2-EXEC-PATCH-2026-07-10-002 --operator-choice 4 --input-package-json development/openrouter-skill-tests/janus-executioner/spec31_2_routine_reuse_hardening_2026-07-10/input_package.json --allowlist-file development/openrouter-skill-tests/janus-executioner/spec31_2_routine_reuse_hardening_2026-07-10/allowlist.txt --estimated-codex-saved-tokens 15000 --estimated-delegation-overhead-tokens 4500 --execute-live-cursor`
   - Result:
     - final outcome surfaced to operator as `CURSOR_WORKER_OUTPUT_UNREADABLE`
     - no usable worker patch payload was produced
     - run directory was created but no reviewable `dispatcher_result.json` artifact was persisted under:
       - `documentation/codex/model-routing/cursor-worker-runs/WF-SPEC31.2-EXEC-PATCH-2026-07-10-002/`
     - local evidence suggests a `cp1252` / `None stdout` handling weakness in `documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py`

4. Codex local fallback completed the bounded slice
   - Result:
     - Codex reviewed the live Cursor probe evidence
     - Codex implemented only the bounded runtime hardening and focused tests locally
     - local validation finished green before documentation closeout

## Interpretation

- Cursor-first evidence was still successfully captured for this slice:
  - the shared execution gate stayed healthy
  - the operator-facing recommendation correctly preferred Cursor
  - both live Cursor paths produced useful operational evidence instead of being silently skipped
- The delegated worker did not deliver a usable patch this time, so Codex completed the bounded product change locally after the probe:
  - Composer timed out under the bounded live window
  - Cursor API fallback hit a worker-runner output parsing failure before a reviewable artifact could be produced

## Recommended Use

- Keep this probe artifact bound to `TASK-SPEC31.2_execution_result.md`.
- Treat the Cursor failures as execution-lane evidence, not as a product blocker for `TASK-SPEC31.2`.
- Capture the worker-runner decode issue later as a separate Lean-Dev follow-up if it recurs or becomes a throughput bottleneck.
