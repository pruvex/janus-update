# Execution Write Apply Cursor Live Smoke 2026-07-06

## Scope

- lane: `execution_write_apply_candidate`
- task_id: `TASK-EX-002`
- workflow_id: `WF-CURSOR-SHADOW-EXEC-WRITE-LIVE-001`
- operator choice: `2 = Cursor`
- mode: explicit bounded live smoke against the new shadow accepted-source fixture

## Command

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_write_apply_candidate --task-id TASK-EX-002 --workflow-id WF-CURSOR-SHADOW-EXEC-WRITE-LIVE-001 --operator-choice 2 --input-package-json documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/input_package.json --allowlist-file documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/allowlist.txt --accepted-source-run-dir documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/accepted_source/WF-CURSOR-SHADOW-EXEC-ACCEPTED-001 --estimated-codex-saved-tokens 28000 --estimated-delegation-overhead-tokens 10000 --minimum-net-codex-saved-tokens 12000 --execute-live-cursor
```

## Result

- canonical state: `BLOCKED`
- observed behavior: the delegated Python process spawned `janus_cursor_worker_runner.py`, which in turn launched `agent -p`, but the run did not finish within the local Codex timeout window (`244038 ms`)
- on-disk workflow directory `documentation/codex/model-routing/cursor-worker-runs/WF-CURSOR-SHADOW-EXEC-WRITE-LIVE-001/` was created, but no `dispatcher_result.json`, `cursor_response.json`, `stdout.log`, or `stderr.log` artifacts were flushed before the hang
- no sandbox file changes were detected under the allowlisted shadow path
- the focused local shadow pytest stayed green after the aborted live attempt

## Process Evidence

Observed process chain before manual termination:

- `python documentation/codex/model-routing/scripts/janus_delegate.py ... --execute-live-cursor`
- `python documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py ... --execute-live`
- `cmd.exe /c C:\Users\pruve\AppData\Local\cursor-agent\agent.CMD -p ...`
- `powershell.exe ... cursor-agent.ps1 -p ...`
- `node.exe ... index.js -p ...`

## Follow-up Hypothesis

The accepted-source execution lane now passes contract and no-live validation, but the live call appears to stall inside the Cursor agent runtime before the Janus wrapper can capture result artifacts. The next likely hardening slice is:

1. add an internal subprocess timeout and partial-artifact flush in `janus_cursor_worker_runner.py`
2. optionally reduce workspace scope for the accepted-source shadow lane if the full repo workspace is causing the agent stall
3. rerun the same bounded live smoke after the timeout/flush hardening

## Local Validation

```powershell
python -m pytest documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/sandbox/test_gate_prompt_apply_shadow.py -q
```

Result: `1 passed`

## Follow-up After Runner Hardening

Two later reruns improved the quality of the blocker evidence:

- `WF-CURSOR-SHADOW-EXEC-WRITE-LIVE-003`
- `WF-CURSOR-SHADOW-EXEC-WRITE-LIVE-004`

Additional hardening added before those reruns:

1. worker-side live subprocess timeout handling in `janus_cursor_worker_runner.py`
2. deterministic partial-artifact flush on timeout:
   - `dispatcher_result.json`
   - `cursor_response.json`
   - `stdout.log`
   - `stderr.log`
   - `changed_files.txt`
3. narrowed live workspace root to the common allowlist directory:
   - `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/sandbox`

Observed outcome after hardening:

- both reruns ended cleanly with `final_outcome = CURSOR_AGENT_TIMEOUT`
- timeout was now emitted by the Janus worker itself after `30s`
- no hanging delegated Python/agent process tree remained afterward
- result artifacts were written deterministically to the workflow run directory
- even with the narrowed sandbox workspace root, the Cursor agent still failed to return within the bounded timeout

Implication:

The problem is no longer missing runner control. The remaining blocker is inside the Cursor agent runtime behavior for this accepted-source/write-style prompt shape, not in Janus gate wiring, missing artifact flush, or full-repo workspace size alone.

## Follow-up After Prompt Reduction

One additional rerun tested a deliberately smaller prompt/runtime shape:

- `WF-CURSOR-SHADOW-EXEC-WRITE-LIVE-005`

Additional reduction added before that rerun:

1. `cursor_prompt_mode = minimal_write_apply` on the input package
2. compact prompt containing only:
   - task label
   - workspace-relative file list
   - accepted-source summary line
   - one validation command
   - concise JSON return instruction

Observed outcome after prompt reduction:

- the reduced prompt variant still ended with `final_outcome = CURSOR_AGENT_TIMEOUT`
- timeout remained deterministic at `30s`
- no sandbox file changes were made
- focused local pytest remained green

Implication:

The blocker survives both runner hardening and a materially smaller prompt shape. At this point, the most likely next differentiator is not more prompt trimming, but a different execution surface for this lane, such as a different backend or a more isolated non-Cursor worker pattern.

## Comparison Against Local Write-Apply Surface

To isolate whether the lane itself was broken or only the Cursor runtime path was a bad fit, the same bounded accepted-source shadow lane was replayed through the existing local deterministic write-apply surface:

- accepted-source package:
  - `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/accepted_source/WF-SHADOW-LOCAL-APPLY-COMPARE-001/`
- validation-only gate:
  - `WF-SHADOW-LOCAL-APPLY-COMPARE-VALIDATE-001`
- live local-apply comparison:
  - `WF-SHADOW-LOCAL-APPLY-COMPARE-LIVE-001`

Commands:

```powershell
python documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py --task-label "Shadow local apply compare" --normal-target-model "5.4 medium" --operator-choice delegated --workflow-id WF-SHADOW-LOCAL-APPLY-COMPARE-VALIDATE-001 --accepted-source-run-dir documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/accepted_source/WF-SHADOW-LOCAL-APPLY-COMPARE-001
```

```powershell
python documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py --task-label "Shadow local apply compare" --normal-target-model "5.4 medium" --operator-choice delegated --workflow-id WF-SHADOW-LOCAL-APPLY-COMPARE-LIVE-001 --accepted-source-run-dir documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/accepted_source/WF-SHADOW-LOCAL-APPLY-COMPARE-001 --execute-live-sidecar
```

Observed outcome:

- validation-only gate: `PASS`
- deterministic local apply: `PASS`
- final outcome:
  - `EXECUTION_WRITE_APPLY_LIVE_WRITE_READY_FOR_CODEX_ACCEPT_REJECT`
- touched file matched the exact allowlist
- focused shadow pytest still passed afterward

Conclusion:

The accepted-source write lane itself is functional. The evidence now points much more specifically to the Cursor execution surface as the bad fit for this lane, not to Janus delegation, accepted-source package shape, or deterministic local write-apply mechanics.
