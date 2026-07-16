# PRE-IMPLEMENTATION CHECK - TASK-CHATGPT-DEVICE-CODE-PROVIDER.4

PRE-CHECK RESULT

PRE-CHECK BLOCKED: HARD_NATIVE_ACTION_DISABLEMENT_UNPROVEN

## Pre-Check Identity

- Target Task: `TASK-CHATGPT-DEVICE-CODE-PROVIDER.4`
- Target Subtask: N/A WITH REASON - one approved provider-parity slice
- Task: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md`
- Spec: `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- Task Breakdown: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_task_breakdown.md`
- Backlog Item: N/A WITH REASON - compiled Feature Spec task
- Mode: SINGLE_TASK_PRECHECK
- Assigned Model: `5.6 Sol`
- Identity Result: PASS - exactly one approved Task `.4` is bound.

## Passed Gates

- Spec review metadata is `APPROVED`, complexity `78`, risk `HIGH`, `Skill-1 Ready: YES`, split not required.
- Goal, scope, exclusions, fourteen binary acceptance criteria, bound file cluster, test ownership, and Task `.5` production boundary are explicit.
- The repository pins official `@openai/codex` exactly to `0.144.4`; the bundled Windows x64 executable is present and reports `codex-cli 0.144.4`.
- Schemas generated locally and account-free by that exact binary confirm ephemeral App-Server threads, thread/turn lifecycle, client-tool call/response types, agent events, completion, and interruption surfaces.
- The exact pinned schema confirms `dynamicTools` registration only in the schema generated with `--experimental`; stable schema generation omits that registration field. The approved option-A Spec explicitly permits this bounded experimental dependency.
- Existing Janus ownership is concrete: App-Server lifecycle, transport layer, new ChatGPT silo, runtime/gateway router, central orchestrator/`ToolExecutor`, request schema, frontend stream/privacy gate, durable notice, and focused tests.
- The current privacy seam is identifiable: `ACK_STORAGE_KEY`, `NOTICE_VERSION`, and `hasCurrentAck()` exist. `ChatRequest` currently has no backend acknowledgement field, so Task `.4` correctly binds `backend/data/schemas.py` for backend-before-thread enforcement and the required notice-version bump.
- Existing production activation remains source-bound and unset; Task `.4` cannot make production transport available and Task `.5` remains the only activation/evidence gate.
- Task `.3` current-session verified-model eligibility and stale-selection self-healing remain explicit pre-send prerequisites.
- No open product decision remains: option A, no degraded text-only fallback, no API-key fallback, no persistent Codex history, and Task `.5` evidence requirements are locked.

## Blocking Gate

Mandatory stop gate 3 requires account-free executable evidence that every Codex-native action surface is disabled before execution, leaving only Janus-provided client tools.

The exact pinned `0.144.4` runtime does not expose a documented or schema-bound built-in-tool allowlist or a single `dynamicTools-only` execution mode:

- Feature flags can individually disable surfaces such as shell, apps/browser/computer use, multi-agent, hooks, plugins, and related facilities, while web search has a separate disabled setting.
- The generated protocol still exposes native command execution, file-change approvals, permissions/approval requests, web-search items, and other agent-event/action types.
- `sandboxPolicy: read-only` constrains effects after a native tool choice; it does not remove the native action surface before dispatch.
- Approval rejection, prompt instructions, notification suppression, client-side event hiding, or rejecting an action after it is requested do not prove non-execution and are explicitly insufficient under the approved Task/Spec.
- No official runtime/config contract found in the pinned binary, generated schemas, feature list, or current official App-Server/config documentation proves that file changes and every other native action type are absent while experimental client tools remain enabled.

Therefore Janus cannot currently establish the approved security invariant that Codex-native actions are impossible before execution. Implementation must not start.

## Other Gate Status

- Experimental capability negotiation: protocol source identified; implementation remains blocked by the native-action invariant.
- Provider/gateway ownership: PASS - exact existing/new files are bound.
- Janus tool authority: structurally bindable through existing selection and `ToolExecutor`; execution cannot be released until native tools are proven absent.
- Backend privacy ordering: exact source files and required before-thread boundary are bound; no new product decision is required.
- Cancellation, redaction, model eligibility, default-deny/test isolation, privacy text/version, and test ownership: explicit and measurable in the bound task.
- Product tests/TestRuns: not executed by design in precheck.
- Account/login/message/tool action: not performed.

## Required Resolution

1. Use `janus-debug` for a read-only, source-bound analysis of official `openai/codex` tag `rust-v0.144.4` and the generated protocol/config surface.
2. Identify an officially supported configuration or embedding boundary that removes every Codex-native action before dispatch while retaining client `dynamicTools`; provide executable account-free evidence.
3. If no such boundary exists, document the runtime capability as unavailable and route back to `janus-feature-design` for a product decision: wait for upstream support or revise the provider-parity requirement. Do not silently weaken option A.
4. Rerun this exact precheck only after the missing capability/evidence is source-of-truth bound.

## Scope Rule

- Do not implement the transport, add gateway/runtime resolution, change privacy behavior, run an account turn, send content, invoke tools, activate production, or expand into Task `.5` while this blocker remains.

## Automated Evidence Gate

- N/A WITH REASON - implementation/test execution is forbidden because the required pre-execution native-action invariant is not established.

## Oracle-/TestPlan-Regel

- Do not create or patch generated TestPlan/TestResult artifacts. Bound source tests may be changed only after a future precheck PASS; TestSpec/oracle changes route through `janus-test-pipeline`.

## Validation

- Blocker structure, target identity, pinned-runtime identity, schema comparison, source/file/test ownership, and scoped documentation diff: PASS.
- `validate_precheck.py`: N/A WITH REASON - the repository validator accepts only the native `PRE-CHECK PASSED` execution-handoff template and must not be satisfied by inserting PASS literals into a blocked artifact.

## NEXT STEP

Recommended Skill: `janus-debug`

Recommended Model: `5.6 Sol`

Recommended Intelligence: high

User Action: Permit the read-only pinned-runtime source analysis; no account or product action is required.

```text
NEXT: janus-debug
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.4
Canonical State: BLOCKED
Missing Capability: Official hard pre-dispatch disablement of every Codex-native action while retaining experimental client dynamicTools
Evidence Scope: pinned openai/codex rust-v0.144.4 source, generated schemas, documented config/feature surface; account-free and read-only
Return Gate: rerun janus-preimplementation-check only if executable non-execution evidence exists; otherwise route to janus-feature-design
```
