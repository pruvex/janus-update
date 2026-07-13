# LATEST DECISION SUMMARY

Feature Name: M6B.6 Gemini normal tool-loop transport delegation

Primary Goal: Extend the Phase-B transport flag to the normal Gemini tool-loop without widening into Gemini's engine-owned or drill-down paths.

User Problem: Enabling every Gemini path together would mix native policy, grounding, cost attribution, and drill-down behavior into one non-reversible change.

User Value: The normal Gemini chat/tool path can use the transport seam while advanced Gemini paths remain behavior-preserving.

Primary Target Surface: Existing Gemini provider gateway.

Existing or New Surface: Existing surface.

Existence Confirmation: verified in repository (`GeminiGateway._run_simple_tool_loop`).

User Trigger: `TRANSPORT_LAYER_ENABLED=true` with provider `gemini` or `google` on the normal Gemini tool-loop.

Success Behavior: The normal Gemini tool-loop receives `GeminiNativeTransport` only at its existing service request and second-call-history seams. Gateway-owned model policy, grounding, cost attribution, synthesis, and response behavior stay intact.

Failure Behavior: With the flag absent or false, all Gemini paths keep legacy behavior. With the flag true, engine-owned and drill-down paths retain their current service seams, and other providers receive no Gemini transport.

User Action Surface: None; this is an internal feature flag.

Data / Persistence: No new data, credentials, or migration.

Security / Privacy: No new external service or secret handling; existing provider access policy remains before delegation.

Edge Cases: `google` follows the existing Gemini-family route only when it already reaches that gateway; engine-owned and drill-down flows stay excluded even with the flag on.

Out of Scope: Gemini engine-owned paths, drill-down, streaming, grounding/cost-policy migration, OpenRouter, Ollama, Codex, Websearch cleanup, fallback redesign, and legacy-code removal.

Routing Decision: FULL FEATURE PIPELINE (bounded implementation continuation).

Routing Reason: User locked the normal Gemini tool-loop as the next isolated provider rollout.

Recommended Next Skill: `janus-task-breakdown`, then `janus-preimplementation-check`.
