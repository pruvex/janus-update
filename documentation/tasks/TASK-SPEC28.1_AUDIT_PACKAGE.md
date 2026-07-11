# AUDIT_PACKAGE

Generated: 2026-07-05 12:52:18 UTC

## Goal

Audit TASK-SPEC28.1 as the first productive bounded OR LIVE_TEST_EXECUTION visibility gate slice

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: APPROVED_WITH_NOTES - documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
- Task File: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
- Backlog Item: BACKLOG-118
- Pre-Implementation Check: documentation/tasks/TASK-SPEC28.1_preimplementation_check.md
- Manual Janus Evidence: N/A WITH REASON - infrastructure gate visibility slice only; no Janus product runtime, auth worker, delegated evidence write, or live retest execution behavior changed yet.
- Pipeline Completion Status: implementation complete yes; final audit pending

## Backlog Item

```text
### BACKLOG-118 - Bounded OR Lane fuer LIVE_TEST_EXECUTION in der Testpipeline

- **Typ:** IMPROVEMENT
- **Status:** IN PROGRESS
- **Quelle:** User Intake
- **Erstellt:** 2026-07-01
- **Aktualisiert:** 2026-07-01
- **Follow-up zu:** BACKLOG-117 - Strong OR Agent Lane fuer echte ausgelagerte Testarbeit
- **Kurzbeschreibung:** Die Janus-Testpipeline soll fuer geeignete Live-Retests eine sichtbare bounded OR-Lane bekommen, damit Codex den echten Lauf nicht immer selbst ausfuehren muss. Die Lane soll lokale API-/Health-/Prompt-Retests inklusive Evidenzsammlung delegierbar machen, waehrend Codex finale PASS/FAIL-Hoheit behaelt.
- **Erwartetes Verhalten:** Bei eligible `LIVE_TEST_EXECUTION`-Slices zeigt `janus-test-pipeline` ein sichtbares `1 = Codex / 2 = OR` Gate. Wenn der Nutzer `2 = OR` waehlt, darf ein bounded Worker den allowlisted lokalen Retest-Ablauf ausfuehren, Evidenz erzeugen und Codex die Ergebnisse zur finalen Bewertung zurueckgeben.
- **Tatsaechliches Verhalten:** Der aktuelle `LIVE_TEST_EXECUTION`-Pfad ist Codex-owned. Obwohl es bereits bounded OR-Lanes fuer Generator-Review, Triage und den Strong Test Worker gibt, wird der eigentliche lokale Live-Retest derzeit nicht als freigegebene OR-Lane angeboten.
- **Reproduktion / Kontext:** Im `BACKLOG-116`-Retest am 2026-07-01 wurde nach erfolgreichem Debug-Fix erneut `OK START LIVE TEST` ausgefuehrt. Der Retest lief gruen, musste aber komplett von Codex ueber den lokalen Dev-API-Pfad inklusive internem Header, Chat-Erzeugung, Prompt-Ausfuehrung und Evidenzablage gefahren werden. Nutzerfrage danach: warum dieser Test nicht durch ein OR-Modell gelaufen ist; Folgeentscheidung: eine eigene bounded OR-Lane fuer diesen Modus aufbauen.
- **Betroffener Bereich:** Dev-Infrastruktur / OR-Model-Routing / janus-test-pipeline / lokale Live-Retests
- **Nachweise:** `documentation/test-runs/BACKLOG-116_live_retest_after_debug_2026-07-01.md`; `documentation/test-results/BACKLOG-116-live-retest-after-debug-2026-07-01/BACKLOG-116_live_retest_after_debug_api_evidence.json`; User-Entscheidung vom 2026-07-01.
- **Akzeptanzkriterien:**
  - [ ] `janus-test-pipeline` beschreibt eine sichtbare bounded OR-Lane fuer eligible `LIVE_TEST_EXECUTION`-Retests mit `1 = Codex / 2 = OR`.
  - [ ] Die Lane definiert einen klaren allowlisted Worker-Vertrag fuer lokale Health-/Chat-/Prompt-/Evidenz-Schritte statt breiter Shell-Freiheit.
  - [ ] Lokale Auth-/Header-Anforderungen fuer den Dev-API-Pfad sind bounded im Worker-Paket oder gleichwertig abgesichert, ohne Secrets in versionierte Artefakte zu schreiben.
  - [ ] OR darf den Lauf ausfuehren und Evidenz buendeln, aber keine finale PASS-/Release-/Git-/Routing-Autoritaet beanspruchen.
  - [ ] Regressionstests decken Eligibility, Gate-Ausgabe, Paketvertrag und Review-Handoff dieser Lane ab.
- **Fehlende Informationen:**
  - Keine
- **Wichtigkeit:** HIGH
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** M
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW
- **Entry Point:** EXECUTION_READY
- **Routing reason:** Lean-Dev OR-Infrastruktur mit bestandenem Precheck fuer `TASK-SPEC28.1`; der erste bounded Umsetzungsslice ist jetzt fuer `janus-executioner` freigegeben, bleibt aber strikt auf den sichtbaren Eligibility-/Gate-Einstieg begrenzt.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-07-01
- **Handoff:** documentation/tasks/TASK-SPEC28.1_task_breakdown.md
- **Recommended next skill:** SKILL 4
- **Handoff created:** 2026-07-01
- **Precheck artifact:** documentation/tasks/TASK-SPEC28.1_preimplementation_check.md
- **Target Task:** TASK-SPEC28.1
- **Notizen:** Lean-Dev-Infrastrukturarbeit, aber kein Quickchange: die Lane beruehrt Governance, lokalen Auth-Pfad, Worker-Grenzen, Evidenzschema und Testpipeline-UX. Erst nach Priorisierung/Handoff implementieren.
```

## Task Acceptance Scope

```text
TASK-SPEC28
- Source Spec: `documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md`
- Backlog Item: `BACKLOG-118`
- Feature: Bounded OR Lane fuer LIVE_TEST_EXECUTION
- Generated At: 2026-07-01

## Generated Tasks

### TASK-SPEC28.1 Add bounded eligibility and visible operator gate for local LIVE_TEST_EXECUTION retests
- Ziel:
  - Erweitere den bestehenden `janus-test-pipeline`-Einstieg so, dass nur klar geeignete lokale `LIVE_TEST_EXECUTION`-Slices eine sichtbare Wahl `1 = Codex` / `2 = OR` erhalten.
- Scope:
  - Nur Eligibility-, Sichtbarkeits- und Gate-Integration fuer lokale Live-Retests im bestehenden Testpipeline-Einstieg. Keine OR-Ausfuehrung, keine Auth-Mechanik und keine breite Aktivierung fuer andere Testpfade.
- Files:
  - `documentation/codex/skills/janus-test-pipeline/SKILL.md`
  - `documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py`
  - `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
  - `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
  - `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- Steps:
  1. Definiere eine fail-closed Eligibility-Regel fuer lokale, bounded `LIVE_TEST_EXECUTION`-Retests.
  2. Binde die sichtbare Codex-vs-OR-Wahl nur an diese eligible Retest-Slices.
  3. Stelle sicher, dass ungeeignete, zu breite oder nicht lokal gebundene Live-Retests weiterhin Codex-only bleiben.
  4. Halte Skill-Wording, Runner-Einstieg und Gate-Ausgabe konsistent.
- Acceptance Criteria:
  - Ein eligible lokaler `LIVE_TEST_EXECUTION`-Retest zeigt die Wahl `1 = Codex` / `2 = OR`.
  - Ein nicht eligible oder zu breiter Live-Retest zeigt keine normale OR-Wahl.
  - Die Sichtbarkeit impliziert weder globale Live-Test-Freigabe noch broad delegated authority.
  - Skill-Text und technischer Gate-Einstieg beschreiben denselben bounded Lane-Fall.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q`
  - `python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q -k "live or gate or eligibility"`
  - `python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- Model: 5.4
- Reason:
  - Die Sichtbarkeit muss vor jeder Ausfuehrung klar und fail-closed sein; ohne diese Slice wuerde die Lane schon am Einstieg unsauber oder zu breit werden.

### TASK-SPEC28.2 Define the bounded local live-retest worker contract, auth handling, and evidence outputs
- Ziel:
  - Schaffe einen bounded Worker-Vertrag fuer lokale Live-Retests inklusive erlaubter Schritte, lokaler Auth-Behandlung und review-faehiger Evidenzartefakte.
- Scope:
  - Nur der bounded Vertragsrahmen fuer `api/health`, Chat-Erzeugung, gebundene Prompt-Laeufe und Evidenzsammlung im lokalen Dev-Pfad. Keine finale PASS/FAIL-Autoritaet und keine generische Shell-Freiheit.
- Files:
  - `documentation/codex/skills/janus-test-pipeline/SKILL.md`
  - `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
  - `documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`
  - `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
  - `documentation/codex/model-routing/strong-or-fixtures/`
  - `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
- Steps:
  1. Definiere einen allowlisted Worker-Vertrag fuer lokale Health-/Chat-/Prompt-/Evidenz-Schritte.
  2. Binde den lokalen Dev-API-Auth-/Header-Pfad so ein, dass die Lane technisch funktioniert, ohne versionierte Secrets in Artefakte zu schreiben.
  3. Stelle sicher, dass der Worker nur review-faehige Evidenz und keinen delegierten Abschlussanspruch zurueckgibt.
  4. Halte Dispatcher-, Worker- und Fixture-Vertrag auf denselben bounded Lane-Fall ausgerichtet.
- Acceptance Criteria:
  - Der Worker-Vertrag erlaubt nur die fuer den lokalen Live-Retest noetigen bounded Schritte.
  - Lokale Auth-/Header-Unterstuetzung bleibt bounded und leakt keine versionierten Secrets in Repo-Artefakte.
  - Die Rueckgabe an Codex enthaelt review-faehige Evidenz und keinen finalen PASS-/Release-/Routing-Anspruch.
  - Der Vertrag aktiviert keine generische Delegation beliebiger Live-Tests.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q`
  - `python -m py_compile documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
  - fixture-based contract check for the bounded local live-retest package
- Model: 5.4
- Reason:
  - Der eigentliche Sicherheits- und Governance-Kern der Lane liegt im Worker- und Evidenzvertrag, nicht nur im sichtbaren Gate.

### TASK-SPEC28.3 Add regression coverage and Codex-owned accept/reject handoff for delegated live retests
- Ziel:
  - Sichere die neue Lane mit Regressionen und einem klaren Codex-owned Abschlussmodell ab, damit sichtbare Delegation nicht in implizite Abschlussautoritaet kippt.
- Scope:
  - Nur Regressionen, Review-Handoff und fail-closed Accept/Reject-Verhalten fuer die neue lokale Live-Retest-Lane. Keine neuen Produktfeatures und keine broad Registry-Ausweitung.
- Files:
  - `documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py`
  - `documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py`
  - `documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py`
  - `documentation/codex/skills/janus-test-pipeline/SKILL.md`
  - `documentation/codex/model-routing/or_everyday_operator_registry_summary_2026-06-24.md`
- Steps:
  1. Ergaenze Positiv- und Negativregressionen fuer eligible und nicht eligible lokale Live-Retests.
  2. Sichere ab, dass unvollstaendige Evidenz, fehlende Auth-Voraussetzungen oder zu breite Worker-Pakete fail-closed bei Codex landen.
  3. Halte den sichtbaren Lane-Nachweis und den Codex-owned Accept/Reject-Handoff konsistent.
  4. Stelle sicher, dass die Lane nicht versehentlich als globale OR-Live-Test-Freigabe in Registry- oder Summary-Artefakten auftaucht.
- Acceptance Criteria:
  - Eligible und nicht eligible lokale Live-Retests sind durch Regressionen klar voneinander getrennt.
  - Fehlende oder unsaubere Evidenz fuehrt zu einem lokalen Codex-owned Reject oder Fallback.
  - Die neue Lane behauptet nirgends delegierte finale PASS-/Release-/Routing-Hoheit.
  - Registry-/Summary-Artefakte ueberzeichnen die Lane nicht als globale Live-Test-Freigabe.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests -q -k "live_retest or accept or reject or fallback"`
  - `python -m pytest documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py -q`
  - `python -m py_compile documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py`
- Model: 5.4
- Reason:
  - Der Nutzerwert der Lane haengt am vertrauenswuerdigen Abschluss; ohne klaren Codex-owned Reject-/Fallback-Schutz waere der sichtbare OR-Live-Retest nur halb abgesichert.

@janus-task-breakdown
Spec: documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
Task: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
Backlog Item: BACKLOG-118
Target Task: TASK-SPEC28.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC28.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
Spec: documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
Backlog Item: BACKLOG-118
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it adds only the fail-closed eligibility and visible operator gate for local `LIVE_TEST_EXECUTION` retests inside the existing `janus-test-pipeline` path.
- Artifact identity is consistent across `BACKLOG-118`, approved Spec 28, generated `TASK-SPEC28`, and the released target-task handoff `TASK-SPEC28.1`.
- The affected file cluster is concrete and bounded to the repo-versioned `janus-test-pipeline` skill text, the shared bounded eligibility helper, the existing live-test gate runner path, and the focused regression tests for eligibility and gate visibility.
- Risk is HIGH because this slice opens a new operator-visible OR entry seam inside a real live-retest path. Skill 4 must preserve the hard boundary: no local auth/header contract work, no worker package details, no delegated evidence-write semantics, no final Codex-owned accept/reject wiring, and no broad live-test delegation beyond the eligible local lane.
- This slice is visibility-only for the first live-retest OR rollout. It may decide when the normal `1 = Codex` / `2 = OR` choice appears for bounded local retests, but it must not implement the later bounded worker/auth/evidence contract from `TASK-SPEC28.2` or the later accept/reject and registry-regression fence from `TASK-SPEC28.3`.
Affected Files:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q
- python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q -k "live or gate or eligibility"
- python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- git diff --check -- documentation/codex/skills/janus-test-pipeline/SKILL.md documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py documentation/tasks/TASK-SPEC28.1_preimplementation_check.md
- one focused negative-path check that non-eligible, too-broad, or non-local live-retest flows remain Codex-only without a visible OR gate
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q
- python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q -k "live or gate or eligibility"
- python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28.1_task_breakdown.md
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
Drop Context:
- later TASK-SPEC28.2 worker/auth/evidence-contract work
- later TASK-SPEC28.3 accept-reject and registry-regression work
- unrelated historical OR pilot, release, audit, or product-runtime bug history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The first live-retest OR lane slice is implementation-ready and tightly bounded to fail-closed eligibility plus visible gate behavior only.
User Action: Say `ok` to start implementation of `TASK-SPEC28.1` with the bound scope and evidence gate above.
```

## Changed Files

```text
M documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
 M documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
 M documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
 M documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
 M documentation/codex/skills/janus-test-pipeline/SKILL.md
?? documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
?? documentation/codex/model-routing/execution-review-fixtures/task_spec28_1_execution_patch_candidate_input_package_2026-07-01.json
?? documentation/codex/model-routing/execution-review-fixtures/task_spec28_1_execution_patch_candidate_input_package_compact_2026-07-01.json
?? documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-AUDIT-PROMPT-001/operator_choice_prompt.json
?? documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-AUDIT-PROMPT-002/operator_choice_prompt.json
?? documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-001/editable_paths.txt
?? documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-001/operator_choice_prompt.json
?? documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-002/editable_paths.txt
?? documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-002/operator_choice_prompt.json
?? documentation/tasks/TASK-SPEC28.1_AUDIT_PACKAGE.md
?? documentation/tasks/TASK-SPEC28.1_execution_result.md
?? documentation/tasks/TASK-SPEC28.1_preimplementation_check.md
?? documentation/tasks/TASK-SPEC28.1_task_breakdown.md
?? documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-SPEC28.1_task_breakdown.md (3124 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-review-fixtures\task_spec28_1_execution_patch_candidate_input_package_2026-07-01.json (7506 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\execution-review-fixtures\task_spec28_1_execution_patch_candidate_input_package_compact_2026-07-01.json (3410 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\sidecar-runs\TP-LIVE-GATE-PROMPT-001\operator_choice_prompt.json (1725 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\sidecar-runs\TP-LIVE-GATE-PROMPT-001\editable_paths.txt (195 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\sidecar-runs\TP-LIVE-GATE-PROMPT-002\operator_choice_prompt.json (1496 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\sidecar-runs\TP-LIVE-GATE-PROMPT-002\editable_paths.txt (195 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\sidecar-runs\TP-LIVE-GATE-AUDIT-PROMPT-001\operator_choice_prompt.json (1731 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\sidecar-runs\TP-LIVE-GATE-AUDIT-PROMPT-002\operator_choice_prompt.json (1502 bytes)
```

## Diff Summary

```text
.../scripts/bounded_or_worker_eligibility.py       | 187 ++++++++++++++++
 .../test_pipeline_sidecar_write_pilot_runner.py    | 235 ++++++++++++++++++---
 .../tests/test_bounded_or_worker_eligibility.py    |  30 ++-
 ...est_test_pipeline_sidecar_write_pilot_runner.py | 182 +++++++++++++++-
 .../codex/skills/janus-test-pipeline/SKILL.md      |  74 ++++++-
 5 files changed, 673 insertions(+), 35 deletions(-)
```

## Validation

```text
TASK EXECUTION RESULT
Canonical State: HANDOFF
Target Task: TASK-SPEC28.1
Changed Files:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/execution-review-fixtures/task_spec28_1_execution_patch_candidate_input_package_2026-07-01.json
- documentation/codex/model-routing/execution-review-fixtures/task_spec28_1_execution_patch_candidate_input_package_compact_2026-07-01.json
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-001/operator_choice_prompt.json
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-001/editable_paths.txt
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-002/operator_choice_prompt.json
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-002/editable_paths.txt
- documentation/tasks/TASK-SPEC28.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Executed Checks:
- `python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q`
- `python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q -k "live or gate or eligibility"`
- `python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- `python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --mode LIVE_TEST_EXECUTION --testspec-path documentation/TEST_SPEC/example.md --test-run-id TEST-RUN-2026-07-01-301 --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id TP-LIVE-GATE-PROMPT-001 --live-test-scope local_bounded_retest --sidecar-model moonshotai/kimi-k2.5`
- `python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --mode LIVE_TEST_EXECUTION --testspec-path documentation/TEST_SPEC/example.md --test-run-id TEST-RUN-2026-07-01-302 --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id TP-LIVE-GATE-PROMPT-002 --live-test-scope non_local_live_test --sidecar-model moonshotai/kimi-k2.5`
- `git diff --check -- documentation/codex/skills/janus-test-pipeline/SKILL.md documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py documentation/tasks/TASK-SPEC28.1_preimplementation_check.md`
- `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC28.1_execution_result.md`
Auto-Verification:
- Status: PASS
- Evidence:
  - The shared eligibility helper now exposes a dedicated fail-closed `LIVE_TEST_EXECUTION` gate that allows only `local_bounded_retest` and rejects `local_broad_retest`, `non_local_live_test`, and `not_a_retest`.
  - `test_pipeline_sidecar_write_pilot_runner.py` now renders two distinct operator-entry shapes for `LIVE_TEST_EXECUTION`: a visible `1 = Codex` / `2 = OR` gate for eligible local bounded retests and a Codex-only fallback with no visible `2 = OR` line for non-eligible slices.
  - The `janus-test-pipeline` skill text now describes the same bounded live-retest visibility contract as the runner entry, without claiming delegated auth, worker, or evidence authority before `TASK-SPEC28.2`.
  - The two live prompt artifacts prove the visible split on the real entry surface: `TP-LIVE-GATE-PROMPT-001` emitted `choice_2 = OR` for `local_bounded_retest`, while `TP-LIVE-GATE-PROMPT-002` stayed fail-closed and Codex-only for `non_local_live_test`.
  - The direct OR execution-patch attempt for this task ultimately produced one syntactically valid bounded artifact only after prompt compaction, but the proposed patch drifted from the real file structure; Codex therefore rejected it and implemented the bounded live-gate slice locally.
Manual Janus Validation Gate:
- Status: N/A WITH REASON
- Test Example: N/A - this slice changes only repo-owned skill wording, bounded OR gate visibility logic, and focused runner/test behavior for the infrastructure entry. It does not yet change Janus product runtime, local auth execution, delegated evidence writes, or the actual live retest worker contract.
- Expected Result: N/A - no user-facing Janus product behavior should change beyond when the bounded infrastructure gate text becomes visible versus fail-closed inside the `LIVE_TEST_EXECUTION` entry contract.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts:
- documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28.1_task_breakdown.md
- documentation/tasks/TASK-SPEC28.1_preimplementation_check.md
- documentation/tasks/TASK-SPEC28.1_execution_result.md
Evidence Paths:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-001/operator_choice_prompt.json
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-002/operator_choice_prompt.json
- documentation/tasks/TASK-SPEC28.1_execution_result.md
Failure Code: N/A
Changed Files:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/execution-review-fixtures/task_spec28_1_execution_patch_candidate_input_package_2026-07-01.json
- documentation/codex/model-routing/execution-review-fixtures/task_spec28_1_execution_patch_candidate_input_package_compact_2026-07-01.json
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-001/operator_choice_prompt.json
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-001/editable_paths.txt
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-002/operator_choice_prompt.json
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-PROMPT-002/editable_paths.txt
- documentation/tasks/TASK-SPEC28.1_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Decision: HANDOFF
Reason: The first Spec-28 slice now cleanly exposes the visible `1 = Codex` / `2 = OR` choice only for one eligible local bounded live-retest seam and keeps all broader or non-local `LIVE_TEST_EXECUTION` cases fail-closed, while actual delegated worker/auth/evidence behavior remains explicitly deferred to `TASK-SPEC28.2`.
Recommended Model: 5.5
Recommended Intelligence: high
New Chat: no
Next User Action: Say `ok` to run `janus-final-audit` for `TASK-SPEC28.1`, or `bleib hier` if you want to move directly into precheck planning for `TASK-SPEC28.2`.
```

## Notes

No additional notes provided.

## Risks

No known unresolved high-risk issues.

## Open Issues

None reported.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: janus-final-audit
MODEL: 5.5/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-SPEC28.1_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.
