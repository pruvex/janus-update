PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.1
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only the first Phase-B vertical slice: the minimal BaseTransport contract plus an OpenAI-compatible adapter over the existing OpenAI service seam.
- Execution is Cursor-first and bounded to the five listed new files; Codex reviews the resulting diff and evidence. `5.6 Terra/high` remains the required Codex review model for this architecture-sensitive seam.
- The Phase-B flag remains default-off. No existing caller is rerouted, so Phase-A's committed/manual-validated behavior is not part of the change surface.
Affected Files:
- backend/llm_providers/shared/base_transport.py
- backend/llm_providers/transports/__init__.py
- backend/llm_providers/transports/openai_compat.py
- backend/tests/test_base_transport.py
- backend/tests/test_openai_compat_transport.py
Evidence Focus:
- python -m pytest --noconftest backend/tests/test_base_transport.py backend/tests/test_openai_compat_transport.py -q
- python -m py_compile backend/llm_providers/shared/base_transport.py backend/llm_providers/transports/__init__.py backend/llm_providers/transports/openai_compat.py
- focused existing OpenAI service and ToolCallAdapter regression selected by the executioner
- git diff --check and a scoped review against the exclusions below
Scope-Regel:
- Implement only TASK-M6B.1. No modification to existing OpenAI service/gateway/runner files; no runtime resolver, gateway delegation, provider expansion, OpenRouter endpoint, Gemini/Ollama transport, OAuth, Websearch, streaming, cost-model change, or TRANSPORT_LAYER_ENABLED consumer/flip.
Automated Evidence Gate:
- python -m pytest --noconftest backend/tests/test_base_transport.py backend/tests/test_openai_compat_transport.py -q
- python -m py_compile backend/llm_providers/shared/base_transport.py backend/llm_providers/transports/__init__.py backend/llm_providers/transports/openai_compat.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and task-breakdown handoff verified. The Spec is APPROVED and Phase-A's task artifact records all T-A1 through T-A5 as complete.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task does not change a TestSpec or test oracle; the two named unit tests are source-owned focused regressions.
Keep Context:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_b.md
- documentation/tasks/TASK-M6B.1_task_breakdown.md
- backend/llm_providers/openai/service.py and backend/llm_providers/shared/tool_call_adapter.py as read-only delegation seams
Drop Context:
- completed Phase-A implementation and audit history
- later Phase-B tasks M6B.2 through M6B.5
- unrelated ChromaDB-dependent suites and all release/Git history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Cursor-first implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: The implementation scope is one contract plus one concrete adapter, all files and hermetic evidence are explicit, and no unresolved product or architecture decision remains. Cursor-first execution must remain within the allowlisted file set.
User Action: Start the bounded Cursor-first execution slice in this worktree; return the candidate diff and focused evidence to Codex for review.
