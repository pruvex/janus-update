Title

Non-binding milestone draft: Sidecar runner hardening and first accepted read-only pilot

Summary

The sidecar runner hardening reached a usable safety baseline. Windows-specific launch, timeout, and artifact-classification issues were addressed well enough to support bounded sidecar use without claiming production readiness. The accepted live pilot confirmed that a read-only sidecar can complete a concrete, workflow-like Janus task and return a reviewable draft. The safest validated usage class so far is non-binding `janus-documentation-update` draft work with Codex App still acting as operator and reviewer.

Evidence

Runner hardening covered direct `node.exe ... codex.js` execution, removal of the unsupported approval flag, file-first artifact capture, timeout guarding, process-tree cleanup, and null-exit-code normalization from final artifacts. `CURRENT_STATE.md` records a clean `PASS` confirmation for `SIDECAR-LIVE-PILOT-READONLY-180-002` and a completed bounded draft task in `SIDECAR-DOC-DRAFT-001`. The live pilot result note states that the first real read-only pilot is accepted and identifies `janus-documentation-update` as the first validated sidecar candidate class.

Next Step

Use the sidecar only for bounded, read-only, non-binding documentation-draft tasks, with Codex App reviewing the output before any broader rollout or write-capable pilot is considered.

No File Edits

No repository state was updated by this draft.
No file edits were made.
