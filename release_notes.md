# Janus Projekt 0.4.17-beta.23
**Released:** 2026-05-10 02:23

### Fixed
- **BACKLOG-019:** Hardcoded gpt-5-mini verursacht Fallback-Warnung nach OpenAI-Key-Eingabe. Alle hardcoded Modell-IDs (gpt-5-mini) aus Backend-Code entfernt und durch dynamische Auswahl aus Model-Katalog ersetzt. Neue Helper-Funktion `get_first_available_text_model_with_provider()` in llm_gateway.py wählt deterministisch (provider, model_id) aus Katalog. main.py und calendar_ai_engine.py nutzen dynamische Auswahl statt hardcoded Fallback. Provider/Model-Mismatch behoben: Provider wird jetzt immer passend zum Modell aus Katalog gesetzt. Robust gegen leere Kataloge: gibt leeren String zurück bei leerem Katalog. Files: `backend/services/llm_gateway.py`, `backend/main.py`, `backend/services/calendar/calendar_ai_engine.py`. Manual Janus Test PASS.
## 📦 Installation
Download the installer from the GitHub releases page.

## 🐛 Known Issues
None reported for this release.
