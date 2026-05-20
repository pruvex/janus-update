# JANUS PIPELINE CONTRACT V3.1 (MODULAR STANDARD)

## P0: SAFETY & INTEGRITY
- **No Architecture Drift:** Implementation must not change architecture, public APIs, routing, storage contracts, provider behavior, or security boundaries unless explicitly required by the bound Spec/Task.
- **No Provider Fallback:** Janus is BYOK-isolated. Provider-specific failures must be fixed in that provider path, not hidden by fallback to another provider.
- **No Manual Bypass:** Automated evidence must not be replaced by prose claims. Manual checks are allowed only when explicitly required or when automation is technically blocked and the block is documented.
- **No Scope Escape:** Fixes must stay inside the declared task scope. Required out-of-scope fixes must stop and route to debug/replanning.

## P1: GATES & ARTIFACTS
- **Single Source of Truth:** Only the artifacts named in the skill invocation are binding. Chat history is secondary and must not extend or override the artifacts.
- **Command-First:** For implementation tasks, the verification plan or Mini-TestPlan must be stated before product-code edits.
- **Evidence-First Completion:** Completion requires executed validation evidence. N/A is allowed only with explicit reason, affected paths, and next gate.
- **One Canonical Final State:** Each skill output must end in exactly one canonical state: `PASS`, `BLOCKED`, `NEEDS_INFO`, `FAILED`, `HANDOFF`, or `ESCALATED`.

## P1.1: CANONICAL STATE MATRIX
Skill-specific display labels are allowed, but they must map to one canonical state.

| Canonical State | Allowed Display Labels |
| --- | --- |
| `PASS` | `TASK COMPLETE`, `ALL TASKS COMPLETE`, `FIXED`, `READY FOR LIVE TEST`, `FINAL AUDIT PASS` |
| `BLOCKED` | `LIVE TEST BLOCKED`, `DEBUG PACKAGE INCOMPLETE`, `EXECUTION ARTIFACTS INVALID`, `N/A-SCOPE CLOSURE` |
| `NEEDS_INFO` | `TASK NEEDS EVIDENCE`, `NEEDS RETEST`, `NEEDS INFO` |
| `FAILED` | `TASK EXECUTION FAILED`, `FIX LOOP LIMIT REACHED`, `TEST RUN FAILED` |
| `HANDOFF` | `NEXT_SKILL_HANDOFF` |
| `ESCALATED` | `MODEL SWITCH REQUIRED`, `SKILL 5 ESCALATION REQUIRED` |

## P1.2: CREDENTIAL CHECK STANDARD
When automation depends on local provider credentials, every "not automatable" or "config missing" conclusion must include this block. Never print secrets.

```text
Credential Check:
Config Path:
Provider:
Key Present: YES | NO
Key Format Plausible: YES | NO | N/A
Secret Printed: NO
Result: AUTOMATABLE | CONFIG_BLOCKED | PROVIDER_BLOCKED
```

## P2: OUTPUT & HANDOVER
Every inter-skill handoff uses the extended V3.1 block:

```text
NEXT_SKILL_HANDOFF
Target Skill:
Canonical State:
Required Artifacts:
Evidence Paths:
Failure Code:
Changed Files:
Decision:
Reason:
Copy Prompt:
```

Rules:
- `Canonical State` must be one of the P1.1 states.
- `Evidence Paths` must contain real paths or `N/A WITH REASON`.
- `Failure Code` must be an exact generator/runner taxonomy code or `N/A`.
- `Changed Files` must list touched product/test/docs files or `NONE`.

## P3: RESOURCE & MODEL AWARENESS
- `[PRIMARY_CODING]`: Default implementation model (for example SWE 1.6).
- `[STRONGEST_REASONING]`: Audit, security, unclear risk, release-critical escalation (for example GPT-5.5).
- `[LOW_COST_DETERMINISTIC]`: Deterministic markdown, registry, and low-risk structure work (for example Kimi k2.5).
- Prefer the cheapest model that can satisfy the required confidence; escalate when ambiguity or risk demands it.

## INVALID EXAMPLES
- "Frontend cannot be automated, test manually" without automation attempt or documented blocker.
- Fixing router/API/protocol behavior when the task scope only allowed engine-local logic.
- "TASK COMPLETE" without validation evidence.
- Adding requirements from chat that are absent from the bound Spec/Task.
- Calling a provider-specific failure fixed by switching providers.
