# Janus Projekt 0.4.17-beta.44
**Released:** 2026-05-27 01:52

### Fixed
- **BACKLOG-097 / Lokales LLM Setup erneut ausfuehrbar machen:** Der Button `Lokales LLM einrichten` ist jetzt nach dem Erstsetup erneut nutzbar. Der Hardwarecheck zieht aktuelle Empfehlungen aus der Ollama-Library, haengt zusaetzlich zwei Coding/Vibecoding-Modelle an, schreibt deutsche Use-Case-Texte und zeigt fehlende Groessenangaben als Klartext statt `0 GB`. Validation: `py_compile` PASS; fokussierte pytest PASS; Logs sauber. Files: `backend/services/ollama_manager.py`, `backend/tests/test_ollama_manager_recommendations.py`, `frontend/src/components/Settings/LocalLLMWizard.tsx`.
## Installation
Download the installer from the GitHub releases page.

## Known Issues
None reported for this release.
