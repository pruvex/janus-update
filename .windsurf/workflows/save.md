---
description: Atomic-State-Save für Diamond-OS/Janus. Speichert einen validierten stabilen Arbeitsstand per Commit und Push nach backup/develop. Kein Production Release.
---

# /save – Atomic-State-Save

## Zweck

`/save` sichert einen stabilen, dokumentierten Zwischenstand.

Dieser Workflow ist:

- ein Backup-/Arbeitsstands-Save
- ein Commit nach `develop`
- ein Push nach Remote `backup`

Dieser Workflow ist NICHT:

- ein Production Release
- ein GitHub-Origin-Publish
- ein Version-Bump
- ein Ersatz für `SKILL 8 – BUILD RELEASE`

## Ziel-Remote

Verbindliches Ziel:

```text
git push backup develop
```

`origin` darf durch `/save` nicht gepusht werden.

## Zulässige Savepoints

`/save` ist zulässig:

- nach erfolgreichem `SKILL 4 – EXECUTIONER` mit PASS-Validierung vor dem nächsten Task
- nach `SKILL 5 – FEATURE DEBUG`, wenn Code geändert wurde und der manuelle Janus-Retest PASS ist
- nach erfolgreichem `SKILL 7 – DOKUMENTATIONSUPDATE`
- nach einem explizit stabilen Arbeitsstand, wenn der Nutzer `/save` ausdrücklich anfordert und keine Blocker vorliegen

## Harte Blocker

STOP. Kein Commit und kein Push, wenn eines davon gilt:

- Tests oder Validierungen sind bekannt fehlgeschlagen
- `TASK EXECUTION FAILED`
- `NEEDS RETEST`
- `ESCALATION REQUIRED`
- `BLOCKED`
- Skill 5 ist `BLOCKED`
- Skill 6 benötigt noch einen Retest
- unklare oder widersprüchliche Arbeitsanweisung
- Nutzer verlangt versehentlich Production Release statt Save
- aktueller Branch ist nicht `develop`
- Remote `backup` fehlt

Bei Blocker:

```text
SAVE BLOCKED

Reason:
- <konkreter Blocker>

Action:
- <nächster sicherer Schritt>
```

## Preflight

Vor jeder Save-Aktion prüfen:

1. Aktueller Branch:

```powershell
git branch --show-current
```

Muss sein:

```text
develop
```

2. Remotes:

```powershell
git remote -v
```

Muss enthalten:

```text
backup
```

3. Arbeitsstand:

```powershell
git status --short
```

4. Optionaler Diff-Überblick, wenn der Arbeitsstand unklar ist:

```powershell
git diff --stat
```

## Validierung

Führe die für den aktuellen Arbeitsstand passenden minimalen Validierungen aus.

Beispiele:

- Backend Python:

```powershell
python -m py_compile <geänderte-python-dateien>
```

- gezielte Tests:

```powershell
python -m pytest <relevante-tests> -q
```

- Dashboard/API/UI TypeScript:

```powershell
npx tsc --noEmit --pretty false
```

Nur relevante Checks ausführen. Keine unnötig breiten oder riskanten Kommandos.

Wenn keine sinnvolle automatische Validierung möglich ist:

- explizit melden
- nur fortfahren, wenn kein bekannter Blocker existiert und der Nutzer den Save bestätigt

## Commit-Regeln

Vor Commit:

- kurz zusammenfassen, welche Dateien geändert sind
- keine fremden/unverstandenen Änderungen verschweigen
- bei riskanten oder unerwarteten Änderungen nachfragen

Staging:

```powershell
git add <relevante-dateien>
```

Wenn der Nutzer ausdrücklich den gesamten stabilen Arbeitsstand speichern will:

```powershell
git add -A
```

Commit-Message-Format:

```text
save: <kurze beschreibung des stabilen stands>
```

Beispiele:

```text
save: dashboard backlog handoff snapshot cache
save: post skill 7 documentation update
save: stable backlog pipeline state
```

Commit:

```powershell
git commit -m "save: <kurze beschreibung>"
```

Wenn es nichts zu committen gibt:

```text
SAVE SKIPPED

Reason:
- No changes to commit.
```

## Push-Regeln

Nach erfolgreichem Commit:

```powershell
git push backup develop
```

Nicht pushen nach:

```text
origin
```

Wenn Push fehlschlägt:

```text
SAVE PARTIAL

Commit:
- created locally

Push:
- failed

Reason:
- <Fehler>

Action:
- Remote/Auth/Network prüfen und `/save` erneut ausführen oder Push manuell wiederholen.
```

## Output-Format

Am Ende immer ausgeben:

```text
SAVE RESULT: PASS | BLOCKED | PARTIAL | SKIPPED

Branch:
- <branch>

Remote:
- backup/develop

Validation:
- <ausgeführte Checks oder skipped + reason>

Files saved:
- <Kurzliste oder Anzahl>

Commit:
- <hash oder none>

Push:
- PASS | FAILED | SKIPPED

Notes:
- <wichtige Hinweise>
```

## Sicherheitsregel

`/save` darf niemals:

- Releases bauen
- Versionen bumpen
- nach `origin` pushen
- fehlschlagende oder blockierte Zustände als stabil speichern
- unklare fremde Änderungen ohne Hinweis einschließen
