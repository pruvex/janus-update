# Janus Projekt 0.4.17-beta.45
**Released:** 2026-05-27 20:03

### Fixed
- **BACKLOG-098 / Lokale GPU-Erkennung fuer Modell-Empfehlungen gehaertet:** Der Local-LLM-Hardwarecheck erkennt dedizierte GPUs unter Windows jetzt robuster ueber mehrere Quellenketten (`nvidia-smi`, CIM/PowerShell, `wmic`, Registry, `dxdiag`) statt bei einem einzelnen Ausfall auf "keine dedizierte GPU" zu fallen. VRAM-Werte werden transparent mit Herkunft und Sicherheit markiert, inklusive Heuristik-Fallback fuer bekannte Kartenprofile (u. a. RX 7700 XT). Die UI zeigt bei unsicherem VRAM jetzt explizit "nicht sicher ermittelbar" und blendet Debug-Evidence zur Erkennungsquelle ein. Validation: `py_compile` PASS; fokussierte pytest PASS (7/7); Vite-Build + frontend-dist check PASS. Files: `backend/services/ollama_manager.py`, `backend/tests/test_ollama_manager_recommendations.py`, `frontend/src/components/Settings/LocalLLMWizard.tsx`, `frontend/css/settings.css`.
## Installation
Download the installer from the GitHub releases page.

## Known Issues
None reported for this release.
