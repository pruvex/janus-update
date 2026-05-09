# Janus Projekt 0.4.17-beta.22
**Released:** 2026-05-09 01:08

### Fixed
- **BACKLOG-017:** ChromaDB-Module fehlen im PyInstaller-Bundle. PyInstaller spec um ChromaDB-Submodule erweitert: `collect_data_files('chromadb')`, `collect_data_files('chromadb', include_py_files=True)`, `hiddenimports=['chromadb.telemetry.product.posthog', 'chromadb.api.rust']`. Vektor-Service und Skill-Router starten ohne ChromaDB-Import-Fehler. Manual Janus Test PASS. Files: `janus_backend.spec`. Version: 0.4.17-beta.22.
## 📦 Installation
Download the installer from the GitHub releases page.

## 🐛 Known Issues
None reported for this release.
