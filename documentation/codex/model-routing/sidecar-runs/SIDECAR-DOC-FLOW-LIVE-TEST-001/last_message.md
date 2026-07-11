# Title

Everyday Documentation Skill Workflow Test Note

# Summary

For a bounded documentation draft task, the operator can choose `1 = Codex` or `2 = Sidecar`. This choice is for drafting only and does not change Janus authority boundaries.

# Workflow Test

Use `1 = Codex` when the Codex App should draft and review in one place. Use `2 = Sidecar` when a bounded, read-only sidecar draft is acceptable for a normal documentation-skill workflow test. The returned sidecar result is only a draft for review.

# Boundaries

The Sidecar path is read-only and non-binding. It must not perform file writes, Git actions, release decisions, routing decisions, or authoritative documentation updates. Codex App remains the reviewer and keeps Janus governance authority.

# Next Step

For real workflow usage, the safe next step is to run the operator gate for an eligible bounded documentation draft, choose `1` or `2`, review the resulting draft in Codex App, and let Codex App perform any binding documentation writes locally if the draft is accepted.

# No File Edits

Codex App remains responsible for any final accepted documentation sync, including any local binding updates after review.

No file edits were made.