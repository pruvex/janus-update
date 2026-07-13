# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.6 Terra
recommended_reasoning: high
new_chat: no
complexity_score: 30
confidence: HIGH
dashboard_hint: SAFE
reason: Two-skill hermetic parity contract protects the established shared provider adapter boundary.

## FEATURE IDENTITY

- Feature Name: M6C.4 OpenAI/Gemini Canonical Tool-ID Parity
- Feature ID: M6C4-PROVIDER-TOOL-ID-PARITY
- Parent Initiative: Epic 4 Provider Transport Refactor, Phase C
- Decision Source: `documentation/tasks/TASK-M6C.4_decision_summary.md`
- Feature Type: Internal regression coverage

## USER VALUE

The same shared Janus skills keep their canonical identities across OpenAI and Gemini provider adaptation.

## TARGET SURFACE

- Primary Surface: Existing shared ToolCallAdapter provider boundary
- Existing or New Surface: Existing adapter with a new parity-only backend test module
- Existence Confirmation: confirmed by repository review
- Affected Provider Families: OpenAI-compatible and Gemini-native
- Non-Surfaces: Runtime provider calls, UI, persistence, streaming, and tool execution

## USER ACTION SURFACE

- User Trigger: Phase-C T-C4 continuation
- Success Feedback: Hermetic regression evidence only
- Cancel or Undo: Not applicable

## SYSTEM BEHAVIOR

- The parity test uses canonical `system.weather` and `system.websearch` IDs.
- OpenAI and Gemini outbound names are asserted to be provider-safe and equal for these IDs.
- OpenAI and Gemini inbound mapping is asserted to restore the canonical Janus IDs.
- The test does not contact a provider or alter adapter behavior.

## DATA / PERSISTENCE

- New Data: None
- Data Migration: None
- Persistence Change: None
- Credentials or Secrets: None

## CONSTRAINTS

- The slice covers exactly `system.weather` and `system.websearch`.
- The slice adds regression evidence only and must not modify product source behavior.
- T-C3 cleanup, whole-catalog parity, Ollama, OpenRouter, transport enablement, and runtime calls remain excluded.

## SECURITY / PRIVACY

- Sensitive Data: None
- External Services: None
- Privacy Constraint: No credentials, prompts, or live provider output may be used.

## EDGE CASES

- Provider-safe outbound names must not replace canonical internal IDs.
- A test failure reports the provider and skill ID that drifted.

## DEFINITION OF DONE

- [ ] Wenn `system.weather` geprüft wird, dann stellen OpenAI und Gemini denselben kanonischen Skill-ID-Roundtrip her.
- [ ] Wenn `system.websearch` geprüft wird, dann stellen OpenAI und Gemini denselben kanonischen Skill-ID-Roundtrip her.
- [ ] Wenn ein Outbound-Name geprüft wird, dann ist er für beide Provider provider-sicher und vom kanonischen ID-Vertrag ableitbar.
- [ ] Wenn die Parity-Suite läuft, dann benötigt sie keine Provider-Credentials oder Netzwerkzugriffe.
- [ ] Wenn der Slice fertig ist, dann enthält der Diff keine Produktcodeänderung.

## TEST STRATEGY

- Automated Coverage: new hermetic parity test plus existing ToolCallAdapter regression module
- Manual Evidence: Not applicable; test-only coverage with no runtime behavior change
- Regression Boundary: scoped diff contains only test and bound pipeline artifacts
- Network Requirement: None

## OUT OF SCOPE

- Product implementation or adapter behavior changes
- Runtime provider, transport, streaming, fallback, or tool-execution changes
- C3 branch deletion and whole-catalog parity
- Ollama, OpenRouter, Codex/OAuth, persistence, UI, release, and Git actions

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 6
- Architectural Risk: 6
- State / Persistence Complexity: 0
- Cross-System Dependencies: 10
- Ambiguity Level: 8
- Total Complexity Score: 30
- Routing Decision: 5.6 Terra
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: SAFE

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 30
- **Risk:** LOW
- **Recommended Review Model:** 5.6 Terra
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-13
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review
