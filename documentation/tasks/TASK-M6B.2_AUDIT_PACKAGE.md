# AUDIT_PACKAGE

Generated: 2026-07-12 12:58:54 UTC

## Goal

Audit TASK-M6B.2: thin default-off unintegrated GeminiNativeTransport 1:1 existing-service wrapper.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: PRESENT: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md, APPROVED, Phase-B T-B3.
- Task File: documentation\tasks\TASK-M6_transport_phase_b.md
- Backlog Item: N/A - approved spec-driven infrastructure slice.
- Pre-Implementation Check: documentation\tasks\TASK-M6B.2_preimplementation_check.md
- Manual Janus Evidence: PRESENT: Gemini weather prompt with TRANSPORT_LAYER_ENABLED=false returned Berlin weather from Open-Meteo at approximately 14:53 Europe/Berlin on 2026-07-12.
- Pipeline Completion Status: TASK-M6B.2 implementation and validation complete; later Phase-B tasks M6B.3-M6B.5 are explicitly out of scope.

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
TASK-M6B
- Source Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`
- Backlog Item: `N/A`
- Feature: Epic 4 Provider Transport Refactor, Phase B Transport Layer
- Generated At: 2026-07-11

## Generated Tasks

### TASK-M6B.1 Establish the BaseTransport contract and OpenAI-compatible vertical slice
- Ziel:
  - Introduce the provider-family transport contract from Spec Sections 2.2, 3.1, and Phase-B `T-B1`/`T-B2`, then implement the first concrete `openai_compat` adapter over the existing OpenAI service seam.
- Scope:
  - Add `BaseTransport` and `OpenAICompatTransport` only. The transport owns the normalized non-streaming `send`, tool normalization, and second-call history seams that are explicitly named by the Spec. It delegates to the existing `OpenAIServiceProvider`; it does not move request compilation, cost accounting, streaming, tool execution, gateway synthesis, runtime resolution, or gateway selection.
  - Preserve `TRANSPORT_LAYER_ENABLED=false` as the default. Do not wire either class into a gateway, `ToolLoopRunner`, `runtime_llm`, `llm_gateway`, OpenRouter, Gemini, Ollama, OAuth, Websearch, or the streaming engine in this task.
- Files:
  - `backend/llm_providers/shared/base_transport.py`
  - `backend/llm_providers/transports/__init__.py`
  - `backend/llm_providers/transports/openai_compat.py`
  - `backend/tests/test_base_transport.py`
  - `backend/tests/test_openai_compat_transport.py`
- Steps:
  1. Define the minimal abstract transport interface for the Spec-owned `send`, `prepare_history_for_second_call`, and tool-normalization boundary.
  2. Implement the OpenAI-compatible adapter by delegating request execution and history preparation to the existing OpenAI service while keeping transport-specific normalization at this boundary.
  3. Add hermetic focused tests using a fake/mocked service to prove abstract-contract enforcement, delegated request arguments, normalized tool handling, response pass-through, and history delegation without a network call.
- Acceptance Criteria:
  - `BaseTransport` is importable and cannot be instantiated without implementations of the declared contract methods.
  - `OpenAICompatTransport` implements the contract and delegates its non-streaming request/history seams to `OpenAIServiceProvider` without duplicating service request construction or cost handling.
  - Transport tool normalization uses the existing canonical OpenAI tool-call adapter boundary; canonical skill IDs remain preserved until that boundary.
  - Existing production paths remain unchanged because `TRANSPORT_LAYER_ENABLED` stays default-off and no gateway/resolver integration is added.
  - The focused tests run without credentials or external API calls.
- Tests:
  - `python -m pytest --noconftest backend/tests/test_base_transport.py backend/tests/test_openai_compat_transport.py -q`
  - `python -m py_compile backend/llm_providers/shared/base_transport.py backend/llm_providers/transports/__init__.py backend/llm_providers/transports/openai_compat.py`
  - targeted existing OpenAI service/tool-adapter regressions selected by precheck
- Model: 5.6 Terra
- Reason:
  - The approved Spec requires `OpenAICompatTransport` first. Pairing it with the minimal base contract proves one real API-family implementation before adding provider-native transports or changing any live dispatch path.
- Closeout:
  - Final Audit: `PASS` in `documentation/tasks/TASK-M6B.1_final_audit.md`.
  - Added the minimal abstract `BaseTransport` contract plus injected-service `OpenAICompatTransport`; no existing gateway, service, runner, resolver, feature-flag consumer, or production path changed.
  - Focused transport regressions (`6/6`), existing ToolCallAdapter regression (`12/12`), syntax, scoped diff, Cursor allowlist evidence, and manual default-off OpenAI Berlin-weather smoke passed; the combined audit rerun passed `18/18`.
  - Non-blocking follow-up: the shared Cursor delegate wrapper still forwards unsupported `--cursor-pool`; the direct Cursor worker is the documented temporary fallback.
  - `TASK-M6B.2` through `TASK-M6B.5` remain open and are not covered by this closeout.
  - Changelog skipped: internal, default-off transport-contract groundwork with no user-facing behavior change.

### TASK-M6B.2 Add the Gemini-native transport as a 1:1 service wrapper
- Ziel:
  - Implement Phase-B `T-B3` as a Gemini-native transport that wraps the existing service without moving Gemini policy or proto/history semantics.
- Scope:
  - `GeminiNativeTransport` only, after `TASK-M6B.1` has validated the base contract. No resolver or gateway integration.
- Files:
  - `backend/llm_providers/transports/gemini_native.py`
  - focused transport tests
- Steps:
  1. Implement the base contract through the existing Gemini service seam.
  2. Preserve native schema/proto/history behavior in the existing Gemini boundary.
  3. Add hermetic contract and delegation regressions.
- Acceptance Criteria:
  - Gemini implements the established transport contract without changing gateway policy or live routing.
- Tests:
  - focused Gemini transport and existing adapter regressions selected by precheck
- Model: 5.6 Terra
- Reason:
  - The Spec explicitly requires a 1:1 existing-service wrapper after the OpenAI-compatible first slice.

### TASK-M6B.3 Add the Ollama-local transport
- Ziel:
  - Implement Phase-B `T-B4` as an Ollama-local transport over the existing local service seam.
- Scope:
  - `OllamaLocalTransport` only, after the base contract is proven. No resolver or gateway integration.
- Files:
  - `backend/llm_providers/transports/ollama_local.py`
  - focused transport tests
- Steps:
  1. Implement the base contract through the existing Ollama service seam.
  2. Add hermetic delegation and local-capability regressions.
- Acceptance Criteria:
  - Ollama implements the established contract without changing live routing.
- Tests:
  - focused Ollama transport regressions selected by precheck
- Model: 5.6 Terra
- Reason:
  - This maps directly to the approved Phase-B `T-B4` scope.

### TASK-M6B.4 Introduce runtime_llm resolution and the transport registry seam
- Ziel:
  - Implement Phase-B `T-B5`: resolve provider/model to the approved `api_mode`, credentials/base URL, transport class, and model ID.
- Scope:
  - `runtime_llm.py` and the bounded `llm_gateway.py` registry seam only, after concrete transports exist. No broad gateway delegation.
- Files:
  - `backend/llm_providers/runtime_llm.py`
  - `backend/services/llm_gateway.py`
  - focused resolver tests
- Steps:
  1. Implement the Spec mapping for OpenAI, Gemini, OpenRouter, Ollama, and the Epic-5 Codex placeholder.
  2. Add deterministic resolver and failure-mode tests.
- Acceptance Criteria:
  - The resolver returns the Spec-declared API-family mapping without creating provider-specific gateway paths.
- Tests:
  - focused runtime resolver tests selected by precheck
- Model: 5.6 Terra
- Reason:
  - The resolver is a distinct dispatch decision and must follow contract-proven concrete transports.

### TASK-M6B.5 Delegate gateways through the transport layer behind the Phase-B flag
- Ziel:
  - Implement Phase-B `T-B6` by routing the bound gateway entry point through the resolver, transport, and shared runner behind `TRANSPORT_LAYER_ENABLED=false`.
- Scope:
  - One bounded gateway integration after individual transport/resolver evidence. No Phase-C Websearch cleanup or provider-branch removal beyond the bound delegation path.
- Files:
  - bound gateway files determined by precheck
  - `backend/services/llm_gateway.py`
  - focused flag-off/flag-on regressions
- Steps:
  1. Add the default-off integration seam.
  2. Prove legacy-path preservation and enabled-path transport delegation.
  3. Record focused provider parity evidence.
- Acceptance Criteria:
  - The flag-off path remains behavior-preserving and the enabled path reaches transport plus runner for the bound providers.
- Tests:
  - focused gateway/transport parity regressions selected by precheck
- Model: 5.6 Terra
- Reason:
  - Live delegation is explicitly later than the transport contracts and resolver and remains a separately auditable risk slice.
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.2
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only the Phase-B T-B3 thin Gemini-native transport wrapper over the existing Gemini service seam.
- Execution is Cursor-first and bounded to the two transport files and one new hermetic test; Codex reviews the allowlisted diff and evidence on 5.6 Terra/high.
- The existing Gemini service remains the authority for native proto/schema/history conversion, tool adaptation, and request/response semantics. No caller is rerouted and `TRANSPORT_LAYER_ENABLED` remains default-off and unconsumed.
Affected Files:
- backend/llm_providers/transports/gemini_native.py
- backend/llm_providers/transports/__init__.py
- backend/tests/test_gemini_native_transport.py
Evidence Focus:
- python -m pytest --noconftest backend/tests/test_gemini_native_transport.py -q
- python -m py_compile backend/llm_providers/transports/__init__.py backend/llm_providers/transports/gemini_native.py
- focused existing Gemini service and ToolCallAdapter regressions selected by the executioner
- git diff --check and scoped review against the exclusions below
Scope-Regel:
- Implement only TASK-M6B.2. No change to Gemini service/gateway, ToolLoopRunner, ToolCallAdapter, runtime resolver, llm_gateway, execution engine, native proto/schema/history behavior, model/Flash policy, grounding/cost attribution, synthesis/drill-down, streaming, provider fallback, resolver/gateway integration, or TRANSPORT_LAYER_ENABLED consumer/flip.
Automated Evidence Gate:
- python -m pytest --noconftest backend/tests/test_gemini_native_transport.py -q
- python -m py_compile backend/llm_providers/transports/__init__.py backend/llm_providers/transports/gemini_native.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and task-breakdown handoff verified. `TASK-M6B.1` is independently closed; `TASK-M6B.2` is the unique next target in the same approved Phase-B task artifact.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task changes no TestSpec or oracle; the named transport test is a source-owned focused regression.
Keep Context:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_b.md
- documentation/tasks/TASK-M6B.2_task_breakdown.md
- backend/llm_providers/shared/base_transport.py and backend/llm_providers/gemini/service.py as read-only contract/service seams
Drop Context:
- completed M6B.1 implementation/audit history
- later M6B.3 through M6B.5 tasks
- unrelated ChromaDB-dependent suites and Git/release history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Cursor-first implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: The one-wrapper scope, three-file allowlist, binary acceptance criteria, and hermetic evidence are explicit; Gemini-native behavior stays delegated to the existing service.
User Action: Start only the bounded Cursor-first TASK-M6B.2 execution slice and return the candidate diff and focused evidence for Codex review.
```

## Changed Files

```text
M backend/llm_providers/transports/__init__.py
?? backend/llm_providers/transports/gemini_native.py
?? backend/tests/test_gemini_native_transport.py
```

## Artifact Inventory

```text
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.2_execution_result.md (3495 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.2_task_breakdown.md (4200 bytes)
DIR C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B2-CURSOR-DIRECT-20260712 (6 files)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B2-CURSOR-DIRECT-20260712\changed_files.txt (144 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B2-CURSOR-DIRECT-20260712\cursor_response.json (1719 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B2-CURSOR-DIRECT-20260712\dispatcher_result.json (4564 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B2-CURSOR-DIRECT-20260712\session_id.txt (38 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B2-CURSOR-DIRECT-20260712\stderr.log (0 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B2-CURSOR-DIRECT-20260712\stdout.log (1640 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\Cursor specs\PROVIDER_TRANSPORT_REFACTOR_SPEC.md (27280 bytes)
```

## Diff Summary

```text
backend/llm_providers/transports/__init__.py | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)
```

## Validation

```text
# TASK EXECUTION RESULT - TASK-M6B.2

Canonical State: HANDOFF
Target Task: TASK-M6B.2

## Scope Delivered
- Added `GeminiNativeTransport` as the thin `BaseTransport` implementation over an injected existing Gemini service seam.
- Delegated non-streaming send, ToolCallAdapter-backed Gemini tool conversion, and second-call history preparation unchanged to the existing service.
- Exported the transport and added hermetic fake-service regressions. No Gemini service, gateway, ToolLoopRunner, ToolCallAdapter, resolver, feature-flag consumer, or live runtime path changed.

Changed Files:
- `backend/llm_providers/transports/gemini_native.py`
- `backend/llm_providers/transports/__init__.py`
- `backend/tests/test_gemini_native_transport.py`

## Cursor-First Execution Evidence
- Shared delegate attempt: blocked before Cursor start because the wrapper still passes unsupported `--cursor-pool`; evidence: `documentation/tasks/TASK-M6B.2_cursor_delegate_result.json`.
- Direct approved Cursor Composer fallback: `PASS`, session `5fe52784-f7b0-4d5b-894f-cf487808b5a9`; all three changed files matched the exact allowlist and the worker reported no blockers.
- Cursor evidence: `documentation/codex/model-routing/cursor-worker-runs/WF-M6B2-CURSOR-DIRECT-20260712/`.

Executed Checks:
- Cursor focused pytest: PASS (`4 passed in 2.81s`).
- Cursor `py_compile`: PASS.
- Codex focused suite: `python -m pytest --noconftest backend/tests/test_gemini_native_transport.py backend/tests/test_tool_call_adapter.py backend/tests/llm_providers/test_gemini_service.py::test_provider_generate_response_with_tool_call backend/tests/llm_providers/test_gemini_service.py::test_gemini_name_mapping_resolves_provider_safe_names_to_canonical_skill -q` - PASS (`18 passed in 2.14s`).
- Codex `py_compile` for the Gemini transport package: PASS.
- `git diff --check`: PASS.
- Precheck handoff validator: PASS before implementation.

Auto-Verification:
- Status: PASS
- Evidence: focused transport, existing ToolCallAdapter, focused Gemini-service, syntax, allowlist, and diff checks all pass.

Manual Janus Validation Gate:
- Status: PASS
- Test Example: In a development session with `TRANSPORT_LAYER_ENABLED` unset or `false`, select Gemini and send `Wie ist das Wetter in Berlin?`.
- Expected Result: PASS on 2026-07-12 at approximately 14:53 Europe/Berlin. With Gemini and `TRANSPORT_LAYER_ENABLED=false`, Janus executed the existing weather path and returned Berlin weather sourced from Open-Meteo without transport-layer activation or visible native-Gemini regression.
- If Failed: route to janus-debug with the request, provider/model, backend log excerpt, and the flag value.
- If Passed: route to janus-final-audit after creating an audit package.

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts:
- `documentation/tasks/TASK-M6B.2_preimplementation_check.md`
- this execution result
- Cursor run directory and focused test output
Audit Package: create from this now-complete execution evidence before final audit.
Evidence Paths:
- `documentation/codex/model-routing/cursor-worker-runs/WF-M6B2-CURSOR-DIRECT-20260712/`
Failure Code: N/A
Changed Files: three allowlisted backend files only.
Decision: HANDOFF to audit-package creation and final audit.
Reason: Automated evidence and the explicit manual default-off Gemini smoke are PASS.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
New Chat: no
Next User Action: none; proceed with the bound final audit.
```

## Notes

No additional notes provided.

## Risks

Transport is intentionally unintegrated; future resolver/gateway wiring is outside this target. Native Gemini proto/schema/history, policy, grounding/cost attribution, synthesis, and streaming remain owned by existing service/gateway seams. Shared Cursor delegate wrapper still has an unrelated --cursor-pool defect.

## Open Issues

None for TASK-M6B.2; later M6 Phase-B tasks remain separate.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.2_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
