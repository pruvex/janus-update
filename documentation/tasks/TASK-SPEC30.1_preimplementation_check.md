PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC30.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Spec: documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it defines only the two shadow work classes, their isolated task packages, allowlists, forbidden actions, acceptance criteria, and the fixed two-model comparison config for later evaluation slices.
- Artifact identity is consistent across approved Spec 30, generated TASK-SPEC30, the released target-task handoff `TASK-SPEC30.1`, and this precheck artifact.
- The affected file cluster is concrete and bounded to the shadow-eval fixture surface, the gateway/contract scripts that describe or validate bounded packages, and focused tests that keep the evaluation surface fail-closed.
- Risk is MEDIUM because this slice does not run live worker models yet, but it sets the comparison boundary that later shadow runs must obey. Skill 4 must preserve the hard boundary: no live model runs, no final recommendation package, no real product-code delegation, no real consumer activation, and no repo writeback outside the isolated shadow-eval sandbox.
- This slice should make TASK-SPEC30.2 possible by defining the exact shadow-package and comparison structure that later comparable runs must consume without widening scope.
Affected Files:
- development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q -k "shadow or evaluation or allowlist"
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "shadow or evaluation or sandbox"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py
- git diff --check -- documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/tests/test_janus_worker_contract.py documentation/codex/model-routing/tests/test_janus_worker_gateway.py documentation/tasks/TASK-SPEC30.1_preimplementation_check.md
- focused negative-path checks for third-class drift, missing allowlists, forbidden actions, and comparison-config expansion beyond exactly two models per class
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q -k "shadow or evaluation or allowlist"
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "shadow or evaluation or sandbox"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
- documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
- documentation/tasks/TASK-SPEC30.1_task_breakdown.md
- development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
Drop Context:
- later TASK-SPEC30.2 comparable shadow-run execution
- later TASK-SPEC30.3 consumer recommendation synthesis
- old Spec-29 implementation history except where the existing gateway contract surface directly constrains this slice
- OpenCode, OpenHands, broad OR routing policy, release, Git governance, and unrelated Janus product bug history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The first Spec-30 slice is implementation-ready and tightly bounded to shadow-task packaging, fixed comparison config, sandbox limits, and focused validation only.
User Action: Say `ok` to start implementation of `TASK-SPEC30.1` with the bound scope and evidence gate above.
