# AUDIT_PACKAGE

Generated: 2026-07-13 13:44:38 UTC

## Goal

Audit TASK-M6B.6: direct Gemini normal tool-loop transport delegation behind the default-off Phase-B flag.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: N/A WITH REASON: Phase-B source spec remains active for subsequent provider rollouts; this audit closes only TASK-M6B.6.
- Task File: documentation\tasks\TASK-M6_transport_phase_b.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation\tasks\TASK-M6B.6_preimplementation_check.md
- Manual Janus Evidence: PRESENT
- Pipeline Completion Status: remaining tasks continue independently; TASK-M6B.6 implementation complete yes

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
- Closeout:
  - Final Audit: `PASS` in `documentation/tasks/TASK-M6B.2_final_audit.md`.
  - Added `GeminiNativeTransport` as a thin injected-service wrapper and exported it from the transport package; no Gemini service, gateway, ToolLoopRunner, ToolCallAdapter, resolver, feature-flag consumer, or production path changed.
  - Focused transport (`4/4`), existing ToolCallAdapter plus Gemini-service checks (`14/14`), combined audit rerun (`18/18`), syntax, scoped diff, Cursor allowlist evidence, and manual default-off Gemini Berlin-weather smoke passed.
  - Non-blocking follow-up: the shared Cursor delegate wrapper still forwards unsupported `--cursor-pool`; the direct Cursor worker is the documented temporary fallback.
  - `TASK-M6B.3` through `TASK-M6B.5` remain open and are not covered by this closeout.
  - Changelog skipped: internal, default-off transport-contract groundwork with no user-facing behavior change.

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
- Closeout:
  - Final Audit: `PASS` in `documentation/tasks/BACKLOG-127_FINAL_AUDIT.md`.
  - Added and exported `OllamaLocalTransport` as the same thin existing-service wrapper proven for the preceding transports; no resolver, gateway integration, flag consumer, or live routing changed.
  - The mandatory default-off Ollama weather smoke passed after the independently tracked BACKLOG-125/126/127 service, gateway, and Atomic-loop fixes. Focused combined suite: `27 passed`; syntax and scoped diff: PASS.
  - Non-blocking follow-up: the shared Cursor wrapper output decoding/argument path remains separate tooling debt; direct Cursor work stayed bounded and Codex-owned validation accepted the diff.
  - `TASK-M6B.4` and `TASK-M6B.5` remain open and are not covered by this closeout.
  - Changelog updated: default-off local-Ollama runtime recovery is user-visible.

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
- Closeout:
  - Final Audit: `PASS` in `documentation/tasks/TASK-M6B.4_FINAL_AUDIT.md`.
  - Added deterministic `runtime_llm` provider-family resolution and a non-consuming registry lookup seam in `llm_gateway.py`; no gateway call site, flag consumer, credential retrieval, fallback, streaming, or live routing changed.
  - Focused resolver plus Ollama regression suite (`17 passed`), syntax, scoped diff, bounded Cursor-worker review, and default-off Ollama Berlin-weather smoke passed.
  - The manual smoke also identified and then validated the independent `BACKLOG-128` canonical weather-alias repair; it does not expand T-B5's resolver contract.
  - `TASK-M6B.5` remains open.

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
- Closeout:
  - Final Audit: `PASS` in `documentation/tasks/TASK-M6B.5_FINAL_AUDIT.md`.
  - The first enabled path is deliberately restricted to the existing direct `openai` gateway. With `TRANSPORT_LAYER_ENABLED=false` or absent, legacy silo dispatch is unchanged; with the flag true, the gateway receives `OpenAICompatTransport` only at its existing service request and second-call-history seams.
  - Gateway-owned policy, tool-loop control, synthesis, response shaping, cost persistence, and streaming remain untouched. OpenRouter, Gemini, Google, Ollama, Codex, and Phase-C work remain outside this delivery.
  - Focused flag-off/flag-on gateway, runner, and resolver regressions (`27 passed`), syntax, scoped diff, and enabled OpenAI Berlin-weather smoke passed.
  - Non-blocking follow-up: the shared Cursor delegate still forwards unsupported `--cursor-pool`; the direct worker did not return a completion artifact, so Codex-owned review and validation remain authoritative.

### TASK-M6B.6 Add the Gemini normal tool-loop to the Phase-B flag
- Ziel:
  - Extend Phase-B `T-B6` with one provider-isolated Gemini normal-tool-loop transport path after the direct OpenAI slice.
- Scope:
  - With `TRANSPORT_LAYER_ENABLED=true`, inject `GeminiNativeTransport` into the existing direct `gemini` gateway only for `_run_simple_tool_loop` and its existi
```

## Pre-Implementation Check

```text
# PREIMPLEMENTATION CHECK - TASK-M6B.6

PRE-CHECK RESULT
PRE-CHECK PASSED

## Bound Identity

- Target Task: `TASK-M6B.6`
- Target Subtask: `N/A`
- Task: `documentation/tasks/TASK-M6_transport_phase_b.md`
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Phase-B T-B6)
- Decision Summary: `documentation/tasks/TASK-M6B.6_decision_summary.md`
- Backlog Item: `N/A WITH REASON` (approved Phase-B task continuation, not a Backlog item)
- Assigned Model: `5.6 Terra`
- Mode: `SINGLE_TASK_PRECHECK`

## Gate Decision

- Atomic scope: PASS. The task adds one direct `gemini` transport injection behind the existing default-off `TRANSPORT_LAYER_ENABLED` flag.
- Scope boundary: PASS. Only `GeminiGateway._run_simple_tool_loop` receives the injected seam. Engine-owned Gemini and drill-down stay on their current service seams; no direct `google` gateway route exists or is created.
- Product decisions: PASS. The operator selected normal Gemini tool-loop only; no unresolved provider, fallback, credential, or architecture decision remains.
- Risk: MEDIUM. The change touches a live provider dispatch seam, but the default is false and tests can prove both routing states and exclusions hermetically.
- Test surface: PASS. Focused flag routing/injection tests plus existing Gemini runner coverage are available without credentials or network access.

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.6
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A WITH REASON
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Inject GeminiNativeTransport only when TRANSPORT_LAYER_ENABLED is true and the existing direct gemini silo is selected.
- Pass the transport only into the normal _run_simple_tool_loop request and second-call-history seams.
- Keep engine-owned Gemini, drill-down, Google, OpenRouter, Ollama, Codex, streaming, model policy, grounding, cost attribution, synthesis, and response shaping unchanged.
Affected Files:
- backend/services/llm_gateway.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_transport_layer_gemini_gateway.py
Evidence Focus:
- python -m pytest backend/tests/test_transport_layer_gemini_gateway.py backend/tests/test_gemini_tool_loop_runner.py backend/tests/test_runtime_llm.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/gemini/gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_transport_layer_gemini_gateway.py backend/tests/test_gemini_tool_loop_runner.py backend/tests/test_runtime_llm.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound Phase-B T-B6 task and locked normal-loop-only decision
- direct gemini silo and GeminiGateway service/history seams
- focused regression commands
Drop Context:
- old failed drafts
- unrelated provider rollouts, backlog work, and audit history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end
```

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
User Action: Codex continues with the bounded Cursor-first execution slice; manual validation is requested only after automated evidence passes.
```

## Changed Files

```text
M backend/llm_providers/gemini/gateway.py
 M backend/services/llm_gateway.py
?? backend/tests/test_transport_layer_gemini_gateway.py
```

## Artifact Inventory

```text
FILE C:\KI\Janus-M6-Transport-Prep\backend\tests\test_transport_layer_gemini_gateway.py (15427 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.6_decision_summary.md (2186 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.6_task_breakdown.md (2113 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.6_execution_result.md (4305 bytes)
DIR C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B6-CURSOR-20260713-R2 (6 files)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B6-CURSOR-20260713-R2\changed_files.txt (128 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B6-CURSOR-20260713-R2\cursor_response.json (1858 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B6-CURSOR-20260713-R2\dispatcher_result.json (4936 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B6-CURSOR-20260713-R2\session_id.txt (38 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B6-CURSOR-20260713-R2\stderr.log (0 bytes)
  FILE C:\KI\Janus-M6-Transport-Prep\documentation\codex\model-routing\cursor-worker-runs\WF-M6B6-CURSOR-20260713-R2\stdout.log (1779 bytes)
```

## Diff Summary

```text
backend/llm_providers/gemini/gateway.py | 100 ++++++++++++++++++++++++++++++--
 backend/services/llm_gateway.py         |   6 ++
 2 files changed, 100 insertions(+), 6 deletions(-)
```

## Validation

```text
# TASK EXECUTION RESULT - TASK-M6B.6

TASK EXECUTION RESULT
Canonical State: HANDOFF
Target Task: TASK-M6B.6

## Bound Result

- With `TRANSPORT_LAYER_ENABLED` absent or false, the direct Gemini silo dispatch remains unchanged and receives no transport dependency.
- With the flag true, only the direct `gemini` silo constructs `GeminiNativeTransport` from its existing gateway service.
- The transport is supplied only to `_run_simple_tool_loop` and reaches the normal legacy-loop request/history seams and runner/MoA-synthesis seams.
- Gateway-owned model policy, grounding, cost attribution, synthesis behavior, response shaping, and streaming remain in `GeminiGateway`.
- Engine-owned and drill-down Gemini paths do not receive the transport. No direct `google` route was added; OpenAI, OpenRouter, Ollama, and Codex remain outside this slice.

Changed Files:
- `backend/services/llm_gateway.py`
- `backend/llm_providers/gemini/gateway.py`
- `backend/tests/test_transport_layer_gemini_gateway.py`

## Cursor-first Evidence

- Shared Cursor Composer delegate: tooling failure only (`CURSOR_WORKER_OUTPUT_UNREADABLE`) because it still passes unsupported `--cursor-pool`; evidence: `documentation/tasks/TASK-M6B.6_cursor_delegate_result.json`.
- Direct Cursor Composer worker: PASS as a bounded proposal-first candidate with the exact three-file allowlist; Codex reviewed the diff and made two in-scope seam repairs (preserve injected legacy service when flag-off and send MoA synthesis through the enabled transport).
- Worker evidence: `documentation/codex/model-routing/cursor-worker-runs/WF-M6B6-CURSOR-20260713-R2/`.

Executed Checks:
- `validate_precheck.py documentation/tasks/TASK-M6B.6_preimplementation_check.md`: PASS.
- `python -m pytest backend/tests/test_transport_layer_gemini_gateway.py backend/tests/test_gemini_tool_loop_runner.py backend/tests/test_runtime_llm.py -q`: PASS (`31 passed`).
- `python -m pytest backend/tests/test_transport_layer_gemini_gateway.py backend/tests/test_gemini_tool_loop_runner.py backend/tests/test_runtime_llm.py backend/tests/test_transport_layer_openai_gateway.py -q`: PASS (`40 passed`).
- `python -m py_compile backend/services/llm_gateway.py backend/llm_providers/gemini/gateway.py`: PASS.
- `git diff --check`: PASS.
- `npx playwright test --list`: PASS (the repository has no bounded provider-transport browser test; live provider verification is the manual gate below).

Auto-Verification:
- Status: PASS
- Evidence: focused flag-off/flag-on routing, legacy and runner request/history seams, MoA synthesis seam, engine/drill-down exclusion, existing Gemini runner, resolver, OpenAI non-regression, syntax, diff, and Playwright discovery checks.

Manual Janus Validation Gate:
- Status: PASS
- Test Example: In `C:\KI\Janus-M6-Transport-Prep`, run `$env:TRANSPORT_LAYER_ENABLED = "true"` and `npm run start-dev`; choose a working Gemini model and send `Wie ist das Wetter in Berlin?`.
- Expected Result: PASS at 2026-07-13 15:42 â€” Janus rendered the Berlin weather answer with `Quelle: Open-Meteo`, without raw tool JSON, a gateway exception, or a transport error.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts: `documentation/tasks/TASK-M6B.6_execution_result.md`; `documentation/tasks/TASK-M6B.6_preimplementation_check.md`; `documentation/tasks/TASK-M6B.6_task_breakdown.md`; `documentation/tasks/TASK-M6B.6_decision_summary.md`
Audit Package: pending build
Evidence Paths: `documentation/codex/model-routing/cursor-worker-runs/WF-M6B6-CURSOR-20260713-R2/`; `documentation/tasks/TASK-M6B.6_cursor_delegate_result.json`; focused pytest output recorded above
Failure Code: N/A
Changed Files: `backend/services/llm_gateway.py`; `backend/llm_providers/gemini/gateway.py`; `backend/tests/test_transport_layer_gemini_gateway.py`
Decision: HANDOFF
Reason: Automated evidence and the required enabled Gemini runtime smoke both pass; final audit is required before documentation closure.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Next User Action: Final audit and documentation closure continue automatically in this Codex task. No commit, push, or sync has been performed; remote state does not yet contain M6B.6.
```

## Notes

No additional notes provided.

## Risks

Shared Cursor delegate passes unsupported --cursor-pool; direct worker evidence and Codex-owned review remain authoritative. No direct google gateway route exists or is introduced.

## Open Issues

None. Manual enabled Gemini weather smoke passed at 15:42.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.6_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
