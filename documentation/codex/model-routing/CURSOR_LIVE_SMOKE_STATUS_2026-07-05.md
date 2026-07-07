# Cursor Live Smoke Status

Date: `2026-07-05`

## Status update

The initial local smoke in this repo was blocked by using the wrong reachable wrapper path (`cursor ...` / `cursor agent ...`) instead of the real Cursor Agent CLI.

Operator-confirmed Cursor evidence now shows the correct Windows headless path is working when invoked as:

```powershell
agent -p --output-format json --workspace <temp> --model auto --trust --force "<prompt>"
```

Confirmed evidence from the operator/Cursor reply:

- `agent --version`: `2026.07.01-41b2de7`
- JSON success output with `session_id`
- isolated temp `notes.txt` changed from `BASELINE` to `BASELINE + CURSOR_SMOKE_OK`

Implication for Janus:

- live Cursor delegation must use `agent -p`
- `cursor agent` should not be used for Janus live worker runs
- the next meaningful proof is a bounded live smoke through `janus_cursor_worker_runner.py`, not another direct raw CLI smoke

## Runner smoke update

The first repo-bound bounded runner smoke was executed as:

```powershell
python documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py `
  --lane test_fixture_worker `
  --workflow-id WF-CURSOR-LIVE-SMOKE-002 `
  --input-package-json documentation/codex/model-routing/fixtures/examples/test_fixture_worker_input_package_example.json `
  --allowlist-file documentation/codex/model-routing/fixtures/examples/allowlists/test_fixture_allowlist.txt `
  --execute-live
```

Result:

- `validation_result`: `FAIL`
- `final_outcome`: `CURSOR_AGENT_EXIT_NONZERO`
- no changed files
- no allowlist violation

Captured stderr:

```text
Warning: The provided API key is invalid.
The API key was loaded from the CURSOR_API_KEY environment variable.
Please check you have the right key, create a new one, or authenticate without it.
```

Interpretation:

- the Janus runner now reaches the correct Agent CLI path
- package validation and allowlist validation both pass
- the current blocker for this repo-bound live smoke is Cursor authentication, not routing or runner wiring

## Successful rerun

After refreshing the shell environment from the persisted Windows user variables and using the valid user-level `CURSOR_API_KEY`, the exact same bounded runner smoke was rerun successfully:

```powershell
python documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py `
  --lane test_fixture_worker `
  --workflow-id WF-CURSOR-LIVE-SMOKE-002 `
  --input-package-json documentation/codex/model-routing/fixtures/examples/test_fixture_worker_input_package_example.json `
  --allowlist-file documentation/codex/model-routing/fixtures/examples/allowlists/test_fixture_allowlist.txt `
  --execute-live
```

Successful result:

- `validation_result`: `PASS`
- `final_outcome`: `CURSOR_WORKER_READY_FOR_CODEX_REVIEW`
- `session_id`: `7ea26f22-dc37-45b8-ab2a-7b1e07b96b42`
- `changed_files`:
  - `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/fixtures/contact_memory_fixture.json`
  - `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/tests/test_contact_memory_fixture.py`
- `changed_outside_allowlist`: none

Codex review notes:

- the worker stayed inside the exact allowlist
- local verification also passed:
  - `python -m pytest development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/tests/test_contact_memory_fixture.py -q`
  - result: `5 passed`

Conclusion:

- the bounded Cursor runner path is now proven end-to-end for option `2 = Cursor`
- remaining next work is productizing that path through the higher-level skill/operator flow, not proving basic runner viability again

## Scope

Bounded live Cursor smoke for the tri-modal delegation path, approved by the user, with no OpenRouter call, no commit, and no Janus product-file edits.

## What was tested

1. Local Cursor auth availability for headless usage
2. Real Cursor CLI invocation against an isolated temp workspace
3. JSON output mode and write-bounded scratch edit behavior

## Temp workspace

- `C:\Users\pruve\AppData\Local\Temp\janus-cursor-live-smoke-001`
- baseline file: `notes.txt`
- copied worker rule: `.cursor/rules/janus-delegated-worker.mdc`

## Commands attempted

1. `cursor agent -p --output-format json --workspace <temp> --model auto --trust --force ...`
2. `cursor -p --output-format json --workspace <temp> --model auto --trust --force ...`
3. bundled Node direct:
   `resources\helpers\node.exe resources\app\out\cli.js -p --output-format json --workspace <temp> --model auto --trust --force ...`

## Result

Canonical state: `BLOCKED` for the initial wrapper-based local attempts only

All three commands returned exit code `0`, but none executed a real headless agent run:

- no JSON response body was emitted
- `notes.txt` remained unchanged (`BASELINE` only)
- stderr showed CLI-option passthrough warnings such as:
  - `Warning: 'p' is not in the list of known options`
  - `Warning: 'output-format' is not in the list of known options`
  - `Warning: 'workspace' is not in the list of known options`

This indicates the currently reachable local `cursor` wrapper is not behaving like the documented headless Cursor CLI path for non-interactive agent runs on this machine.

## Additional finding

The Cursor prerequisites runner had one real production issue independent of the local install state:

- official Cursor CLI docs use `--resume`
- the local runner was using `--resume-session-id`
- this was corrected before the smoke run

## Evidence

Run directory:

- `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-LIVE-SMOKE-001/`

Key files:

- `invocation.json`
- `live_cli_stderr.log`
- `live_cli_stderr_cursor_print.log`
- `live_cli_stderr_node_direct.log`
- `workspace_notes.txt`
- `workspace_notes_cursor_print.txt`
- `workspace_notes_node_direct.txt`

## Recommended next step

Install the **separate Cursor Agent CLI** (not the desktop `cursor.cmd` wrapper):

```powershell
irm 'https://cursor.com/install?win32=true' | iex
```

Open a **fresh terminal**, verify `agent --version`, then rerun the isolated smoke from `HANDOFF_CURSOR_DIRECT_SUPPORT_2026-07-05.md` (Resolution section).

Runner fix: `janus_cursor_worker_runner.py` now invokes `agent -p`, not `cursor agent -p`.
