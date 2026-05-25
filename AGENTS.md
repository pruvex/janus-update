# Janus Codex Operating Rules

Diese Datei ist fuer Codex verbindlich, wenn im Repository `C:\KI\Janus-Projekt` gearbeitet wird.

## Core Rule

Jede Janus-Anfrage wird zuerst geroutet. Nicht direkt implementieren, wenn Backlog-, Spec-, TestSpec-, Handoff- oder Validierungsartefakte fehlen.

## Routing Pflicht

Vor groesseren Arbeitsschritten ausgeben:

```text
MODEL SWITCH GATE
- Skill:
- Empfohlenes Modell:
- Empfohlene Intelligenz:
- Neuer Chat:
- Kontextstrategie:
- Grund:
```

Danach auf User-Freigabe warten, wenn ein Modell-, Intelligenz- oder Chatwechsel empfohlen wird.

User-Antworten:

- `ok`: im empfohlenen Setup weiterarbeiten.
- `bleib hier`: im aktuellen Setup weiterarbeiten.
- anderes Modell genannt: Empfehlung neu bewerten und fortfahren.

## Aktuelle Modellmatrix

| Modell | Standardnutzung | Intelligenz |
| --- | --- | --- |
| `5.5` | Architektur, Security, Privacy, Prompt-Injection, komplexe Fehleranalyse, Release-Gates, finale Audits | hoch bis sehr hoch |
| `5.4` | Feature-Design, Specs, TestSpecs, komplexe Produktentscheidungen, Review von Pipeline-Artefakten | mittel bis hoch |
| `5.4 mini` | Backlog-Pflege, Doku-Normalisierung, Snapshot-/Dashboard-Sync, mechanische Checks | niedrig bis mittel |
| `5.3 codex` | Implementierung, Refactoring, Tests, Debugging, lokale Repo-Arbeit | mittel bis hoch |
| `5.2` | einfache Zusammenfassungen, kleine Textaenderungen, Statusberichte | niedrig |

## Janus Skill Map

| Situation | Skill |
| --- | --- |
| Vage Feature-Idee, Produktverhalten klaeren | `janus-feature-design` |
| Passenden Prozess, Modell, Kontext und naechsten Schritt bestimmen | `janus-skill-router` |
| Kleine Bugs, Verbesserungen, lokale Aenderungen | `janus-backlog-intake` / Backlog-Pipeline |
| Feature-Spec aus Decision Summary erzeugen | `janus-spec-generator` |
| Spec copy-safe und parserfaehig finalisieren | `janus-spec-normalizer` |
| Spec pruefen, bevor Tasks entstehen | `janus-spec-review` |
| Spec in Tasks ueberfuehren | `janus-spec-to-task` |
| Tasks zerlegen und verifizieren | `janus-task-breakdown` |
| Vor Implementierung Artefakte und Tests pruefen | `janus-preimplementation-check` |
| Code umsetzen | `janus-executioner` |
| Fehlgeschlagene Umsetzung debuggen | `janus-debug` |
| Ergebnis final auditieren | `janus-final-audit` |
| Registry, Backlog, Dashboard und Doku aktualisieren | `janus-documentation-update` |
| Build, Release und Artefaktnachweis erstellen | `janus-build-release` |
| Hygiene, veraltete Artefakte, Inkonsistenzen finden | `janus-health-check` |
| Git/GitHub, Commit, Push, Checkpoint, Branch, Tag, PR | `janus-git-governance` |

## Single Sources of Truth

- Backlog: `documentation/backlog/BACKLOG.md`
- Pipeline Contract: `documentation/pipeline/PIPELINE_CONTRACT.md`
- Feature Specs: `documentation/SPEC/`
- TestSpecs: `documentation/TEST_SPEC/`
- Test runs: `documentation/test-runs/`
- Test results: `documentation/test-results/`
- Dashboard snapshot: `janus-dashboard/data/backlog.snapshot.json`
- Versionierte Codex-Skill-Quellen: `documentation/codex/skills/`
- Installierte Codex-Skill-Arbeitskopien: `C:\Users\pruve\.codex\skills\janus-*`
- Legacy Windsurf workflows: `.windsurf/workflows/`

## Token Economy

- Zuerst `rg` und gezielte Dateiansichten nutzen.
- Keine Vollrepo-Ladung.
- Nur bindende Artefakte laden: Backlog-Item, Spec, TestSpec, Handoff, direkt betroffene Dateien.
- Lange Historie nur als Archiv behandeln, nicht als aktive Anforderung.
- Bei neuem Feature, langem Chat oder unabhaengigem Audit neuen Chat empfehlen.

## Git/GitHub Governance

- Normalarbeit findet auf `develop` statt.
- `master` ist nur fuer Releases.
- `backup` ist der private Sicherheits-Remote fuer Entwicklungscommits.
- `origin` ist der oeffentliche/update Remote und bekommt nur `master` plus explizite Release-Tags.
- Nie blind `git add .` verwenden, wenn der Worktree nicht vollstaendig als ein Changeset geprueft wurde.
- Vor Commit/Push immer `janus-git-governance` verwenden.
- Vor unabhaengigen Audits muss ein sauberer Checkpoint-Commit empfohlen werden.
- Commit-Gruppen muessen fachlich zusammenhaengen: Code + passende Tests + passende Doku/Evidenz.
- Keine Secrets, lokalen DBs, Build-Artefakte, privaten Logs oder grossen Dateien committen, ausser explizit geprueft und begruendet.
- Commit/Push/Tag/Merge nur nach expliziter User-Freigabe ausfuehren.
- Janus-Codex-Skills muessen im Repo unter `documentation/codex/skills/` versioniert werden; die Kopien unter `C:\Users\pruve\.codex\skills` gelten als installierte Arbeitskopien.

## Completion Rules

Ein Schritt ist erst fertig, wenn es echte Evidenz gibt oder ein Blocker dokumentiert ist.

Jeder Abschluss nennt:

- canonical state: `PASS`, `BLOCKED`, `NEEDS_INFO`, `FAILED`, `HANDOFF` oder `ESCALATED`
- ausgefuehrte Checks
- geaenderte Dateien
- naechster Skill oder Gate
