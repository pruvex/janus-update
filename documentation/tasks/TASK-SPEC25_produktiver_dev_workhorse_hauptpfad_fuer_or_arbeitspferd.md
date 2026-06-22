TASK-SPEC25
- Source Spec: documentation/SPEC/Spec Done/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- Backlog Item: N/A
- Feature: Produktiver Dev-Workhorse-Hauptpfad fuer OR-Arbeitspferd
- Generated At: 2026-06-22

## Generated Tasks

### TASK-SPEC25.1 Pin the first productive Dev-workhorse work classes and their fixed recommended OR models
- Ziel: Den dedizierten produktiven Dev-Workhorse-Pfad so nachschaerfen, dass genau die ersten erlaubten bounded Schreib- und Umsetzungsarbeitsklassen plus ihre festen empfohlenen OR-Modelle explizit hinterlegt und lokal pruefbar sind.
- Scope: Konfigurations- und Eligibility-Haertung fuer den dedizierten Dev-Workhorse-Pfad, explizite erste Arbeitsklassen fuer bounded Schreib-/Umsetzungsarbeit, feste empfohlene OR-Modelle pro Arbeitsklasse und keine implizite Rueckkehr zu gemischten breiteren Pilotklassen.
- Files:
  - documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json
  - documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json
  - documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
  - documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- Steps:
  - Den dedizierten `productive_dev_workhorse_path` auf genau die ersten produktiven bounded Schreib- und Umsetzungsarbeitsklassen verengen, statt weiter eine gemischte Review-/Write-Kombination still mitzutragen.
  - Fuer jede erste erlaubte Arbeitsklasse eine feste empfohlene OR-Modellzuordnung in den produktiven Dev-Workhorse-Contract aufnehmen.
  - Eligibility- und Missing-Config-Grenzen so haerten, dass ohne feste empfohlene Modellzuordnung kein produktiver OR-Gate-Pfad erscheint.
  - Sicherstellen, dass bestehende Assist-only- oder Skill-spezifische Pilotpfade dadurch nicht still umdefiniert werden.
- Acceptance Criteria:
  - Der dedizierte produktive Dev-Workhorse-Pfad erlaubt nur die explizit festgezogenen ersten bounded Schreib-/Umsetzungsarbeitsklassen.
  - Jede erlaubte Arbeitsklasse liefert eine feste empfohlene OR-Modellzuordnung fuer den produktiven Gate-Pfad.
  - Fehlende Klassen- oder Modellzuordnung blockiert vor jeder produktiven OR-Auswahl.
  - Bestehende Spec-21-, Spec-22- oder Spec-23-Pfade bleiben ausserhalb des dedizierten Dev-Workhorse-Pfads unveraendert.
- Tests:
  - Positivtest fuer eine erlaubte erste produktive Arbeitsklasse mit vorhandener Modellzuordnung
  - Negativtest fuer eine nicht mehr erlaubte gemischte Review-Klasse im dedizierten Pfad
  - Negativtest fuer fehlende feste Modellzuordnung
  - Regressionstest gegen unbeabsichtigte Aenderung bestehender Pilotpfade
- Model: 5.4
- Reason: Diese Slice zieht die produktive Hauptpfadgrenze endlich auf die wirklich gewollten Workhorse-Klassen und verhindert, dass das Zielbild wieder in fruehere gemischte Pilotlogik verschwimmt.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC25.1_final_audit.md` dokumentiert. Der erste produktive Dev-Workhorse-Klassen-/Modell-Contract ist damit task-scharf abgeschlossen: der dedizierte Hauptpfad erlaubt nur noch `execution_patch_candidate` und `execution_write_apply_candidate`, beide mit fester Empfehlung `deepseek/deepseek-v4-flash`, waehrend fehlende Modellzuordnungen fail-closed blockieren; Spec 25 insgesamt bleibt bewusst offen, weil `TASK-SPEC25.2` und `TASK-SPEC25.3` die sichtbare Gate-Schicht und die produktive Runtime erst noch umsetzen.

### TASK-SPEC25.2 Show the fixed recommended OR model and pre-call cost basis in the productive Dev-workhorse operator gate
- Ziel: Die sichtbare Operator-Auswahl im dedizierten produktiven Dev-Workhorse-Pfad so erweitern, dass pro erlaubter Arbeitsklasse die feste empfohlene OR-Modellzuordnung und die zugehoerige Pre-Call-Kostenbasis explizit angezeigt werden.
- Scope: Dedizierter produktiver Dev-Workhorse-Runner, Gate-Ausgabe, Pflichtanzeige fuer feste Modellzuordnung und Pre-Call-Kostenbasis, fail-closed Abort bei fehlenden Pflichtdaten und keine freie manuelle Modellwahl in dieser Stufe.
- Files:
  - documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
  - documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
  - documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
  - documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- Steps:
  - Den dedizierten produktiven Runner so erweitern, dass das Gate fuer jede erlaubte Arbeitsklasse das feste empfohlene OR-Modell sichtbar ausgibt.
  - Die Gate-Ausgabe mit der vorhandenen Pre-Call-Kostenbasis und den schon erwarteten Estimate-/Confidence-Feldern zu einem konsistenten Operator-Block zusammenfuehren.
  - Den Pfad fail-closed halten, wenn feste Modellzuordnung, Kostenbasis oder sonstige Gate-Pflichtdaten fehlen.
  - Das Dev-Runbook auf genau diesen produktiven Gate-Standard nachziehen, ohne daraus breite Skill-Aktivierung oder freie Modellwahl abzuleiten.
- Acceptance Criteria:
  - Der dedizierte produktive Gate-Pfad zeigt die feste empfohlene OR-Modellzuordnung pro Arbeitsklasse sichtbar an.
  - Die Gate-Ausgabe zeigt die Pre-Call-Kostenbasis zusammen mit den Pflichtfeldern fuer Estimate und Confidence.
  - Fehlende feste Modellzuordnung oder fehlende Kostenbasis blockieren vor jeder Dispatcher- oder Wrapper-Invocation.
  - Das Runbook beschreibt den produktiven Gate-Standard nur fuer den dedizierten Dev-Workhorse-Pfad.
- Tests:
  - Positivtest fuer Gate-Ausgabe mit fester Modellzuordnung und Kostenbasis
  - Negativtest fuer fehlende Modellzuordnung
  - Negativtest fuer fehlende Kostenbasis
  - Regressionstest fuer lokalen Codex-only Ausgang bei `1`
- Model: 5.4
- Reason: Der produktive Hauptpfad wird erst im Alltag nutzbar, wenn die Wahl `2 = OR-Arbeitspferd` nicht abstrakt bleibt, sondern sofort das feste Zielmodell und die erwartete Kostenbasis sichtbar macht.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC25.2_final_audit.md` dokumentiert. Die sichtbare Gate-Schicht des produktiven Dev-Workhorse-Hauptpfads ist damit task-scharf abgeschlossen: der dedizierte Operator-Block zeigt jetzt pro erlaubter Arbeitsklasse das feste empfohlene OR-Modell aus dem versiegelten `TASK-SPEC25.1`-Contract plus die Pre-Call-Kostenbasis mit Estimate- und Confidence-Pflichtfeldern sichtbar an, waehrend fehlende Pflichtdaten weiter fail-closed vor jeder Wrapper- oder Dispatcher-Invocation blockieren. Spec 25 bleibt bewusst offen, weil `TASK-SPEC25.3` die produktive bounded Runtime und den explizit Codex-owned Abschluss noch separat umsetzen muss.

### TASK-SPEC25.3 Route the productive Dev-workhorse main path only into bounded write/apply execution with explicit Codex-owned acceptance
- Ziel: Den dedizierten produktiven Dev-Workhorse-Pfad so an die vorhandenen bounded Ausfuehrungsbausteine anbinden, dass genau die ersten erlaubten bounded Schreib- und Umsetzungsarbeitsklassen produktiv laufen koennen und jeder Abschluss explizit Codex-owned bleibt.
- Scope: Dispatcher- und Runner-Anbindung nur fuer die ersten erlaubten bounded Schreib-/Umsetzungsklassen, file-first Artefakte, lokale Validierung, sichtbarer Accept-/Reject-/Fallback-Ausgang und keine Rueckausweitung auf gemischte Review-Pfade.
- Files:
  - documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py
  - documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py
  - documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
- Steps:
  - Den dedizierten produktiven Runner nur an die ersten erlaubten bounded Schreib- und Umsetzungsbausteine anbinden.
  - Sicherstellen, dass jedes delegierte Ergebnis in einem sichtbaren Codex-owned `accept`, `reject`, `fallback` oder `manual review`-Ausgang endet.
  - File-first Ergebnisartefakte, lokale Validierung und Abschlussstatus fuer diesen Hauptpfad als Pflichtausgang beibehalten.
  - Explizit absichern, dass keine gemischten Assist-only- oder Review-Klassen still in diesen produktiven Hauptpfad zurueckrutschen.
- Acceptance Criteria:
  - Der dedizierte produktive Dev-Workhorse-Pfad kann genau die ersten erlaubten bounded Schreib- und Umsetzungsarbeitsklassen produktiv ausfuehren.
  - Jedes delegierte Ergebnis endet in einem klaren Codex-owned Abschlussstatus.
  - File-first Artefakte und lokale Validierung bleiben fuer akzeptierte und nicht akzeptierte Laeufe sichtbar erhalten.
  - Gemischte Review-/Assist-only-Klassen erhalten durch diese Slice keinen stillen produktiven Hauptpfad-Einstieg.
- Tests:
  - Positivtest fuer die erste erlaubte bounded Patch-/Umsetzungsklasse
  - Positivtest fuer die zweite erlaubte bounded Patch-/Umsetzungsklasse
  - Negativtest fuer einen out-of-scope oder scope-escapenden Ergebnisfall
  - Negativtest fuer eine nicht erlaubte Review-/Assist-only-Klasse im produktiven Hauptpfad
- Model: 5.4
- Reason: Diese Slice ist der eigentliche Produktivkern der neuen Hauptpfad-Architektur und sorgt dafuer, dass OR als Arbeitspferd echte bounded Schreibarbeit uebernehmen kann, waehrend Codex sichtbar die letzte Kontrolle behaelt.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC25.3_final_audit.md` dokumentiert. Die produktive bounded Runtime des Dev-Workhorse-Hauptpfads ist damit task-scharf abgeschlossen: der dedizierte produktive Runner bleibt auf genau `execution_patch_candidate` und `execution_write_apply_candidate` begrenzt, bindet das erfolgreiche Gate-Modell run-scoped einmal pro Lauf und verwendet dieselbe kanonische Modellidentitaet unveraendert fuer Dispatcher und Telemetrie weiter, waehrend alle Abschlusszustaende explizit Codex-owned und reviewbar bleiben. Damit ist Spec 25 insgesamt abgeschlossen und als DONE nach `documentation/SPEC/Spec Done/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md` ueberfuehrt, ohne Produktionsrouting, kanonische Routing-Tabellen-Aktivierung, globale OR-Freigabe, Git- oder Release-Autoritaet zu aktivieren.

## Spec 25 Closeout

- Overall Status: DONE
- Final Audit Chain:
  - `documentation/tasks/TASK-SPEC25.1_final_audit.md` - PASS
  - `documentation/tasks/TASK-SPEC25.2_final_audit.md` - PASS
  - `documentation/tasks/TASK-SPEC25.3_final_audit.md` - PASS
- Spec Location: `documentation/SPEC/Spec Done/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md`
- Completion Summary: Der produktive Dev-Workhorse-Hauptpfad ist jetzt vollstaendig als eng gebundener Zwei-Klassen-Pfad abgeschlossen. Er kombiniert den versiegelten festen Modell-Contract, die sichtbare Gate-Schicht mit Pre-Call-Kostenbasis und den bounded produktiven Runtime-Pfad mit explizit Codex-owned Accept-/Reject-/Fallback-/Manual-Review-Abschluss. Es wurde keine breite Skill-Aktivierung, kein Produktionsrouting und keine globale OR-Autoritaet freigegeben.

@janus-task-breakdown
Spec: documentation/SPEC/Spec Done/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Task: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Backlog Item: N/A
Target Task: TASK-SPEC25.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF
