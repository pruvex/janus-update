# TEST-PIPELINE SIDECAR RUNTIME COMMAND FIX 2026-06-27

SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 2
Progress-Validierung: Failure Code `GENERATOR_RUNNER_FAILED`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- after the prompt de-trigger repair, the delegated worker no longer failed on skill-loading subprocesses
- the remaining blocker was narrower: the delegated inner command attempted the host-visible full path `C:\nvm4w\nodejs\node.exe`
- inside the delegated `workspace-write` worker command step, that host-visible full path was not callable even though the outer sidecar process itself was launched through the same executable
- this made the inner generator command fail before any bounded output artifact could be created

Fix Summary:
- updated `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py` so the generated delegated prompt now uses a runtime-visible Node command token instead of the host-only absolute Node path
- added `resolve_delegated_node_command(...)` and switched the generated inner command contract to `& "node" ...`
- kept local validator ownership on the host-resolved Node executable, so local artifact checks still use the known-good host binary after a delegated run
- extended focused tests so the prompt contract now fails if it regresses back to the absolute host Node path

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m unittest documentation.codex.model-routing.tests.test_test_pipeline_sidecar_write_pilot_runner`
  - `python -m py_compile documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
  - prompt generation proof `SIDECAR-TEST-ARTIFACT-PROMPT-2026-06-27-127`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
- this debug slice changes the delegated command contract only; no fresh live delegated retry was run yet

Changed Files:
- `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/test_pipeline_sidecar_write_runtime_command_fix_2026-06-27.md`

NEXT_STEP
Target Skill: janus-test-pipeline
Canonical State: HANDOFF
Required Artifacts:
- `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/test_pipeline_sidecar_write_live_retry_result_2026-06-27_run126.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-PROMPT-2026-06-27-127/generated_prompt.md`
Evidence Paths:
- `documentation/codex/model-routing/test_pipeline_sidecar_write_runtime_command_fix_2026-06-27.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-PROMPT-2026-06-27-127/generated_prompt.md`
Failure Code:
- `GENERATOR_RUNNER_FAILED`
Changed Files:
- `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/test_pipeline_sidecar_write_runtime_command_fix_2026-06-27.md`
Decision:
- run one fresh bounded `janus-test-pipeline` live retry only after explicit approval, now using the runtime-visible `node` inner command
Reason:
- the remaining blocker was narrowed to the inner command contract, and that contract is now locally repaired but not yet re-proven live
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- explicitly approve one fresh bounded live retry if you want end-to-end proof that the delegated worker can now reach the generator step with the runtime-visible Node command
