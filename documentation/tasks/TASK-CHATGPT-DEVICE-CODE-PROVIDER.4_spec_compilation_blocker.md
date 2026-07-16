# SPEC COMPILATION BLOCKER - TASK-CHATGPT-DEVICE-CODE-PROVIDER.4

## RESULT

SPEC COMPILATION BLOCKED: MISSING_PRODUCT_DECISION

## Bound Source

- Spec: `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- Review Status: `APPROVED`
- Target Task: `TASK-CHATGPT-DEVICE-CODE-PROVIDER.4`
- Scope: ChatGPT transport, ephemeral context, Janus-only skill/tool authority, privacy gate, failure isolation, and continued production default-deny

## Compiler Evidence

- The official App Server documentation binds `thread/start`, `turn/start`, streamed events, and `turn/interrupt` for the conversation lifecycle.
- A locally generated official stable App-Server schema contains the client request `item/tool/call` and the dynamic-tool request/response types, but stable `ThreadStartParams` exposes no `dynamicTools` registration field.
- The schema generated with `codex app-server generate-json-schema --experimental` adds `dynamicTools`; therefore the only evidenced route for registering Janus-owned tool definitions is currently an experimental App-Server field.
- The stable thread/turn contract also does not by itself prove that all Codex-native shell, file, approval, MCP, or other actions are disabled before execution. Prompt instructions or merely hiding events cannot satisfy the approved fail-closed boundary.

No account login, message submission, network transport, credential action, or product-code execution was used for this evidence.

## Why Compilation Must Stop

The approved Spec requires both production-capable Janus tool parity and a hard prohibition on Codex-native actions. It does not decide whether Janus may depend on the experimental `dynamicTools` field. Compiling a task that silently selects that field would introduce a new release and compatibility decision; omitting Janus tools would contradict the approved provider-parity behavior.

The task also cannot claim implementation readiness until a documented configuration or protocol mechanism proves that Codex-native actions cannot execute before Janus rejects them.

## Required Product Decision

A) Permit the experimental App-Server `dynamicTools` contract for Task `.4`, but keep production default-deny through Task `.5`, pin and validate the runtime schema, fail closed when the field or hard native-tool disablement is absent, and prohibit activation without evidence for both boundaries.

B) Keep ChatGPT text-only without Janus skill/tool calls until OpenAI exposes a stable client-tool registration and hard native-tool-disable contract; revise the currently approved provider-parity requirement accordingly.

Recommendation: A, because it preserves the user-approved Janus-provider parity while Task `.5` remains the explicit production evidence gate. This is still a product/release-risk decision and cannot be inferred by the compiler.

## Decision Resolution

- Locked At: 2026-07-16
- User Choice: A
- Resolution: Task `.4` may use the experimental client-tool contract only with exact runtime-contract verification and fail-closed unavailability. Task `.5` must prove both that contract and hard non-execution of Codex-native actions before production activation.
- Next Gate: Amend and re-review the Feature Spec, then rerun compilation for exactly Task `.4`.

## Unchanged Boundaries

- Tasks `.1`, `.2`, and `.3` remain completed and are not reopened.
- Task `.5` remains the only production activation gate.
- API-key providers remain unchanged and are never a fallback.
- No product code, task implementation, account action, Git action, sync, release, or production activation is authorized by this blocker.

## NEXT STEP

Recommended Skill: `janus-feature-design`

Recommended Model: `5.6 Sol`

Recommended Intelligence: high

Decision Question: experimental `dynamicTools` with evidence-bound default-deny, or no Janus tools until a stable contract exists.
