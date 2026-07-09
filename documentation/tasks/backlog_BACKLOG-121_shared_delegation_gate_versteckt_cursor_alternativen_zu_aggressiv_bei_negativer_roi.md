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
