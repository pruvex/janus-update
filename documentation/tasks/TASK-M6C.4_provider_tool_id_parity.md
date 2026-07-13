TASK-M6C.4
- Source Spec: `documentation/SPEC/M6C4_provider_tool_id_parity.md`
- Backlog Item: `N/A`
- Feature: Epic 4 Provider Transport Refactor, Phase C Tool-ID Parity
- Generated At: 2026-07-13

## Generated Tasks

### TASK-M6C.4 Add hermetic OpenAI/Gemini canonical tool-ID parity coverage
- Ziel:
  - Add one hermetic regression module proving canonical tool-ID roundtrip parity for `system.weather` and `system.websearch`.
- Scope:
  - Assert OpenAI and Gemini outbound names are provider-safe and equal for the two selected canonical IDs.
  - Assert each provider adapter restores the provider-safe names to the original canonical IDs.
  - Preserve all product source behavior; this slice adds tests only.
- Files:
  - `backend/tests/test_provider_parity.py` (new)
  - `backend/tests/test_tool_call_adapter.py` (existing regression selection only)
- Steps:
  1. Express the approved two-skill matrix as parameterized hermetic assertions.
  2. Check outbound provider-safe naming and inbound canonical restoration for both providers.
  3. Run the new suite with the existing adapter regression module and scoped diff validation.
- Acceptance Criteria:
  - `system.weather` has OpenAI/Gemini canonical roundtrip parity.
  - `system.websearch` has OpenAI/Gemini canonical roundtrip parity.
  - The new suite requires no network access or provider credentials.
  - No non-test product source file changes.
- Tests:
  - `python -m pytest backend/tests/test_provider_parity.py backend/tests/test_tool_call_adapter.py -q`
  - Syntax and scoped diff checks selected by preimplementation check.
- Model: 5.6 Terra
- Reason:
  - The approved C4 Spec defines one small, binary test-only parity slice with no runtime provider authority.
