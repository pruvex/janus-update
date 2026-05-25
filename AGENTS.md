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

## Codex Plugins

Plugins unterstuetzen den Janus-Skill-Workflow, ersetzen ihn aber nicht. Zuerst wird immer ueber `janus-skill-router` entschieden, welcher Janus-Skill fuehrt. Danach werden Plugins gezielt als Werkzeuge fuer Artefakte, Evidenz oder externe Formate genutzt.

Standardnutzung:

- `Codex Security`: gezielte Security-/Privacy-/Attack-Path-Pruefungen, besonders vor Final Audit, Release oder bei sicherheitsrelevanten Aenderungen.
- `Documents`: `.docx`/Word-Artefakte nur, wenn der Nutzer ein teilbares Dokument, Review-Dokument, Bericht oder extern nutzbares Protokoll braucht.
- `Spreadsheets`: strukturierte Auswertungen, Kosten-/Skill-Usage-Analysen, Tabellen, CSV/XLSX oder Metriken, wenn Markdown nicht mehr ausreicht.
- `Presentations`: Entscheidungs-, Review- oder Stakeholder-Decks, nicht fuer normale interne Janus-Arbeit.
- `Browser`: falls in der aktuellen Codex-Umgebung verfuegbar, fuer lokale UI-Pruefung, Screenshots, Klicktests und visuelle Evidenz nach Frontend-Aenderungen.

Nicht automatisch neue Plugins installieren. Erst den bestehenden Workflow nutzen und nur dann gezielt ein Plugin vorschlagen, wenn ein wiederkehrender Engpass dadurch klar geloest wird.

## Janus Arbeitsmodus

Die kompakte Praxisanleitung steht in `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`.

Standard:

- ein Ziel
- ein Skill
- ein gebundenes Artefakt oder eine klare Entscheidungsfrage
- eine Modell-/Intelligenz-Empfehlung
- ein naechster Gate- oder Handoff-Schritt
- Evidenz oder dokumentierter Blocker

Bei einer neuen Janus-Arbeitssession zuerst einen leichten `janus-health-check DAILY` ausfuehren oder empfehlen, bevor in Backlog-, Spec-, Implementierungs- oder Release-Arbeit eingestiegen wird. Weekly/Monthly Healthchecks laufen ueber die Codex-Automation: samstags, erster Samstag im Monat als `MONTHLY`, sonst `WEEKLY`.

Wenn der Nutzer nur `ok`, `weiter`, `los` oder aehnlich schreibt, fuehrt Codex den zuletzt empfohlenen naechsten Schritt aus, sofern dieser keine riskante Git-, Release-, Delete- oder Publish-Aktion ist. Fuer Commit, Push, Tag, Merge, Release, Delete oder riskante Auto-Fixes bleibt explizite Freigabe erforderlich.

## Wunsch-Intake

Wenn der Nutzer einen konkreten, klein wirkenden Wunsch beschreibt, zum Beispiel ein bestehendes UI-Verhalten, eine gespeicherte Einstellung, einen kleinen Bug oder eine klar begrenzte Verbesserung, macht Codex zuerst eine kurze Bewertung:

- vermuteter Pfad: Backlog-Pipeline oder Feature-Pipeline
- empfohlene Modelle fuer Bewertung, Planung und Umsetzung
- grober Aufwand: S, M oder L
- Risiko: niedrig, mittel oder hoch
- Nutzen: niedrig, mittel oder hoch
- naechster Skill und ob ein Dashboard-/Backlog-Task angelegt werden soll

Kleine, klare Verbesserungen gehen standardmaessig in `janus-backlog-intake`, danach Priorisierung und Dashboard-Handoff. Codex implementiert nicht direkt, solange kein Backlog-/Handoff-/Precheck-Artefakt gebunden ist.

Wenn der Wunsch groesser, produktentscheidend, mehrdeutig, surface-uebergreifend, persistenzrelevant oder riskant wirkt, geht Codex automatisch zuerst in `janus-feature-design`. Dort wird der Wunsch mit dem Nutzer entschieden und fixiert. Erst danach entstehen Spec, normalisierte Spec, Review, Tasks und Backlog-/Dashboard-Sichtbarkeit.

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

Substantielle Skill-Laeufe werden fuer spaetere Optimierung in `documentation/codex/SKILL_USAGE_LOG.md` dokumentiert. Dafuer bevorzugt das Script `documentation/codex/scripts/record_skill_usage.py` nutzen. Reine Rueckfragen, kurze Statusantworten und reine Git-Ausfuehrung ohne neue Prozessentscheidung muessen nicht geloggt werden.

`WHAT_I_LEARNED.md` ist das Langzeitgedaechtnis fuer validierte, wiederverwendbare technische Muster. Nicht vollstaendig laden. Vor Debug-, Build-/Release-, TestPipeline-Generator- und Final-Audit-Blockern gezielt suchen mit `documentation/codex/scripts/search_what_i_learned.py`. Neue Eintraege nur append-only und nur bei validierter Root Cause, Loesung, Haertung und Tripwire; bevorzugt `documentation/codex/scripts/append_learning_pattern.py` nutzen.
