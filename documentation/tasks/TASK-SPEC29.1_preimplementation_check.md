PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC29.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it defines only the normalized worker task/result contract, fixture validation, and fail-closed classification for the future `janus-worker` gateway.
- Artifact identity is consistent across approved Spec 29, generated TASK-SPEC29, the released target-task handoff `TASK-SPEC29.1`, and this precheck artifact.
- The affected file cluster is concrete and bounded to the new contract module, the lightweight gateway entry surface, focused tests, and any small fixture data needed for deterministic validation.
- Risk is HIGH because this contract becomes the trust boundary between Codex and cheaper external worker runs. Skill 4 must preserve the hard boundary: no live Aider/OpenRouter execution, no OpenRouter API call, no worker copy-back path, no OpenCode/OpenHands backend, and no delegated Git, release, publish, dependency, security, privacy, or architecture authority.
- This slice should make TASK-SPEC29.2 possible by defining what every later worker backend must emit and what Codex must reject.
Affected Files:
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- documentation/codex/model-routing/strong-or-fixtures/
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "contract or result or fail_closed"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py
- git diff --check -- documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/tests/test_janus_worker_contract.py documentation/codex/model-routing/tests/test_janus_worker_gateway.py documentation/tasks/TASK-SPEC29.1_preimplementation_check.md
- focused negative-path checks for missing artifacts, forbidden actions, empty allowlists, scope drift, red checks, and inconsistent `success` claims
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "contract or result or fail_closed"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29.1_task_breakdown.md
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
Drop Context:
- later TASK-SPEC29.2 live Aider/OpenRouter runner wiring
- later TASK-SPEC29.3 operator guidance and live-dev pilot
- OpenCode, OpenHands, broad OR routing, release, Git governance, and product-runtime bug history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The first worker-gateway slice is implementation-ready and tightly bounded to contract, validators, fixtures, and focused tests only.
User Action: Say `ok` to start implementation of `TASK-SPEC29.1` with the bound scope and evidence gate above.
