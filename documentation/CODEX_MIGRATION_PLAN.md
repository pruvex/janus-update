# Janus Codex Migration Plan

Stand: 2026-05-25

## Ziel

Die bestehende Janus Diamond Pipeline wird von Windsurf/Cascade auf Codex-native Arbeit migriert, ohne bestehendes Wissen, Reports, Specs, TestSpecs oder Backlog-Historie zu verlieren.

## Prinzipien

- Nicht loeschen.
- Nicht blind verschieben.
- Erst klassifizieren, dann migrieren.
- Backlog bleibt Quelle, Dashboard bleibt Ansicht.
- Skills bleiben klein und triggerbar.
- Modell- und Kontextwahl wird proaktiv empfohlen.

## Aktive Quellen

| Bereich | Aktiver Pfad |
| --- | --- |
| Projektregeln fuer Codex | `AGENTS.md` |
| Backlog | `documentation/backlog/BACKLOG.md` |
| Pipeline-Vertrag | `documentation/pipeline/PIPELINE_CONTRACT.md` |
| Feature-Specs | `documentation/SPEC/` |
| TestSpecs | `documentation/TEST_SPEC/` |
| TestRun-Artefakte | `documentation/test-runs/` |
| TestResult-Artefakte | `documentation/test-results/` |
| Dashboard-App | `janus-dashboard/` |
| Dashboard-Snapshot | `janus-dashboard/data/backlog.snapshot.json` |
| Versionierte Codex-Skills | `documentation/codex/skills/` |
| Installierte Codex-Skills | `C:\Users\pruve\.codex\skills\janus-*` |

## Legacy-Quellen

| Bereich | Legacy-Pfad | Behandlung |
| --- | --- | --- |
| Windsurf Workflows | `.windsurf/workflows/` | Referenz fuer Codex-Skill-Migration |
| Diamond Systemnotizen | `.diamond/` | Historische Prozesslogik, nicht automatisch aendern |
| alte Reports | `documentation/archive/`, `documentation/_archive/`, `documentation/reports/` | Archiv, nur gezielt lesen |

## Codex Skill Migration

| Alt | Neu | Status |
| --- | --- | --- |
| Brainstorming Mode | `janus-feature-design` | erstellt |
| Skill-Auswahl / Prozesssteuerung | `janus-skill-router` | erstellt |
| Backlog Skill 1 | `janus-backlog-intake` | erstellt |
| Backlog Skill 2 | `janus-backlog-prioritization` | erstellt |
| Backlog Skill 3 | `janus-backlog-handoff` | erstellt |
| Spec Generator | `janus-spec-generator` | erstellt |
| Spec Normalizer | `janus-spec-normalizer` | erstellt |
| Spec Skill 1 | `janus-spec-review` | erstellt |
| Skill 1 | `janus-spec-to-task` | erstellt |
| Skill 2 | `janus-task-breakdown` | erstellt |
| Skill 3 | `janus-preimplementation-check` | erstellt |
| Skill 4 | `janus-executioner` | erstellt |
| Skill 5 | `janus-debug` | erstellt |
| Skill 6 | `janus-final-audit` | erstellt |
| Skill 7 | `janus-documentation-update` | erstellt |
| Skill 8 | `janus-build-release` | erstellt |
| System Health | `janus-health-check` | erstellt |
| Test Skill 1-5 | `janus-test-pipeline` | erstellt |
| Git/GitHub Save/Commit/Release Guard | `janus-git-governance` | erstellt |

## Skill-Versionierung

Die installierten Skills unter `C:\Users\pruve\.codex\skills\janus-*` sind die aktive Codex-Arbeitskopie. Damit die Skill-Pipeline nicht verloren geht, wird jede Janus-spezifische Skill-Quelle zusaetzlich im Repo unter `documentation/codex/skills/` versioniert.

Regel:

- Aenderungen an Janus-Skills zuerst bewusst in der aktiven Arbeitskopie testen.
- Danach die gepruefte `SKILL.md` und zugehoerige Scripts nach `documentation/codex/skills/<skill>/` spiegeln.
- Commits enthalten die Repo-Kopie; die Home-Kopie allein gilt nicht als gesichert.

## Betriebsmodus

Die Migration der Janus-Diamond-Skills ist abgeschlossen. Der laufende Codex-Arbeitsmodus steht in:

- `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`

Naechste Arbeit ist keine weitere Migration, sondern Anwendung und Schaerfung im echten Janus-Alltag:

1. Neue Aufgaben zuerst ueber `janus-skill-router` routen.
2. Backlog- und Dashboard-Flow mit realen READY Items testen.
3. Einen kleinen Feature-Pfad von `janus-feature-design` bis `janus-documentation-update` komplett durchlaufen.
4. `janus-health-check` regelmaessig als DAILY/WEEKLY Kontrollinstrument nutzen.
