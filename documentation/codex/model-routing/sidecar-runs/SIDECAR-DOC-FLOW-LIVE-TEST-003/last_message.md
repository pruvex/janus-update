## Title
Bounded Sidecar Documentation Draft Workflow Note

## Summary
The operator can choose `1 = Codex` or `2 = Sidecar` for an eligible documentation draft task. This note is non-binding and describes the safe review flow only.

## Workflow Test
Use `1 = Codex` when the draft should stay fully local in Codex App. Use `2 = Sidecar` when a bounded read-only draft is acceptable and the goal is to gather a reviewable draft before any authoritative documentation step.

## Boundaries
The Sidecar path is read-only and intended for bounded drafts only. It must not perform binding documentation writes, Git actions, release decisions, or authority updates such as `CURRENT_STATE`, backlog, registry, or changelog acceptance. Codex App remains the reviewer and performs any binding documentation writes locally after review.

## Next Step
The next safe step is to review the draft and confirm it is acceptable before any local documentation update is performed by Codex App.

## No File Edits
This response is a draft note only. It does not claim that repository documentation, workflow state, or any local file was updated.

No file edits were made.