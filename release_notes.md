# Janus Projekt 0.4.17-beta.43
**Released:** 2026-05-27 01:52

### Fixed
- **BACKLOG-096 / Chat-Header-Modellwahl beim neuen Chat im selben Fenster beibehalten:** Beim Start eines neuen Chats bleibt die explizit gesetzte Header-Modellwahl jetzt auch im selben Fenster erhalten; nur Fenster ohne expliziten Override folgen weiterhin `wie Sidebar`. Zusaetzlich schreibt Janus Renderer-Console-Ausgaben in `documentation/logs/janus_frontend.log`, damit Frontend- und Backend-Verhalten beim Debugging nebeneinander nachvollziehbar sind. Validation: `node --check frontend/js/chat-manager.js` PASS; `node --check main.electron.cjs` PASS; manuelle Janus-Bestaetigung fuer GPT- und Gemini-Fall. Files: `frontend/js/chat-manager.js`, `main.electron.cjs`.
## Installation
Download the installer from the GitHub releases page.

## Known Issues
None reported for this release.
