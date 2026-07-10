# Codex Model Migration - 2026-06-02

## Update 2026-07-10 - GPT-5.6 family

Canonical State: `PASS`

The local Codex model cache on `2026-07-10` now exposes these visible coding
models:

- `gpt-5.6-sol` / `GPT-5.6-Sol` - "Latest frontier agentic coding model."
- `gpt-5.6-terra` / `GPT-5.6-Terra` - "Balanced agentic coding model for
  everyday work."
- `gpt-5.6-luna` / `GPT-5.6-Luna` - "Fast and affordable agentic coding
  model."
- older still-available fallbacks: `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`
- `gpt-5.2` is no longer present in the local visible model cache

Observed local reasoning support from `models_cache.json`:

- `gpt-5.6-sol`: `low`, `medium`, `high`, `xhigh`, `max`, `ultra`
- `gpt-5.6-terra`: `low`, `medium`, `high`, `xhigh`, `max`, `ultra`
- `gpt-5.6-luna`: `low`, `medium`, `high`, `xhigh`, `max`

Updated Janus model matrix:

| Zweck | Modell | Reasoning |
| --- | --- | --- |
| Janus-Workhorse: Umsetzung, Debugging, Tests, Specs, Reviews, Task-Pipeline | `5.6 Terra` | `medium` bis `high` |
| Mechanische Arbeit: Backlog-Pflege, Doku-Normalisierung, Snapshot-Sync, Health DAILY, einfache Status-/Kurztexte | `5.6 Luna` | `low` bis `medium` |
| Eskalation: Security, Privacy, Architektur, Final Audit, Release-/Publish-Gates | `5.6 Sol` wenn vom aktuellen Codex-Run unterstuetzt, sonst `5.6 Terra` | `high` bis `max`; Fallback `high` |

Fallback-Regel:

- `5.5` bleibt ein valider Eskalations-Fallback, wenn ein laufender Kontext
  bewusst dort gehalten wird.
- Wenn Codex beim echten Start meldet, dass `gpt-5.6-sol` mit dem aktiven
  ChatGPT-Konto nicht unterstuetzt wird, ist `5.6 Terra/high` der bevorzugte
  Audit-/Eskalationsfallback. Der Grund wird als
  `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT` dokumentiert.
- `5.4` und `5.4 mini` bleiben Legacy-Fallbacks fuer bereits warme aeltere
  Kontexte und historische Handoffs, sind aber nicht mehr die
  Standardempfehlung fuer neue Janus-Slices.

Updated cache strategy:

- Fuer neue Janus-Arbeit wird `5.6 Terra` als Standardmodell gehalten.
- Innerhalb eines laufenden Workflows soll Codex bevorzugt nur die
  Reasoning-Stufe wechseln, statt das Modell zu wechseln.
- `5.6 Luna` lohnt nur bei klar mechanischen, risikoarmen Bloecken, wenn der
  Wechsel trotz eventuellen Cacheverlusts guenstiger bleibt als `5.6 Terra`
  mit niedriger Intelligenz.
- `5.6 Sol` bleibt fuer echte Risiko-/Qualitaetseskalation reserviert, sofern
  der aktive Codex-Account-Kontext es ausfuehren darf.
- Bereits warme `5.5`-/`5.4`-Kontexte duerfen fuer kleine Restbloecke bewusst
  zu Ende gefahren werden, wenn ein Wechsel keinen echten Mehrwert bringt.

Update evidence:

- local file `C:\Users\pruve\.codex\models_cache.json` fetched at
  `2026-07-10T13:04:31.517489700Z`
- local file `C:\Users\pruve\.codex\.codex-global-state.json` contains
  `seen-model-upgrade-list = ["gpt-5.6-sol"]`
- local visible model set count = `7`: `gpt-5.6-sol`, `gpt-5.6-terra`,
  `gpt-5.6-luna`, `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `codex-auto-review`
- Runtime observation on 2026-07-10: the Codex app picker may show Sol while a
  concrete Codex execution still returns `The 'gpt-5.6-sol' model is not
  supported when using Codex with a ChatGPT account.` Treat picker visibility as
  weaker evidence than a successful backend start.

This update supersedes the role assignment below while preserving the historical
record of the 2026-06-02 migration away from `5.3 codex`.

## Historical Context - 2026-06-02

Nach dem Windows-Codex-Update sind in der sichtbaren Modellauswahl nur noch
`5.5`, `5.4` und `5.4 mini` verfuegbar. Das bisherige Codex-Arbeitspferd
`5.3 codex` ist fuer die Janus-Skillpipeline nicht mehr verfuegbar.

## Historical Decision

Canonical State at 2026-06-02: `PASS`

Historical Janus model matrix at 2026-06-02:

| Zweck | Modell | Reasoning |
| --- | --- | --- |
| Janus-Workhorse: Umsetzung, Debugging, Tests, Specs, Reviews, Task-Pipeline | `5.4` | `medium` bis `high` |
| Mechanische Arbeit: Backlog-Pflege, Doku-Normalisierung, Snapshot-Sync, Health DAILY | `5.4 mini` | `low` bis `medium` |
| Eskalation: Security, Privacy, Architektur, Final Audit, Release-/Publish-Gates | `5.5` | `high` bis `xhigh` |

## Historical Cache Strategy

At that time Janus kept `5.4` as the standard model. Within a running workflow
Codex was supposed to prefer changing only the reasoning level instead of the
model itself.

Begruendung:

- gleicher Modellpfad ist cache-freundlicher als haeufige Modellwechsel
- Reasoning-Wechsel ist ein kleinerer Steuerungswechsel als Modellwechsel
- `5.4` deckt Planung, Umsetzung, Debugging und Reviews breit genug ab
- `5.4 mini` lohnt nur bei klar mechanischen, risikoarmen Bloecken
- `5.5` bleibt fuer echte Risiko-/Qualitaetseskalation reserviert

Hinweis: Dieser Abschnitt ist nur die historische Cache-Begruendung vom
2026-06-02. Die aktive Strategie steht im Update-Block vom 2026-07-10 sowie in
`AGENTS.md`, `CODEX_PROJECT_PROFILE.md` und `CODEX_WORKFLOW_PLAYBOOK.md`.

## Historical Skill Adjustments

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

## Historical Gate Rule

Jedes User-Gate, bei dem der Nutzer mit `ok`, `weiter`, `los` oder einer
Freigabe antworten soll, muss kuenftig enthalten:

- empfohlenes Modell
- empfohlene Reasoning-/Intelligenz-Stufe
- ob ein Modellwechsel empfohlen wird
- ob ein neuer Chat empfohlen wird

## Historical Evidence

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

## Historical Next Gate

Commit der Modellmigration und Skill-Cache-Optimierung, danach Push nach
`backup/develop`.
