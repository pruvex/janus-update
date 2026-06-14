# Codex Sidecar Agent Live Pilot Result - 2026-06-14

## Result

SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 1
Progress-Validierung: Failure Code `GENERATOR_RUNNER_FAILED`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

## Root Cause

The first live sidecar attempts exposed Windows/Codex CLI runner issues before a stable content result was possible:

- `ProcessStartInfo.ArgumentList` was not usable in the current Windows PowerShell runtime.
- The installed `codex` command resolves to a PowerShell shim (`C:\nvm4w\nodejs\codex.ps1`), which is not safe to start directly as an executable.
- The current `codex exec` version does not support the previously assumed `--ask-for-approval` flag.
- A live `codex exec` child process can continue running after an interrupted Codex App tool call unless the runner enforces timeout and process-tree cleanup.

## Fix Summary

`documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1` was hardened:

- resolves the PowerShell shim to direct `node.exe ...\@openai\codex\bin\codex.js`
- removes unsupported `--ask-for-approval` from the actual CLI invocation while preserving the policy in metadata
- writes file-first artifacts for command, prompt, stdout, stderr, exit code, last message, event stream, and summary
- adds `TimeoutSeconds`
- kills the spawned process tree on timeout
- records `TIMEOUT` instead of allowing indefinite hanging
- treats a completed run with non-empty final artifacts as success when Windows returns a null exit code

## Auto-Verification

- Status: PASS for runner safety and first read-only sidecar content completion
- Evidence:
  - `documentation/codex/model-routing/sidecar-runs/SIDECAR-DRY-RUN-TIMEOUT-CHECK/summary.json`
  - `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-TIMEOUT-GUARD-002/summary.json`
  - `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-001/last_message.md`

## Artifact Identity Check

PASS

The validated pilot path used:

- runner: `documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1`
- prompt: `documentation/codex/model-routing/sidecar-fixtures/sidecar_live_pilot_prompt_2026-06-14.md`
- timeout guard run: `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-TIMEOUT-GUARD-002/`
- accepted read-only run: `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-001/`

## Final Feature Suite

N/A WITH REASON

This was a sidecar runner and pilot-validation pass, not a Janus product behavior change.

## Live Pilot Outcome

The timeout-guard validation returned:

- status: `TIMEOUT`
- timeout_seconds: `20`
- stdout captured: yes
- stderr captured: yes
- summary captured: yes
- process-tree cleanup: PASS
- lingering pilot process after timeout: none found

The first full read-only live pilot under `TimeoutSeconds 180` returned usable content:

- `last_message.md`: present
- `stdout.log`: present
- lingering pilot process after completion: none found
- sidecar recommendation: `janus-documentation-update` as the first real read-only pilot

The sidecar output concluded:

- `janus-documentation-update` should be the first real sidecar pilot
- the pilot should stay read-only and non-binding
- `janus-test-pipeline` remains a later candidate with a weaker initial trust posture

The remaining bug after that run was runner-side only: `summary.json` still reported `FAILED` with `exit_code = null`, even though `last_message.md` and `stdout.log` both contained the completed result. The runner was patched after that run to normalize this Windows null-exit-code case using artifact success.

A second confirmation run under the same `TimeoutSeconds 180` profile then returned:

- status: `PASS`
- `exit_code`: `null`
- `artifact_success`: `true`
- `last_message_present`: `true`
- `stdout_present`: `true`

This confirms that the patched runner now classifies the Windows null-exit-code path correctly when final artifacts are present.

## Model Guidance

This work does not require `5.5`.

Recommended model for the next sidecar runner iteration:

- model: `5.4`
- reasoning: `medium`

Use `5.5` only if later review finds security, governance, prompt-injection, release, or architecture risk.

## Changed Files

- `documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-DRY-RUN-TIMEOUT-CHECK/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-TIMEOUT-GUARD-002/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-001/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-002/*`
- `documentation/codex/model-routing/codex_sidecar_agent_live_pilot_result_2026-06-14.md`

## NEXT_STEP

Target Skill: `janus-debug`
Canonical State: HANDOFF
Required Artifacts:

- `documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-TIMEOUT-GUARD-002/summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-001/last_message.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-001/summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-002/summary.json`

Evidence Paths:

- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-TIMEOUT-GUARD-002/`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-001/`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-002/`

Failure Code: `GENERATOR_RUNNER_FAILED`

Changed Files:

- `documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1`
- `documentation/codex/model-routing/codex_sidecar_agent_live_pilot_result_2026-06-14.md`

Decision:

The first real read-only sidecar pilot is accepted, and the patched runner has one confirmed clean `PASS` summary. Treat `janus-documentation-update` as the first validated sidecar candidate class for non-binding draft work.

Reason:

Runner safety is fixed, one read-only sidecar pilot completed successfully, and the patched wrapper now classifies the null Windows exit-code path correctly.

Recommended Model: `5.4`

Recommended Intelligence: `medium`

Next User Action:

Use the sidecar path next for a bounded, non-binding `janus-documentation-update` draft task. Keep the work read-only until we deliberately decide to validate a write-capable sidecar path.
