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
| `5.6 Sol` | Architektur, Security, Privacy, Prompt-Injection, komplexe Fehleranalyse, Release-Gates, finale Audits, haerteste Forschung-/Review-/Escalation-Slices, wenn der aktuelle Codex-Run dieses Modell wirklich starten kann | hoch bis maximal |
| `5.6 Terra` | Janus-Workhorse: Feature-Design, Specs, TestSpecs, Implementierung, Refactoring, Tests, Debugging, Pipeline-Reviews | mittel bis hoch |
| `5.6 Luna` | Backlog-Pflege, Doku-Normalisierung, Snapshot-/Dashboard-Sync, mechanische Checks und einfache Status-/Kurztexte als eigener guenstiger Block | niedrig bis mittel |
| `5.5` | Legacy-Fallback-Eskalation, wenn ein bestehender laufender Kontext bewusst auf `5.5` gehalten werden soll | mittel bis hoch |
| `5.4` / `5.4 mini` | Legacy-Fallbacks fuer bestehende warme Kontexte oder aeltere Handoffs; nicht mehr Standardempfehlung fuer neue Janus-Slices | niedrig bis hoch |

## Janus Skill Map

| Situation | Skill |
| --- | --- |
| Vage Feature-Idee, Produktverhalten klaeren | `janus-feature-design` |
| Passenden Prozess, Modell, Kontext und naechsten Schritt bestimmen | `janus-skill-router` |
| Triviale lokale Aenderung mit klarer Evidenz | `janus-quickchange` |
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
- Fuer Codex-Projektstarts zuerst das kompakte Profil `documentation/codex/CODEX_PROJECT_PROFILE.md` nutzen, danach nur bindende Artefakte laden.
- Nur bindende Artefakte laden: Backlog-Item, Spec, TestSpec, Handoff, direkt betroffene Dateien.
- Lange Historie nur als Archiv behandeln, nicht als aktive Anforderung.
- Bei neuem Feature, langem Chat oder unabhaengigem Audit neuen Chat empfehlen.
- Cache-Strategie nach dem `GPT-5.6`-Update: fuer neue Janus-Arbeit moeglichst auf `5.6 Terra` bleiben und nur die Intelligenz/Reasoning-Stufe wechseln. Wenn der `5.6 Terra`-Kontext warm ist und die Aufgabe kurz, mechanisch oder direkt an dieselben Janus-Artefakte gebunden ist, bevorzugt `5.6 Terra` mit niedriger Intelligenz statt `5.6 Luna` nutzen. Zu `5.6 Luna` nur wechseln, wenn der mechanische Block trotz warmem `5.6 Terra`-Cache voraussichtlich guenstiger bleibt und danach kein teurer Rueckwechsel/Neuladen dominiert; zu `5.6 Sol` nur bei echter Risiko-, Audit-, Security-, Privacy-, Architektur- oder Release-Eskalation wechseln und nur, wenn der aktuelle Codex-Run `gpt-5.6-sol` wirklich starten kann. Wenn Codex meldet, dass `gpt-5.6-sol` mit dem ChatGPT-Konto nicht unterstuetzt wird, `5.6 Terra/high` als dokumentierten Fallback nutzen und `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT` als Grund notieren. Bereits warme `5.5`-/`5.4`-Kontexte duerfen fuer kurze Restbloecke bewusst weitergenutzt werden, wenn ein Wechsel teurer waere als der verbleibende Nutzen.

## Codex Plugins

Plugins unterstuetzen den Janus-Skill-Workflow, ersetzen ihn aber nicht. Zuerst wird immer ueber `janus-skill-router` entschieden, welcher Janus-Skill fuehrt. Danach werden Plugins gezielt als Werkzeuge fuer Artefakte, Evidenz oder externe Formate genutzt.

Standardnutzung:

- `Codex Security`: gezielte Security-/Privacy-/Attack-Path-Pruefungen, besonders vor Final Audit, Release oder bei sicherheitsrelevanten Aenderungen.
- `GitHub Connector`: PRs, Issues, Reviews, CI-Checks und Publish-Flows, wenn der Workflow ueber GitHub laeuft oder Review-/Actions-Evidenz gebraucht wird.
- `Documents`: `.docx`/Word-Artefakte nur, wenn der Nutzer ein teilbares Dokument, Review-Dokument, Bericht oder extern nutzbares Protokoll braucht.
- `Spreadsheets`: strukturierte Auswertungen, Kosten-/Skill-Usage-Analysen, Tabellen, CSV/XLSX oder Metriken, wenn Markdown nicht mehr ausreicht.
- `Presentations`: Entscheidungs-, Review- oder Stakeholder-Decks, nicht fuer normale interne Janus-Arbeit.
- `Browser`: falls in der aktuellen Codex-Umgebung verfuegbar, fuer lokale UI-Pruefung, Screenshots, Klicktests und visuelle Evidenz nach Frontend-Aenderungen.

GitHub-Connector bevorzugen fuer:

- Pull Requests erstellen, aktualisieren und reviewen
- Action-Checks, Review-Feedback und Merge-Zustand pruefen
- Issues, Labels, Assignees und Backlog-Nachverfolgung auf GitHub spiegeln
- Release-/Publish-Vorbereitung, wenn der naechste Schritt direkt ueber GitHub laeuft

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

- vermuteter Pfad: Quickchange, Backlog-Pipeline oder Feature-Pipeline
- empfohlene Modelle fuer Bewertung, Planung und Umsetzung
- grober Aufwand: S, M oder L
- Risiko: niedrig, mittel oder hoch
- Nutzen: niedrig, mittel oder hoch
- naechster Skill und ob ein Dashboard-/Backlog-Task angelegt werden soll

Triviale, risikoarme Mini-Aenderungen duerfen in `janus-quickchange` laufen, wenn sie auf eine kleine Datei-/Komponenten-Gruppe begrenzt sind, keine Produktentscheidung brauchen und vor dem Edit ein Mini-Testplan plus klare Akzeptanz formuliert werden kann. Typische Beispiele: Copy-Fix, Label-Tausch, Prozentanzeige, lokale Darstellungskorrektur. Sobald Scope, Risiko oder Testflaeche wachsen, faellt der Wunsch zurueck in `janus-backlog-intake` oder `janus-feature-design`.

Kleine, klare Verbesserungen gehen standardmaessig in `janus-backlog-intake`, danach Priorisierung und Dashboard-Handoff. Codex implementiert nicht direkt, solange kein Backlog-/Handoff-/Precheck-Artefakt gebunden ist.

Wenn der Wunsch groesser, produktentscheidend, mehrdeutig, surface-uebergreifend, persistenzrelevant oder riskant wirkt, geht Codex automatisch zuerst in `janus-feature-design`. Dort wird der Wunsch mit dem Nutzer entschieden und fixiert. Erst danach entstehen Spec, normalisierte Spec, Review, Tasks und Backlog-/Dashboard-Sichtbarkeit.

## Git/GitHub Governance (Solo Git v2)

Canonical doc: `documentation/codex/JANUS_SOLO_GIT.md`

- Normalarbeit: `master` + ein aktiver `feature/*`-Branch; nach Validierung merge nach `master`.
- `develop` ist legacy/deprecated — nicht fuer neue Arbeit.
- VM-Snapshot des Operators bleibt das primaere Rollback-Sicherheitsnetz; Git ist Historie + Remote-Backup.
- `backup/master` ist der private Sicherheits-Remote nach fertigem Feature-Merge.
- `origin` bekommt nur `master` plus explizite Release-Tags sowie den ChatGPT-Sync-Branch `codex-sync`.
- Keine Git-Worktrees als Standard; keine Worktree-Archaeologie, ausser der Operator fragt explizit danach.
- Wenn ein Schritt direkt auf GitHub laeuft, bevorzuge den GitHub-Connector fuer PRs, Reviews, Issues, CI-Checks und Publish-Flows statt sofort auf CLI-Fallbacks zu gehen.
- Nie blind `git add .` verwenden, ausser beim einmaligen Migrations-Archiv mit expliziter Freigabe.
- Vor Commit/Push/Merge/Sync immer `janus-git-governance` verwenden.
- Ein validierter Delivery-Block darf ein Commit sein; nicht automatisch in viele Micro-Commits splitten.
- Keine Secrets, lokalen DBs, Build-Artefakte, privaten Logs oder grossen Dateien committen, ausser explizit geprueft und begruendet.
- Commit/Push/Tag/Merge/codex-sync nur nach expliziter User-Freigabe ausfuehren.
- Janus-Codex-Skills muessen im Repo unter `documentation/codex/skills/` versioniert werden; die Kopien unter `C:\Users\pruve\.codex\skills` gelten als installierte Arbeitskopien.

## Versioning And Electron Auto-Update Releases

- `package.json` ist die Versionsquelle fuer Janus Releases.
- `package-lock.json` und `backend/version.py` muessen vor Build/Release dieselbe Version tragen.
- Normale Beta-/Auto-Update-Releases erhoehen nur die Beta-Nummer, z.B. `0.4.17-beta.38` -> `0.4.17-beta.39`.
- Stable-, Patch-, Minor- oder Major-Wechsel brauchen explizite User-Freigabe.
- Version bump und Doku-Sync laufen ueber `janus-documentation-update`.
- Build, Installer, Auto-Update-Manifest und GitHub Release laufen ueber `janus-build-release`.
- Production Publish laeuft nur sauber von `master`, cleanem Worktree, synchronem `backup/master`, explizitem Tag/Origin-Schritt und finaler Freigabe `Publish: YES`.
- Das Electron Auto-Update gilt erst als releasebereit, wenn `latest.yml`, `janus-update-manifest.json`, Installer, Blockmap falls vorhanden, lokale Hashes und GitHub Assets validiert sind.

## Mandatory CURRENT_STATE update

Jeder substantielle Janus-Arbeitsblock endet mit einem Update von:

- `documentation/ai/CURRENT_STATE.md`

Substantiell bedeutet: mindestens eines trifft zu.

- Dateien wurden geaendert.
- Validierung wurde ausgefuehrt.
- Ein Blocker wurde dokumentiert.
- Ein formaler Next-Skill-Handoff wurde erzeugt.

Reine Rueckfragen, Routing-only, kurze Statusantworten und andere Mini-Interaktionen zaehlen nicht als substantielle Janus-Arbeitsbloecke.

Das CURRENT_STATE-Update bleibt kompakt und enthaelt mindestens:

- current goal
- active phase
- last Codex work
- changed files
- tests / validation performed
- open risks
- next recommended step for ChatGPT
- next recommended step for Codex
- last updated timestamp

Kein substantieller Janus-Arbeitsblock gilt als abgeschlossen, bevor `documentation/ai/CURRENT_STATE.md` aktualisiert wurde.

CURRENT_STATE ist ein Rolling Snapshot fuer Synchronisierung zwischen Codex und ChatGPT. Es ersetzt nicht Backlog, Spec, TestSpec, TestRun, TestResult, Audit Package oder Dashboard-Snapshot als Single Source of Truth.

Keine Secrets, API-Keys, Credentials, privaten Tokens oder sensiblen lokalen Maschinendetails in CURRENT_STATE schreiben.

Commit und Push bleiben an `janus-git-governance` und explizite User-Freigabe gebunden.

Wenn kein Push erfolgt oder der Push fehlschlaegt, muss der Abschluss explizit sagen, dass ein Remote-Stand wie GitHub den neuesten CURRENT_STATE noch nicht enthalten muss. ChatGPT darf dann keinen aktuellen Remote-Stand annehmen.

Wenn ChatGPT den aktuellen CURRENT_STATE-Stand jederzeit zuverlaessig kennen soll, gilt zusaetzlich diese Sync-Regel:

- die verbindliche ChatGPT-Remote-Wahrheit fuer `documentation/ai/CURRENT_STATE.md` ist `origin/codex-sync`
- nach jedem substantiellen Janus-Arbeitsblock soll Codex den Sync zu `origin/codex-sync` empfehlen; bevorzugt `documentation/codex/scripts/sync_codex_current_state.ps1`
- ohne diesen Sync darf ChatGPT keinen aktuellen Remote-Stand annehmen, selbst wenn `backup/master` oder andere Branches neuer sind
- diese Regel betrifft nur den ChatGPT-Sync-Punkt fuer `CURRENT_STATE.md`; sie ersetzt nicht die normale Git-Governance fuer Backup-, Release- oder Produkt-Branches

## Completion Rules

Ein Schritt ist erst fertig, wenn es echte Evidenz gibt oder ein Blocker dokumentiert ist.

Jeder Abschluss nennt:

- canonical state: `PASS`, `BLOCKED`, `NEEDS_INFO`, `FAILED`, `HANDOFF` oder `ESCALATED`
- ausgefuehrte Checks
- geaenderte Dateien
- naechster Skill oder Gate
- bei jedem `ok`-/`weiter`-/Freigabe-Gate: empfohlenes Modell und empfohlene Intelligenz/Reasoning-Stufe

Substantielle Skill-Laeufe werden fuer spaetere Optimierung in `documentation/codex/SKILL_USAGE_LOG.md` dokumentiert. Dafuer bevorzugt das Script `documentation/codex/scripts/record_skill_usage.py` nutzen. Reine Rueckfragen, kurze Statusantworten und reine Git-Ausfuehrung ohne neue Prozessentscheidung muessen nicht geloggt werden.

`WHAT_I_LEARNED.md` ist das Langzeitgedaechtnis fuer validierte, wiederverwendbare technische Muster. Nicht vollstaendig laden. Vor Debug-, Build-/Release-, TestPipeline-Generator- und Final-Audit-Blockern gezielt suchen mit `documentation/codex/scripts/search_what_i_learned.py`. Neue Eintraege nur append-only und nur bei validierter Root Cause, Loesung, Haertung und Tripwire; bevorzugt `documentation/codex/scripts/append_learning_pattern.py` nutzen.

## Lean Dev Mode

Fuer interne Dev- und OR-Infrastrukturarbeit gilt zusaetzlich ein schlanker Arbeitsmodus, wenn alle folgenden Bedingungen erfuellt sind:

- die Arbeit aendert keine Janus-Produktlogik
- die Arbeit bleibt ein kleiner oder mittlerer bounded Dev-Slice
- keine Security-/Privacy-Eskalation ist betroffen
- kein Release-, Tag-, Publish- oder sonstiges Git-Governance-Risiko ist betroffen
- keine neue produktive Freigabe wird in diesem Slice entschieden
- der Scope ist klar und driftet nicht

Lean Dev Mode bedeutet:

- weniger Prozess-Overhead als die volle Janus-Produktpipeline
- Validation bleibt Pflicht
- `documentation/ai/CURRENT_STATE.md` bleibt fuer substantielle Bloecke Pflicht
- ein sauberer Git-Checkpoint bleibt bei sinnvollen Lieferbloecken Pflicht
- Dev-Arbeit soll bevorzugt auf die Source-of-Truth unter `development/` und die direkt betroffenen Repo-Governance-Dateien begrenzt bleiben

Lean Dev Mode endet sofort und der strenge Modus gilt wieder, wenn mindestens eines davon eintritt:

- Janus-Produktlogik ist betroffen
- Security/Privacy wird beruehrt
- Release/Git-Governance wird beruehrt
- der Scope ist unklar oder driftet
- eine neue produktive Freigabe oder Autoritaetsgrenze wird entschieden

Diese Regel lockert nicht die Janus-Produktpipeline. Janus-Produktarbeit bleibt immer im strengen Modus.
