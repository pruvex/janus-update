# Janus Projekt 0.4.17-beta.47
**Released:** 2026-05-27 21:05

### Fixed
- **Auto-Update Feed-Reihenfolge repariert:** Der GitHub-Publisher setzt neue Releases jetzt explizit auf den aktuellen Git-HEAD (`target_commitish`), damit frische Beta-Tags im GitHub-Release-Feed korrekt vor aelteren Beta-Releases erscheinen. Dadurch findet Electron-Updater fuer installierte `0.4.17-beta.44` Clients wieder den neuesten Beta-Release statt am aelteren Feed-Eintrag haengen zu bleiben. Files: `scripts/publish_to_github.cjs`.
## Installation
Download the installer from the GitHub releases page.

## Known Issues
None reported for this release.
