# Janus Projekt 0.4.17-beta.42
**Released:** 2026-05-27 00:23

### Fixed
- **BACKLOG-095 / Einheitliche Antwortform fuer Wetteranfragen:** Wetterantworten werden jetzt fuer GPT/HPZ und Gemini im gleichen klaren Bulletpoint-Layout ausgegeben, inklusive Wetterlage, Temperaturen, Niederschlagswahrscheinlichkeit, Wind und sauberer Quellenzeile. Validation: fokussierte Weather-Regression PASS; `py_compile` PASS; Final Audit `PASS WITH FIXES`. Files: `backend/tools/weather_service.py`, `backend/renderers/implementations/weather_renderer.py`, `backend/renderers/attribution.py`, `backend/services/orchestrator/execution_engine.py`, `backend/services/orchestrator/response_finalizer.py`.
## Installation
Download the installer from the GitHub releases page.

## Known Issues
None reported for this release.
