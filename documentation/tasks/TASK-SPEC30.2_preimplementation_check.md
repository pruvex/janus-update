PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC30.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Spec: documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it runs and captures exactly the first comparable shadow evaluations for the two already-seeded work classes `docs_fleissarbeit` and `test_fixture_arbeit`, each against the fixed model pair `openrouter/qwen/qwen3-coder-30b-a3b-instruct` and `openrouter/moonshotai/kimi-k2.5`.
- Artifact identity is consistent across approved Spec 30, generated TASK-SPEC30, the completed setup slice `TASK-SPEC30.1`, the released target-task handoff `TASK-SPEC30.2`, and this precheck artifact.
- The affected file cluster is concrete and bounded to the existing isolated runner, gateway result validation, the shadow-eval sandbox surface, and focused tests for normalized result capture, fail-closed blocked outcomes, scope drift rejection, missing-artifact rejection, and comparison-summary behavior.
- Risk is HIGH because this slice is the first real comparable shadow-run execution across two classes and two fixed models. Skill 4 must preserve the hard boundary: no final first-consumer recommendation, no real worker-consumer activation, no product-code delegation, no Git or release authority, and no repo writeback outside the isolated shadow-eval sandbox.
- This slice should make TASK-SPEC30.3 possible by producing comparable per-run and per-class evidence only; it must not itself decide the final Go, No-Go, or narrower retest recommendation for the first real consumer.
Affected Files:
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/shadow_evaluation_manifest.json
- development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/docs_fleissarbeit/
- development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py -q -k "shadow or evaluation"
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "comparison or result or fail_closed"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- git diff --check -- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py documentation/codex/model-routing/tests/test_janus_worker_gateway.py development/openrouter-skill-tests/janus-worker-gateway-shadow-eval documentation/tasks/TASK-SPEC30.2_preimplementation_check.md
- focused negative-path checks for missing run artifacts, failed checks, missing usage or cost hints, scope drift, and any attempted writeback outside the bounded sandbox
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py -q -k "shadow or evaluation"
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "comparison or result or fail_closed"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
- documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
- documentation/tasks/TASK-SPEC30.1_execution_result.md
- documentation/tasks/TASK-SPEC30.2_task_breakdown.md
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/shadow_evaluation_manifest.json
Drop Context:
- completed TASK-SPEC30.1 audit and documentation detail beyond the sealed setup boundary it established
- later TASK-SPEC30.3 consumer recommendation synthesis
- old Spec-29 rollout history except where the isolated runner behavior directly constrains this slice
- OpenCode, OpenHands, broad OR routing policy, release, Git governance, and unrelated Janus product bug history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The comparable shadow-run slice is implementation-ready and tightly bounded to fixed-pair execution, normalized result capture, fail-closed comparison evidence, and no final consumer recommendation yet.
User Action: Say `ok` to start implementation of `TASK-SPEC30.2` with the bound scope and evidence gate above.
