# BACKLOG-070 Final Audit

## Skill 6 Contract State

FINAL AUDIT RESULT: PASS

Audit Model Gate: SWE 1.6

Backlog Item: BACKLOG-070 - Lokaler marked-Fallback fuer Chat-Markdown Rendering

Implementation Type: Frontend robustness fix; no backend or provider behavior change.

## Scope

Janus Chat-Markdown rendering no longer depends on an external `marked` CDN script. The chat renderer uses a local adapter that delegates to `window.marked` if present and otherwise renders escaped readable text with line breaks.

## Changes Audited

- Removed the runtime `https://cdn.jsdelivr.net/npm/marked/marked.min.js` script from `frontend/index.html`.
- Removed `cdn.jsdelivr.net` from the Vite development CSP `script-src`.
- Added `frontend/js/markdown-renderer.js` with `configureMarkdownRenderer()` and `renderChatMarkdown()`.
- Replaced direct `marked.parse(...)` and `marked.setOptions(...)` calls in `frontend/js/chat.js`.
- Added a focused Node regression test for unavailable `marked` and available `marked` paths.

## Evidence

- Unit regression: `node --test frontend/tests/markdown-renderer.test.mjs` PASS 2/2.
- Syntax gate: `node --check frontend/js/chat.js` PASS.
- Syntax gate: `node --check frontend/js/markdown-renderer.js` PASS.
- Static scan: no remaining `cdn.jsdelivr`, `marked is not defined`, or direct `marked.parse` references outside the local adapter.
- Frontend build: `PYTHONIOENCODING=UTF-8 npm run build` PASS, including `scripts/verify-frontend-dist.cjs`.
- Browser console check at `http://127.0.0.1:5173/`: no `marked`, `cdn.jsdelivr`, or `ERR_BLOCKED_BY_CLIENT` console entries after load.

## Validation Matrix

- `marked` no longer exclusively required from CDN: PASS.
- Missing `marked` does not crash `chat.js`: PASS.
- Chat content remains readable via escaped fallback with line breaks: PASS.
- No `ReferenceError: marked is not defined` in focused browser check: PASS.
- No new external runtime CDN dependency for chat Markdown: PASS.

## Residual Risk / Watchpoints

- The fallback is intentionally conservative plain-text HTML with `<br>` line breaks. Rich Markdown output is only available if a compatible local or global `marked` implementation is supplied later.
- The first plain `npm run build` on Windows failed before Vite due to console encoding in `tools/generate_release_notes.py`; rerunning the same build with `PYTHONIOENCODING=UTF-8` passed. This is an existing build-environment issue, not a BACKLOG-070 product blocker.

## Decision

BACKLOG-070 is resolved. Final audit result is PASS with focused regression evidence, full frontend build verification and browser-console validation for the original `marked is not defined` failure mode.
