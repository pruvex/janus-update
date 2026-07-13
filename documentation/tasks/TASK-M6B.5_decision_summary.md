# LATEST DECISION SUMMARY

Feature Name: M6B.5 first flag-gated transport delegation

Primary Goal: Prove the Phase-B transport layer in one live, reversible provider path before widening it.

User Problem: A multi-provider flag enablement would make a transport-layer regression difficult to isolate or roll back.

User Value: A successful first flag-on path establishes a safe basis for later provider rollout while preserving the existing default behavior.

Primary Target Surface: Existing internal LLM gateway runtime.

Existing or New Surface: Existing surface.

Existence Confirmation: verified in repository (`llm_gateway.reason_and_respond`).

User Trigger: `TRANSPORT_LAYER_ENABLED=true` with the existing live `openai` provider path.

Success Behavior: Only the existing OpenAI gateway path obtains its service-level calls through `OpenAICompatTransport`; the existing gateway retains tool-loop, policy, synthesis, response shaping, and cost behavior.

Failure Behavior: With the flag absent or false, every provider keeps the exact legacy gateway dispatch. With the flag true for Gemini, Google, Ollama, OpenRouter, unsupported providers, and the Epic-5 Codex placeholder, no new path is selected. OpenRouter remains resolver metadata only because no direct OpenRouter gateway route exists in the current runtime.

User Action Surface: None; this is an internal feature flag.

Data / Persistence: No new persistent data, credential retrieval, or configuration migration.

Security / Privacy: No new external service or secret handling; the existing provider access gate remains before delegation.

Edge Cases: Flag parsing is case-insensitive; OpenRouter follows the OpenAI-compatible path; request tools, forced tools, image payloads, and tool-loop continuation retain current gateway-owned behavior.

Out of Scope: OpenRouter live routing, Gemini, Google, Ollama, Codex, streaming changes, Websearch cleanup, provider-policy migration, fallback redesign, and removal of legacy code.

Routing Decision: FULL FEATURE PIPELINE (bounded implementation continuation).

Routing Reason: The user locked a single first provider family for a flag-gated runtime integration.

Recommended Next Skill: `janus-task-breakdown`, then `janus-preimplementation-check`.
