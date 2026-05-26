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

Bei einer neuen Janus-Arbeitssession fuehrt Codex zuerst einen leichten `janus-health-check DAILY` aus oder empfiehlt ihn, wenn der Nutzer erkennbar nur eine kurze Status-/Antwortfrage stellt. Das gilt besonders bei Formulierungen wie `neue Session`, `weiter an Janus`, `lass uns anfangen`, `was steht an` oder aehnlich.

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

## Wunsch-Intake im Alltag

Wenn der Nutzer einen konkreten Wunsch nennt, klassifiziert Codex ihn zuerst in eine von zwei Bahnen:

1. Kleine, klare Verbesserung: bestehende Oberflaeche, einzelnes Verhalten, lokaler Bug, gespeicherte Einstellung, kleiner UI-/UX-Schliff oder klar begrenzte technische Schuld.
2. Groesseres Feature: neue oder unklare Oberflaeche, mehrere Entscheidungen, neue Persistenz/Integration, Sicherheits-/Datenschutzrisiko, mehrere betroffene Bereiche oder unklarer Nutzen/Scope.

Bei einer kleinen, klaren Verbesserung macht Codex kurz:

- relevante Dateien/Artefakte gezielt anschauen
- Backlog-/Dashboard-Task ueber `janus-backlog-intake` vorbereiten
- kurze Einschaetzung geben: empfohlene Modelle, grober Aufwand, Risiko, Nutzen
- naechsten Gate nennen: Priorisierung, Handoff oder Preimplementation Check

Bei einem groesseren oder unscharfen Feature startet Codex automatisch mit `janus-feature-design`, also Brainstorming/Entscheidungsmodus. Der Wunsch wird erst mit dem Nutzer besprochen, geplant und als `LATEST DECISION SUMMARY` fixiert. Danach folgen Spec-Generator, Spec-Normalizer, Spec-Review und erst dann Tasks/Backlog/Dashboard.

Heuristik:

- S-Aufwand: ein klarer Task, wenige Dateien, wenig Testflaeche.
- M-Aufwand: mehrere Dateien oder Persistenz/Testanpassungen, aber ein klares Ziel.
- L-Aufwand: neue UX-Flows, mehrere Systeme, Migrationen, Provider-/Security-/Release-Risiko.
- Niedriges Risiko: lokales Verhalten, gute Testbarkeit, keine Datenmigration.
- Mittleres Risiko: Persistenz, bestehende Nutzerzustaende, mehrere Einstiegspunkte.
- Hohes Risiko: Security, Privacy, Provider, Release, Datenverlust, Architekturgrenzen.

## Modell- und Kostenregeln

| Aufgabe | Modell | Intelligenz | Neuer Chat |
| --- | --- | --- | --- |
| Status, kleine Doku, Commit-Governance | `5.4 mini` oder `5.2` | niedrig | nein |
| Backlog, Dashboard, Normalisierung, Health DAILY | `5.4 mini` | niedrig bis mittel | nein |
| Feature-Design, Spec, Review, Task Breakdown | `5.4` | mittel | bei langem Chat ja |
| Code, Tests, lokale Debugging-Arbeit | `5.3 codex` | mittel bis hoch | meist nein |
| Final Audit, Security, Privacy, Release-Risiko | `5.5` | hoch | ja |

Codex soll proaktiv eine Umstellung empfehlen, wenn der naechste Schritt deutlich guenstiger oder sicherer mit einem anderen Modell ist.

## Plugin-Einsatz

Plugins sind Hilfswerkzeuge innerhalb des Janus-Skill-Flusses. Die Reihenfolge bleibt:

1. `janus-skill-router` bestimmt Ziel, Skill, Modell und Kontext.
2. Der fuehrende Janus-Skill definiert Artefakte, Checks und Gates.
3. Plugins werden nur eingesetzt, wenn sie fuer Evidenz, Ausgabeformat oder Analyse konkret nuetzen.

Standardregeln:

- `Codex Security`: bei Security-/Privacy-/Provider-Risiko, vor releasekritischen Audits oder wenn ein Finding validiert werden soll. Ergebnis fliesst in `janus-final-audit`, `janus-debug` oder Backlog.
- GitHub-Connector: bei PRs, Issues, Reviews, CI-Checks, Merge-Zustand und Publish-Flows. Das ist der bevorzugte Weg, wenn der naechste Schritt direkt auf GitHub stattfindet.
- `Documents`: wenn ein extern teilbares Word-Dokument gebraucht wird, zum Beispiel Review-Bericht, Entscheidungsprotokoll oder formale Dokumentation. Interne Janus-Quellen bleiben Markdown.
- `Spreadsheets`: wenn Skill-Usage, Healthcheck, Kosten, Testmatrix oder Backlog-Signale tabellarisch ausgewertet werden sollen. Markdown bleibt Standard, XLSX/CSV nur bei echtem Analysewert.
- `Presentations`: wenn Ergebnisse fuer Stakeholder, Review-Meetings oder Roadmap-Entscheidungen als Deck gebraucht werden. Nicht fuer normale Taskarbeit.
- `Browser`: wenn in der Umgebung verfuegbar, fuer lokale UI-/Dashboard-Pruefung, Screenshots, Klickpfade und visuelle Regressionen nach Frontend-Aenderungen.

Automatisierung:

- Bei Frontend-/Dashboard-Tasks im Precheck pruefen, ob Browser-Evidenz sinnvoll ist.
- Bei PR-/Review-/CI-/Publish-Arbeit den GitHub-Connector vor CLI-Fallbacks bevorzugen.
- Bei Security-/Privacy-Hinweisen im Router eine Security-Pruefung als moeglichen Gate nennen.
- Bei Weekly/Monthly Healthcheck koennen Skill-Usage- oder Healthdaten als Spreadsheet empfohlen werden, wenn Muster sonst schwer erkennbar sind.
- Bei Abschluss groesserer Phasen kann Documents oder Presentations empfohlen werden, wenn ein teilbares Ergebnis benoetigt wird.
- Plugin-Nutzung in `documentation/codex/SKILL_USAGE_LOG.md` als Check oder Artefakt dokumentieren, wenn sie fuer die Entscheidung relevant war.

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

GitHub-Connector bevorzugen, sobald der naechste Git-Schritt direkt auf GitHub stattfindet:

- Pull Requests aufmachen oder aktualisieren
- Review-Feedback abarbeiten
- GitHub Actions pruefen oder debuggen
- Issues und Labels spiegeln
- Publish-/Release-Schritte vorbereiten, wenn GitHub die Zielplattform ist

Immer:

- `janus-git-governance` vor Commit/Push nutzen
- Pfade explizit stage'n
- nie `git add .` im grossen Dirty Tree
- normale Entwicklungscommits nur nach `backup/develop` pushen

## Versionierung Und Auto-Update Release

Codex fuehrt Versionierung und Electron Auto-Update Release ueber Skills, nicht per Ad-hoc-Kommandos:

- Version bump: `janus-documentation-update`
- Commit/Push/Merge/Tag Gate: `janus-git-governance`
- Build, Manifest, Publish, Post-Publish Check: `janus-build-release`

Regeln:

- `package.json` ist Versionsquelle.
- `package-lock.json` und `backend/version.py` muessen synchron sein.
- Standard-Beta-Release: nur Beta-Nummer erhoehen, z.B. `0.4.17-beta.38` -> `0.4.17-beta.39`.
- Stable-, Patch-, Minor- oder Major-Wechsel nur nach expliziter Entscheidung.
- Electron Auto-Update Release braucht valide `latest.yml`, `janus-update-manifest.json`, Installer, optionale Blockmap, Hash-/Asset-Verifikation und GitHub Release Evidence.
- Publish zu `origin`/GitHub Release passiert erst nach `Publish: YES`.

## Completion-Check

Jeder Arbeitsblock endet mit:

- Canonical State: `PASS`, `BLOCKED`, `NEEDS_INFO`, `FAILED`, `HANDOFF` oder `ESCALATED`
- ausgefuehrte Checks
- geaenderte Dateien
- naechster Skill
- Modell-/Chat-Empfehlung fuer den naechsten Schritt

## Skill-Nutzungslog

Substantielle Skill-Laeufe werden im Log dokumentiert:

- `documentation/codex/SKILL_USAGE_LOG.md`

Nicht loggen:

- reine Rueckfragen
- kurze Statusantworten
- reine Commit-/Push-Ausfuehrung ohne neue Skill-Entscheidung
- fehlgeschlagene Shell-Versuche ohne Prozessrelevanz

Loggen:

- Routing-Entscheidungen
- Feature-/Spec-/Backlog-/Test-/Audit-/Release- und Health-Arbeitsbloecke
- Blocker, Eskalationen und Modellwechsel
- auffaellige Reibung, zum Beispiel zu viel Kontext, falscher Skill, fehlendes Artefakt, unklare Handoffs
- konkrete Optimierungsideen

Standardbefehl:

```powershell
python documentation\codex\scripts\record_skill_usage.py --skill <skill> --trigger "<kurzer Anlass>" --model <model> --intelligence <level> --chat same --state <PASS|BLOCKED|NEEDS_INFO|FAILED|HANDOFF|ESCALATED> --artifacts "<paths>" --checks "<checks>" --friction "none" --optimization "none"
```

Auswertung:

```powershell
python documentation\codex\scripts\summarize_skill_usage.py
```

Review-Rhythmus:

- nach jedem groesseren Arbeitsblock kurz loggen
- `janus-health-check` DAILY prueft Log-Existenz und Eintragszahl
- `janus-health-check` WEEKLY wertet Skills, States, Modelle, Reibung und Optimierungsideen aus
- `janus-health-check` MONTHLY nutzt wiederholte Reibung als Signal fuer Router-/Skill-Verbesserungen
- Samstag-Automation: erster Samstag im Monat = MONTHLY, sonst WEEKLY
- Daily ist keine Uhrzeit-Automation, sondern Session-Start-Regel
- bei wiederholter Reibung den betroffenen Skill oder Router schaerfen

## WHAT_I_LEARNED

`WHAT_I_LEARNED.md` ist das Janus-Langzeitgedaechtnis fuer wiederverwendbare technische Muster. Es wird nicht vollstaendig in den Kontext geladen.

Gezielt suchen:

```powershell
python documentation\codex\scripts\search_what_i_learned.py --query "<error tags root cause>"
```

Neues Pattern nur dann ergaenzen, wenn eine echte wiederverwendbare Erkenntnis vorliegt:

- Root Cause ist verstanden.
- Fix oder Regel wurde validiert.
- Es gibt eine klare Tripwire-Regel fuer die Zukunft.
- Das Pattern ist nicht schon vorhanden.

Standard ist append-only:

```powershell
python documentation\codex\scripts\append_learning_pattern.py --id <PatternId> --title "<title>" --context "<context>" --problem "<problem>" --solution "<solution>" --hardening "<evidence/tests>" --tripwire "<future warning sign>" --location "<files>" --epic "<backlog/spec/test-run>" --tags "<tags>"
```

Pflege-Rhythmus:

- Vor Debug, Build/Release-Fehlern, TestPipeline-Generatorproblemen und Final-Audit-Blockern gezielt suchen.
- Nach Debug/Fix/Audit/Dokumentationsabschluss nur dann ergaenzen, wenn ein wiederverwendbares Pattern entstanden ist.
- Im Healthcheck MONTHLY wiederkehrende Reibung aus Skill-Usage und WHAT_I_LEARNED als Optimierungssignal betrachten.
