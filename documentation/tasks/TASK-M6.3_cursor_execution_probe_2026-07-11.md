# TASK-M6.3 Cursor Execution Probe - 2026-07-11

Canonical State: PASS WITH FALLBACK NOTE
Target Task: TASK-M6.3

## Goal

Collect bounded Cursor Composer execution evidence for the prechecked OpenAI ToolLoopRunner extraction while retaining Codex review, validation, and acceptance ownership.

## Boundaries

- Proposal-first Cursor execution only; no delegated Git, release, audit, or final task-completion authority.
- Exact allowlist: `tool_loop_runner.py`, the OpenAI gateway, the focused runner test, and the bound OpenAI routing regression.
- No Gemini migration, streaming, transport classes, runtime resolver, OAuth, OpenRouter product work, ToolCallAdapter change, provider-policy change, or MoA hierarchy change.

## Evidence

- `WF-M6.3-EXECUTION-GATE-2026-07-11-001`: the shared delegate failed before agent startup because it passed unsupported `--cursor-pool auto_composer` to `janus_cursor_worker_runner.py` (`CURSOR_WORKER_OUTPUT_UNREADABLE`).
- `WF-M6.3-EXECUTION-GATE-2026-07-11-002`: the direct worker used the valid inner `worker_package.json`; package and allowlist validation passed and Cursor Composer started, then timed out after 180 seconds without structured result artifacts (`CURSOR_AGENT_TIMEOUT`).
- The timed-out Composer process left only allowlisted runner, gateway, and focused-test changes. Codex reviewed the candidate, kept the default-off gateway dispatch, and made bounded testability corrections so the runner defers heavy shared-utility imports until a real flag-on run.

## Result

- Cursor Composer is proven to start in the bounded M6.3 proposal-first lane after the worker-package contract is used directly.
- The shared delegate/worker wrapper remains unproductive because of the unsupported argument, and the direct Composer run remains unaccepted because it timed out without structured output or self-reported checks.
- The reviewed M6.3 result is accepted only on Codex-owned focused regression, syntax, and scope evidence.

## Next Improvement

Route the shared delegate/worker argument mismatch and Composer structured-output timeout to one bounded Cursor-infrastructure debug slice. Do not treat this evidence as permission for unreviewed Cursor write authority.
