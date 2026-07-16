# Cursor Review Handoff - ChatGPT Provider Hermes Feasibility

## Review Identity

- Workflow ID: `WF-CHATGPT-DEVICE-CODE-HERMES-FEASIBILITY-2026-07-16-001`
- Task: Independent, read-only feasibility review of a Hermes-artige alternative ChatGPT provider route for Janus.
- Recommended worker: Cursor Composer with highest available reasoning.
- Codex remains final product-decision, security, Git, and release authority.

## User Goal

The user wants a working ChatGPT provider in Janus now. Waiting indefinitely for an upstream App-Server capability is not an acceptable product outcome.

## Verified Current State

- Tasks `.1` to `.3` of `TASK-CHATGPT-DEVICE-CODE-PROVIDER` are completed and audited; they provide Janus-owned isolated credential handling, Settings lifecycle, verified-model visibility, stale-selection self-healing, redaction, API-key non-interference, and production default-deny.
- Task `.4` is currently blocked before implementation.
- Exact bundled official runtime: `codex-cli 0.144.4` / upstream source tag `rust-v0.144.4`.
- Experimental App-Server `dynamicTools` registration and client tool call/response shapes exist.
- The unmodified runtime always exposes at least the Codex-native `update_plan` tool. It has no supported Dynamic-Tools-only mode, no complete core-tool allowlist, and no configuration that proves all Codex-native action surfaces absent before model dispatch.
- Prompt instructions, event hiding, read-only sandboxing, approval rejection, and post-call rejection are insufficient because they do not remove a native tool before dispatch.
- Therefore the current App-Server route cannot meet the locked Janus-only tool boundary. ChatGPT remains default-deny and no product code for Task `.4` has been implemented.

## Question To Resolve

Can a Hermes-artige ChatGPT integration provide the user-requested working provider while preserving all of these non-negotiable Janus boundaries?

1. Janus owns conversation history, redaction, tool selection, permissions, confirmations, and execution.
2. The external ChatGPT route receives only the redacted context required for a turn.
3. No Codex-native tool, command, file mutation, approval flow, browser action, or agent surface is available to the model.
4. ChatGPT-specific privacy notice and consent remain mandatory before the first external content transfer.
5. Existing API-key providers, their credentials, and behavior remain unaffected.
6. No hidden credential import, shared Codex session, undocumented private OAuth flow, browser automation, or API-key fallback is introduced.
7. Production remains default-deny until a later evidence gate passes.

## Required Investigation

1. Identify what the user means by Hermes and locate the exact accessible Hermes implementation, repository, version, or documentation. Do not assume its transport, authentication model, or legal status.
2. Determine whether Hermes uses an official supported interface, a user-owned API key, a browser/session automation path, undocumented endpoints, or another mechanism.
3. Compare that mechanism against the seven Janus boundaries above. State precisely which boundaries it can satisfy, which it cannot, and what evidence is missing.
4. Decide whether it genuinely avoids the App-Server `update_plan`/native-tool problem, or merely moves the risk elsewhere.
5. Recommend exactly one of: `VIABLE_FOR_FEATURE_DESIGN`, `NOT_VIABLE`, or `NEEDS_EXTERNAL_EVIDENCE`.

## Sources Of Truth

- Active Spec: `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- Parent Task: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md`
- Runtime blocker: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_debug_result_native_action_disable.md`
- Precheck blocker: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_precheck.md`
- Decision history: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_upstream_wait_decision_summary.md`

## Boundaries

- Read-only research and review only. No edits, implementation, dependency installation, credentials, login, browser automation, message sending, tests against live accounts, Git, sync, build, release, or production activation.
- Do not weaken the Janus-only tool boundary as a convenience assumption.
- Do not claim Hermes is viable without identifying its actual transport/authentication boundary.
- Redact all tokens, cookies, API keys, headers, device codes, and local-machine details.

## Expected Output

- Recommendation: `VIABLE_FOR_FEATURE_DESIGN`, `NOT_VIABLE`, or `NEEDS_EXTERNAL_EVIDENCE`.
- A concise transport/authentication classification for Hermes, with direct evidence references.
- A seven-point Janus-boundary comparison: satisfied, unsatisfied, or unproven.
- The single most important blocker or next validation needed.
- No implementation proposal beyond a product-level feasibility recommendation.
