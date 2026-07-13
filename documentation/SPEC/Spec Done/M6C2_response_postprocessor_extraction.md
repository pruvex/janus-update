# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.6 Terra
recommended_reasoning: high
new_chat: no
complexity_score: 58
confidence: HIGH
dashboard_hint: CAUTION
reason: Cross-provider synthesis boundary extraction must preserve existing response and attribution behavior.

## FEATURE IDENTITY

- Feature Name: M6C.2 Response Post-Processor Extraction
- Feature ID: M6C2-RESPONSE-POSTPROCESSORS
- Parent Initiative: Epic 4 Provider Transport Refactor, Phase C
- Decision Source: User selection A on 2026-07-13 and approved parent transport-refactor Spec
- Feature Type: Internal behavior-preserving refactor

## USER VALUE

Provider-specific response finishing remains consistent while future provider work avoids duplicating link and grounding handling across gateway paths. Existing chat answers keep their established visible links, source grounding, and response rendering behavior.

## TARGET SURFACE

- Primary Surface: Existing central provider router response-finalization flow after a provider transport response
- Existing or New Surface: Existing router surface with one new shared post-processing ownership boundary
- Existence Confirmation: not confirmed by user; central router verified in repository during task refinement
- Affected Provider Families: OpenAI-compatible and Gemini-native
- Non-Surfaces: Provider selection UI, tool execution, Websearch policy, transport enablement, streaming, persistence, and external APIs

## USER ACTION SURFACE

- User Trigger: A normal provider response requiring the existing OpenAI link repair or Gemini grounding/link rendering behavior
- Success Feedback: The rendered answer preserves the provider-appropriate links and grounding presentation already expected by the user
- Cancel or Undo: Not applicable; no new user action or setting is introduced

## SYSTEM BEHAVIOR

- OpenAI-compatible response finishing uses a shared post-processing boundary for the established release-list link behavior.
- Gemini-native response finishing uses the same shared boundary for the established grounding metadata and link-rendering behavior.
- The central provider router invokes the provider-family-appropriate post-processing after a selected provider silo returns.
- Existing provider-specific synthesis behavior is preserved rather than redesigned.
- A provider family without a registered post-processor keeps its existing response unchanged.

## DATA / PERSISTENCE

- New Data: None
- Data Migration: None
- Persistence Change: None
- Credentials or Secrets: None

## CONSTRAINTS

- Both OpenAI-compatible and Gemini-native response finishing migrate in this one bounded C2 slice.
- The central provider router, not either provider gateway, owns invocation of the shared post-processing boundary.
- Flag-off and existing provider response contracts remain behavior-preserving.
- No new provider fallback, model policy, transport routing, Websearch policy, tool contract, or streaming behavior is introduced.
- The parent Phase-C work remains incomplete after C2; C3 and C4 stay separate.

## SECURITY / PRIVACY

- Sensitive Data: Existing response and grounding metadata only; no new collection or persistence.
- External Services: No new service or credential use.
- Privacy Constraint: Post-processing must not expose metadata that was not already eligible for the existing renderer path.

## EDGE CASES

- Missing or empty provider metadata leaves the response safely unchanged.
- Malformed optional grounding metadata does not fail the whole response rendering path.
- A provider without a registered processor returns the unchanged response.
- Existing visible link and grounding behavior remains available on normal successful provider responses.

## DEFINITION OF DONE

- [ ] Wenn eine OpenAI-kompatible Antwort den bestehenden Release-List-Link-Fall erreicht, dann bleibt die sichtbare Link-Darstellung nach der gemeinsamen Post-Processing-Grenze erhalten.
- [ ] Wenn eine Gemini-native Antwort Grounding- und Link-Metadaten enthält, dann bleibt die bestehende sichtbare Grounding- und Link-Darstellung nach der gemeinsamen Post-Processing-Grenze erhalten.
- [ ] Wenn keine passende Provider-Familie oder verwertbare optionale Metadaten vorliegen, dann bleibt die Antwort ohne Fehler unverändert.
- [ ] Wenn der gemeinsame Post-Processing-Pfad genutzt wird, dann ändern sich weder Tool-Ausführung noch Websearch-Policy, Provider-Fallback, Transport-Aktivierung oder Streaming-Verhalten.
- [ ] Wenn die fokussierten Regressionen laufen, dann benötigen sie keine neuen Provider-Zugangsdaten oder Netzwerkaufrufe.

## TEST STRATEGY

- Automated Coverage: Hermetische Regressionen für OpenAI-Link-Erhalt, Gemini-Grounding/Link-Erhalt, fehlende optionale Metadaten und unveränderte unregistrierte Provider-Familien
- Manual Evidence: Ein normaler OpenAI- oder Gemini-Chat mit vorhandener Link- oder Grounding-Darstellung nach erfolgreicher automatischer Evidenz
- Regression Boundary: Bestehende provider-spezifische Synthesis- und Response-Shaping-Tests bleiben Teil der fokussierten Auswahl
- Network Requirement: Keine neuen Netzwerkaufrufe

## OUT OF SCOPE

- Websearch provider/model coercion and T-C1 changes
- Dead provider-branch removal under T-C3
- Provider parity suite under T-C4
- New providers, OpenRouter, Codex/OAuth, provider fallbacks, model hierarchy changes, tool-loop behavior, persistence, streaming, and UI redesign

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 14
- Architectural Risk: 14
- State / Persistence Complexity: 0
- Cross-System Dependencies: 16
- Ambiguity Level: 14
- Total Complexity Score: 58
- Routing Decision: 5.6 Terra
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 58
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.6 Terra
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-13
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-07-13
- **Validation Evidence:** `documentation/tasks/TASK-M6C.2_FINAL_AUDIT.md`; focused response-postprocessor and transport-gateway suite `24 passed`; scoped syntax/diff checks PASS; enabled Gemini Berlin-weather smoke with Open-Meteo PASS.
- **Scope Note:** This closes only the C2 delta Spec. Parent Phase C remains active for T-C3 and T-C4.
