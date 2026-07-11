# Cursor Delegation Prerequisites

This document covers only the Cursor-side prerequisites for tri-modal delegation.

## Scope

- `2 = Cursor` is the bounded tool-worker option.
- Codex remains `1 = Codex` and final acceptance owner.
- OpenRouter remains `3 = OpenRouter`.
- No live Cursor call should run without explicit operator approval.

## API Key

Use a Cursor user API key for non-interactive CLI usage.

PowerShell for the current terminal session:

```powershell
$env:CURSOR_API_KEY = "paste-your-cursor-user-api-key-here"
```

Persist for future terminals on Windows:

```powershell
setx CURSOR_API_KEY "paste-your-cursor-user-api-key-here"
```

Notes:

- `setx` affects new terminals, not the current one.
- The key should not be committed, logged, or written into task packages.
- The bounded runner blocks if `CURSOR_API_KEY` is missing.
- If local live smoke attempts show warnings like `Warning: 'p' is not in the list of known options`, the currently reachable `cursor` wrapper is not acting like the documented headless CLI. In that case, install or repair the official Cursor CLI from the current Cursor docs and retry from a fresh terminal.

## Runner Contract

Primary entry:

```powershell
python documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py --lane <lane> --workflow-id <id> --input-package-json <pkg> --allowlist-file <allowlist> --dry-run
```

For real Cursor execution, the runner must call the official Agent CLI shape:

```powershell
agent -p --output-format json --workspace <path> --model <model> ...
```

Do not use `cursor agent` for live Janus delegation.

Delegate-level dry-run planning stays here:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane <lane> --workflow-id <id> --operator-choice 2 --input-package-json <pkg> --allowlist-file <allowlist>
```

An explicitly approved live Cursor delegate path is now wired, but remains opt-in only:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane <lane> --workflow-id <id> --operator-choice 2 --input-package-json <pkg> --allowlist-file <allowlist> --execute-live-cursor
```

Without `--execute-live-cursor`, `janus_delegate.py` must stay plan-only.

Current modes:

- `assist_only`: no `--force`
- `proposal_first`: `--force --trust --approve-mcps`

The runner writes artifacts under:

```text
documentation/codex/model-routing/cursor-worker-runs/<WORKFLOW-ID>/
```

And appends a compact row to:

```text
documentation/codex/model-routing/cursor_delegation_log.jsonl
```

## Safety Boundaries

- allowlist required when the manifest says so
- no commit, push, tag, merge, release, or publish
- no secrets in prompts, logs, or summaries
- changed files outside the allowlist fail closed
- Codex reviews every result before accepting it

## Repo Hints

Auto-apply worker guidance:

- `.cursor/rules/janus-delegated-worker.mdc`

Indexing noise reduction:

- `.cursorignore`
