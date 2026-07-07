# Cursor Direct Support Handoff

Date: `2026-07-05`

## Goal

Help diagnose why the local Windows Cursor installation does not behave like the documented headless Cursor CLI for non-interactive agent runs.

Please answer with:

1. the exact supported Windows command for a real headless agent run
2. whether a separate CLI install or PATH repair is required in addition to the desktop app
3. one minimal verification command that should produce a real JSON result on Windows
4. whether `cursor agent -p ...` is valid on Windows in the current Cursor release
5. whether the local wrapper behavior below indicates a broken/stale install

## Environment

- OS: Windows
- Repo workspace: `C:\KI\Janus-Projekt`
- Local Cursor app path:
  - `C:\Users\pruve\AppData\Local\Programs\cursor\Cursor.exe`
- Local wrapper path:
  - `C:\Users\pruve\AppData\Local\Programs\cursor\resources\app\bin\cursor.cmd`

Wrapper content:

```bat
@echo off
setlocal
set VSCODE_DEV=
set ELECTRON_RUN_AS_NODE=1
"%~dp0..\..\..\Cursor.exe" "%~dp0..\out\cli.js" %*
IF %ERRORLEVEL% NEQ 0 EXIT /b %ERRORLEVEL%
endlocal
```

## Expected behavior from docs

We expected the documented headless/non-interactive CLI shape to work, including flags such as:

- `-p` / `--print`
- `--output-format json`
- `--workspace <path>`
- `--model <model>`
- `--trust`
- `--force`
- `--resume <id>`

We also expected non-interactive output to emit one JSON object on success.

## What we tried

All tests were run against an isolated temp workspace, not against product files.

Temp workspace:

- `C:\Users\pruve\AppData\Local\Temp\janus-cursor-live-smoke-001`

Baseline file:

- `notes.txt`

Prompt used:

```text
Append exactly one new line 'CURSOR_SMOKE_OK' to notes.txt. Change no other files. Do not run terminal commands. Return one short sentence confirming what you changed.
```

### Attempt 1

```powershell
cursor agent -p --output-format json --workspace <temp> --model auto --trust --force "<prompt>"
```

### Attempt 2

```powershell
cursor -p --output-format json --workspace <temp> --model auto --trust --force "<prompt>"
```

### Attempt 3

Direct bundled Node path:

```powershell
node.exe out\cli.js -p --output-format json --workspace <temp> --model auto --trust --force "<prompt>"
```

## Observed result

All attempts returned exit code `0`, but none behaved like a real headless agent run:

- no JSON result body
- no file edit
- `notes.txt` stayed unchanged
- stderr warnings like:

```text
Warning: 'p' is not in the list of known options
Warning: 'output-format' is not in the list of known options
Warning: 'workspace' is not in the list of known options
Warning: 'model' is not in the list of known options
Warning: 'trust' is not in the list of known options
```

This makes it look as if the reachable local `cursor` command is not actually acting like the documented headless CLI.

## Additional finding from our integration

We also found and fixed one local runner issue on our side:

- the runner originally used `--resume-session-id`
- official docs indicate `--resume`
- we corrected our local runner to `--resume`

So the current blocker is no longer that flag mismatch; it is the local CLI/install behavior itself.

## Resolution (2026-07-05)

Canonical state: **ROOT CAUSE IDENTIFIED**

### Answers

| # | Question | Answer |
| --- | --- | --- |
| 1 | Exact Windows headless command | **`agent -p ...`** — not `cursor`, not `cursor agent` |
| 2 | Separate install required? | **Yes.** Desktop `cursor.cmd` is the editor launcher only |
| 3 | Minimal JSON verification | `agent --version` then `agent status --format json` then smoke below |
| 4 | Is `cursor agent -p` valid? | **No** — not documented; hits editor wrapper |
| 5 | Warning pattern = broken install? | **Not broken desktop app** — wrong binary. `-p` is unknown to `cursor.cmd` |

### Verified on this machine

- `C:\Users\pruve\AppData\Local\Programs\cursor\resources\app\bin\cursor.cmd` → **exists**
- `%USERPROFILE%\.local\bin\agent.exe` → **missing**

### Fix steps

```powershell
# 1. Install Cursor Agent CLI (separate from desktop app)
irm 'https://cursor.com/install?win32=true' | iex

# 2. Fresh terminal, then verify
agent --version
agent status --format json

# 3. Auth (one of)
agent login
# or set CURSOR_API_KEY for headless

# 4. Minimal write smoke in temp dir
$ws = Join-Path $env:TEMP "janus-cursor-live-smoke-002"
New-Item -ItemType Directory -Force -Path $ws | Out-Null
Set-Content -Path (Join-Path $ws "notes.txt") -Value "BASELINE"
agent -p --output-format json --workspace $ws --model auto --trust --force `
  "Append exactly one new line CURSOR_SMOKE_OK to notes.txt. Change no other files."
Get-Content (Join-Path $ws "notes.txt")
```

Expected: JSON on stdout with `session_id`, `notes.txt` contains `CURSOR_SMOKE_OK`.

### Runner fix applied

`janus_cursor_worker_runner.py` was calling `cursor agent -p` (wrong). It now:

- resolves `agent` binary via PATH or `%USERPROFILE%\.local\bin\agent.exe`
- blocks with `CURSOR_AGENT_CLI_MISSING` when not installed
- invokes `agent -p --workspace ... --output-format json ...`

### Docs

- https://cursor.com/docs/cli/installation
- https://cursor.com/docs/cli/headless
- https://cursor.com/docs/cli/reference/output-format

---

## Original questions (archived)

Repo evidence summary:

- `documentation/codex/model-routing/CURSOR_LIVE_SMOKE_STATUS_2026-07-05.md`
- `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-LIVE-SMOKE-001/`

Main question:

```text
What exact Windows installation/repair step and exact verification command should we use so Cursor headless agent mode actually works as documented for our bounded delegation runner?
```
