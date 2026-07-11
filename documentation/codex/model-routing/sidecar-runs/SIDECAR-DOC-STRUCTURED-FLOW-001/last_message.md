## Title
Sidecar Documentation Milestone Draft

## Summary
The sidecar runner hardening is now in a safe enough state for bounded read-only use. The accepted live pilot confirmed that a non-binding sidecar run can complete, capture final artifacts, and return a usable recommendation without leaving lingering processes. The first validated everyday use is `janus-documentation-update` draft support in read-only mode.

## Evidence
Runner hardening covered direct `node.exe` invocation, unsupported flag removal, timeout enforcement, process-tree cleanup, file-first artifact capture, and null-exit-code success normalization on Windows. The live pilot outcome moved from guarded timeout validation to an accepted read-only completion, then to a clean `PASS` classification with `artifact_success=true` and `last_message_present=true`. `CURRENT_STATE.md` also records a completed bounded documentation draft flow and identifies read-only documentation drafting as the currently accepted sidecar class.

## Next Step
Use the sidecar only for bounded, non-binding `janus-documentation-update` draft tasks in read-only mode. Keep authoritative documentation updates, validation, and acceptance with Codex App until a separate write-capable path is explicitly hardened and approved.

## No File Edits
This is a draft only and does not claim any repository update.

No file edits were made.