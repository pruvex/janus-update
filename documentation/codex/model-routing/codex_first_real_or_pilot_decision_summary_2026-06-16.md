LATEST DECISION SUMMARY
Feature Name: First Real OR Pilot for Bounded Janus Delegation
Primary Goal: Prove one real bounded OR-assisted write task under Codex-owned review and acceptance.
User Problem: Suitable low-risk Janus work should be delegable to a cheaper external worker path without losing local validation, diff review, or final acceptance control.
User Value: The operator gets a real everyday delegation option that can save Codex quota on small tasks while preserving Janus safety and auditability.
Primary Target Surface: `janus-quickchange` bounded delegated write candidate
Existing or New Surface: Existing surface extension
Existence Confirmation: verified in repo
User Trigger: The operator selects a tiny prechecked quickchange task and chooses the delegated path instead of the fully local Codex path.
Success Behavior: One tiny allowlisted quickchange returns a reviewable diff, changed-files list, validation evidence, and an explicit Codex-owned accept-or-reject handoff with no authority drift.
Failure Behavior: Any missing artifact, allowlist escape, touched-file-cap escape, delete or rename or move activity, or failed validation discards the delegated result and falls back to local Codex handling without claiming task completion.
User Action Surface: The operator sees one bounded gate for the chosen quickchange slice, chooses `1 = Codex` or `2 = Delegated`, and receives a compact post-run review summary.
Data / Persistence: The pilot creates only bounded run artifacts such as diff, changed-files, validation summary, stdout/stderr, and operator review output; no schema, migration, or product data shape change is part of the pilot itself.
Security / Privacy: No secrets, private raw logs, local databases, Git authority, release authority, production routing, or broad repo-write scope may enter the pilot. Exact editable-path allowlist, touched-file cap, delete or rename or move tripwires, and Codex-owned final acceptance remain mandatory.
Edge Cases: Empty diff, changed file outside allowlist, more touched files than declared, missing validation summary, failed local validation, delegated output claiming final completion, and multi-file-cluster drift must all end in reject or fallback, not silent acceptance.
Out of Scope: Broad `janus-executioner` code delegation, test-pipeline write retries, Auto Router, production routing, canonical routing-table updates, Git or release actions, and any multi-task or architecture-changing write attempt.
Routing Decision: BACKLOG PIPELINE
Routing Reason: The next step is one small bounded improvement to an existing workflow surface. It should be proven first on the safest write-capable class before any broader execution-class delegation is retried.
Recommended Next Skill: janus-quickchange
