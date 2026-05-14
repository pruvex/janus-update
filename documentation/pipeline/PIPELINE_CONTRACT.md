# 📜 JANUS PIPELINE CONTRACT V3 (MODULAR STANDARD)

## ⚖️ P0: SAFETY & INTEGRITY
- **No Architecture Drift:** Implementation must not change architecture, public APIs, routing, storage contracts, provider behavior, or security boundaries unless explicitly required by the bound Spec/Task.
- **No Provider Fallback:** Janus is BYOK-isolated. Provider-specific failures must be fixed in that provider path, not hidden by fallback to another provider.
- **No Manual Bypass:** Automated evidence must not be replaced by prose claims. Manual checks are allowed only when explicitly required or when automation is technically blocked and the block is documented.
- **No Scope Escape:** Fixes must stay inside the declared task scope. Required out-of-scope fixes must stop and route to debug/replanning.

## 🚧 P1: GATES & ARTIFACTS
- **Single Source of Truth:** Only the artifacts named in the skill invocation are binding. Chat history is secondary and must not extend or override the artifacts.
- **Command-First:** For implementation tasks, the verification plan or Mini-TestPlan must be stated before product-code edits.
- **Evidence-First Completion:** Completion requires executed validation evidence. N/A is allowed only with explicit reason, affected paths, and next gate.
- **One Final State:** Each skill output must end in exactly one final state: PASS, BLOCKED, NEEDS_INFO, FAILED, or HANDOFF.

## 📋 P2: OUTPUT & HANDOVER
Every inter-skill handoff uses:
NEXT_SKILL_HANDOFF
Target Skill:
Required Artifacts:
Decision:
Reason:
Copy Prompt:

## 💰 P3: RESOURCE & MODEL AWARENESS
- [PRIMARY_CODING]: Default implementation model (e.g., SWE 1.6).
- [STRONGEST_REASONING]: Audit, security, unclear risk, release-critical escalation (e.g., GPT-5.5).
- [LOW_COST_DETERMINISTIC]: Deterministic markdown, registry, and low-risk structure work (e.g., Kimi k2.5).
- Prefer the cheapest model that can satisfy the required confidence; escalate when ambiguity or risk demands it.

## 🚫 INVALID EXAMPLES
- "Frontend cannot be automated, test manually" without automation attempt or documented blocker.
- Fixing router/API/protocol behavior when the task scope only allowed engine-local logic.
- "TASK COMPLETE" without validation evidence.
- Adding requirements from chat that are absent from the bound Spec/Task.
