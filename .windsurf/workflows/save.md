---
description: Auto-Backup zu Janus-Backup (hardened /save)
---

# Skill: /save
Automatisches Backup des Codes zu Janus-Backup (privates Repo).

**Policy:**
- Commits gehen NUR auf `develop` (nie auf `master`).
- Blocker-Check: Abbruch bei Dateien >90 MB, die nicht in .gitignore stehen.
- Push zum Remote `backup` (Janus-Backup).

**Atomic State-Save Pattern (VERPFLICHTEND):**
Bevor das Save-Skript ausgeführt wird: Analysiere die letzten Änderungen der Session, verfasse ein neues [CURRENT_SESSION_DELTA] im Tabellenformat und füge es in PROJECT_STATE.md ein. Erhöhe die Beta-Version im Datei-Header um +1.

**Ausführung:**
// turbo
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/save.ps1
```

Alternativ manuell (wenn Script fehlt):
```powershell
git add .
git commit -m "Auto-Save $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git push backup develop
```
