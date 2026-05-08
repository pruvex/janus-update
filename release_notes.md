# Janus Projekt 0.4.17-beta.17
**Released:** 2026-05-08 00:13

### Fixed
- **BACKLOG-011:** Video-Modal False-Positive Fix + Gemini List-Mode Override. URL-Detection Fallback in `response_finalizer.py` deaktiviert, modal_request wird ausschließlich aus video.search tool_results abgeleitet. Zusätzlich Backend-Override in `tool_executor.py` erzwingt `mode="list"` für `video.search`, da Gemini den Schema-Default ignoriert und immer `"single"` setzt. Gemini zeigt jetzt mehrere Videos aufgelistet und das Modal öffnet automatisch mit dem ersten Video.
## 📦 Installation
Download the installer from the GitHub releases page.

## 🐛 Known Issues
None reported for this release.
