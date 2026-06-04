# BACKLOG-102 Task Spec - Gemini-Streaming-Kosten erscheinen im DeepDive als Attributionsluecke

## Source Backlog Item

BACKLOG-102 - Gemini-Streaming-Kosten erscheinen im DeepDive als Attributionsluecke

## Problem / Goal

Im Gemini-DeepDive erscheint fuer Juni 2026 eine sichtbare Attributionsluecke von 0,2891 EUR, obwohl die zugrunde liegenden Kostenzeilen bereits in der Datenbank vorhanden sind. Ziel ist, den Gemini-Streaming-Kostenpfad so zu korrigieren, dass neue Konversationskosten entweder mit konsistenten Attributionsfeldern persistiert oder nicht doppelt als unattribuierte Zusatzzeilen geschrieben werden.

## Scope

- Den Gemini-relevanten Streaming-Kostenpersistenzpfad rund um `stream_final_usage=1` untersuchen.
- Den Abgleich zwischen Gemini-Gateway-Attributionspersistenz und allgemeiner Streaming-Kostenpersistenz klarziehen.
- Sicherstellen, dass neue Gemini-Konversationskosten nicht mehr als kuenstliche `attribution_gap`-Restposten im DeepDive auftauchen.
- Eine gezielte Regression-Absicherung fuer den betroffenen Kosten-/Attributionspfad ergaenzen.

## Acceptance Criteria

- Neue Gemini-Streaming-Kosten werden nicht mehr als unattribuierte Legacy-Zeilen ohne `attribution_request_id` gespeichert.
- Der relevante Persistenzpfad verwendet konsistente Gemini-Attributionsfelder oder verhindert eine Doppelpersistenz derselben Anfrage.
- Der DeepDive zeigt fuer neu erzeugte Gemini-Konversationseintraege keine kuenstliche Attributionsluecke mehr aus dem `stream_final_usage=1`-Pfad.
- Historische echte Legacy-Restposten bleiben nur dort sichtbar, wo sie fachlich wirklich nicht rekonstruierbar sind.
- Mindestens ein fokussierter Test deckt den Gemini-Streaming-/Attributionspfad gegen Regression ab.

## Verification Plan

- Den betroffenen Gemini-Streaming-Pfad mit gezielter Code-/Testinspektion reproduzierbar eingrenzen.
- Fokussierte Tests fuer Kostenpersistenz und DeepDive-Attribution ausfuehren.
- Pruefen, dass neue Gemini-Konversationskosten im relevanten Pfad mit Attributionsfeldern erscheinen oder nicht doppelt geschrieben werden.
- Den DeepDive-Status fuer den betroffenen Fall nach dem Fix gegen die Anomalie `Attributionsluecke` verifizieren.

## Out Of Scope

- Breitere DeepDive-UX-Umbauten ausserhalb des konkreten Gemini-Attributionsfehlers.
- Historische Vollreparatur aller bereits vorhandenen Mai-/Legacy-Kostenbloecke.
- Allgemeine Preis- oder Modellpolitik-Aenderungen ausserhalb des betroffenen Persistenzpfads.

## Implementation Metadata

- **Implementation Status:** DONE
- **Completed At:** 2026-06-04
- **Final Audit:** `documentation/test-runs/BACKLOG-102_final_audit.md` (PASS)
- **Validation Evidence:** `python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q` PASS (10/10)
- **Changed Files:** `backend/services/orchestrator/execution_engine.py`, `backend/tests/test_cost_token_tracking_completeness.py`
