# Operator-Facing OR Lane Inventory

Stand: `2026-06-29`

Zweck: kompakte Momentaufnahme der bereits auf Current Shape nachgezogenen operator-facing Janus-Skill-Lanes mit sichtbarem `1 = Codex` / `2 = OR`-Gate.

## Statusklassen

- `OR_PROPOSAL_FIRST`: `2 = OR` nutzt einen echten bounded OR-Pfad, aber Codex behaelt Review/Apply/Finalentscheidung.
- `OR_ASSIST_ONLY`: `2 = OR` liefert bounded Review/Hypothesen/Interpretation; Codex behaelt alle Folgeschritte.
- `STRUCTURED_LOCAL_INTERIM`: `2 = OR` ist sichtbar, aber technisch noch kein echter externer OR-Workerpfad, sondern ein strukturierter lokaler Executor-Zwischenstand.

## Inventory

| Skill | Visible gate | Current `2 = OR` path | Preferred model/path | Latest refreshed evidence | Cost signal | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `janus-executioner` | YES | bounded direct OR patch candidate, then Codex review | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-EXEC-EVERYDAY-PROMPT-2026-06-28`, `WF-EXEC-EVERYDAY-LOCAL-2026-06-28`, `WF-EXEC-EVERYDAY-OR-2026-06-28` | actual `0.00063384` | `OR_PROPOSAL_FIRST` |
| `janus-quickchange` | YES | bounded direct OR patch proposal, with deeper accepted-source write-apply derivative available | `qwen/qwen3-coder-30b-a3b-instruct` for patch review; accepted-source bridge for write-apply | `WF-QCW-EVERYDAY-PROMPT-2026-06-29-001`, `WF-QCW-EVERYDAY-DELEGATED-2026-06-29-001` | estimated gate proof `0.00095`; accepted-source delegated proof PASS | `OR_PROPOSAL_FIRST` |
| `janus-spec-generator` | YES | bounded file-first structured spec draft proposal, then Codex local final write | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-SPEC-GEN-CURRENT-001`, `WF-SPEC-GEN-CURRENT-002` | actual fixture-backed proof `0.00071` | `OR_PROPOSAL_FIRST` |
| `janus-feature-design` | YES | bounded file-first decision-summary draft or blocking question, then Codex local final decision | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-FEATURE-DESIGN-PROMPT-2026-06-29-001`, `WF-FEATURE-DESIGN-DELEGATED-2026-06-29-001`, accepted live base `WF-FEATURE-DESIGN-CURRENT-002` | actual accepted live proof `0.00031` | `OR_PROPOSAL_FIRST` |
| `janus-spec-normalizer` | YES | bounded file-first normalized spec draft, then Codex local final review and write | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-SPEC-NORMALIZER-PROMPT-2026-06-29-001`, `WF-SPEC-NORMALIZER-DELEGATED-2026-06-29-001`, `WF-SPEC-NORMALIZER-LIVE-REPEAT-2026-06-26` | actual live proof `0.00018921` | `OR_PROPOSAL_FIRST` |
| `janus-spec-to-task` | YES | bounded file-first task-compilation draft, then Codex local final task-artifact write | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-SPEC-TO-TASK-PROMPT-PROOF-2026-06-28`, `WF-SPEC-TO-TASK-LOCAL-PROOF-2026-06-28`, `WF-SPEC-TO-TASK-FIXTURE-CHECK-2026-06-26` | actual fixture-backed proof `0.00068685` | `OR_PROPOSAL_FIRST` |
| `janus-task-breakdown` | YES | bounded file-first single-target handoff draft, then Codex local final handoff write | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-TASK-BREAKDOWN-PROMPT-PROOF-2026-06-28`, `WF-TASK-BREAKDOWN-LOCAL-PROOF-2026-06-28`, `WF-TASK-BREAKDOWN-FIXTURE-CHECK-2026-06-26` | actual fixture-backed proof `0.00017092` | `OR_PROPOSAL_FIRST` |
| `janus-preimplementation-check` | YES | bounded file-first precheck review recommendation, then Codex local final precheck decision | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-PRECHECK-PROMPT-PROOF-2026-06-28`, `WF-PRECHECK-LOCAL-PROOF-2026-06-28`, `WF-PRECHECK-FIXTURE-CHECK-2026-06-25` | actual fixture-backed proof `0.00009588` | `OR_ASSIST_ONLY` |
| `janus-spec-review` | YES | bounded file-first spec review recommendation plus metadata suggestion, then Codex local final metadata write | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-SPEC-REVIEW-PROMPT-PROOF-2026-06-28`, `WF-SPEC-REVIEW-LOCAL-PROOF-2026-06-28`, `WF-SPEC-REVIEW-FIXTURE-CHECK-2026-06-25` | actual fixture-backed proof `0.00015036` | `OR_ASSIST_ONLY` |
| `janus-debug` | YES | bounded hypothesis review only | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-DEBUG-EVERYDAY-PROMPT-2026-06-29-001`, `WF-DEBUG-EVERYDAY-DELEGATED-2026-06-29-001` | actual `0.00045678` | `OR_ASSIST_ONLY` |
| `janus-test-pipeline` | YES | bounded test-result triage review only | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-TRIAGE-EVERYDAY-PROMPT-2026-06-29-001`, `WF-TRIAGE-EVERYDAY-DELEGATED-2026-06-29-001` | actual `0.00028765` | `OR_ASSIST_ONLY` |
| `janus-test-pipeline` | YES | structured local executor for deterministic generator path | structured local executor / `gpt-5.4` | `SIDECAR-TEST-ARTIFACT-PROMPT-2026-06-28-905`, `SIDECAR-TEST-ARTIFACT-STRUCTURED-LOCAL-2026-06-28-905` | no external OR cost in this refreshed slice | `STRUCTURED_LOCAL_INTERIM` |
| `janus-health-check` | YES | bounded read-only review | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-HEALTH-CHECK-EVERYDAY-PROMPT-2026-06-28`, `WF-HEALTH-CHECK-EVERYDAY-OR-2026-06-28` | fixture-only, actual `0.0` | `OR_ASSIST_ONLY` |
| `janus-skill-router` | YES | bounded routing recommendation review | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-SKILL-ROUTER-EVERYDAY-PROMPT-2026-06-28`, `WF-SKILL-ROUTER-EVERYDAY-OR-2026-06-28` | fixture-only, actual `0.0` | `OR_ASSIST_ONLY` |
| `janus-backlog-handoff` | YES | bounded handoff review | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-BACKLOG-HANDOFF-EVERYDAY-PROMPT-2026-06-28`, `WF-BACKLOG-HANDOFF-EVERYDAY-OR-2026-06-28` | actual `0.00017933` | `OR_ASSIST_ONLY` |
| `janus-backlog-prioritization` | YES | bounded prioritization review | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-BACKLOG-PRIO-EVERYDAY-PROMPT-2026-06-27`, `WF-BACKLOG-PRIO-EVERYDAY-OR-2026-06-27` | fixture-backed current-shape proof | `OR_ASSIST_ONLY` |
| `janus-backlog-intake` | YES | bounded intake drafting/review | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-BACKLOG-EVERYDAY-PROMPT-2026-06-27`, `WF-BACKLOG-EVERYDAY-OR-2026-06-27` | fixture-backed current-shape proof | `OR_ASSIST_ONLY` |

## Practical reading

- Heute am staerksten als echter OR-Workhorse vorbereitet ist `janus-executioner`, aber weiterhin nur proposal-first oder accepted-source-backed und nie broad autonomous write authority.
- `janus-quickchange` ist ebenfalls stark: sichtbares bounded Patch-Review plus tieferer akzeptierter Write-Apply-Ableger fuer winzige Datei-Aenderungen.
- `janus-spec-generator`, `janus-feature-design`, `janus-spec-normalizer`, `janus-spec-to-task` und `janus-task-breakdown` bilden inzwischen die starke Draft-/Schreibvorstufen-Gruppe: OR kann bounded Entwuerfe liefern, Codex behaelt finale Review-, Schreib- und Freigabehoheit.
- `janus-preimplementation-check` ist jetzt ebenfalls sauber sichtbar und current-shape bestaetigt, bleibt aber bewusst assist-only: OR liefert bounded eine file-first Precheck-Review-Empfehlung, waehrend Codex die finale Governance-/Precheck-Entscheidung lokal trifft.
- `janus-spec-review` ist jetzt ebenfalls sauber sichtbar und current-shape bestaetigt, bleibt aber bewusst assist-only: OR liefert bounded Review-Output plus Metadata-Vorschlag, Codex schreibt die finale `SPEC REVIEW METADATA` weiterhin lokal.
- Hinter `janus-executioner` existiert zusaetzlich bereits der tiefere derivative Pfad `execution_write_apply_candidate`: accepted proposal package rein, bounded lokales Apply unter Guardrails, danach Codex accept/reject.
- `janus-debug` und `janus-test-pipeline` Triage sind als bounded externe Denkarbeiter sauber vorbereitet, nicht als fixer oder lokaler Ausfuehrer.
- Der `janus-test-pipeline` Generator-Pfad ist operator-facing sauber, aber der `2`-Pfad dort bleibt Zwischenstand und kein vollwertiger OpenRouter-Dateischreiber.
- Die Intake-/Review-Lanes sind fuer alltaegliche Auswahl schon sichtbar nutzbar, aber bewusst assist-only.

## Next rollout decision

- Der operator-facing Kern fuer den Alltag ist jetzt breit genug, um echte Nutzung statt weiterer Beweisrunden zu rechtfertigen.
- Neue Lane-Arbeit sollte nur noch dort passieren, wo entweder viel Codex-Kontingent verbrannt wird oder ein bestehender Skill noch keinen sichtbaren `1 = Codex` / `2 = OR`-Pfad hat.
