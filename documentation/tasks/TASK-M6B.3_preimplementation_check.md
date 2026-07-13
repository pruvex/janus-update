PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.3
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only the Phase-B T-B4 thin Ollama-local transport wrapper over the existing `OllamaServiceProvider` seam.
- Execution is Cursor-first and bounded to the two transport files and one new hermetic test; Codex reviews the allowlisted diff and evidence on 5.6 Terra/high.
- The existing Ollama service remains the authority for local endpoint/model-node resolution, capability cache and native-tool fallback, retry/deadline behavior, request/response normalization, tool conversion, and history semantics. No caller is rerouted and `TRANSPORT_LAYER_ENABLED` remains default-off and unconsumed.
- The selected OpenRouter precheck-review gate returned `OPENROUTER_WORKER_DRY_RUN_READY`; its runner is absent from this isolated worktree and the gate permits no live execution. This is non-blocking assist-only evidence; Codex is the final precheck owner.
Affected Files:
- backend/llm_providers/transports/ollama_local.py
- backend/llm_providers/transports/__init__.py
- backend/tests/test_ollama_local_transport.py
Evidence Focus:
- python -m pytest --noconftest backend/tests/test_ollama_local_transport.py backend/tests/llm_providers/test_ollama_adapter.py -q
- python -m py_compile backend/llm_providers/transports/__init__.py backend/llm_providers/transports/ollama_local.py
- git diff --check and scoped review against the exclusions below
Scope-Regel:
- Implement only TASK-M6B.3. No change to Ollama service/gateway/adapter or legacy import, ToolLoopRunner, ToolCallAdapter, runtime resolver, llm_gateway, execution engine, local endpoint/model-node routing, capability cache or tool fallback, retry/deadline behavior, streaming, structured/image response behavior, provider fallback, resolver/gateway integration, or TRANSPORT_LAYER_ENABLED consumer/flip.
Automated Evidence Gate:
- python -m pytest --noconftest backend/tests/test_ollama_local_transport.py backend/tests/llm_providers/test_ollama_adapter.py -q
- python -m py_compile backend/llm_providers/transports/__init__.py backend/llm_providers/transports/ollama_local.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and task-breakdown handoff verified. `TASK-M6B.1` and `TASK-M6B.2` are independently closed; `TASK-M6B.3` is the unique next target in the same approved Phase-B task artifact.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task changes no TestSpec or oracle; the named transport and Ollama-adapter tests are source-owned focused regressions.
Keep Context:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_b.md
- documentation/tasks/TASK-M6B.3_task_breakdown.md
- backend/llm_providers/shared/base_transport.py and backend/llm_providers/ollama/service.py as read-only contract/service seams
Drop Context:
- completed M6B.1/M6B.2 implementation and audit history
- later M6B.4 through M6B.5 tasks
- unrelated ChromaDB-dependent suites, main-repository hygiene, and Git/release history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Cursor-first implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: The three-file allowlist, one-wrapper scope, existing service seams, default-off constraint, and hermetic focused evidence are explicit. The OpenRouter review lane is assist-only and unavailable live in this isolated worktree, while Codex has completed the binding gate locally.
User Action: Authorize only the bounded Cursor-first TASK-M6B.3 execution slice and return the candidate diff plus focused evidence for Codex review.
