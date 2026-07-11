# FEATURE DESIGN HANDOFF - Allgemeines semantisches, parameterisiertes Routine-Reuse fuer mehrschrittige Routinen

## SOURCE

- Backlog Item: `BACKLOG-123`
- Entry Point: `SPEC_PIPELINE_START`
- Source of Truth: `documentation/backlog/BACKLOG.md`
- Suggested Save Path: `documentation/Planned Features/backlog_BACKLOG-123_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md`

## LATEST DECISION SUMMARY

Feature Name: Allgemeines semantisches, parameterisiertes Routine-Reuse fuer mehrschrittige Routinen
Primary Goal: Gespeicherte mehrschrittige Routinen sollen aus natuerlicher Sprache wiederverwendet werden koennen, auch wenn die neue Anfrage frische konkrete Parameter mitbringt.
User Problem: Das aktuelle Routine-Reuse ist produktseitig auf enge Sonderfaelle begrenzt. Nutzer muessen dadurch entweder exakt passende Anfragen wiederholen oder profitieren nur bei einzelnen fest verdrahteten Skill-Kombinationen von gespeicherten Routinen.
User Value: Janus fuehlt sich bei wiederkehrenden Multi-Step-Aufgaben deutlich intelligenter und nuetzlicher an, weil gespeicherte Routinen nicht nur starr wiederholt, sondern passend zur neuen Anfrage wiederverwendet werden.
Primary Target Surface: bestehende Chat-basierte Routinenutzung im normalen Janus-Gespraech
Existing or New Surface: bestehend
Existence Confirmation: confirmed by user
User Trigger: eine natuerliche Anfrage, die semantisch zu einer bereits gespeicherten mehrschrittigen Routine passt, aber neue konkrete Parameter wie Datum, Stadt oder Route enthaelt
Success Behavior: Janus erkennt die passende gespeicherte Routine ueber ihre mehrschrittige Struktur, bindet die angefragten frischen Parameter sicher neu ein, fuehrt die Routine transparent aus und sagt weiterhin knapp, dass eine passende gespeicherte Routine genutzt wurde.
Failure Behavior: Wenn keine hinreichend sichere Uebereinstimmung besteht oder erforderliche Parameter fehlen, widerspruechlich sind oder nicht verlaesslich extrahiert werden koennen, fuehrt Janus die alte Routine nicht blind aus und faellt fail-closed auf den normalen Anfragepfad zurueck.
User Action Surface: keine neue Pflichtaktion im Chat; Reuse bleibt automatisch und transparent, ohne dass Nutzer Routinenamen kennen oder bestaetigen muessen
Data / Persistence: bestehende gespeicherte Routinen bleiben die Persistenzbasis; neu ist nur das Produktverhalten fuer semantisches Matching und frische Parameterbindung bei der Wiederverwendung
Security / Privacy: keine aggressive Vermutung von Parametern, kein blindes Wiederverwenden alter Werte bei mehrdeutigen oder abweichenden Anfragen, keine stillen Seiteneffekte ausser der ohnehin erlaubten Routinenutzung
Edge Cases: gleiche Skill-Familie aber andere Parameterbedeutung; teilweise passende Mehrfachroutinen; fehlende Orts- oder Datumsangaben; explizit widerspruechliche Angaben; bestehender `calendar+weather`-Pfad darf nicht regressieren; spaetere weitere Skill-Familien muessen moeglich bleiben
Out of Scope: allgemeine Embedding-/Vektorsuche fuer Routinen; freies fuzzy Matching ohne klare Skill- und Constraint-Grenzen; neue UI fuer Routinenverwaltung; Umsetzung weiterer Pilotfamilien ueber den ersten abgesicherten Product Slice hinaus ohne separate Evidenz
Routing Decision: FULL FEATURE PIPELINE
Routing Reason: Das ist ein produktrelevantes Verhaltens-Upgrade mit mehreren Entscheidungen zu Matching-Grenzen, Parameterbindung, Fail-Closed-Verhalten, Pilotumfang und Regressionsschutz fuer bestehendes Routine-Reuse.
Recommended Next Skill: janus-spec-generator

## BOUNDED PRODUCT DECISIONS

- Der erste verpflichtende Pilotfall ist `calendar.list_events + system.routing`.
- Der bestehende `calendar.list_events + system.weather`-Pfad bleibt Referenz und Regression-Watchpoint, aber nicht die einzige Zielkombination.
- Reuse wird nicht ueber freien Aehnlichkeitsscore definiert, sondern ueber klare mehrschrittige Struktur plus skill-spezifische Constraint-Familien.
- Frische Nutzerparameter haben Vorrang vor alten gespeicherten Laufwerten.
- Bei unsicherer oder widerspruechlicher Parameterauslegung gilt fail-closed statt heuristischer Ausfuehrung.

## HANDOFF_SCOPE

- Backlog Item: `BACKLOG-123`
- Entry Point: `SPEC_PIPELINE_START`
- Required Artifact: `documentation/Planned Features/backlog_BACKLOG-123_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md`
- Required Next Skill: `janus-spec-generator`
- Evidence Paths:
  - `documentation/tasks/TASK-WORKFLOW-M3.4_execution_result.md`
  - `documentation/tasks/TASK-SPEC29.2_debug_result_passive_promotion_signature_drift_2026-07-09.md`
  - `documentation/tasks/TASK-SPEC29.2_debug_result_passive_promotion_signature_drift_cursor_fix_2026-07-09.md`
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/services/workflow/routine_runner.py`
- Dropped Context:
  - Einzelne Spec-29.2 Debug-Loops fuer Gemini-Routing und Candidate-Promotion sind nicht mehr der Hauptgegenstand dieses Artefakts.
  - `calendar+routing` wird hier absichtlich als Pilot und nicht als finale Produktgrenze behandelt.

## Next Skill Copy Prompts

```text
NEXT: janus-spec-generator
NEW_CHAT_HANDOFF
Spec Seed: documentation/Planned Features/backlog_BACKLOG-123_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
Backlog Item: BACKLOG-123
```
