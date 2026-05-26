# Janus Projekt 0.4.17-beta.41
**Released:** 2026-05-26 22:08

### Changed
- **Release Governance / Diamond Standard:** Added a canonical release route playbook with strict rehearsal-first gates, two-checkpoint flow, artifact integrity checks, publish safety (`Publish: YES` only), and evidence-first/post-publish verification rules. Reference: `documentation/release/RELEASE_PLAYBOOK.md`.

### Fixed
- **BACKLOG-094 / Zwei Chats parallel mit eigener Modellwahl:** Chat A und Chat B koennen jetzt gleichzeitig streamen, ohne dass ein Fenster das andere blockiert. Pro Fenster werden Request-Lifecycle, Loading/Cancel/Error und Modell-/Provider-Zustand isoliert verarbeitet. Fuer Auditierbarkeit wurden STREAM_AUDIT und TOKEN_AUDIT Logging erweitert und zusaetzlich nach `C:\KI\Janus-Projekt\documentation\logs\janus_backend.log` gespiegelt. Validation: `npx playwright test tests/functional/chat-core.spec.js --reporter=list --workers=1` PASS; Final Audit `PASS WITH FIXES`. Files: `backend/api/routers/chat.py`, `backend/main.py`, `backend/logger_config.py`, `backend/services/logging/supabase_client.py`, `frontend/js/chat.js`, `playwright.config.js`, `tests/functional/chat-core.spec.js`.
- **BACKLOG-093 / Gespeicherte API-Keys werden in den Einstellungen doppelt angezeigt:** Die Settings-Ansicht zeigt gespeicherte Provider-API-Keys jetzt wieder genau einmal an. Der Renderpfad ignoriert stale async responses, dedupliziert Provider vor dem Einfuegen und wurde mit einem schnellen Live-Janus-Sichtcheck bestaetigt. Validation: `node --check frontend/js/settings.js` PASS; `LIVE_JANUS_SMOKE` PASS. Files: `frontend/js/settings.js`, `documentation/tasks/backlog_BACKLOG-093_execution_result.md`, `documentation/test-runs/BACKLOG-093_live_janus_smoke.md`, `documentation/test-runs/BACKLOG-093_final_audit.md`.
- **BACKLOG-091 / Chat-Header-Modellwahl pro Chat persistent speichern:** Chat-Header-Provider und -Modell werden jetzt pro Chat in der Datenbank gespeichert, per API aktualisiert und beim Laden eines Chats sowie nach Janus-Neustart wiederhergestellt. Sidebar-Default bleibt bestehen, wenn kein Override gesetzt ist. Validation: `tests/unit/test_chat_header_llm_override.py` PASS, Python compile PASS, JS syntax checks PASS, manueller Restart-Test PASS. Files: `backend/data/models.py`, `backend/data/schemas.py`, `backend/data/crud.py`, `backend/data/database.py`, `backend/api/routers/chat.py`, `frontend/js/window-state.js`, `frontend/js/chat-manager.js`, `frontend/js/app.js`, `tests/unit/test_chat_header_llm_override.py`, `alembic/versions/2026_05_25_chat_header_llm_override.py`.
## Installation
Download the installer from the GitHub releases page.

## Known Issues
None reported for this release.
