PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.4
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Add only a deterministic `runtime_llm.resolve()` module and a bounded, non-consuming transport registry seam in `llm_gateway.py`.
- Map `openai`/`openrouter` to `openai_compat`, `gemini`/`google` to `gemini_native`, and `ollama` to `ollama_local`; the Epic-5 Codex placeholder must fail explicitly without introducing a transport.
Affected Files:
- backend/llm_providers/runtime_llm.py
- backend/services/llm_gateway.py
- backend/tests/test_runtime_llm.py
Evidence Focus:
- python -m pytest backend/tests/test_runtime_llm.py -q
- python -m py_compile backend/llm_providers/runtime_llm.py backend/services/llm_gateway.py backend/tests/test_runtime_llm.py
- git diff --check
Scope-Regel:
- Implement only TASK-M6B.4. No gateway delegation, feature-flag consumer, transport send path, provider fallback, service/gateway policy, resolver use-site, Websearch, streaming, or credential retrieval change.
Automated Evidence Gate:
- python -m pytest backend/tests/test_runtime_llm.py -q
- python -m py_compile backend/llm_providers/runtime_llm.py backend/services/llm_gateway.py backend/tests/test_runtime_llm.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Phase-B T-B5, TASK-M6B.4, task-breakdown handoff, and runtime_llm Spec mapping verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task changes no TestSpec or oracle.
Keep Context:
- T-B5 mapping table and existing transport exports
- TASK-M6B.4 breakdown
Drop Context:
- completed M6B.3 and BACKLOG-125/126/127 closeout
- later T-B6 gateway delegation and Phase-C work
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Cursor-first bounded resolver/registry implementation result, focused tests, then a manual non-routing verification gate.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: The resolver registry creates a provider-family boundary and needs high-reasoning scope discipline, while the live gateway path remains excluded.
User Action: Authorize only the bounded Cursor-first TASK-M6B.4 execution slice.
