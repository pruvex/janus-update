# TEST-PIPELINE SIDECAR RUNTIME DEBUG 2026-06-27

SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 1
Progress-Validierung: Failure Code `GENERATOR_RUNNER_FAILED`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- the delegated `workspace-write` attempt did not fail on the generator contract anymore
- the bounded live prompt still named the work as a `janus-test-pipeline` sidecar task
- that wording triggered internal workflow routing and skill loading inside the delegated Codex runtime
- `stderr.log` shows the delegated runtime failing during those internal PowerShell reads with `windows sandbox: CreateProcessWithLogonW failed: 1056`
- the runtime therefore never reached a trustworthy generator execution step

Fix Summary:
- hardened `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py` so the generated live prompt is now a pre-scoped bounded worker prompt instead of a skill-facing Janus task prompt
- removed direct skill-trigger language such as `janus-test-pipeline`, `codex-start-of-work-check`, and routing-style wording from the generated prompt contract
- added a regression test that fails if the prompt reintroduces those trigger strings

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m unittest documentation.codex.model-routing.tests.test_test_pipeline_sidecar_write_pilot_runner`
  - `python -m py_compile documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
  - prompt generation proof `SIDECAR-TEST-ARTIFACT-PROMPT-2026-06-27-125`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
- no fresh live delegated retry was run in this debug slice, so the bounded runtime seam is not yet re-proven end-to-end

Changed Files:
- `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/test_pipeline_sidecar_write_runtime_debug_2026-06-27.md`

NEXT_STEP
Target Skill: janus-test-pipeline
Canonical State: HANDOFF
Required Artifacts:
- `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/test_pipeline_sidecar_write_live_retry_result_2026-06-27.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-124/stderr.log`
Evidence Paths:
- `documentation/codex/model-routing/test_pipeline_sidecar_write_runtime_debug_2026-06-27.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-PROMPT-2026-06-27-125/generated_prompt.md`
Failure Code:
- `GENERATOR_RUNNER_FAILED`
Changed Files:
- `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/test_pipeline_sidecar_write_runtime_debug_2026-06-27.md`
Decision:
- run one fresh bounded `janus-test-pipeline` live retry only after explicit approval, using the de-triggered generated prompt
Reason:
- the debug slice produced a concrete runtime hypothesis and a bounded code fix, but the lane still needs one new live end-to-end attempt before it can be called repaired
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- explicitly approve one fresh bounded live retry for the same test-artifact slice if you want end-to-end proof of the prompt hardening
