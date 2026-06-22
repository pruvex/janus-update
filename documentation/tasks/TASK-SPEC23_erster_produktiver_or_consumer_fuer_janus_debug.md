TASK-SPEC23
- Source Spec: documentation/SPEC/Spec Done/23_erster_produktiver_or_consumer_fuer_janus_debug.md
- Backlog Item: N/A
- Feature: Erster produktiver OR-Consumer fuer `janus-debug`
- Generated At: 2026-06-21

## Generated Tasks

### TASK-SPEC23.1 Add a bounded productive OR eligibility and operator gate to `janus-debug`
- Ziel: Den bestehenden `janus-debug`-Pfad so erweitern, dass nur klar geeignete Debug-Faelle eine sichtbare Codex-vs-OR-Auswahl erhalten und alle anderen Faelle deterministisch Codex-only bleiben.
- Scope: Eligibility-Anbindung fuer den ersten produktiven Consumer, sichtbares Gate nur in klar bounded Debug-Faellen, kein stilles OR fuer ungeeignete Faelle und keine Ausweitung auf andere Skills oder Debug-Modi.
- Files:
  - documentation/codex/skills/janus-debug/SKILL.md
  - documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
  - documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
  - documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py
- Steps:
  - Den `janus-debug`-Workflow an den bestehenden bounded OR-Eligibility-Pfad fuer genau den ersten produktiven Consumer anbinden.
  - Die sichtbare Codex-vs-OR-Auswahl nur dann ausgeben, wenn der konkrete Debug-Fall klar bounded und eligible ist.
  - Sicherstellen, dass ungeeignete Debug-Faelle ohne OR-Gate sauber Codex-only bleiben.
  - Die Skill- und Integrationslogik so begrenzen, dass keine implizite Aktivierung in anderen Debug-Modi oder anderen Janus-Skills entsteht.
- Acceptance Criteria:
  - In klar ungeeigneten `janus-debug`-Faellen erscheint keine OR-Auswahl.
  - In klar geeigneten `janus-debug`-Faellen erscheint eine explizite Wahl zwischen Codex und OR.
  - Andere Debug-Modi oder andere Skills erhalten durch diese Slice keinen produktiven OR-Pfad.
  - Der lokale Codex-Pfad bleibt ausserhalb eligible Faelle unveraendert verfuegbar.
- Tests:
  - Positivtest fuer einen eligible `janus-debug`-Fall mit sichtbarem Gate
  - Negativtest fuer einen nicht eligible `janus-debug`-Fall ohne Gate
  - Regressionstest gegen implizite Aktivierung in anderen Debug-Modi
- Model: 5.4
- Reason: Diese Slice schafft den ersten echten Nutzer-Einstieg in den produktiven Consumer, ohne schon die gesamte Ergebnis- und Fallback-Semantik mit zu vermischen.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC23.1_final_audit.md` dokumentiert. Die bounded Eligibility- und sichtbare Operator-Gate-Schicht fuer `janus-debug` ist damit task-scharf abgeschlossen; Spec 23 insgesamt blieb dabei bewusst offen, weil `TASK-SPEC23.2` die produktive bounded Delegation, den direkten Codex-Fallback und den finalen Codex-owned Abschluss erst noch verankern musste.

### TASK-SPEC23.2 Wire bounded OR debug execution and direct Codex fallback into the productive `janus-debug` path
- Ziel: Den produktiven `janus-debug`-Consumer so anbinden, dass OR bounded Analyse- und Patch-Kandidaten-Arbeit liefern kann, waehrend Codex die finale Kontrolle behaelt und bei schwachen Ergebnissen direkt lokal uebernimmt.
- Scope: Bounded OR-Ausfuehrung fuer den freigegebenen `janus-debug`-Pfad, Codex-owned Ergebnispruefung, direkter Codex-Fallback bei unvollstaendigem, zu teurem oder qualitativ unsauberem OR-Ergebnis und sichtbarer Abschlussstatus.
- Files:
  - documentation/codex/skills/janus-debug/SKILL.md
  - documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py
  - documentation/codex/model-routing/tests/test_assistive_or_review_consumer_integration.py
- Steps:
  - Den freigegebenen `janus-debug`-Pfad an die bestehende bounded OR-Ausfuehrung fuer Analyse- und Patch-Kandidaten-Arbeit anbinden.
  - Sicherstellen, dass Codex das OR-Ergebnis lokal prueft und final ueber Annahme, Verwerfung oder lokale Uebernahme entscheidet.
  - Direkten Codex-Fallback fuer unvollstaendige, cap-verletzende oder qualitativ unsaubere OR-Ergebnisse verankern.
  - Den Abschluss fuer den Nutzer klar sichtbar halten, damit kein haengender Zwischenzustand entsteht.
- Acceptance Criteria:
  - Ein geeigneter `janus-debug`-Fall kann bounded OR-Analyse- oder Patch-Kandidaten-Arbeit ausfuehren.
  - Ein schwaches oder unvollstaendiges OR-Ergebnis fuehrt direkt zu einem klaren Codex-Fallback.
  - Der finale Abschluss bleibt explizit Codex-owned.
  - Der produktive `janus-debug`-Consumer aktiviert keine unbounded Schreib- oder Routing-Autoritaet.
- Tests:
  - Positivtest fuer einen bounded OR-Debug-Lauf mit finalem Codex-owned Abschluss
  - Negativtest fuer direkten Codex-Fallback bei unvollstaendigem oder qualitativ unsauberem OR-Ergebnis
  - Negativtest fuer Cap- oder Guardrail-Verletzung mit lokalem Abschluss
- Model: 5.4
- Reason: Diese Slice liefert den eigentlichen alltagstauglichen Produktivwert und haelt gleichzeitig die bounded OR-Grenze mit direkter lokaler Rueckfallebene stabil.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC23.2_final_audit.md` dokumentiert. Die produktive bounded Delegation, der direkte Codex-Fallback und der explizit Codex-owned Abschluss fuer den ersten `janus-debug`-OR-Consumer sind damit task-scharf abgeschlossen; Spec 23 insgesamt ist DONE und bleibt weiterhin strikt auf diesen einen bounded `debug_hypothesis_review`-Pfad begrenzt.

@janus-task-breakdown
Spec: documentation/SPEC/23_erster_produktiver_or_consumer_fuer_janus_debug.md
Task: documentation/tasks/TASK-SPEC23_erster_produktiver_or_consumer_fuer_janus_debug.md
Backlog Item: N/A
Target Task: TASK-SPEC23.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
