# Janus Solo Git v2

**Status:** aktiv ab 2026-07-12  
**Zielgruppe:** Operator (VM-Snapshots) + Codex + Cursor  
**Prinzip:** Einfach, schnell, ein Feature zur Zeit — kein Worktree-Archäologie-Theater.

---

## Kurzfassung

```text
master                 ← einziger Integrations-Branch (aktueller Wahrheitsstand)
feature/<kurzname>     ← genau ein aktiver Feature-Branch (empfohlen)
backup/master          ← privates Remote-Backup nach fertigem Feature
origin/master          ← nur Releases + Tags
origin/codex-sync      ← nur CURRENT_STATE für ChatGPT
VM-Snapshot            ← echtes Rollback-Sicherheitsnetz (Operator)
```

**Legacy:** `develop` ist deprecated. Nicht für neue Arbeit anlegen. Bestehende Historie wird einmalig nach `master` überführt.

---

## Wer macht was?

| Aufgabe | Werkzeug |
|---------|----------|
| „Alles kaputt, zurück“ | **VM-Checkpoint** (Operator) |
| Feature-Historie, Offsite-Backup | **Git → backup** |
| ChatGPT weiß, was Codex tat | **origin/codex-sync** (nur `CURRENT_STATE.md`) |
| Öffentliches Release | **origin/master** + Tag |

Git ersetzt **nicht** die VM. Git ist Tagebuch + Backup + ChatGPT-Sync.

---

## Täglicher Ablauf (Codex / Cursor)

### 1. Neues Feature starten

```powershell
git checkout master
git pull backup master
git checkout -b feature/<kurzname>
```

Vor riskanter Arbeit: **VM-Snapshot** (Operator).

### 2. Arbeiten

- Codex/Cursor arbeiten **nur** auf dem aktiven `feature/*`-Branch.
- Kein paralleles Epic auf demselben Branch.
- Keine Git-Worktrees, außer der Operator verlangt ausdrücklich parallele Epics.

### 3. Feature fertig + validiert

```powershell
git checkout master
git merge feature/<kurzname> --no-ff
git push backup master
git branch -d feature/<kurzname>
```

Ein Feature = **ein Commit auf dem Feature-Branch ist OK** (Lean Delivery). Nicht in viele Mini-Commits zerlegen.

### 4. ChatGPT-Sync (Pflicht nach substantiellem Block)

Nach `CURRENT_STATE.md`-Update:

```powershell
.\documentation\codex\scripts\sync_codex_current_state.ps1
```

Oder manuell — siehe Abschnitt „codex-sync“ unten. **Nur mit Operator-Freigabe** (`sync: YES`).

### 5. Release (selten)

Über `janus-build-release` + `janus-git-governance`:

1. `master` sauber und validiert  
2. Version bump + Tag auf `master`  
3. Build/Verify  
4. `git push origin master` + expliziter Release-Tag  

---

## Regeln für Codex (verbindlich)

1. **Kein `develop`** für neue Arbeit — immer `master` + `feature/*`.
2. **Keine Worktree-Archäologie** — dirty files nicht klassifizieren/sortieren, außer der Operator fragt explizit danach.
3. **Maximal ein aktiver `feature/*`-Branch** — vor neuem Feature altes mergen oder parken.
4. **Commit/Push/Merge/Sync** nur nach expliziter Operator-Freigabe (`commit: YES`, `push: YES`, `sync: YES`).
5. **`git add .` verboten**, außer beim einmaligen Archive-WIP-Migrationsschritt mit Operator-Freigabe.
6. **Nach fertigem Feature:** merge → `backup/master` push → `codex-sync` empfehlen/ausführen (mit Freigabe).
7. **`git_guard.py` / `propose_changesets.py`** nur bei unklarem Scope oder Release — nicht bei jedem kleinen Slice.

---

## codex-sync (ChatGPT-Remote-Wahrheit)

- **Branch:** `origin/codex-sync`
- **Datei:** nur `documentation/ai/CURRENT_STATE.md`
- **Wann:** nach jedem substantiellen Janus-Arbeitsblock (siehe AGENTS.md)
- **Warum:** ChatGPT darf keinen aktuellen Stand annehmen, wenn dieser Sync fehlt — auch nicht von `backup/master`.

Script (bevorzugt):

```powershell
.\documentation\codex\scripts\sync_codex_current_state.ps1
```

---

## Commit-Nachricht (kurz)

```text
type(scope): summary

Evidence:
- pytest … PASS
```

Typen: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `build`, `release`

---

## Einmalige Migration (develop → master, Mixed-WIP archivieren)

**Nur mit VM-Snapshot zuvor. Nur mit Operator-Freigabe.**

```powershell
.\documentation\codex\scripts\migrate_solo_git_once.ps1 -ArchiveMixedWip
```

Schritte des Scripts:

1. Prüft VM-Hinweis / dirty state  
2. Fast-forward `master` auf Stand von `develop` (committed history)  
3. Optional: alle offenen Änderungen als ein Archiv-Commit (`chore: archive mixed WIP before solo-git v2`)  
4. Setzt `master` als Arbeitsbranch  
5. Druckt nächste Schritte (backup push, codex-sync)

**M6-Worktree:** Vor Migration entscheiden — M6-Branch mergen oder Worktree separat lassen.

---

## Was bewusst wegfällt

- Dauer-Branch `develop` für Normalarbeit  
- Git-Worktrees als Standard  
- Ständige „1036 dirty entries“-Reports  
- Multi-Commit-Splitting für ein kleines Backlog-Item  
- `git push backup develop`  

---

## Referenzen

- Skill: `documentation/codex/skills/janus-git-governance/SKILL.md`
- Operator-Regeln: `AGENTS.md` → Git/GitHub Governance
- Sync-Script: `documentation/codex/scripts/sync_codex_current_state.ps1`
- Migration: `documentation/codex/scripts/migrate_solo_git_once.ps1`
