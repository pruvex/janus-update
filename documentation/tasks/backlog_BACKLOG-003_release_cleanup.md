# BACKLOG TASK – BACKLOG-003 – Alte Release-Installer in release/ aufräumen

## 1. Ziel
Alte janus-setup-*.exe Dateien aus release/ entfernen und nur das neueste Release behalten, um ~2GB Speicherplatz freizugeben.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-003
- **Beeinflusst:** release/ Ordner
- **Risiko-Einschätzung:** LOW

## 3. Scope
### IN SCOPE
- Entfernen von janus-setup-0.4.17-beta.4.exe
- Entfernen von janus-setup-0.4.17-beta.9.exe
- Entfernen von janus-setup-0.4.17-beta.10.exe
- Behalten von janus-setup-0.4.17-beta.11.exe (neuestes vorhandenes Release)

### OUT OF SCOPE
- Keine Änderung an release/ Konfigurationsdateien (yml, json)
- Keine Änderung an Update-Manifest-Logik
- Keine Änderung an electron-builder Konfiguration

## 4. Umsetzungsschritte
1. release/ Ordner prüfen und aktuelle Dateien auflisten
2. Identifizieren des neuesten janus-setup-*.exe (beta.11)
3. Löschen von janus-setup-0.4.17-beta.4.exe
4. Löschen von janus-setup-0.4.17-beta.9.exe
5. Löschen von janus-setup-0.4.17-beta.10.exe
6. Verifizieren, dass nur janus-setup-0.4.17-beta.11.exe verbleibt

## 5. Acceptance Criteria
- [ ] release/ enthält nur janus-setup-0.4.17-beta.11.exe
- [ ] release/ enthält keine janus-setup-0.4.17-beta.4.exe
- [ ] release/ enthält keine janus-setup-0.4.17-beta.9.exe
- [ ] release/ enthält keine janus-setup-0.4.17-beta.10.exe
- [ ] release/ Konfigurationsdateien (yml, json) sind unverändert

## 6. Tests / Validierung
- Manuelles Prüfen des release/ Ordners nach Löschung
- Verifizieren, dass keine Fehler in electron-builder Logs auftreten

## 7. Model
- **Assigned Model:** Kimi k2.5
- **Reason:** Deterministische Löschaktion mit klarer Scope-Definition, kein Code-Change, keine Integration, keine Security-Impact.

---

## POST-IMPLEMENTATION AUDIT TRAIL

### Implementation Scope
- **Implemented tasks:** BACKLOG-003 (Release-Cleanup)
- **Feature status:** DONE
- **Final audit status:** PASS

### Files Changed
- **release/janus-setup-0.4.17-beta.4.exe:** Gelöscht
- **release/janus-setup-0.4.17-beta.9.exe:** Gelöscht
- **release/janus-setup-0.4.17-beta.10.exe:** Gelöscht
- **release/janus-setup-0.4.17-beta.11.exe:** Behalten (neuestes Release)

### What Was Done
Drei alte Release-Installer (beta.4, beta.9, beta.10) aus release/ Ordner entfernt, um ~1.46 GB Speicherplatz freizugeben. Nur das neueste Release (beta.11) verbleibt. Konfigurationsdateien (yml, json) unverändert.

### Validation Evidence
- **Manual Janus test:** PASS — release/ Ordner enthält nur janus-setup-0.4.17-beta.11.exe
- **Skill 6:** N/A — kein Debug nötig
- **Git Status:** release/ zeigt keine getrackten Änderungen (nicht-getrackte .exe Dateien gelöscht)

### Final Audit Fixes
- Keine Fixes nötig.

### Version Bump
- **Old version:** 0.4.17-beta.12
- **New version:** 0.4.17-beta.12 (kein Code-Change)
- **Files changed:** None

### Remaining Risks
- Keine Risiken.

## DEBUGGING LOG

- Keine Probleme. Deterministische Löschaktion erfolgreich.
