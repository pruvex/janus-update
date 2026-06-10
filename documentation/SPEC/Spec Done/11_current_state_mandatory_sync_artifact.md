# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium
new_chat: no
complexity_score: 42
confidence: HIGH
dashboard_hint: CAUTION
reason: Governance change across workflow docs and skills, but scope is still bounded and low-risk to implement incrementally.

## FEATURE IDENTITY

- Feature Name: CURRENT_STATE as mandatory Janus sync artifact
- Primary Goal: Keep Codex and ChatGPT aligned through one compact repository-based current-state artifact.
- Feature Type: Workflow governance enhancement
- Primary Trigger: Completion of a substantial Janus work block, defined as any Janus skill run where at least one of these is true: files changed, validation executed, a blocker documented, or a formal next-skill handoff produced
- Primary Artifact: documentation/ai/CURRENT_STATE.md

## USER VALUE

Janus work should no longer rely on broad chat history to reconstruct the latest project state. A concise shared state artifact should allow ChatGPT to resume planning, review, and handoff work from repository context after Codex completes and pushes meaningful updates.

## TARGET SURFACE

- Primary Surface: Janus workflow governance
- Surface Type: Internal process documentation and skill completion rules
- Existing or New: Existing workflow surface plus one new shared-state artifact
- Primary Actor: Codex during substantial Janus skill completion
- Secondary Actor: ChatGPT reading repository state after sync updates

## USER ACTION SURFACE

- Triggering Action: A substantial Janus skill run reaches completion or a documented blocker, where substantial means at least one of these is true: files changed, validation executed, a blocker documented, or a formal next-skill handoff produced.
- Required Codex Action: Update the shared current-state artifact before the work block is treated as complete.
- ChatGPT Consumption Action: Read the artifact as the compact project-sync source before preparing the next Codex handoff.
- Manual Git Action: Commit and push remain separate gated actions under existing Janus Git governance.

## SYSTEM BEHAVIOR

When a substantial Janus work block finishes, Janus must update one concise current-state artifact that summarizes the latest goal, phase, work performed, changed files, validation, open risks, and next recommended steps for ChatGPT and Codex.

The artifact is mandatory for substantial work blocks and is part of completion evidence. A substantial work block is any Janus skill run where at least one of these is true: files changed, validation executed, a blocker documented, or a formal next-skill handoff produced. Minor replies, routing-only messages, and small status exchanges do not require an update.

The current-state artifact must stay compact and current. It must function as a synchronization summary, not as a detailed historical diary or replacement for backlog, spec, test, or audit artifacts.

If the state cannot be summarized clearly, the work block must end with a documented blocker or needs-info result rather than silently skipping the artifact update.

Commit and push behavior must continue to follow existing Janus Git governance. Updating the artifact does not grant automatic permission to commit or push.

## DATA / PERSISTENCE

- Persistent Artifact: documentation/ai/CURRENT_STATE.md
- Update Frequency: Once per substantial Janus work block that reaches a meaningful completion state
- Required Content Areas: current goal, active phase, last Codex work, changed files, tests or validation, open risks, next recommended step for ChatGPT, next recommended step for Codex, last updated timestamp
- Retention Style: Rolling current snapshot, not append-only history
- Non-Goals: No machine-readable companion artifact in the first step

## CONSTRAINTS

The shared state must remain concise enough to be read quickly and reliably reused as sync context.

The artifact must not replace existing single sources of truth such as backlog entries, specs, test artifacts, or audit evidence.

The update rule applies only to substantial Janus work blocks, defined as Janus skill runs with changed files, executed validation, documented blockers, or formal next-skill handoffs, not to every assistant utterance.

Commit and push must remain governed by explicit user approval and the existing `janus-git-governance` path.

## SECURITY / PRIVACY

- Secret Handling: The artifact must never contain secrets, API keys, credentials, private tokens, or equivalent sensitive material.
- Local Sensitivity: The artifact must avoid private machine-specific details unless they are already safe, repository-relevant, and necessary.
- Privacy Scope: The artifact may summarize workflow state but must not expose unrelated personal or operationally sensitive details.
- Governance Boundary: The artifact must not weaken existing Git, release, or approval gates.

## EDGE CASES

If a substantial work block produces no file changes but does produce meaningful validation or a blocker, the current-state artifact should still capture that outcome.

If a work block ends in `BLOCKED`, `FAILED`, or `NEEDS_INFO`, the artifact should summarize the blocker or missing information rather than pretending completion.

If commit or push is not approved, unavailable, or fails, the current-state artifact may still be updated locally and the Git status must be reported through the normal governance path. In that case, the completion or handoff output must explicitly state that GitHub or other remotes may not reflect the latest CURRENT_STATE yet and ChatGPT must not assume the remote repository is current.

If a previously small change expands beyond a minor interaction and becomes a substantial Janus block, the current-state requirement begins to apply.

## DEFINITION OF DONE

- [ ] Wenn ein substantieller Janus-Arbeitsblock abgeschlossen wird, dann wird ein kompakter CURRENT_STATE-Snapshot als Pflichtartefakt behandelt.
- [ ] Wenn CURRENT_STATE aktualisiert wird, dann enthaelt es die definierten Kernfelder zum Ziel, Status, letzter Arbeit, Validierung, Risiken und den naechsten Schritten.
- [ ] Wenn eine Interaktion nur Routing, Rueckfrage oder Kurzstatus ist, dann ist kein CURRENT_STATE-Update erforderlich.
- [ ] Wenn ein Arbeitsblock blockiert oder unklar endet, dann spiegelt CURRENT_STATE den Blocker oder Informationsbedarf sichtbar wider.
- [ ] Wenn Git-Aktionen noetig werden, dann bleiben Commit und Push an die bestehenden Janus-Governance-Gates gebunden.
- [ ] Wenn CURRENT_STATE nur lokal aktualisiert wurde und kein Push erfolgt ist, dann weist der Abschluss explizit darauf hin, dass ein Remote-Stand wie GitHub noch nicht aktuell sein muss.
- [ ] Wenn ChatGPT den Repository-Stand nach einer Aktualisierung liest, dann kann es CURRENT_STATE als kompakte Sync-Quelle verwenden, ohne dass es die uebrigen Kernartefakte ersetzt.

## TEST STRATEGY

- Validation Style: Documentation and skill-governance review with targeted completion-flow checks
- Primary Checks: rule presence in governance docs, rule presence in relevant skills, completeness of required CURRENT_STATE fields, preservation of Git approval gates
- Negative Checks: no blanket requirement for every minor reply, no automatic push bypass, no replacement of backlog/spec/test sources of truth
- Evidence Expectation: updated docs and skills plus one example current-state artifact aligned with the rule

## OUT OF SCOPE

Automatic commit or push on every task.

Replacing backlog, spec, test, audit, or dashboard artifacts with CURRENT_STATE.

Creating a machine-readable JSON companion in the first implementation step.

Expanding the artifact into a full historical activity log.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 9
- Architectural Risk: 6
- State / Persistence Complexity: 7
- Cross-System Dependencies: 10
- Ambiguity Level: 10
- Total Complexity Score: 42
- Routing Decision: 5.4
- Routing Reasoning: medium
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 42
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-10
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS WITH FIXES
- **Completed At:** 2026-06-10
- **Validation Evidence:** documentation/tasks/TASK-SPEC11_AUDIT_PACKAGE.md; documentation/tasks/TASK-SPEC11_validation_summary.md; documentation/ai/CURRENT_STATE.md
