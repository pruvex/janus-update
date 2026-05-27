# Janus Projekt 0.4.17-beta.46
**Released:** 2026-05-27 20:46

### Fixed
- **Auto-Update Beta-Channel-Erkennung gehaertet:** Der Electron-Updater nutzt jetzt explizit den `beta` Channel (`autoUpdater.channel = 'beta'`) und die Release-Pipeline verarbeitet Channel-Metadaten konsistent (`beta.yml` statt stillschweigender `latest.yml`-Annahme). Manifest-Generierung, Artefakt-Verifikation, Publish-Upload und Published-Verification sind channel-aware und laden/verifizieren die passende Channel-Datei deterministisch. Zusaetzlich loggt der Updater `update-not-available` mit aktueller/remote Version fuer schnellere Diagnose auf Testsystemen. Files: `main.electron.cjs`, `electron/update-manager.cjs`, `scripts/generate_update_manifest.cjs`, `scripts/verify_update_artifacts.cjs`, `scripts/publish_to_github.cjs`, `scripts/verify_published_release.cjs`, `package.json`.
## Installation
Download the installer from the GitHub releases page.

## Known Issues
None reported for this release.
