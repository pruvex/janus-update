# AUDIT_PACKAGE

Generated: 2026-07-05 13:14:26 UTC

## Goal

Final audit TASK-SPEC28.2 bounded OR live-retest worker/auth/evidence contract.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
- Task File: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
- Backlog Item: BACKLOG-118
- Pre-Implementation Check: documentation/tasks/TASK-SPEC28.2_preimplementation_check.md
- Manual Janus Evidence: N/A WITH REASON - infrastructure contract only; precheck forbids real live retest in TASK-SPEC28.2.
- Pipeline Completion Status: TASK-SPEC28.2 implementation complete after audit-prompt wording delta; final audit pending; TASK-SPEC28.3 accept/reject registry hardening not in scope.

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
- **Tatsaechliches Verhalten:** PARTIAL - `TASK-SPEC28.1` hat die sichtbare `1 = Codex / 2 = OR`-Wahl fuer eligible lokale bounded `LIVE_TEST_EXECUTION`-Retests audit-clean geoeffnet; der eigentliche Worker/Auth/Evidence-Pfad und Codex-owned Accept/Reject-Abschluss stehen noch aus.
- **Reproduktion / Kontext:** Im `BACKLOG-116`-Retest am 2026-07-01 wurde nach erfolgreichem Debug-Fix erneut `OK START LIVE TEST` ausgefuehrt. Der Retest lief gruen, musste aber komplett von Codex ueber den lokalen Dev-API-Pfad inklusive internem Header, Chat-Erzeugung, Prompt-Ausfuehrung und Evidenzablage gefahren werden. Nutzerfrage danach: warum dieser Test nicht durch ein OR-Modell gelaufen ist; Folgeentscheidung: eine eigene bounded OR-Lane fuer diesen Modus aufbauen.
- **Betroffener Bereich:** Dev-Infrastruktur / OR-Model-Routing / janus-test-pipeline / lokale Live-Retests
- **Nachweise:** `documentation/test-runs/BACKLOG-116_live_retest_after_debug_2026-07-01.md`; `documentation/test-results/BACKLOG-116-live-retest-after-debug-2026-07-01/BACKLOG-116_live_retest_after_debug_api_evidence.json`; User-Entscheidung vom 2026-07-01; `documentation/tasks/TASK-SPEC28.1_final_audit.md`; `documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-AUDIT-PROMPT-001/operator_choice_prompt.json`; `documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-AUDIT-PROMPT-002/operator_choice_prompt.json`.
- **Akzeptanzkriterien:**
  - [x] `janus-test-pipeline` beschreibt eine sichtbare bounded OR-Lane fuer eligible `LIVE_TEST_EXECUTION`-Retests mit `1 = Codex / 2 = OR`.
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
- **Handoff:** documentation/tasks/TASK-SPEC28.2_task_breakdown.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-07-01
- **Precheck artifact:** documentation/tasks/TASK-SPEC28.1_preimplementation_check.md
- **Target Task:** TASK-SPEC28.2
- **Completed Task:** TASK-SPEC28.1 - `documentation/tasks/TASK-SPEC28.1_final_audit.md`
- **Audit Package:** `documentation/tasks/TASK-SPEC28.1_AUDIT_PACKAGE.md`
- **Documentation Update:** `documentation/tasks/TASK-SPEC28.1_documentation_update.md`
- **Next Target Task:** TASK-SPEC28.2
- **Notizen:** Lean-Dev-Infrastrukturarbeit, aber kein Quickchange: die Lane beruehrt Governance, lokalen Auth-Pfad, Worker-Grenzen, Evidenzschema und Testpipeline-UX. `TASK-SPEC28.1` ist erledigt und oeffnet nur die sichtbare Gate-Wahl. `TASK-SPEC28.2` muss als naechstes den bounded Worker/Auth/Evidence-Vertrag liefern, bevor echte delegierte Live-Retests produktiv laufen koennen.
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
- Status: DONE
- Completed: 2026-07-05
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
- Preimplementation Check: PASS - `documentation/tasks/TASK-SPEC28.1_preimplementation_check.md`
- Execution Result: PASS/HANDOFF - `documentation/tasks/TASK-SPEC28.1_execution_result.md`
- Audit Package: `documentation/tasks/TASK-SPEC28.1_AUDIT_PACKAGE.md`
- Final Audit: PASS - `documentation/tasks/TASK-SPEC28.1_final_audit.md`
- Documentation Update: PASS - `documentation/tasks/TASK-SPEC28.1_documentation_update.md`
- Completion Evidence:
  - `documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-AUDIT-PROMPT-001/operator_choice_prompt.json`
  - `documentation/codex/model-routing/sidecar-runs/TP-LIVE-GATE-AUDIT-PROMPT-002/operator_choice_prompt.json`

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

Target Task: TASK-SPEC28.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
Spec: documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
Backlog Item: BACKLOG-118
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it defines the bounded local live-retest worker/auth/evidence contract that comes after the already-audited visible `LIVE_TEST_EXECUTION` gate in TASK-SPEC28.1.
- Artifact identity is consistent across BACKLOG-118, approved Spec 28, generated TASK-SPEC28, completed TASK-SPEC28.1, and the released target-task handoff `documentation/tasks/TASK-SPEC28.2_task_breakdown.md`.
- The implementation surface is bounded to repo-owned OR/test-pipeline infrastructure: the `janus-test-pipeline` skill text, the live-test sidecar runner, the isolated worker runner integration surface, the bounded delegation dispatcher touchpoint if needed, focused runner tests, and a fixture/package contract under `documentation/codex/model-routing/strong-or-fixtures/` or an adjacent scoped fixture path.
- Risk is HIGH because this slice touches local auth/header boundaries and the first practical worker/evidence contract for real OR live-retest work. Skill 4 must preserve the hard boundary: no versioned secrets, no broad shell authority, no generic live-test delegation, no real live retest run as part of this slice, no final PASS/release/Git/routing authority for OR, and no TASK-SPEC28.3 accept/reject registry hardening.
- The expected implementation result is a reviewable package/contract shape and deterministic fixture validation, not a production live-run acceptance decision.
Affected Files:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/strong-or-fixtures/
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
- documentation/tasks/TASK-SPEC28.2_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Evidence Focus:
- Validate that a bounded local live-retest worker contract exists for only allowed local health, chat creation, bound prompt execution, and evidence collection steps.
- Validate that local auth/header support is represented as a bounded runtime/local-context requirement and never serialized as real secret values in versioned fixtures, packages, prompts, summaries, or evidence.
- Validate that returned worker artifacts are reviewable by Codex and do not claim final PASS, release, Git, routing, or task-completion authority.
- Validate that the worker package cannot be reused as broad shell delegation or generic live-test delegation.
- Preserve the TASK-SPEC28.1 gate behavior: eligible `local_bounded_retest` may expose `2 = OR`, while non-eligible scopes remain Codex-only.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q
- python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q -k "live"
- python -m py_compile documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- fixture/package validation command for the bounded local live-retest package, including secret-redaction and allowlist checks
- git diff --check -- documentation/codex/skills/janus-test-pipeline/SKILL.md documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/strong-or-fixtures/ documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py documentation/tasks/TASK-SPEC28.2_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28.2_task_breakdown.md
- documentation/tasks/TASK-SPEC28.1_final_audit.md
- documentation/tasks/TASK-SPEC28.1_documentation_update.md
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
Drop Context:
- TASK-SPEC28.1 implementation chatter beyond final audit and documentation closeout
- later TASK-SPEC28.3 accept/reject and registry-regression work
- unrelated OR pilots, broad worker experiments, product-runtime bugs, release work, and dirty worktree debris
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, bounded worker/auth/evidence contract artifacts, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: `TASK-SPEC28.2` is implementation-ready as a bounded worker/auth/evidence contract slice after the visible gate passed final audit; the scope is high-risk but concrete and evidence-gated.
User Action: Continue with `janus-executioner` for `TASK-SPEC28.2` in this chat.
```

## Changed Files

```text
M documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
 M documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
 M documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
 M documentation/codex/skills/janus-test-pipeline/SKILL.md
?? documentation/codex/model-routing/sidecar-runs/TP-LIVE-RETEST-AUDIT-PROMPT-002/operator_choice_prompt.json
?? documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md
?? documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_worker_package_2026-07-05.json
?? documentation/tasks/TASK-SPEC28.2_execution_result.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\codex\skills\janus-test-pipeline\SKILL.md (22178 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\test_pipeline_sidecar_write_pilot_runner.py (47087 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\isolated_aider_workspace_runner.py (50061 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\tests\test_test_pipeline_sidecar_write_pilot_runner.py (29929 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\strong-or-fixtures\strong_live_retest_worker_package_2026-07-05.json (2209 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\strong-or-fixtures\strong_live_retest_evidence_fixture_2026-07-05.md (249 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\sidecar-runs\TP-LIVE-RETEST-AUDIT-PROMPT-002\operator_choice_prompt.json (1797 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-SPEC28.2_execution_result.md (7972 bytes)
```

## Diff Summary

```text
.../scripts/isolated_aider_workspace_runner.py     |  74 ++++
 .../test_pipeline_sidecar_write_pilot_runner.py    | 481 +++++++++++++++++++--
 ...est_test_pipeline_sidecar_write_pilot_runner.py | 392 ++++++++++++++++-
 .../codex/skills/janus-test-pipeline/SKILL.md      |  74 +++-
 4 files changed, 987 insertions(+), 34 deletions(-)
```

## Validation

```text
TASK EXECUTION RESULT
Canonical State: HANDOFF
Target Task: TASK-SPEC28.2
Changed Files:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_worker_package_2026-07-05.json
- documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-RETEST-AUDIT-PROMPT-002/operator_choice_prompt.json
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-RETEST-AUDIT-PROMPT-002/editable_paths.txt
- documentation/tasks/TASK-SPEC28.2_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Executed Checks:
- `python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q`
- `python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py -q -k "live"`
- `python -m py_compile documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
- `python -c "import importlib.util, json, pathlib; p=pathlib.Path('documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py'); spec=importlib.util.spec_from_file_location('runner', p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); pkg=json.loads(pathlib.Path('documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_worker_package_2026-07-05.json').read_text(encoding='utf-8')); r=m.validate_live_retest_worker_package_contract(pkg); print(json.dumps(r, indent=2)); raise SystemExit(0 if r['validation_result']=='PASS' else 1)"`
- `python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --mode LIVE_TEST_EXECUTION --testspec-path documentation/TEST_SPEC/example.md --test-run-id TEST-RUN-2026-07-05-AUDIT-PROMPT-FIXED --normal-target-model "5.4 medium" --operator-choice prompt --workflow-id TP-LIVE-RETEST-AUDIT-PROMPT-002 --live-test-scope local_bounded_retest --sidecar-model moonshotai/kimi-k2.5 --isolated-aider-package-json documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_worker_package_2026-07-05.json`
- `git diff --check -- documentation/codex/skills/janus-test-pipeline/SKILL.md documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/strong-or-fixtures/ documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py documentation/tasks/TASK-SPEC28.2_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md`
Auto-Verification:
- Status: PASS
- Evidence:
  - `test_pipeline_sidecar_write_pilot_runner.py` now builds and validates a bounded `LIVE_TEST_EXECUTION` local retest worker package with exactly the allowed steps: `api_health_check`, `create_chat`, `run_bound_prompt`, and `collect_evidence`.
  - The package contract represents local auth as runtime-only metadata and fails if secret-like values such as bearer tokens, API keys, passwords, or token markers appear anywhere in the serialized package.
  - The `LIVE_TEST_EXECUTION` delegated branch now validates the package before invoking the isolated worker runner, rejects invalid packages with `LIVE_RETEST_WORKER_CONTRACT_REJECTED`, and annotates returned worker summaries with contract validation, eligibility, Codex review requirement, and final-authority boundaries.
  - `isolated_aider_workspace_runner.py` independently validates the same live-retest contract shape before accepting a worker package, so bypassing the sidecar runner does not remove the package boundary.
  - Versioned fixtures under `documentation/codex/model-routing/strong-or-fixtures/` prove the intended package/evidence shape without storing credentials or live Janus response data.
  - Focused tests cover valid package validation, secret-like package rejection, delegated handoff forwarding, and rejected secret-bearing `LIVE_TEST_EXECUTION` packages.
  - Final-audit spot-check found and fixed one stale prompt wording mismatch: when a worker package is supplied, `operator_choice_prompt.json` now states that the bounded worker package is present, will be validated before OR runs, uses runtime-only auth metadata, rejects serialized secrets, and keeps Codex as final reviewer.
Manual Janus Validation Gate:
- Status: N/A WITH REASON
- Test Example: N/A - this slice intentionally defines and validates the bounded worker/auth/evidence contract only. The preimplementation gate explicitly forbids running a real live retest as part of TASK-SPEC28.2.
- Expected Result: N/A - no Janus product runtime behavior changes in this slice; the observable change is infrastructure readiness for a future bounded local live-retest worker handoff.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts:
- documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
- documentation/tasks/TASK-SPEC28.2_task_breakdown.md
- documentation/tasks/TASK-SPEC28.2_preimplementation_check.md
- documentation/tasks/TASK-SPEC28.2_execution_result.md
Evidence Paths:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_worker_package_2026-07-05.json
- documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-RETEST-AUDIT-PROMPT-002/operator_choice_prompt.json
- documentation/tasks/TASK-SPEC28.2_execution_result.md
Failure Code: N/A
Changed Files:
- documentation/codex/skills/janus-test-pipeline/SKILL.md
- documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py
- documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
- documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_worker_package_2026-07-05.json
- documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-RETEST-AUDIT-PROMPT-002/operator_choice_prompt.json
- documentation/codex/model-routing/sidecar-runs/TP-LIVE-RETEST-AUDIT-PROMPT-002/editable_paths.txt
- documentation/tasks/TASK-SPEC28.2_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Decision: HANDOFF
Reason: TASK-SPEC28.2 now has a bounded local live-retest worker/auth/evidence contract that can be reviewed and rejected deterministically before any OR worker run, while preserving Codex as final reviewer and preventing serialized secrets, generic live-test delegation, broad shell authority, Git, release, routing, or final PASS authority.
Recommended Model: 5.5
Recommended Intelligence: high
New Chat: no
Next User Action: Continue with `janus-final-audit` for `TASK-SPEC28.2`.
```

## Notes

No additional notes provided.

## Risks

High-risk boundary area around local auth and live execution; mitigated by runtime-only auth metadata, secret-like value rejection, allowlisted worker files, no broad shell, prompt evidence for contract-backed package gate, and Codex final authority. No real OR live retest was run in this slice by design.

## Open Issues

Real productive OR live-retest execution remains pending after final audit/documentation; TASK-SPEC28.3 still needed for accept/reject registry hardening.

## Re-Audit Delta

Primary blocker: Audit spot-check found stale LIVE_TEST_EXECUTION prompt wording that still claimed no worker/auth/evidence contract when a worker package was supplied.

Updated prompt_summary to distinguish prompt-only gates from contract-backed worker-package gates; added regression test for package-backed LIVE_TEST_EXECUTION prompt; generated TP-LIVE-RETEST-AUDIT-PROMPT-002 evidence showing package present, validation-before-OR-run, runtime-only auth metadata, serialized-secret rejection, and Codex final review authority.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.5/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-SPEC28.2_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Change the model/reasoning to `5.5/high`, paste the block above into a fresh chat, write `ok`, and the final audit starts immediately.

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.
