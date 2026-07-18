# TASK .6 Qwen Tool Choice Oracle Repair Execution Result

TASK EXECUTION HANDOFF

## Scope

Repair only the dedicated Task `.6` runner invocation semantics that added an unbound named OpenRouter tool choice to `LIVE-04` through `LIVE-07`. This slice does not retest a provider, certify a model, alter the runtime registry, or activate production behavior.

## Implementation

- The live executor now leaves `tool_choice` on OpenRouter auto-selection for all four tool-bound scenarios.
- The strict response/tool safety oracles remain unchanged.
- The test double records and verifies absence of `force_tool_name` for each affected scenario.
- The generated runner is bound to executor-source identity in addition to the canonical plan identity, then regenerated.

Auto-Verification:
- Status: PASS
- Focused conformance suite: `78 passed`.
- Python compilation: PASS for conformance compiler, live executor, and generated runner.
- Dedicated generator/plan validation: PASS.
- Runtime empty-registry SHA256: PASS, `7712D5B2775F5BDED03EF1C2DAE4228F9FCC8B7441140FC4F1AB8F56210EC46F`.
- Model transmissions during this repair: `0`.

Manual Janus Validation Gate:
- Status: N/A WITH REASON
- Test Example: no manual product observation applies to this offline certification-runner invocation repair.
- Expected Result: a fresh TestPipeline preflight and separately authorized live matrix will test the same bound model candidates without named tool forcing.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit

Changed Files:

- `backend/services/conformance/openrouter_conformance_runner.py`
- `backend/services/conformance/openrouter_live_certification.py`
- `backend/tests/test_openrouter_conformance.py`
- `documentation/test-runs/TEST-RUN-2026-07-17-006_generated.py`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_debug_result_qwen_tool_choice_oracle.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_execution_result_qwen_tool_choice_oracle.md`

## NEXT_STEP

Target Skill: `janus-test-pipeline`

Canonical State: HANDOFF

Required Artifacts:

- `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md`
- `documentation/test-runs/TEST-RUN-2026-07-17-006_plan.json`
- `documentation/test-runs/TEST-RUN-2026-07-17-006_generated.py`
- fresh public masked credential state, operator credit attestation, and no-call preflight output

Evidence Paths:

- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_debug_result_qwen_tool_choice_oracle.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_execution_result_qwen_tool_choice_oracle.md`
- `documentation/test-results/TEST-RUN-2026-07-17-006_results.json`

Failure Code: `ASSERTION_ORACLE_TOO_NARROW` fixed offline; `LIVE_RETEST_REQUIRES_FRESH_AUTHORIZATION` remains open.

Changed Files: the bounded runner, executor, focused tests, generated runner, and repair reports listed above.

Decision: hand off to a new `LIVE_PREFLIGHT_ONLY` step, then wait for a new exact live authorization before a complete four-candidate retest.

Reason: only a complete repeat on the same candidate set can establish whether all candidates now meet the unchanged certification oracles. The historical 38-call run and its prior approval cannot be reused.

Recommended Model: `5.6 Sol`

Recommended Intelligence: `high`

Next User Action: confirm sufficient remaining budget on the Janus-only certification key, or install a fresh finite-budget certification key, then authorize the no-call preflight.
