TASK-M6C.2
- Source Spec: `documentation/SPEC/Spec Done/M6C2_response_postprocessor_extraction.md`
- Backlog Item: `N/A`
- Feature: Epic 4 Provider Transport Refactor, Phase C Response Post-Processor Extraction
- Generated At: 2026-07-13

## Generated Tasks

### TASK-M6C.2 Extract shared OpenAI and Gemini response post-processors
- Ziel:
  - Deliver the approved Phase-C T-C2 behavior-preserving shared response post-processing boundary for both OpenAI-compatible and Gemini-native response finishing.
- Scope:
  - Add the shared response-postprocessor registry named by the approved parent Spec.
  - Move only the existing OpenAI release-list link behavior and Gemini grounding/link-rendering behavior into that boundary.
  - Make `backend/services/llm_gateway.py:reason_and_respond` the selected central post-response owner after a provider silo returns.
  - Remove only the selected direct OpenAI/Gemini post-processing invocations from gateway ownership; preserve preceding gateway-owned quality, cost, and synthesis behavior.
  - Preserve unchanged responses for missing optional metadata or an unregistered provider family.
  - Keep T-C1 Websearch policy, T-C3 provider-branch removal, T-C4 parity work, provider fallback, model policy, tool execution, streaming, persistence, and UI redesign out of scope.
- Files:
  - `backend/llm_providers/shared/response_postprocessors.py` (new)
  - `backend/services/llm_gateway.py`
  - `backend/llm_providers/openai/gateway.py`
  - `backend/llm_providers/gemini/gateway.py`
  - `backend/tests/test_response_postprocessors.py` (new)
  - Existing focused OpenAI and Gemini response regression tests selected by task breakdown
- Steps:
  1. Bind the consumed `llm_gateway.reason_and_respond` return seam and the exact existing OpenAI/Gemini synthesis context it receives.
  2. Introduce a provider-family registry that applies the existing selected behavior after a silo response without changing the provider response contract.
  3. Route only that central return seam through the registry, remove the selected direct gateway invocations, and retain unchanged behavior for unregistered families or absent optional metadata.
  4. Add hermetic regressions for OpenAI links, Gemini grounding/links, missing metadata, and unregistered provider families.
- Acceptance Criteria:
  - Existing OpenAI release-list link output remains visible after the shared boundary.
  - Existing Gemini grounding and link output remains visible after the shared boundary.
  - Missing optional metadata and unregistered families leave the response unchanged without a rendering failure.
  - No Websearch, provider fallback, model policy, transport enablement, tool execution, streaming, persistence, or unrelated provider branch behavior changes.
  - Focused regressions run without network access or provider credentials.
- Tests:
  - New hermetic response-postprocessor regression module.
  - Existing focused OpenAI and Gemini response/synthesis regressions selected after live-seam discovery.
  - Syntax and scoped-diff checks selected by preimplementation check.
- Model: 5.6 Terra
- Reason:
  - User locked the full two-provider T-C2 migration as one behavior-preserving Phase-C slice; the provider response seam is cross-system and requires high-reasoning task refinement before implementation.

## Deferred Phase-C Work

- `T-C3` dead provider-branch removal and `T-C4` provider parity tests remain separate later tasks.
