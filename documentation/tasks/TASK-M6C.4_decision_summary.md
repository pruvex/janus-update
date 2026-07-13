# LATEST DECISION SUMMARY - TASK-M6C.4

Feature Name: M6C.4 OpenAI/Gemini canonical tool-ID parity tests

Primary Goal: Prove that the two established provider adapters preserve the same canonical Janus skill IDs for `system.weather` and `system.websearch` while emitting provider-safe outbound tool names.

User Value: Future provider cleanup cannot silently reintroduce tool-name drift for two real, shared chat skills.

Primary Target Surface: Existing `ToolCallAdapter` provider adaptation boundary and its backend regression suite.

Existing or New Surface: Existing adapter surface; new parity-only test module.

Existence Confirmation: confirmed by repository review.

User Trigger: Phase-C T-C4 continuation.

Success Behavior: Both provider adapters map the two canonical IDs to the same expected provider-safe names and restore those names back to their canonical Janus IDs.

Failure Behavior: A parity mismatch fails hermetically without a provider credential, network call, or product behavior fallback.

User Action Surface: None; internal regression evidence only.

Data / Persistence: No product data changes.

Security / Privacy: No external calls, credentials, prompt capture, or logging changes.

Edge Cases: Empty or unknown IDs are excluded; the slice proves only the two selected shared skills and does not claim whole-catalog parity.

Out of Scope: Runtime provider calls, transport enablement, streaming, tool execution, provider fallback, C3 deletion, Ollama, OpenRouter, persistence, UI, and whole-catalog parity.

Routing Decision: FULL FEATURE PIPELINE

Routing Reason: A provider-bound test contract needs an approved, binary parity definition before its new test module is created.

Recommended Next Skill: janus-spec-generator
