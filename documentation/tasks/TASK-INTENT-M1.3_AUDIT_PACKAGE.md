# TASK-INTENT-M1.3 Audit Package

## Scope

- Target task: `TASK-INTENT-M1.3`
- Bound objective: benchmark uplift proof, flag-off parity proof, and latency evidence for the auxiliary intent classifier without changing Janus product intent logic
- Spec: `documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md`
- Task file: `documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md`
- Preimplementation check: `documentation/tasks/TASK-INTENT-M1.3_preimplementation_check.md`
- Backlog item: `N/A WITH REASON` - roadmap/spec milestone slice, not a backlog item
- TestSpec/TestRun: `N/A WITH REASON` - benchmark/evidence slice with pytest and generated markdown proof report
- Manual Janus evidence: `N/A WITH REASON` - no product runtime, UI, provider, or live Janus behavior changed in this slice
- Pipeline completion status: implementation complete, validation complete, final audit pending

## Changed Files

- `backend/scripts/run_intent_benchmark.py`
- `backend/tests/test_intent_benchmark.py`
- `documentation/test-runs/TASK-INTENT-M1.3_benchmark_uplift_2026-07-08.md`
- `documentation/tasks/TASK-INTENT-M1.3_execution_result.md`
- `documentation/tasks/TASK-INTENT-M1.3_debug_result.md`
- `documentation/tasks/TASK-INTENT-M1.3_AUDIT_PACKAGE.md`

## Validation Commands

- `python -m py_compile backend/scripts/run_intent_benchmark.py backend/tests/test_intent_benchmark.py`
  - PASS
- `python -m pytest backend/tests/test_intent_benchmark.py backend/tests/test_intent_aux_classifier.py backend/tests/test_calendar_routing_fix.py -q`
  - PASS (`59 passed`)
- `python -m backend.scripts.run_intent_benchmark --mode m1-proof --output documentation/test-runs/TASK-INTENT-M1.3_benchmark_uplift_2026-07-08.md --write-baseline`
  - PASS
- `python C:\Users\pruve\.codex\skills\janus-debug\scripts\validate_debug_result.py documentation/tasks/TASK-INTENT-M1.3_debug_result.md`
  - PASS

## Key Evidence

- Flag-off parity: PASS
- Contact uplift: `55.0% -> 90.0%` (`+35.0 pp`)
- Pet uplift: `53.3% -> 73.3%` (`+20.0 pp`)
- Recall uplift: `80.0% -> 80.0%` (`+0.0 pp`)
- Calendar unchanged: PASS
- Aux-path latency after harness seam fix: `P95 4.09 ms`

## Debug Delta

- The first M1.3 proof was contaminated by a benchmark seam bug: the deterministic profile patched the module default classifier, but `classify_sync(..., config=...)` rebuilt a fresh classifier on the real default provider path.
- The harness now patches the default provider seam used by config-based reconstruction as well.
- After the seam fix, the latency blocker disappeared; the remaining blocker is Recall uplift only.

## Diff Summary

- `backend/scripts/run_intent_benchmark.py` now has an M1.3 proof mode that compares checked-in baseline, legacy-current parity, and deterministic auxiliary proof results.
- The deterministic proof context now patches the provider callable used by config-based `classify_sync(...)` reconstruction, so the proof path stays local and no longer enters the real default provider callable.
- `backend/tests/test_intent_benchmark.py` now covers baseline parsing, proof-report rendering, and the deterministic provider override.
- Documentation artifacts record the resolved latency blocker and the remaining Recall uplift shortfall.

## Known Risk / Open Issue

- The current deterministic recall path still misses three recall prompts (`INT-M0-R012`, `INT-M0-R014`, `INT-M0-R015`), so M1.3 may remain blocked on the Recall acceptance gate even though the benchmark harness is now correct.
