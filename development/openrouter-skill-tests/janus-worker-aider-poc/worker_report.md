# Worker Report

## POC Summary

- Worker: `aider 0.86.2`
- Model: `openrouter/qwen/qwen3-coder-30b-a3b-instruct`
- Scope: docs-only sandbox in `development/openrouter-skill-tests/janus-worker-aider-poc/`
- Target file edited by worker: `target_doc.md`

## What worked

- The worker accepted a task from `worker_task.md`.
- The worker improved the structure and wording of `target_doc.md`.
- The final edited content stayed semantically aligned with the original rough notes.
- The sandbox files remained isolated enough to review the result cleanly.

## What did not work cleanly

- Aider scanned the full repository even though the real task was tiny.
- Aider attempted an out-of-scope `.gitignore` change by adding `.aider*`.
- Aider created local `.aider` side artifacts in the repo root.
- Codex had to remove the out-of-scope repo side effects after the run.

## Practical verdict

Conditional Go.

This is promising enough to justify a future small real Janus worker test, but not as a direct root-repo everyday workflow yet.

## Conditions before a real small Janus task

- Run the worker in an isolated sandbox, subtree, or dedicated worktree instead of the noisy repo root.
- Keep a strict allowlist and task file exactly like this POC.
- Treat any repo-wide side effect outside the allowlist as a failed run.
- Prefer a tiny docs/test task first before trying product code.

## Go/No-Go Answer

- No-Go for direct casual execution from the repo root as-is.
- Go for a next bounded experiment if the execution surface is isolated first.
