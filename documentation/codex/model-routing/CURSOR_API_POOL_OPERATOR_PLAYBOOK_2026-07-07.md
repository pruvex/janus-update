# Cursor API Pool Operator Playbook

## Goal

Keep the 4-choice delegation gate cheap, predictable, and cache-friendly without adding a second Cursor runner.

## Operator truth

- `1 = Codex`
- `2 = OpenRouter`
- `3 = Cursor Composer`
- `4 = Cursor API`

Options `3` and `4` both route through `documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py`.

## Cache convention

Worker prompts should stay in two blocks:

1. `Stable prefix`
   - lane
   - `janus-delegated-worker` contract
   - output schema
   - hard rules
2. `Variable suffix`
   - bounded task statement
   - allowlisted paths
   - acceptance criteria
   - focused validation command
   - accepted-source summary when present

This keeps retries and adjacent tasks cache-friendly while still letting the task-specific tail change.

## Pool usage

- Use `3 = Cursor Composer` for tool lanes and longer proposal loops.
- Use `4 = Cursor API` for bounded assist/review slices or explicit API-pool tests.
- Keep `2 = OpenRouter` as fallback, not as removed legacy behavior.

## Retry posture

- Prefer the stored `session_id` on retries.
- Do not resend long handoff essays.
- Keep packages compact and lane-bounded.

## Non-goals

- No dashboard polling
- No usage prediction service
- No second Cursor backend
- No production routing activation
