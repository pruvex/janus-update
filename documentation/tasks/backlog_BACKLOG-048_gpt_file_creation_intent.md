# BACKLOG-048: GPT-5.4-nano File-Creation Intent ohne Tool-Ausführung

## Aufgabe
Debug und Fix des GPT-5.4-nano File-Creation Intent ohne Tool-Ausführung.

## Problem
GPT-5.4-nano antwortet mit "Verstanden." auf File-Creation-Intent ohne Tool-Ausführung oder Datei-Keywords. Gemini für denselben Prompt führt Tool erfolgreich aus.

## Erwartetes Verhalten
File-Creation-Intent triggert Filesystem-Tool und Antwort enthält Datei-Keywords wie "Dateien", "Ordner".

## Tatsächliches Verhalten
GPT antwortet nur mit "Verstanden." ohne Tool-Call. TC-001-GEMINI mit gleichem Prompt PASS mit korrekter Tool-Ausführung.

## Reproduktion
TEST-RUN-2026-05-15-011, TC-001-GPT vs TC-001-GEMINI, Prompt "Erstell mir einen Ordner fuer Projekt Alpha".

## Betroffener Bereich
Intent Routing / GPT-5.4-nano Tool-Selection / Skill Selector

## Nachweise
documentation/test-results/TEST-RUN-2026-05-15-011/TC-001-GPT_evidence.json, TC-001-GEMINI_evidence.json (Gemini PASS)

## Akzeptanzkriterien
- [ ] GPT-5.4-nano führt File-Creation-Intent korrekt aus
- [ ] Tool-Ausführung ist erkennbar
- [ ] Antwort enthält Datei-Keywords
- [ ] Provider-Parity mit Gemini ist erreicht
- [ ] TC-001-GPT im Retest PASS

## Technische Hinweise
Provider-Parity-Problem: Intent-Engine oder Tool-Selection muss untersucht werden. Prüfe Skill Selector und Tool-Selection-Logik für GPT-5.4-nano.

## Wichtigkeit
MEDIUM

## Umsetzungsrisiko
MEDIUM

## Aufwand
M
