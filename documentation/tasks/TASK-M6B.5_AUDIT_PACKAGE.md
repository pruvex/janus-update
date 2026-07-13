# AUDIT_PACKAGE

Generated: 2026-07-13 12:49:42 UTC

## Goal

Audit M6B.5 direct OpenAI flag-gated transport injection after manual enabled-path evidence.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: N/A WITH REASON: parent provider transport refactor remains in progress; this audit binds Phase-B T-B6 direct OpenAI slice only.
- Task File: documentation/tasks/TASK-M6_transport_phase_b.md
- Backlog Item: N/A WITH REASON
- Pre-Implementation Check: documentation/tasks/TASK-M6B.5_preimplementation_check.md
- Manual Janus Evidence: PRESENT: 2026-07-13 14:48 enabled TRANSPORT_LAYER_ENABLED=true OpenAI Berlin-weather smoke rendered Open-Meteo answer.
- Pipeline Completion Status: Implementation complete: direct OpenAI Phase-B T-B6 slice only; OpenRouter and other provider paths remain out of scope.

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
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.5
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement one reversible Phase-B flag-on path for the existing direct `openai` provider only. `TRANSPORT_LAYER_ENABLED` is false by default; absent/false continues the exact existing silo dispatch.
- At the gateway router, resolve the provider and inject `OpenAICompatTransport` only when the flag is true, the provider is `openai`, and the selected OpenAI gateway exposes its existing service. The OpenAI gateway consumes the optional transport only for current service-level request and second-call-history seams.
- The existing gateway keeps provider access policy, skill selection, MoA/tool-loop policy, synthesis, response shaping, cost persistence, and streaming ownership. OpenRouter has resolver metadata but no direct runtime gateway silo and stays excluded.
Affected Files:
- backend/services/llm_gateway.py
- backend/llm_providers/openai/gateway.py
- backend/tests/test_transport_layer_openai_gateway.py
- backend/tests/test_runtime_llm.py (only if required to assert the new flag boundary)
Evidence Focus:
- python -m pytest backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_openai_tool_loop_runner.py backend/tests/test_runtime_llm.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/openai/gateway.py backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_runtime_llm.py
- git diff --check
Scope-Regel:
- Implement only the direct OpenAI flag-gated transport injection. No OpenRouter routing, Gemini/Google/Ollama/Codex enablement, transport-contract expansion, provider fallback, credential retrieval, streaming, Websearch, policy migration, legacy removal, or dashboard/documentation closure.
Automated Evidence Gate:
- python -m pytest backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_openai_tool_loop_runner.py backend/tests/test_runtime_llm.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/openai/gateway.py backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_runtime_llm.py
- git diff --check
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Phase-B T-B6, TASK-M6B.5, user-locked first-provider decision, task-breakdown handoff, and current direct OpenAI gateway seam verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task changes no TestSpec or oracle.
Keep Context:
- documentation/tasks/TASK-M6B.5_decision_summary.md
- documentation/tasks/TASK-M6B.5_task_breakdown.md
- backend/services/llm_gateway.py and backend/llm_providers/openai/gateway.py
- focused flag-off/flag-on regression commands
Drop Context:
- completed M6B.1-M6B.4 audit history
- Ollama BACKLOG-125 through BACKLOG-128 recovery details
- later multi-provider rollout and Phase-C work
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Cursor-first bounded implementation candidate, Codex-owned review/validation, then a manual default-off and enabled OpenAI smoke gate.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: This is the first live, flag-gated provider integration; the scope is restricted to one direct provider path and requires strict legacy-path preservation.
User Action: Authorize only the bounded Cursor-first TASK-M6B.5 execution slice.
```

## Changed Files

```text
M backend/llm_providers/openai/gateway.py
 M backend/services/llm_gateway.py
?? backend/tests/test_transport_layer_openai_gateway.py
```

## Artifact Inventory

```text
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.5_execution_result.md (3853 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.5_decision_summary.md (2266 bytes)
```

## Diff Summary

```text
backend/llm_providers/openai/gateway.py | 106 ++++++++++++++++++++++++++++----
 backend/services/llm_gateway.py         |  15 +++++
 backend/tests/test_transport_layer_openai_gateway.py | new focused regression
 3 files changed in bound implementation scope
```

## Validation

```text
python -m pytest backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_openai_tool_loop_runner.py backend/tests/test_runtime_llm.py -q: PASS (27 passed)
python -m py_compile backend/services/llm_gateway.py backend/llm_providers/openai/gateway.py backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_runtime_llm.py: PASS
git diff --check: PASS
Manual Janus evidence: PASS (2026-07-13 14:48, enabled direct OpenAI Berlin-weather smoke returned rendered Open-Meteo answer)
```

## Notes

No additional notes provided.

## Risks

The shared Cursor delegate wrapper has a known unsupported `cursor-pool` argument. The direct worker did not return a completion artifact, so it is non-authoritative; Codex reviewed the complete allowlisted diff and owns all validation. M6B.5 does not enable OpenRouter, Gemini, Google, Ollama, or Codex.

## Open Issues

No open issue in direct OpenAI scope.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B.5_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
