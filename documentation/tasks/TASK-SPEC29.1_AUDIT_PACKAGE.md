# AUDIT_PACKAGE

Generated: 2026-07-02 16:08:24 UTC

## Goal

Audit TASK-SPEC29.1 normalized Janus worker contract slice

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: Spec 29 reviewed APPROVED_WITH_NOTES
- Task File: documentation\tasks\TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation\tasks\TASK-SPEC29.1_preimplementation_check.md
- Manual Janus Evidence: N/A WITH REASON - internal Codex worker-contract scripts/tests only; no Janus product runtime behavior changed.
- Pipeline Completion Status: implementation complete yes; remaining tasks TASK-SPEC29.2 and TASK-SPEC29.3 pending; final audit pending

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
TASK-SPEC29
- Source Spec: `documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md`
- Backlog Item: `N/A`
- Feature: Janus Worker Gateway fuer isolierte Aider/OpenRouter Delegation
- Generated At: 2026-07-02

## Generated Tasks

### TASK-SPEC29.1 Define the normalized worker task and result contract
- Ziel:
  - Definiere den verbindlichen lokalen Vertrag fuer `janus-worker` Aufgabenpakete, Profile, erlaubte Dateigrenzen, verbotene Aktionen und normierte Ergebnisartefakte.
- Scope:
  - Nur Schema, Validierung, Fixture-Vertrag und fail-closed Klassifikation. Keine echte Aider/OpenRouter-Ausfuehrung und kein Copy-back von Worker-Aenderungen.
- Files:
  - `documentation/codex/model-routing/scripts/janus_worker_contract.py`
  - `documentation/codex/model-routing/scripts/janus_worker_gateway.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_contract.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_gateway.py`
  - `documentation/codex/model-routing/strong-or-fixtures/`
- Steps:
  1. Definiere ein maschinenlesbares Task-Paket mit Task-Ziel, Profil, erlaubten Dateien, verbotenen Aktionen, Akzeptanzkriterien und Check-Kommandos.
  2. Definiere das normierte Ergebnisverzeichnis mit mindestens `RESULT.json`, `RESULT.md`, `DIFF.patch`, `FILES_CHANGED.txt`, `CHECKS.log` und `COST.json`.
  3. Implementiere Validierung fuer vollstaendige, unvollstaendige, scope-verletzende und blocked Ergebnisbloecke.
  4. Stelle sicher, dass der Contract ohne Roh-Agentenchat auswertbar ist und fehlende Artefakte fail-closed klassifiziert.
- Acceptance Criteria:
  - Gueltige Task-Pakete und Ergebnisverzeichnisse werden deterministisch akzeptiert.
  - Fehlende Pflichtfelder, verbotene Aktionen, leere Allowlists oder fehlende Ergebnisartefakte werden deterministisch abgelehnt.
  - `success` ist nur moeglich, wenn Ergebnisstatus, Diff, geaenderte Dateien, Checks und Kosten-/Usage-Metadaten im Contract konsistent sind.
  - Der Contract behauptet keine Git-, Release-, Publish-, Dependency-, Security-, Privacy- oder Architekturautoritaet fuer den Worker.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q`
  - `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "contract or result or fail_closed"`
  - `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py`
- Model: 5.4
- Reason:
  - Der MVP steht oder faellt mit dem Ergebnisvertrag; diese Slice macht Codex-Review ohne Rohchat-Abhaengigkeit erst pruefbar.

### TASK-SPEC29.2 Wire the isolated Aider/OpenRouter backend into the worker gateway
- Ziel:
  - Binde den bestehenden isolierten Aider/OpenRouter Runner an den neuen `janus-worker` Gateway-Vertrag und lasse jeden Lauf ein normiertes Ergebnispaket schreiben.
- Scope:
  - Nur Aider/OpenRouter als erstes Backend. Keine OpenCode-/OpenHands-Unterstuetzung, keine globale Skill-Aktivierung und keine produktive Abschlussautoritaet.
- Files:
  - `documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`
  - `documentation/codex/model-routing/scripts/janus_worker_contract.py`
  - `documentation/codex/model-routing/scripts/janus_worker_gateway.py`
  - `documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_gateway.py`
- Steps:
  1. Erweitere den Gateway-Einstieg so, dass Codex ein validiertes Task-Paket mit einem Aider/OpenRouter-Profil ausfuehren oder lokal ablehnen kann.
  2. Fuehre die Worker-Ausfuehrung weiterhin nur in einem isolierten Temp-Workspace mit expliziter Allowlist aus.
  3. Erzeuge nach jedem Lauf das normierte Ergebnispaket, auch bei `blocked`, `failed` oder Operator-Local-Auswahl.
  4. Kopiere Worker-Aenderungen nur bei sauberer Scope-, Check- und Artefaktvalidierung zurueck und markiere alles andere als Codex-Fallback.
- Acceptance Criteria:
  - Ein erfolgreicher isolierter Aider/OpenRouter-Lauf erzeugt alle normierten Ergebnisartefakte und ist fuer Codex reviewbar.
  - Fehlender `OPENROUTER_API_KEY`, ungueltiges Profil, rote Checks, Scope-Drift oder fehlende Artefakte fuehren nicht zu `success`.
  - Der Runner erzeugt keine akzeptierten Repo-Root-Seiteneffekte wie `.aider*` oder `.gitignore`-Aenderungen.
  - Der Worker darf keine Commit-, Push-, Release-, Publish- oder Dependency-Aktionen ausfuehren.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py -q`
  - `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q`
  - `python -m py_compile documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py`
- Model: 5.4
- Reason:
  - Diese Slice macht aus dem vorhandenen Aider-Pfad einen wiederholbaren Gateway statt eines einmaligen POC-Skripts.

### TASK-SPEC29.3 Add regression coverage, operator guidance, and the first bounded live-dev pilot
- Ziel:
  - Sichere den Worker Gateway mit Regressionen, knapper Operator-Dokumentation und einem ersten kleinen Live-Dev-Pilot gegen eine harmlose Dev-/Doku-/Testaufgabe ab.
- Scope:
  - Nur Nachweis, Regressionen, Profil-/Operator-Hinweise und ein kleiner Live-Dev-Pilot. Keine neue Backend-Auswahl, kein Release, keine Security-/Privacy-Arbeit und keine Produktlogik-Aenderung durch den Worker.
- Files:
  - `documentation/codex/model-routing/scripts/janus_worker_gateway.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_contract.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_gateway.py`
  - `documentation/codex/model-routing/janus_worker_gateway_profiles.md`
  - `development/openrouter-skill-tests/janus-worker-gateway-live/`
  - `documentation/tasks/TASK-SPEC29.3_execution_result.md`
- Steps:
  1. Ergaenze Regressionen fuer Erfolg, fehlenden Key, ungueltiges Profil, verbotene Datei, rote Checks, fehlende Artefakte und Operator-Local-Fallback.
  2. Dokumentiere die ersten Aider/OpenRouter-Profile, Kosten-/Usage-Hinweise und die Grenzen fuer geeignete Fleissarbeit.
  3. Fuehre genau einen kleinen bounded Live-Dev-Pilot aus, wenn die lokalen Voraussetzungen vorhanden sind und der Scope nicht produkt- oder sicherheitskritisch ist.
  4. Schreibe den Ausfuehrungsnachweis so, dass Codex den Pilot als Accept, Reject, Retry oder Fallback bewerten kann.
- Acceptance Criteria:
  - Die Regressionen decken erfolgreiche und fail-closed Worker-Ergebnisse ab.
  - Die Operator-Hinweise beschreiben Aider/OpenRouter als MVP-Backend und klaeren OpenCode/OpenHands explizit als spaeteren Nicht-MVP-Pfad.
  - Der Live-Dev-Pilot erzeugt ein normiertes Ergebnispaket oder einen dokumentierten Blocker.
  - Codex akzeptiert kein Worker-Ergebnis ohne Diff-, Check- und Artefaktpruefung.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests -q -k "janus_worker or isolated_aider"`
  - `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`
  - bounded live-dev pilot result or documented blocker under `development/openrouter-skill-tests/janus-worker-gateway-live/`
- Model: 5.4
- Reason:
  - Der Nutzerwert ist erst erreicht, wenn der Gateway nicht nur theoretisch validiert, sondern in einem kleinen Live-Dev-Betrieb beobachtbar nutzbar ist.

@janus-task-breakdown
Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Task: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Backlog Item: N/A
Target Task: TASK-SPEC29.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC29.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Spec: documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it defines only the normalized worker task/result contract, fixture validation, and fail-closed classification for the future `janus-worker` gateway.
- Artifact identity is consistent across approved Spec 29, generated TASK-SPEC29, the released target-task handoff `TASK-SPEC29.1`, and this precheck artifact.
- The affected file cluster is concrete and bounded to the new contract module, the lightweight gateway entry surface, focused tests, and any small fixture data needed for deterministic validation.
- Risk is HIGH because this contract becomes the trust boundary between Codex and cheaper external worker runs. Skill 4 must preserve the hard boundary: no live Aider/OpenRouter execution, no OpenRouter API call, no worker copy-back path, no OpenCode/OpenHands backend, and no delegated Git, release, publish, dependency, security, privacy, or architecture authority.
- This slice should make TASK-SPEC29.2 possible by defining what every later worker backend must emit and what Codex must reject.
Affected Files:
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- documentation/codex/model-routing/strong-or-fixtures/
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "contract or result or fail_closed"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py
- git diff --check -- documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/tests/test_janus_worker_contract.py documentation/codex/model-routing/tests/test_janus_worker_gateway.py documentation/tasks/TASK-SPEC29.1_preimplementation_check.md
- focused negative-path checks for missing artifacts, forbidden actions, empty allowlists, scope drift, red checks, and inconsistent `success` claims
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "contract or result or fail_closed"
- python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29.1_task_breakdown.md
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
Drop Context:
- later TASK-SPEC29.2 live Aider/OpenRouter runner wiring
- later TASK-SPEC29.3 operator guidance and live-dev pilot
- OpenCode, OpenHands, broad OR routing, release, Git governance, and product-runtime bug history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The first worker-gateway slice is implementation-ready and tightly bounded to contract, validators, fixtures, and focused tests only.
User Action: Say `ok` to start implementation of `TASK-SPEC29.1` with the bound scope and evidence gate above.
```

## Changed Files

```text
?? documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
?? documentation/codex/model-routing/scripts/janus_worker_contract.py
?? documentation/codex/model-routing/scripts/janus_worker_gateway.py
?? documentation/codex/model-routing/tests/test_janus_worker_contract.py
?? documentation/codex/model-routing/tests/test_janus_worker_gateway.py
?? documentation/tasks/TASK-SPEC29.1_execution_result.md
?? documentation/tasks/TASK-SPEC29.1_preimplementation_check.md
?? documentation/tasks/TASK-SPEC29.1_task_breakdown.md
?? documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-SPEC29.1_task_breakdown.md (3049 bytes)
FILE C:\KI\Janus-Projekt\documentation\tasks\TASK-SPEC29.1_execution_result.md (5574 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\janus_worker_contract.py (9150 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\janus_worker_gateway.py (2807 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\tests\test_janus_worker_contract.py (6586 bytes)
FILE C:\KI\Janus-Projekt\documentation\codex\model-routing\tests\test_janus_worker_gateway.py (5323 bytes)
```

## Diff Summary

```text
No diff stat available.
```

## Validation

```text
TASK EXECUTION RESULT
Canonical State: PASS
Target Task: TASK-SPEC29.1

Changed Files:
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- documentation/tasks/TASK-SPEC29.1_preimplementation_check.md
- documentation/tasks/TASK-SPEC29.1_task_breakdown.md
- documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md

Executed Checks:
- `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q`: PASS, 10 tests
- `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "contract or result or fail_closed"`: PASS, 5 tests
- `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py`: PASS
- `python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation\tasks\TASK-SPEC29.1_preimplementation_check.md`: PASS
- `git diff --check -- documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/tests/test_janus_worker_contract.py documentation/codex/model-routing/tests/test_janus_worker_gateway.py documentation/tasks/TASK-SPEC29.1_preimplementation_check.md documentation/tasks/TASK-SPEC29.1_task_breakdown.md documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md`: PASS
- ASCII check for new Python/test artifacts: PASS

Auto-Verification:
- Status: PASS
- Evidence:
  - Contract accepts valid task packages and rejects empty allowlists, missing forbidden boundaries, forbidden requested actions, and missing check rationale.
  - Result validation accepts complete success packages, rejects missing artifacts, rejects scope drift, rejects red checks, and keeps blocked results structurally reviewable.
  - Gateway validation returns `TASK_PACKAGE_READY`, `WORKER_SUCCESS_REVIEWABLE`, `WORKER_NON_SUCCESS_REVIEWABLE`, or `GATEWAY_CONTRACT_REJECTED` without executing any worker.

Manual Janus Validation Gate:
- Status: N/A WITH REASON
- Test Example: N/A
- Expected Result: N/A
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit
- Reason: This slice changes only internal Codex/Janus worker-contract scripts and tests. It does not change Janus product runtime behavior, frontend behavior, backend chat behavior, providers, persistence, or UI.

Implementation Notes:
- Added `janus_worker_contract.py` with task package validation, required forbidden-action boundaries, required normalized result artifacts, success semantics, scope-drift detection, check-result validation, and cost metadata validation.
- Added `janus_worker_gateway.py` as a validation-only CLI/function entry. It does not run Aider, call OpenRouter, copy worker changes back, or make acceptance decisions beyond contract validation.
- Added focused tests for valid and invalid packages, result artifact completeness, scope drift, red checks, blocked results, and gateway-level fail-closed behavior.
- Kept TASK-SPEC29.1 bounded. No live OpenRouter call, no Aider run, no OpenCode/OpenHands work, no Git/release/dependency authority, and no product-runtime behavior change.

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts:
- documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/tasks/TASK-SPEC29.1_task_breakdown.md
- documentation/tasks/TASK-SPEC29.1_preimplementation_check.md
- documentation/tasks/TASK-SPEC29.1_execution_result.md
Audit Package: documentation/tasks/TASK-SPEC29.1_AUDIT_PACKAGE.md
Evidence Paths:
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
Failure Code: N/A
Changed Files:
- documentation/codex/model-routing/scripts/janus_worker_contract.py
- documentation/codex/model-routing/scripts/janus_worker_gateway.py
- documentation/codex/model-routing/tests/test_janus_worker_contract.py
- documentation/codex/model-routing/tests/test_janus_worker_gateway.py
- documentation/tasks/TASK-SPEC29.1_execution_result.md
- documentation/tasks/TASK-SPEC29.1_preimplementation_check.md
- documentation/tasks/TASK-SPEC29.1_task_breakdown.md
- documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
- documentation/SPEC/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Decision: HANDOFF
Reason: TASK-SPEC29.1 is locally implemented and auto-verified. Final audit should review the bounded contract slice before TASK-SPEC29.2 wires real Aider/OpenRouter execution.
Recommended Model: 5.4
Recommended Intelligence: high
New Chat: no
Next User Action: Say `ok` to run `janus-final-audit` for `TASK-SPEC29.1`, or `weiter` after audit to start `TASK-SPEC29.2` task breakdown.
```

## Notes

No additional notes provided.

## Risks

Contract is new and TASK-SPEC29.2 must preserve its semantics when adding real Aider/OpenRouter execution; no live worker call was in scope for this slice.

## Open Issues

TASK-SPEC29.2 and TASK-SPEC29.3 remain unimplemented.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.5/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\TASK-SPEC29.1_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Change the model/reasoning to `5.5/high`, paste the block above into a fresh chat, write `ok`, and the final audit starts immediately.

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.
