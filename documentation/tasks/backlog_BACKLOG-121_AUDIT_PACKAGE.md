# AUDIT_PACKAGE

Generated: 2026-07-09 13:18:57 UTC

## Goal

Final audit BACKLOG-121: shared delegation gate should keep bounded Cursor alternatives visible as fallback capacity under negative ROI while Codex remains recommended and non-opted lanes stay fail-closed.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: N/A WITH REASON - Lean-Dev routing-hardening slice on existing shared delegation infrastructure; no product Spec.
- Task File: documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
- Backlog Item: BACKLOG-121
- Pre-Implementation Check: documentation/tasks/backlog_BACKLOG-121_preimplementation_check.md
- Manual Janus Evidence: N/A WITH REASON - internal Codex model-routing policy/operator-gate change only; no Janus product runtime, UI, chat, persistence, or provider behavior changed.
- Pipeline Completion Status: Implementation complete yes; auto-verification PASS; final audit pending.

## Backlog Item

```text
### BACKLOG-121 - Shared-Delegation-Gate versteckt Cursor-Alternativen zu aggressiv bei negativer ROI

- **Typ:** CHANGE
- **Status:** IN PROGRESS
- **Quelle:** User Intake
- **Erstellt:** 2026-07-09
- **Aktualisiert:** 2026-07-09
- **Kurzbeschreibung:** Das aktuelle Shared-Delegation-Gate behandelt Tokenersparnis zu stark als Primaerziel und blendet technisch verfuegbare Cursor-Alternativen komplett aus, sobald `minimum_net_codex_saved_tokens` knapp verfehlt wird. Dadurch verliert der Operator genau dann eine wichtige Ausweichmoeglichkeit, wenn Codex-Kontingent knapp oder aufgebraucht ist und Cursor-Kapazitaet bewusst als produktive Alternative genutzt werden soll.
- **Erwartetes Verhalten:** Wenn eine Lane technisch freigegeben, bounded und sonst eligibel ist, soll die Gate-Logik zwischen Empfehlung und Sichtbarkeit unterscheiden. Schlechte oder nur leicht negative ROI darf die Empfehlung auf Codex verschieben, aber nicht automatisch alle externen Alternativen unsichtbar machen, wenn deren Hauptnutzen die alternative Arbeitskapazitaet ist.
- **Tatsaechliches Verhalten:** Fuer `execution_patch_candidate` blieb am 2026-07-09 trotz gueltigem bounded Package und sichtbarer Cursor-Backend-Konfiguration nur `1 = Codex` sichtbar, weil bei geschaetzten `9500` Netto-Codex-Tokens der Lane-Schwellwert `10000` nicht erreicht wurde. Ein erzwungener Versuch mit `--operator-choice 4 --execute-live-cursor` endete daraufhin mit `DELEGATION_BACKEND_NOT_AVAILABLE`, obwohl das Problem nicht fehlende Cursor-Technik, sondern die vorab versteckte Lane war.
- **Reproduktion / Kontext:** Reale Gate-Probe vom 2026-07-09 fuer `TASK-SPEC29.1` mit `janus_delegate.py --lane execution_patch_candidate --workflow-id WF-EXEC-SPEC29-1-2026-07-09-002 --operator-choice prompt --estimated-codex-saved-tokens 14000 --estimated-delegation-overhead-tokens 4500`. Das Ergebnis zeigte `roi.status = NEGATIVE`, `minimum_net_codex_saved_tokens = 10000`, `net_codex_saved_tokens = 9500` und nur Codex als sichtbare Wahl. User-Entscheidung danach: Alternativkapazitaet und Weiterarbeiten bei erschoepftem Codex-Kontingent sind wichtiger als reine Tokenersparnis; Savings bleiben zweitrangig.
- **Betroffener Bereich:** Codex model-routing / shared delegation gate / janus-executioner / Cursor-Lane-Sichtbarkeit / Operator-UX
- **Nachweise:** `documentation/codex/model-routing/config/delegation_routing_manifest.json`; `documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md`; `documentation/codex/model-routing/HANDOFF_COST_AWARE_4CHOICE_GATE_2026-07-07.md`; `development/openrouter-skill-tests/janus-executioner/spec29_1_candidate_lifecycle_2026-07-09/input_package.json`; reale Gate-Evidenz `WF-EXEC-SPEC29-1-2026-07-09-002`; erzwungener Hidden-Choice-Fehler `DELEGATION_BACKEND_NOT_AVAILABLE`.
- **Akzeptanzkriterien:**
  - [ ] Die Shared-Gate-Policy trennt sichtbar zwischen `Empfehlung` und `sichtbare Alternative`, statt externe Optionen bei leicht negativer ROI pauschal zu verstecken.
  - [ ] Fuer bounded technisch freigegebene Cursor-Lanes kann Alternativkapazitaet ein legitimer Sichtbarkeitsgrund sein, auch wenn die reine Netto-Codex-Ersparnis den Lane-Schwellwert knapp verfehlt.
  - [ ] Die Operator-Ausgabe erklaert klar, wenn eine externe Option als verfuegbare Ausweichlane sichtbar bleibt, aber nicht die kostenoptimierte Empfehlung ist.
  - [ ] Ein bounded `execution_patch_candidate`-Slice mit sonst gueltiger Cursor-Konfiguration scheitert nicht mehr allein deshalb an `DELEGATION_BACKEND_NOT_AVAILABLE`, weil die Sichtbarkeit zuvor nur durch ROI-Hiding unterdrueckt wurde.
  - [ ] Die Loesung bleibt fail-closed fuer wirklich unfreie, unsichere oder nicht validierte Lanes und oeffnet nicht pauschal alle externen Backends.
- **Fehlende Informationen:**
  - Keine
- **Wichtigkeit:** HIGH
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** M
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Lean-Dev routing-hardening slice fuer die bestehende Shared-Gate-Policy; Scope bleibt auf bounded Sichtbarkeits-/Empfehlungslogik, Operator-Messaging und Regressionstests begrenzt.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-07-09
- **Handoff:** documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-07-09
- **Notizen:** Das ist bewusst keine reine Threshold-Tuning-Aufgabe. Der Nutzer will primaer weiterarbeiten koennen, wenn Codex-Kontingent gerade der Engpass ist und Cursor noch Kapazitaet hat. Die bisherige cost-aware 4-choice-Logik und die Delegation-Handoffs nennen Flexibilitaet bei Kontingent- und Kostenentscheidungen bereits als Ziel; die aktuelle Hide-Policy wirkt dazu zu restriktiv.
```

## Task Acceptance Scope

```text
# BACKLOG-121 Task

- **Backlog Item:** BACKLOG-121 - Shared-Delegation-Gate versteckt Cursor-Alternativen zu aggressiv bei negativer ROI
- **Status:** READY
- **Erstellt:** 2026-07-09
- **Aktualisiert:** 2026-07-09
- **Kurzbeschreibung:** Die bestehende Shared-Gate-Policy fuer bounded Delegation soll zwischen `Empfehlung` und `sichtbarer Alternative` unterscheiden, damit technisch freigegebene Cursor-Lanes bei knapper oder leicht negativer ROI nicht automatisch verschwinden, wenn ihr eigentlicher Nutzen die alternative Arbeitskapazitaet ist.
- **Ziel:** Den hide-on-negative-ROI Pfad fuer gebundene externe Alternativen so haerten, dass fail-closed Sicherheit und lane-spezifische Eligibility erhalten bleiben, aber ein bounded Operator nicht mehr seine Ausweichoption verliert, nur weil die reine Netto-Codex-Ersparnis knapp unter dem Lane-Minimum liegt.
- **Scope:** Shared delegation routing policy fuer bestehende bounded Lanes, vor allem `execution_patch_candidate`, inklusive Manifest-Regeln, Sichtbarkeitslogik, Operator-Messaging und fokussierter Regressionstests. Keine neue produktive Lane, kein breites Architektur-Redesign, kein Git-/Release-/Dashboard-Produktfeature und keine pauschale Oeffnung aller externen Backends.
- **Files:**
  - `documentation/codex/model-routing/config/delegation_routing_manifest.json`
  - `documentation/codex/model-routing/scripts/delegation_routing.py`
  - `documentation/codex/model-routing/scripts/janus_delegate.py`
  - `documentation/codex/model-routing/tests/test_delegation_routing.py`
  - `documentation/codex/model-routing/tests/test_janus_delegate.py`
  - `documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md`
  - `documentation/ai/CURRENT_STATE.md`
- **Steps:**
  - Die aktuelle Shared-Gate-Policy fuer ROI-negative oder knapp unter Threshold liegende bounded externe Optionen im echten `execution_patch_candidate`-Pfad nachvollziehen.
  - Eine fail-closed Regel definieren, die Empfehlung und Sichtbarkeit trennt, ohne unfreie, unsichere oder nicht validierte Lanes zu oeffnen.
  - Die Operator-Ausgabe so anpassen, dass sichtbar bleibt, wenn eine externe Option verfuegbar, aber nicht kostenoptimiert empfohlen ist.
  - Regressionstests fuer Delegation-Routing und `janus_delegate` ergaenzen oder anpassen, damit der alte reine hide-on-negative-ROI-Pfad fuer diesen bounded Fall nicht unbemerkt zurueckkehrt.
- **Akzeptanzkriterien:**
  - Die Shared-Gate-Policy trennt sichtbar zwischen `Empfehlung` und `sichtbare Alternative`, statt externe Optionen bei leicht negativer ROI pauschal zu verstecken.
  - Fuer bounded technisch freigegebene Cursor-Lanes kann Alternativkapazitaet ein legitimer Sichtbarkeitsgrund sein, auch wenn die reine Netto-Codex-Ersparnis den Lane-Schwellwert knapp verfehlt.
  - Die Operator-Ausgabe erklaert klar, wenn eine externe Option als verfuegbare Ausweichlane sichtbar bleibt, aber nicht die kostenoptimierte Empfehlung ist.
  - Ein bounded `execution_patch_candidate`-Slice mit sonst gueltiger Cursor-Konfiguration scheitert nicht mehr allein deshalb an `DELEGATION_BACKEND_NOT_AVAILABLE`, weil die Sichtbarkeit zuvor nur durch ROI-Hiding unterdrueckt wurde.
  - Die Loesung bleibt fail-closed fuer wirklich unfreie, unsichere oder nicht validierte Lanes und oeffnet nicht pauschal alle externen Backends.
- **Fehlende Informationen:**
  - Keine
- **Betroffener Bereich:** Codex model-routing / shared delegation gate / janus-executioner / Cursor-Lane-Sichtbarkeit / Operator-UX
- **Nachweise:** `documentation/backlog/BACKLOG.md`; `documentation/codex/model-routing/config/delegation_routing_manifest.json`; `documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md`; `documentation/codex/model-routing/HANDOFF_COST_AWARE_4CHOICE_GATE_2026-07-07.md`; reale Gate-Evidenz `WF-EXEC-SPEC29-1-2026-07-09-002`
- **Notizen:** Lean-Dev-Routing-Hardening, keine Janus-Produktlogik. Der Slice soll eine bestehende Governance-/Operator-Policy reparieren, nicht eine neue Delegationsarchitektur erfinden oder alle ROI-Schranken pauschal abschaffen.

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-121
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
- Required Next Skill: SKILL 3
- Evidence Paths:
  - documentation/codex/model-routing/config/delegation_routing_manifest.json
  - documentation/codex/model-routing/HANDOFF_COST_AWARE_4CHOICE_GATE_2026-07-07.md
  - development/openrouter-skill-tests/janus-executioner/spec29_1_candidate_lifecycle_2026-07-09/input_package.json
- Dropped Context:
  - Spec-29-Routine-Lern-Implementierungsdetails ausser der einen Gate-Repro
  - alte breite OR-/Cursor-Historie ohne direkten Bezug zur Sichtbarkeitsregel

@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-121
Task: documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
Backlog Item: BACKLOG-121
```

## Pre-Implementation Check

```text
PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: BACKLOG-121
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
Spec: N/A WITH REASON - Lean-Dev routing-hardening slice on existing shared delegation infrastructure; no separate product Spec governs this bounded policy repair.
Backlog Item: BACKLOG-121
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: repair the shared delegation visibility policy for bounded external options so technically eligible Cursor alternatives can remain visible for capacity reasons even when pure Codex-token ROI is slightly negative.
- Scope is restricted to the existing shared routing infrastructure around `execution_patch_candidate`, especially manifest policy, `delegation_routing.py`, `janus_delegate.py`, the operator-facing task-list wording, and the focused regression tests that currently enforce the old hide-on-negative-ROI behavior.
- The slice must stay fail-closed. It may refine recommendation-versus-visibility logic, but it must not open unvalidated lanes, remove lane-specific eligibility checks, change accepted-source apply behavior, or broaden into new delegation architecture.
- Risk is MEDIUM because the change affects operator-facing gating semantics across shared bounded lanes, but it remains a Lean-Dev governance slice with a concrete file cluster and no Janus product feature logic.
Affected Files:
- documentation/codex/model-routing/config/delegation_routing_manifest.json
- documentation/codex/model-routing/scripts/delegation_routing.py
- documentation/codex/model-routing/scripts/janus_delegate.py
- documentation/codex/model-routing/tests/test_delegation_routing.py
- documentation/codex/model-routing/tests/test_janus_delegate.py
- documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md
- documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
- documentation/tasks/backlog_BACKLOG-121_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Evidence Focus:
- python -m pytest documentation/codex/model-routing/tests/test_delegation_routing.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_delegate.py -q
- python -m py_compile documentation/codex/model-routing/scripts/delegation_routing.py documentation/codex/model-routing/scripts/janus_delegate.py
- git diff --check -- documentation/codex/model-routing/config/delegation_routing_manifest.json documentation/codex/model-routing/scripts/delegation_routing.py documentation/codex/model-routing/scripts/janus_delegate.py documentation/codex/model-routing/tests/test_delegation_routing.py documentation/codex/model-routing/tests/test_janus_delegate.py documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md documentation/tasks/backlog_BACKLOG-121_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not create new delegation backends, do not remove OpenRouter or Cursor choices globally, do not change deterministic apply semantics for `TASK-EX-002`, and do not widen into dashboard quota polling, billing telemetry services, or general release/governance work.
- Cursor-first should be checked again at execution time for this bounded write-capable slice when the shared execution gate exposes a sensible lane; Codex remains owner of review, validation, and final state.
Automated Evidence Gate:
- python -m pytest documentation/codex/model-routing/tests/test_delegation_routing.py -q
- python -m pytest documentation/codex/model-routing/tests/test_janus_delegate.py -q
- python -m py_compile documentation/codex/model-routing/scripts/delegation_routing.py documentation/codex/model-routing/scripts/janus_delegate.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md
- documentation/tasks/backlog_BACKLOG-121_shared_delegation_gate_versteckt_cursor_alternativen_zu_aggressiv_bei_negativer_roi.md
- documentation/tasks/backlog_BACKLOG-121_preimplementation_check.md
- documentation/codex/model-routing/config/delegation_routing_manifest.json
- documentation/codex/model-routing/scripts/delegation_routing.py
- documentation/codex/model-routing/scripts/janus_delegate.py
- documentation/codex/model-routing/tests/test_delegation_routing.py
- documentation/codex/model-routing/tests/test_janus_delegate.py
- documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md
- the real gate evidence `WF-EXEC-SPEC29-1-2026-07-09-002`
Drop Context:
- Spec-29 routine-learning implementation details beyond the one execution-gate repro
- old OR/Cursor rollout history that does not affect the current visibility-policy repair
- unrelated backlog items, final audits, release work, and provider/product debugging
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: BACKLOG-121 is now a bounded Lean-Dev routing-hardening slice with explicit files, regression tests, and a clear fail-closed scope.
User Action: Continue with janus-executioner for `BACKLOG-121`, and probe the shared execution gate for a sensible Cursor-first write-capable lane before local implementation.
```

## Changed Files

```text
M documentation/codex/model-routing/config/delegation_routing_manifest.json
 M documentation/codex/model-routing/config/delegation_task_list_2026-07-05.md
 M documentation/codex/model-routing/scripts/delegation_routing.py
 M documentation/codex/model-routing/scripts/janus_delegate.py
 M documentation/codex/model-routing/tests/test_delegation_routing.py
 M documentation/codex/model-routing/tests/test_janus_delegate.py
?? documentation/tasks/backlog_BACKLOG-121_execution_result.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\tasks\backlog_BACKLOG-121_execution_result.md (6425 bytes)
```

## Diff Summary

```text
.../config/delegation_routing_manifest.json        | 435 +++++++++++++------
 .../config/delegation_task_list_2026-07-05.md      | 135 +++---
 .../model-routing/scripts/delegation_routing.py    | 472 +++++++++++++++++----
 .../codex/model-routing/scripts/janus_delegate.py  |  71 +++-
 .../model-routing/tests/test_delegation_routing.py | 249 +++--------
 .../model-routing/tests/test_janus_delegate.py     | 468 +++-----------------
 6 files changed, 949 insertions(+), 881 deletions(-)
```

## Validation

```text
- python -m pytest documentation/codex/model-routing/tests/test_delegation_routing.py -q: PASS, 11 tests
- python -m pytest documentation/codex/model-routing/tests/test_janus_delegate.py -q: PASS, 16 tests
- python -m py_compile documentation/codex/model-routing/scripts/delegation_routing.py documentation/codex/model-routing/scripts/janus_delegate.py: PASS
- python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/backlog_BACKLOG-121_execution_result.md: PASS
- python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --task-id TASK-EX-001 --workflow-id WF-BACKLOG-121-AUDIT-2026-07-09-001 --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-executioner/spec29_1_candidate_lifecycle_2026-07-09/input_package.json --allowlist-file development/openrouter-skill-tests/janus-executioner/spec29_1_candidate_lifecycle_2026-07-09/allowlist.txt --estimated-codex-saved-tokens 14000 --estimated-delegation-overhead-tokens 4500: PASS, ROI NEGATIVE with net_codex_saved_tokens 9500, visible choices 1/2/3/4, recommended_choice 1, operator note present
- python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --task-id TASK-EX-001 --workflow-id WF-BACKLOG-121-AUDIT-2026-07-09-002 --operator-choice 4 --input-package-json development/openrouter-skill-tests/janus-executioner/spec29_1_candidate_lifecycle_2026-07-09/input_package.json --allowlist-file development/openrouter-skill-tests/janus-executioner/spec29_1_candidate_lifecycle_2026-07-09/allowlist.txt --estimated-codex-saved-tokens 14000 --estimated-delegation-overhead-tokens 4500: PASS, backend cursor, selected_choice 4, cursor_pool api, final_outcome CURSOR_WORKER_DRY_RUN_READY
```

## Notes

- The implementation adds `negative_roi_visibility_mode = keep_visible_non_recommended` only to the bounded `execution_patch_candidate` lane.
- Shared routing still returns Codex-only visibility on negative ROI for lanes without that explicit opt-in.
- Negative ROI forces `recommended_backend = codex` and `recommended_choice = 1` even when external options remain visible.
- Manual Janus evidence is N/A because this affects internal Codex operator routing, not Janus product runtime behavior.

## Risks

Audit should verify the opt-in does not broaden visibility on non-opted negative-ROI lanes and that recommendation remains Codex on negative ROI.

## Open Issues

None known before final audit.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.5/high
PASS: C:\KI\Janus-Projekt\documentation\tasks\backlog_BACKLOG-121_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Change the model/reasoning to `5.5/high`, paste the block above into a fresh chat, write `ok`, and the final audit starts immediately.

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.
