# Codex Handoff - ChatGPT Provider: Stay Upstream-Wait; Reject Hermes (B) and Codex-Tools Mode (D)

## Handoff Identity

- Workflow ID: `WF-CHATGPT-PROVIDER-STAY-A-REJECT-B-D-2026-07-16-001`
- From: Cursor (feasibility review + operator decision capture)
- To: Codex (`janus-documentation-update` / decision lock; no product implementation)
- Recommended model: `5.6 Terra` / medium-high
- New chat: optional; warm Codex context on Task `.4` is fine if present

## Operator Decision (LOCKED)

User confirmed after Cursor review and recommendation discussion:

**Stay on Option A — upstream-wait. Do not pursue B or D.**

| Option | Meaning | Status |
|--------|---------|--------|
| **A** | Keep official device-code foundation; Task `.4` App-Server chat blocked until official Dynamic-Tools-only / core-tool allowlist; ChatGPT production default-deny; daily chat via BYOK API-key providers | **ACCEPTED** |
| **B** | Hermes-artige private ChatGPT backend (`chatgpt.com/backend-api/codex`) for Abo-chat now | **REJECTED** |
| **D** | OAuth + App Server, but allow Codex-native tools/skills (weaken Janus-only tool boundary) | **REJECTED** |

No Hermes implementation. No Spec weakening for private backends. No `update_plan` exception. No Codex-as-embedded-agent ChatGPT mode as substitute for provider parity.

## Cursor Feasibility Result (Evidence)

- Artifact reviewed: `documentation/tasks/CURSOR_HANDOFF_CHATGPT_DEVICE_CODE_PROVIDER_HERMES_FEASIBILITY_2026-07-16.md`
- Recommendation: **`NOT_VIABLE`** under the seven non-negotiable Janus boundaries
- Hermes identity: NousResearch Hermes Agent (`openai-codex` provider)
- Auth: ChatGPT device-code OAuth, Codex CLI client id `app_EMoamEEZ73f0CkXaXp7hrann`, `auth.openai.com`
- Inference: direct HTTP to `https://chatgpt.com/backend-api/codex` (not App Server; not Platform API key)
- Optional Hermes behavior: import from `~/.codex/auth.json` (forbidden for Janus)
- Effect on `update_plan`: Hermes **avoids** App Server (does not fix it); risk moves to undocumented backend / ToS / Spec Forbidden Integration
- Boundary 6 + Spec line „Forbidden Integration: Keine Hermes-artige …“ → unsatisfied by construction
- Full seven-point comparison was delivered in the Cursor review turn; Codex may treat `NOT_VIABLE` as binding input

## What Remains True

- Tasks `.1`–`.3`: completed foundation (login, isolation, Settings, verified models, redaction, API-key non-interference) — **keep; not wasted**
- Task `.4`: remains **`BLOCKED: UPSTREAM_DYNAMIC_TOOLS_ONLY_MODE_ABSENT`**
- Task `.5`: sole later production activation gate; still not started
- Production: **default-deny** for ChatGPT chat transport
- Prior locked Choice A in `TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_upstream_wait_decision_summary.md` is **reaffirmed**, not replaced

## Codex Required Actions (Docs Only)

1. Update `documentation/ai/CURRENT_STATE.md` with this decision lock and Cursor `NOT_VIABLE` result.
2. Append or refresh a short decision note bound to Task `.4`, e.g. extend or sibling of:
   - `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_upstream_wait_decision_summary.md`
   - Record: Cursor Hermes review `NOT_VIABLE`; operator rejected B and D; A reaffirmed.
3. Do **not** change product code, credentials, runtime pins, or production activation.
4. Do **not** open Feature Design for Hermes backend or Codex-tools mode unless the operator later explicitly reopens.
5. Optionally record skill usage; recommend `origin/codex-sync` after CURRENT_STATE update (await explicit sync approval).

## Explicit Non-Goals

- No Task `.4` implementation
- No Hermes / `backend-api/codex` client
- No patched/forked Codex runtime
- No allowing `update_plan` or other Codex-native action surfaces
- No Git commit/push/sync unless operator separately approves via `janus-git-governance`

## Sources Of Truth

- Spec: `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- Parent task: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md`
- Upstream-wait decision: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_upstream_wait_decision_summary.md`
- Debug blocker: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_debug_result_native_action_disable.md`
- Cursor feasibility handoff: `documentation/tasks/CURSOR_HANDOFF_CHATGPT_DEVICE_CODE_PROVIDER_HERMES_FEASIBILITY_2026-07-16.md`
- This lock handoff: `documentation/tasks/CODEX_HANDOFF_CHATGPT_PROVIDER_STAY_UPSTREAM_WAIT_REJECT_B_D_2026-07-16.md`

## Success Criteria For This Handoff

- Decision A / reject B / reject D is visible in CURRENT_STATE and Task `.4` decision artifacts
- ChatGPT remains default-deny; Task `.4` stays blocked on upstream capability
- No product or account action occurred

## Copy Block For Codex

```text
NEXT: janus-documentation-update (decision lock only)
LOAD:
- documentation/tasks/CODEX_HANDOFF_CHATGPT_PROVIDER_STAY_UPSTREAM_WAIT_REJECT_B_D_2026-07-16.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_upstream_wait_decision_summary.md
- documentation/ai/CURRENT_STATE.md
DO:
- Lock operator decision: Stay A; reject Hermes (B); reject Codex-native-tools mode (D)
- Record Cursor Hermes feasibility = NOT_VIABLE
- Update CURRENT_STATE + Task .4 decision note
- No product code, no account, no Git unless separately approved
MODEL: 5.6 Terra / medium-high
```
