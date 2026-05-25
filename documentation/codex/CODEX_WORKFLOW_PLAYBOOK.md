# Janus Codex Workflow Playbook

Stand: 2026-05-25

## Zweck

Dieses Playbook beschreibt den normalen Arbeitsmodus fuer Janus in Codex. Es ist die kompakte Praxisanleitung zu `AGENTS.md`, den Janus-Skills und dem Pipeline Contract.

Ziel: gefuehrt arbeiten, nichts vergessen, keine Artefakte verlieren, tokenbewusst bleiben und nur dann Komplexitaet laden, wenn sie wirklich gebraucht wird.

## Arbeitsprinzip

Jeder Arbeitsblock hat genau:

- ein Ziel
- einen passenden Skill
- ein gebundenes Artefakt oder eine klare Intake-Frage
- eine Modell-/Intelligenz-Empfehlung
- einen naechsten Gate- oder Handoff-Schritt
- Evidenz oder einen dokumentierten Blocker

Wenn eines davon fehlt, wird nicht blind implementiert. Der naechste Schritt ist dann Routing, Intake, Precheck oder eine Entscheidungsfrage.

## Standardstart

Bei jeder neuen Janus-Aufgabe:

1. `janus-skill-router` klassifiziert die Aufgabe.
2. Codex empfiehlt Modell, Intelligenz, Chatstrategie und Kontextstrategie.
3. Bei Modell-/Chatwechsel wartet Codex auf `ok`, `bleib hier` oder eine andere klare Nutzerentscheidung.
4. Danach laeuft genau ein Skill-Pfad weiter.

## Intake-Pfade

| Nutzerlage | Standardpfad |
| --- | --- |
| Vage Feature-Idee | `janus-feature-design` -> `janus-spec-generator` |
| Fertige Feature-Entscheidung | `janus-spec-generator` -> `janus-spec-normalizer` |
| Fertige Spec | `janus-spec-review` -> `janus-spec-to-task` |
| Grobe Task-Datei | `janus-task-breakdown` |
| Kleiner Bug oder Verbesserung | `janus-backlog-intake` -> `janus-backlog-prioritization` -> `janus-backlog-handoff` |
| READY Backlog-Item aus Dashboard | `janus-backlog-handoff` |
| Umsetzung starten | `janus-preimplementation-check` -> `janus-executioner` |
| TestSpec/TestRun/TestResult | `janus-test-pipeline` |
| Fehler nach Umsetzung/Test | `janus-debug` |
| Abschluss nach Umsetzung | `janus-final-audit` -> `janus-documentation-update` |
| Build/Release | `janus-build-release` + `janus-git-governance` |
| Ordnung/Drift/Altlasten | `janus-health-check` |

## Modell- und Kostenregeln

| Aufgabe | Modell | Intelligenz | Neuer Chat |
| --- | --- | --- | --- |
| Status, kleine Doku, Commit-Governance | `5.4 mini` oder `5.2` | niedrig | nein |
| Backlog, Dashboard, Normalisierung, Health DAILY | `5.4 mini` | niedrig bis mittel | nein |
| Feature-Design, Spec, Review, Task Breakdown | `5.4` | mittel | bei langem Chat ja |
| Code, Tests, lokale Debugging-Arbeit | `5.3 codex` | mittel bis hoch | meist nein |
| Final Audit, Security, Privacy, Release-Risiko | `5.5` | hoch | ja |

Codex soll proaktiv eine Umstellung empfehlen, wenn der naechste Schritt deutlich guenstiger oder sicherer mit einem anderen Modell ist.

## Neuer Chat

Neuen Chat empfehlen bei:

- neuer Feature-Idee
- grosser Spec-Erzeugung
- unabhaengigem Audit
- Release-/Publish-Gate
- langem oder verrauschtem Kontext
- Wechsel von Planung zu Umsetzung, wenn viele alte Entscheidungen im Chat liegen

Im aktuellen Chat bleiben bei:

- laufender kleiner Dokumentations- oder Skill-Arbeit
- direkter Fortsetzung eines gerade validierten Artefakts
- Commit-/Push-Checkpoint
- kurzer Status- oder Routing-Frage

## Stop-Gates

Sofort stoppen und klaeren, wenn:

- kein eindeutiges Artefakt gebunden ist
- Chatwunsch und Spec/Task widersprechen
- Produktentscheidung fehlt
- Scope mehrere gleich plausible Pfade hat
- Sicherheits-, Datenschutz-, Provider- oder Release-Risiko unklar ist
- Tests oder Evidenz fehlen, aber Completion behauptet werden muesste
- Git-Aktion ohne explizite Freigabe noetig waere

## Git-Rhythmus

Commit empfehlen:

- nach einem validierten Skill- oder Doku-Baustein
- nach einer abgeschlossenen Implementierung mit Evidenz
- vor unabhaengigem Audit
- vor riskanter Debug-/Refactor-Arbeit
- vor Release-Vorbereitung

Keinen Commit empfehlen:

- bei reiner Planung ohne Dateiaenderung
- bei gemischten, nicht verstandenen Changesets
- wenn Tests bewusst rot sind und kein WIP-Checkpoint vereinbart wurde

Immer:

- `janus-git-governance` vor Commit/Push nutzen
- Pfade explizit stage'n
- nie `git add .` im grossen Dirty Tree
- normale Entwicklungscommits nur nach `backup/develop` pushen

## Completion-Check

Jeder Arbeitsblock endet mit:

- Canonical State: `PASS`, `BLOCKED`, `NEEDS_INFO`, `FAILED`, `HANDOFF` oder `ESCALATED`
- ausgefuehrte Checks
- geaenderte Dateien
- naechster Skill
- Modell-/Chat-Empfehlung fuer den naechsten Schritt
