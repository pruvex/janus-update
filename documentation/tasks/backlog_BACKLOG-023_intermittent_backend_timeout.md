# Task: BACKLOG-023 – Intermittierender Backend Timeout bei Janus Live-Chat Retest

## Backlog Item

- **ID:** BACKLOG-023
- **Typ:** BUG
- **Status:** READY
- **Quelle:** TestRun
- **TestRun:** TEST-RUN-2026-05-11-005-RETEST-002

## Kurzbeschreibung

Janus beantwortet aufeinanderfolgende Live-Chat-Anfragen im automatisierten Retest nicht zuverlässig; TC-001 besteht, TC-002 läuft in einen Backend-/Chat-Timeout.

## Erwartetes Verhalten

Janus verarbeitet aufeinanderfolgende Chat-/Intent-Anfragen stabil oder liefert einen kontrollierten Timeout-/Fallback-Hinweis.

## Tatsächliches Verhalten

Nach erfolgreichem Config-Fix und Backend-Neustart schlägt TC-002 durch Backend-/Chat-Timeout fehl; 15 weitere TestCases wurden nicht ausgeführt.

## Reproduktion / Kontext

TEST-RUN-2026-05-11-005-RETEST-002; TC-001 PASS nach 23.9s; TC-002 FAIL nach 50.5s; Runner: tests/e2e/generated/TEST-RUN-2026-05-11-005.live.spec.js

## Betroffener Bereich

Backend Chat Processing / Intent Routing / Runtime Stability / Test Infrastructure

## Nachweise

documentation/test-results/TEST-RUN-2026-05-11-005-RETEST-002_results.md; Backend-/Network-Evidence noch zu ergänzen

## Akzeptanzkriterien

- [ ] Janus verarbeitet aufeinanderfolgende Chat-Anfragen stabil ohne Timeout
- [ ] Backend-Logs zeigen keine Fehler bei aufeinanderfolgenden Anfragen
- [ ] Rate-Limit oder Connection-Pool-Probleme sind behoben
- [ ] Live-Test-Pipeline kann alle 17 TestCases erfolgreich ausführen

## Fehlende Informationen

Backend-/Network-Evidence noch zu ergänzen

## Notizen

Config-Fix und Backend-Neustart verbesserten die Situation (TC-001 PASS), aber intermittierendes Timeout besteht weiterhin (TC-002 FAIL). Ursache könnte Rate-Limit, Connection-Pool-Problem oder Backend-Resource-Issue sein.

## Routing

- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Wiederholtes/intermittierendes Timeout blockiert die Live-Test-Pipeline; Debug muss Ursache zwischen Backend Runtime, Chat Processing, API-Key/Auth, Provider-/Rate-Limit und Test-Infrastruktur isolieren.
- **Routing confidence:** MEDIUM
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-05-11
- **Recommended next skill:** SKILL 3

## Bewertung

- **Wichtigkeit:** MEDIUM
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** M
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW
