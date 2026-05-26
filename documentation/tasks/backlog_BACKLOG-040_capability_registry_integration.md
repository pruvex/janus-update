# Task: Capability-Registry-Integration Fix

## Backlog-Item
- **ID:** BACKLOG-040
- **Titel:** Capability-Registry-Integration: Modelle listen Tools auf statt auf Registry zu verweisen
- **Typ:** BUG
- **Wichtigkeit:** MEDIUM
- **Umsetzungsrisiko:** LOW
- **Aufwand:** S

## Problem
Sowohl GPT als auch Gemini listen bei "Welche Tools hast du?" direkt Tools auf statt auf die Capability-Registry zu verweisen. GPT listet einige Tools, Gemini listet alle Tools.

## Erwartetes Verhalten
Bei Tool/Capability-Fragen sollte Janus auf die Capability-Registry verweisen oder eine strukturierte Übersicht geben, nicht eine rohe Tool-Liste.

## Tatsächliches Verhalten
- GPT: "Ich habe Zugriff auf folgende Tool-Gruppen/Schnittstellen (Auszug nach Fähigkeiten): Wissen/Dokumente, Dateien/Filesystem, Kalender"
- Gemini: Listet alle 30+ Tools auf (calendar, communication, contacts, filesystem, knowledge, memory, system, video)

## Betroffener Bereich
Capability Registry / System Prompt / Tool-Response-Format

## Nachweise
- documentation/test-results/TEST-RUN-2026-05-15-003/INT-002-GPT_evidence.json
- documentation/test-results/TEST-RUN-2026-05-15-003/INT-002-GEMINI_evidence.json

## Akzeptanzkriterien
- [ ] Bei Tool/Capability-Fragen verweist Janus auf die Capability-Registry
- [ ] Keine rohe Tool-Liste wird angezeigt
- [ ] Strukturierte Übersicht oder Capability-Registry-Referenz wird verwendet
- [ ] Sowohl GPT als auch Gemini zeigen gleiches Verhalten (Provider Parity)

## Umsetzungsansatz
System-Prompt-Optimierung mit klarer Scope (Capability-Registry-Referenz statt Tool-Liste), keine Architekturänderung.

## TestRun
TEST-RUN-2026-05-15-003
