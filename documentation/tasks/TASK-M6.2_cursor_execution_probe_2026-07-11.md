# TASK-M6.2 Cursor Execution Probe - 2026-07-11

Canonical State: PASS WITH FALLBACK NOTE
Target Task: TASK-M6.2

## Goal

Collect bounded Cursor Composer execution evidence for the prechecked ToolCallAdapter slice while retaining Codex review, validation, and acceptance ownership.

## Boundaries

- Proposal-first Cursor execution only; no delegated Git, release, audit, or final task-completion authority.
- Exact allowlist: the M6.2 adapter, its direct OpenAI/Gemini/ToolManager/prevalidation consumers, and focused tests.
- No ToolLoopRunner, transport classes, runtime resolver, streaming, OAuth, OpenRouter product work, or provider-policy change.

## Evidence

- `WF-M6.2-EXECUTION-GATE-2026-07-11-001`: shared delegate failed before agent startup because it passed unsupported `--cursor-pool auto_composer` to `janus_cursor_worker_runner.py` (`CURSOR_WORKER_OUTPUT_UNREADABLE`).
- `WF-M6.2-EXECUTION-GATE-2026-07-11-002`: direct worker with the outer input package blocked because that runner validated the wrapper package instead of its referenced worker package (`CURSOR_WORKER_INPUT_BLOCKED`).
- `WF-M6.2-EXECUTION-GATE-2026-07-11-003`: direct worker with the valid worker package passed package and allowlist validation, started Cursor Composer, then timed out after 180 seconds without structured output (`CURSOR_AGENT_TIMEOUT`).
- The timed-out Cursor process nevertheless left only allowlisted M6.2 source/test changes. Codex reviewed the diff, completed two bounded adapter compatibility corrections, and ran the focused validation listed in `TASK-M6.2_execution_result.md`.

## Result

- Cursor is proven to start in the bounded M6.2 proposal-first lane after the worker-package contract is used directly.
- The current shared delegate and outer-package consumption paths are not yet productive because of two wrapper integration defects.
- The live Composer run is not accepted as an autonomous completion because it timed out without structured worker artifacts or self-reported checks.
- The reviewed code is accepted only on Codex-owned validation evidence.

## Next Improvement

Route the shared delegate/worker contract mismatch and the Composer timeout behavior to a bounded Cursor-infrastructure debug slice. Do not treat this evidence as permission for unreviewed Cursor write authority.
