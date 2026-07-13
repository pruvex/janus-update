# LATEST DECISION SUMMARY

Feature Name: M6B.7 Ollama gateway request/synthesis transport delegation

Primary Goal: Extend the Phase-B flag to all existing direct Ollama gateway provider requests without changing Atomic/engine execution logic.

User Problem: Ollama does not have the same gateway-owned multi-round tool-loop as OpenAI or Gemini. Treating its Atomic path as a normal gateway loop would mix a previously stabilized execution system into a transport rollout.

User Value: The existing direct Ollama gateway can use the transport seam while the validated Atomic weather execution stays behavior-preserving.

Primary Target Surface: Existing `OllamaGateway.reason_and_respond` service request path.

Existing or New Surface: Existing surface.

Existence Confirmation: verified in repository (`OllamaGateway.reason_and_respond`).

User Trigger: `TRANSPORT_LAYER_ENABLED=true` with direct provider `ollama`.

Success Behavior: The Ollama gateway receives `OllamaLocalTransport` only at its existing provider request seam, for both initial tool-capable request and existing synthesis request. Gateway-owned tool filtering, forced-tool forwarding, budget guard, synthesis selection, and response behavior remain intact.

Failure Behavior: With the flag absent or false, all Ollama paths keep legacy behavior. With the flag true, Atomic/AgentRuntime continues to use the same gateway and service behavior through the thin transport wrapper.

User Action Surface: None; internal feature flag only.

Data / Persistence: No new data, credentials, or migration.

Security / Privacy: No new external service or secret handling; existing local-provider policy remains before delegation.

Edge Cases: Tool-capable initial request, synthesis, and Atomic-originated direct gateway requests use the same injected transport seam; Atomic execution ownership remains unchanged.

Out of Scope: Atomic/AgentRuntime/engine logic changes, tool execution ownership, fallback redesign, OpenAI/Gemini/Google/OpenRouter/Codex changes, streaming, Websearch cleanup, and legacy-code removal.

Routing Decision: FULL FEATURE PIPELINE (bounded implementation continuation).

Routing Reason: User selected the gateway request/synthesis seam only after repository confirmation that Ollama has no comparable normal gateway-owned tool-loop.

Recommended Next Skill: `janus-task-breakdown`, then `janus-preimplementation-check`.
