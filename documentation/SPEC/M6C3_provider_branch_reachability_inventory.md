# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.6 Terra
recommended_reasoning: high
new_chat: no
complexity_score: 42
confidence: HIGH
dashboard_hint: CAUTION
reason: Evidence-only provider reachability inventory must prevent unsafe Phase-C branch deletion.

## FEATURE IDENTITY

- Feature Name: M6C.3 Provider-Branch Reachability Inventory
- Feature ID: M6C3-PROVIDER-BRANCH-INVENTORY
- Parent Initiative: Epic 4 Provider Transport Refactor, Phase C
- Decision Source: `documentation/tasks/TASK-M6C.3_decision_summary.md` (Option A, user-approved 2026-07-13)
- Feature Type: Internal evidence-only technical-debt preparation

## USER VALUE

Provider cleanup is based on documented reachability evidence instead of deleting live streaming, normalization, fallback, or internal-generation behavior by assumption.

## TARGET SURFACE

- Primary Surface: Existing internal provider-routing and orchestration seams
- Existing or New Surface: Existing, verified by repository scan
- Existence Confirmation: confirmed by repository review
- Affected Provider Families: OpenAI-compatible, Gemini-native, Google alias, and Ollama-local
- Non-Surfaces: User-facing chat UI, provider settings, tool contracts, persistence, release configuration

## USER ACTION SURFACE

- User Trigger: Phase-C T-C3 continuation after C1/C2 closure
- Success Feedback: Internal inventory artifact classifies reviewed branches as retained, candidate, or needs runtime evidence
- Cancel or Undo: Not applicable; no runtime behavior changes

## SYSTEM BEHAVIOR

- The inventory records each selected provider-specific branch, its static callers, its runtime contract, and an explicit classification.
- A branch with direct callers is classified retained and receives no deletion task in this slice.
- A branch without a static caller is classified needs runtime evidence unless the inventory has documented proof that no dynamic, test, or runtime path can consume it.
- The inventory creates no deletion, replacement, flag, routing, or provider behavior change.

## DATA / PERSISTENCE

- New Data: One internal documentation inventory only
- Data Migration: None
- Persistence Change: None
- Credentials or Secrets: None

## CONSTRAINTS

- This C3 slice is evidence-only and cannot remove code.
- Streaming, Gemini history normalization, provider fallback, internal generation, transport enablement, tool execution, persistence, and UI behavior remain unchanged.
- The parent Phase-C T-C3 cleanup is not complete after this inventory; any deletion requires a separate decision-locked task and precheck.

## SECURITY / PRIVACY

- Sensitive Data: None beyond existing source-code metadata
- External Services: None
- Privacy Constraint: Do not add logging, capture live prompts, or expose credentials

## EDGE CASES

- Dynamic or indirect call paths keep a candidate classified needs runtime evidence.
- Test-only callers count as evidence that deletion requires explicit test-scope review.
- Provider aliases such as Google and Gemini are recorded as one contract family only when their existing behavior is shared and verified.

## DEFINITION OF DONE

- [ ] Wenn ein ausgewählter Provider-Branch geprüft wird, dann enthält das Inventory seine statischen Call-Sites oder die explizite Feststellung, dass keine gefunden wurden.
- [ ] Wenn ein Branch direkte Call-Sites hat, dann ist er als retained klassifiziert und keine Löschung wird vorgeschlagen.
- [ ] Wenn ein Branch keine statische Call-Site hat, dann ist er als needs runtime evidence klassifiziert, solange kein vollständiger Nicht-Erreichbarkeitsnachweis vorliegt.
- [ ] Wenn das Inventory fertig ist, dann enthält es keine Produktcode- oder Laufzeitverhaltensänderung.
- [ ] Wenn der Inventory-Check läuft, dann benötigt er keine Provider-Credentials oder Netzwerkzugriffe.

## TEST STRATEGY

- Automated Coverage: deterministic repository scans for the selected symbols and focused artifact validation
- Manual Evidence: Not applicable; no user-facing or runtime behavior changes
- Regression Boundary: scoped diff must contain only documentation inventory and bound pipeline artifacts
- Network Requirement: None

## OUT OF SCOPE

- Removing provider branches
- Streaming replacement or parity changes
- Gemini tool-history normalization changes
- Provider fallback or simple internal-generation changes
- T-C4 provider parity suite
- OpenRouter, Codex/OAuth, persistence, UI, tools, release, or Git changes

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 8
- Architectural Risk: 10
- State / Persistence Complexity: 0
- Cross-System Dependencies: 12
- Ambiguity Level: 12
- Total Complexity Score: 42
- Routing Decision: 5.6 Terra
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 42
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.6 Terra
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-13
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review
