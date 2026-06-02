# Codex Model Migration - 2026-06-02

## Anlass

Nach dem Windows-Codex-Update sind in der sichtbaren Modellauswahl nur noch
`5.5`, `5.4` und `5.4 mini` verfuegbar. Das bisherige Codex-Arbeitspferd
`5.3 codex` ist fuer die Janus-Skillpipeline nicht mehr verfuegbar.

## Entscheidung

Canonical State: `PASS`

Neue Janus-Modellmatrix:

| Zweck | Modell | Reasoning |
| --- | --- | --- |
| Janus-Workhorse: Umsetzung, Debugging, Tests, Specs, Reviews, Task-Pipeline | `5.4` | `medium` bis `high` |
| Mechanische Arbeit: Backlog-Pflege, Doku-Normalisierung, Snapshot-Sync, Health DAILY | `5.4 mini` | `low` bis `medium` |
| Eskalation: Security, Privacy, Architektur, Final Audit, Release-/Publish-Gates | `5.5` | `high` bis `xhigh` |

## Cache-Strategie

Fuer Janus wird `5.4` als Standardmodell gehalten. Innerhalb eines laufenden
Workflows soll Codex bevorzugt nur die Reasoning-Stufe wechseln, statt das
Modell zu wechseln.

Begruendung:

- gleicher Modellpfad ist cache-freundlicher als haeufige Modellwechsel
- Reasoning-Wechsel ist ein kleinerer Steuerungswechsel als Modellwechsel
- `5.4` deckt Planung, Umsetzung, Debugging und Reviews breit genug ab
- `5.4 mini` lohnt nur bei klar mechanischen, risikoarmen Bloecken
- `5.5` bleibt fuer echte Risiko-/Qualitaetseskalation reserviert

Hinweis: Exakte Prompt-Cache-Treffer werden nicht garantiert. Sie haengen auch
vom stabilen Prompt-/Kontextprefix und Codex-internen Laufbedingungen ab. Fuer
Kosten und Cache-Lokalitaet ist das Halten desselben Modells trotzdem die
konservative Strategie.

## Skill-Anpassungen

Aktualisiert:

- `AGENTS.md`
- `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`
- `documentation/codex/CODEX_PROJECT_PROFILE.md`
- `documentation/codex/skills/janus-*`
- installierte Arbeitskopien unter `C:\Users\pruve\.codex\skills\janus-*`
- persoenliche Codex-Skills unter `C:\Users\pruve\.codex\skills\codex-*`

Harte `5.3 codex`-Referenzen wurden in der aktiven Janus-Skillpipeline durch
`5.4` ersetzt. `5.4` wird nicht mehr als seltene Eskalation behandelt, sondern
als Janus-Workhorse.

Harte `5.3-codex`- und `5.5-codex`-Handoffs in persoenlichen Codex-Skills
wurden auf `5.4` bzw. `5.5` migriert.

## Gate-Regel

Jedes User-Gate, bei dem der Nutzer mit `ok`, `weiter`, `los` oder einer
Freigabe antworten soll, muss kuenftig enthalten:

- empfohlenes Modell
- empfohlene Reasoning-/Intelligenz-Stufe
- ob ein Modellwechsel empfohlen wird
- ob ein neuer Chat empfohlen wird

## Evidence

- Frisches Codex Manual nennt `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini` und
  `gpt-5.3-codex-spark`, aber kein verfuegbares `4.3 codex`.
- `rg` auf versionierte Janus-Regeln: keine alten `5.3 codex`-Referenzen
  ausser historischer Skill-Usage-Log-Eintraege.
- Installierte Janus-Skills sind mit den versionierten Repo-Skills synchron.
- Vorher groesste Wortzahl-Reduktionen durch Sync:
  - `janus-skill-router`: ca. 1353 Woerter weniger
  - `janus-git-governance`: ca. 1073 Woerter weniger
  - `janus-build-release`: ca. 841 Woerter weniger
  - `janus-backlog-intake`: ca. 584 Woerter weniger

## Naechster Gate

Commit der Modellmigration und Skill-Cache-Optimierung, danach Push nach
`backup/develop`.
